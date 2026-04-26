from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Literal

from omniglyph import __version__
from omniglyph.audit import build_audit_event
from omniglyph.code_linter import scan_text
from omniglyph.config import settings
from omniglyph.explanation import explain_code_security, explain_glyph, explain_term
from omniglyph.guardrail import enforce_grounded_output, validate_output_terms
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
        return {"status": "ok", "service": "omniglyph", "version": __version__}

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

    @app.post("/api/v1/audit/explain")
    def audit_explain_endpoint(request: AuditExplainRequest) -> dict:
        result, action = _explain_for_audit(glyph_repository, request.kind, request.text, request.source_name)
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


app = create_app()


def _explain_for_audit(repository: GlyphRepository, kind: str, text: str, source_name: str | None) -> tuple[dict, str]:
    if kind == "glyph":
        if len(text) != 1:
            raise HTTPException(status_code=400, detail="glyph audit text must contain exactly one Unicode character")
        return explain_glyph(repository, text), "explain_glyph"
    if kind == "term":
        if not text.strip():
            raise HTTPException(status_code=400, detail="term audit text must be non-empty")
        return explain_term(repository, text), "explain_term"
    if kind == "code":
        return explain_code_security(text, source_name=source_name or "<api-text>"), "explain_code_security"
    raise HTTPException(status_code=400, detail=f"unsupported audit kind: {kind}")
