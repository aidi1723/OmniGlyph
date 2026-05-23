from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from omniglyph import __version__
from omniglyph.audit import build_audit_event
from omniglyph.code_linter import scan_text
from omniglyph.config import settings
from omniglyph.explanation import explain_code_security, explain_for_audit, explain_glyph, explain_term
from omniglyph.guardrail import enforce_grounded_output, validate_output_terms
from omniglyph.language_security import enforce_intent_manifest, scan_language_input, scan_output_dlp
from omniglyph.lexicon_pack import validate_lexicon_pack
from omniglyph.normalization import compact_normalize, normalize_tokens
from omniglyph.repository import GlyphRepository


class NormalizeRequest(BaseModel):
    tokens: list[str]


class GuardrailRequest(BaseModel):
    terms: list[str]


class GuardrailEnforceRequest(GuardrailRequest):
    actor_id: str | None = None


class SecurityScanRequest(BaseModel):
    text: str
    source_name: str = "<api-text>"


class LanguageInputScanRequest(BaseModel):
    text: str
    source_name: str = "<api-input>"


class OutputDlpScanRequest(BaseModel):
    text: str
    secret_terms: list[str] = Field(default_factory=list)
    include_lexicon_secrets: bool = False
    source_name: str = "<api-output>"


class IntentEnforceRequest(BaseModel):
    intent_id: str
    manifest: dict
    actor_role: str | None = None
    parameters: dict | None = None


class LexiconValidatePackRequest(BaseModel):
    path: str


class AuditExplainRequest(BaseModel):
    actor_id: str
    kind: Literal["glyph", "term", "code"]
    text: str
    source_name: str | None = None


class AuditSecurityScanRequest(SecurityScanRequest):
    actor_id: str


def create_app(repository: GlyphRepository | None = None) -> FastAPI:
    app = FastAPI(title="OmniGlyph API", version=__version__)
    glyph_repository = repository or GlyphRepository(settings.sqlite_path)
    glyph_repository.initialize()


    @app.get("/api/v1/health")
    def health() -> dict:
        return {
            "status": "ok",
            "service": "omniglyph",
            "version": __version__,
            "database": {
                "path": str(glyph_repository.sqlite_path),
                "exists": glyph_repository.sqlite_path.exists(),
            },
        }

    @app.get("/api/v1/glyph")
    def get_glyph(char: str = Query(...)) -> dict:
        if len(char) != 1:
            raise HTTPException(status_code=400, detail="char must contain exactly one Unicode character")
        record = glyph_repository.find_by_glyph(char)
        if record is None:
            raise HTTPException(status_code=404, detail="glyph not found")
        return record


    @app.get("/api/v1/term")
    def get_term(text: str = Query(..., min_length=1)) -> dict:
        record = glyph_repository.find_term(text)
        if record is None:
            raise HTTPException(status_code=404, detail="term not found")
        return record

    @app.get("/api/v1/lexicon/namespaces")
    def list_lexicon_namespaces_endpoint() -> dict:
        return {"schema": "omniglyph.lexicon_namespaces:0.1", "namespaces": glyph_repository.list_lexical_namespaces()}

    @app.post("/api/v1/lexicon/validate-pack")
    def validate_lexicon_pack_endpoint(request: LexiconValidatePackRequest) -> dict:
        _validate_allowed_pack_path(request.path)
        return validate_lexicon_pack(request.path)

    @app.get("/api/v1/explain/glyph")
    def explain_glyph_endpoint(char: str = Query(...)) -> dict:
        if len(char) != 1:
            raise HTTPException(status_code=400, detail="char must contain exactly one Unicode character")
        return explain_glyph(glyph_repository, char)

    @app.get("/api/v1/explain/term")
    def explain_term_endpoint(text: str = Query(..., min_length=1)) -> dict:
        return explain_term(glyph_repository, text)

    @app.post("/api/v1/explain/code-security")
    def explain_code_security_endpoint(request: SecurityScanRequest) -> dict:
        return explain_code_security(request.text, source_name=request.source_name)

    @app.post("/api/v1/security/scan")
    def security_scan_endpoint(request: SecurityScanRequest) -> dict:
        return scan_text(request.text, source_name=request.source_name)

    @app.post("/api/v1/language-security/scan-input")
    def language_security_scan_input_endpoint(request: LanguageInputScanRequest) -> dict:
        return scan_language_input(request.text, source_name=request.source_name)

    @app.post("/api/v1/language-security/scan-output")
    def language_security_scan_output_endpoint(request: OutputDlpScanRequest) -> dict:
        secret_terms = list(request.secret_terms)
        if request.include_lexicon_secrets:
            secret_terms.extend(glyph_repository.list_secret_terms())
        return scan_output_dlp(request.text, secret_terms=secret_terms, source_name=request.source_name)

    @app.post("/api/v1/language-security/enforce-intent")
    def language_security_enforce_intent_endpoint(request: IntentEnforceRequest) -> dict:
        return enforce_intent_manifest(request.intent_id, request.manifest, actor_role=request.actor_role, parameters=request.parameters)

    @app.post("/api/v1/audit/explain")
    def audit_explain_endpoint(request: AuditExplainRequest) -> dict:
        try:
            result, action = explain_for_audit(glyph_repository, request.kind, request.text, request.source_name or "<api-text>")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"result": result, "audit": build_audit_event(request.actor_id, action, result)}

    @app.post("/api/v1/audit/security-scan")
    def audit_security_scan_endpoint(request: AuditSecurityScanRequest) -> dict:
        result = scan_text(request.text, source_name=request.source_name)
        return {"result": result, "audit": build_audit_event(request.actor_id, "scan_unicode_security", result)}

    @app.post("/api/v1/normalize")
    def normalize(request: NormalizeRequest, mode: str = Query("full")) -> dict:
        results = normalize_tokens(glyph_repository, request.tokens)
        if mode == "compact":
            return compact_normalize(results)
        return {"results": results}


    @app.post("/api/v1/guardrail/validate-output")
    def validate_output(request: GuardrailRequest) -> dict:
        return validate_output_terms(glyph_repository, request.terms)

    @app.post("/api/v1/guardrail/enforce-output")
    def enforce_output(request: GuardrailEnforceRequest) -> dict:
        return enforce_grounded_output(glyph_repository, request.terms, actor_id=request.actor_id)

    return app


_app: FastAPI | None = None


def get_app() -> FastAPI:
    """Lazy app singleton. Use this for programmatic access without side effects."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


# Module-level reference for uvicorn (`uvicorn omniglyph.api:app`).
# Uvicorn needs a concrete ASGI app at import time.
app: FastAPI = get_app()


def _validate_allowed_pack_path(path: str) -> None:
    if settings.lexicon_pack_root is None:
        return
    pack_path = Path(path).resolve()
    root = settings.lexicon_pack_root.resolve()
    if pack_path != root and root not in pack_path.parents:
        raise HTTPException(status_code=403, detail="lexicon pack path is outside OMNIGLYPH_LEXICON_PACK_ROOT")
