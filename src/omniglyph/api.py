import hmac
import os
from typing import Any, Literal, cast

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from omniglyph import __version__
from omniglyph.audit import build_audit_event
from omniglyph.code_linter import scan_text
from omniglyph.config import settings
from omniglyph.explanation import explain_code_security, explain_for_audit, explain_glyph, explain_term
from omniglyph.guardrail import enforce_grounded_output, validate_output_terms
from omniglyph.json_input import ensure_finite_json
from omniglyph.language_security import enforce_intent_manifest, scan_language_input, scan_output_dlp
from omniglyph.lexicon_pack import ensure_allowed_pack_path, validate_lexicon_pack
from omniglyph.limits import TextLimitError
from omniglyph.normalization import compact_normalize, normalize_tokens
from omniglyph.policy_pack import ensure_allowed_policy_pack_path, load_policy_pack, validate_policy_pack
from omniglyph.repository import GlyphRepository


class NormalizeRequest(BaseModel):
    tokens: list[str]


class GuardrailRequest(BaseModel):
    terms: list[str]


class GuardrailEnforceRequest(GuardrailRequest):
    actor_id: str | None = None
    policy: dict | None = None


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
    manifest: object | None = None
    policy_pack_path: str | None = None
    actor_role: str | None = None
    parameters: dict | None = None


class LexiconValidatePackRequest(BaseModel):
    path: str


class PolicyValidatePackRequest(BaseModel):
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

    @app.middleware("http")
    async def require_api_token(request, call_next):
        if request.url.path == "/api/v1/health":
            return await call_next(request)
        expected = os.environ.get("OMNIGLYPH_API_TOKEN", "").strip()
        header = request.headers.get("authorization", "")
        if not expected:
            return JSONResponse(status_code=401, content={"detail": "OMNIGLYPH_API_TOKEN is not configured"})
        if not hmac.compare_digest(header.encode(), f"Bearer {expected}".encode()):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)

    @app.exception_handler(TextLimitError)
    async def text_limit_handler(_request, exc: TextLimitError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/api/v1/health")
    def health() -> dict:
        return {
            "status": "ok",
            "service": "omniglyph",
            "version": __version__,
            "database": {"exists": glyph_repository.sqlite_path.exists()},
        }

    @app.get("/api/v1/glyph")
    def get_glyph(char: str = Query(...)) -> dict:
        if len(char) != 1:
            raise HTTPException(status_code=400, detail="char must contain exactly one Unicode character")
        record = glyph_repository.find_by_glyph(char)
        if record is None:
            raise HTTPException(status_code=404, detail="glyph not found")
        return cast(dict, _strip_local_paths(record))


    @app.get("/api/v1/term")
    def get_term(text: str = Query(..., min_length=1)) -> dict:
        record = glyph_repository.find_term(text)
        if record is None:
            raise HTTPException(status_code=404, detail="term not found")
        return _redact_secret_term(record)

    @app.get("/api/v1/lexicon/namespaces")
    def list_lexicon_namespaces_endpoint() -> dict:
        return {"schema": "omniglyph.lexicon_namespaces:0.1", "namespaces": glyph_repository.list_lexical_namespaces()}

    @app.post("/api/v1/lexicon/validate-pack")
    def validate_lexicon_pack_endpoint(request: LexiconValidatePackRequest) -> dict:
        _validate_allowed_pack_path(request.path)
        return validate_lexicon_pack(request.path)

    @app.post("/api/v1/policy/validate-pack")
    def validate_policy_pack_endpoint(request: PolicyValidatePackRequest) -> dict:
        _validate_allowed_policy_pack_path(request.path)
        return validate_policy_pack(request.path)

    @app.get("/api/v1/explain/glyph")
    def explain_glyph_endpoint(char: str = Query(...)) -> dict:
        if len(char) != 1:
            raise HTTPException(status_code=400, detail="char must contain exactly one Unicode character")
        return cast(dict, _strip_local_paths(explain_glyph(glyph_repository, char)))

    @app.get("/api/v1/explain/term")
    def explain_term_endpoint(text: str = Query(..., min_length=1)) -> dict:
        return _redact_term_explanation(glyph_repository, text)

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
        manifest_provided = "manifest" in request.model_fields_set
        policy_pack_provided = request.policy_pack_path is not None
        if manifest_provided == policy_pack_provided:
            raise HTTPException(status_code=400, detail="provide exactly one of manifest or policy_pack_path")
        manifest = request.manifest
        if request.policy_pack_path is not None:
            _validate_allowed_policy_pack_path(request.policy_pack_path)
            try:
                manifest = load_policy_pack(request.policy_pack_path).to_manifest()
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            ensure_finite_json(request.parameters or {})
            ensure_finite_json(manifest)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return enforce_intent_manifest(request.intent_id, manifest, actor_role=request.actor_role, parameters=request.parameters)

    @app.post("/api/v1/audit/explain")
    def audit_explain_endpoint(request: AuditExplainRequest) -> dict:
        try:
            result, action = explain_for_audit(glyph_repository, request.kind, request.text, request.source_name or "<api-text>")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if request.kind == "term":
            result = _redact_term_explanation(glyph_repository, request.text)
        return {"result": _strip_local_paths(result), "audit": build_audit_event(request.actor_id, action, result)}

    @app.post("/api/v1/audit/security-scan")
    def audit_security_scan_endpoint(request: AuditSecurityScanRequest) -> dict:
        result = scan_text(request.text, source_name=request.source_name)
        return {"result": result, "audit": build_audit_event(request.actor_id, "scan_unicode_security", result)}

    @app.post("/api/v1/normalize")
    def normalize(request: NormalizeRequest, mode: str = Query("full")) -> dict:
        results = [_redact_normalized_term(glyph_repository, item) for item in normalize_tokens(glyph_repository, request.tokens)]
        if mode == "compact":
            return compact_normalize(results)
        return {"results": results}


    @app.post("/api/v1/guardrail/validate-output")
    def validate_output(request: GuardrailRequest) -> dict:
        return validate_output_terms(glyph_repository, request.terms)

    @app.post("/api/v1/guardrail/enforce-output")
    def enforce_output(request: GuardrailEnforceRequest) -> dict:
        try:
            ensure_finite_json(request.policy or {})
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return enforce_grounded_output(glyph_repository, request.terms, actor_id=request.actor_id, policy=request.policy)

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
        raise HTTPException(status_code=403, detail="OMNIGLYPH_LEXICON_PACK_ROOT is required")
    try:
        ensure_allowed_pack_path(path, settings.lexicon_pack_root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _validate_allowed_policy_pack_path(path: str) -> None:
    if settings.policy_pack_root is None:
        raise HTTPException(status_code=403, detail="OMNIGLYPH_POLICY_PACK_ROOT is required")
    try:
        ensure_allowed_policy_pack_path(path, settings.policy_pack_root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _redact_secret_term(record: dict) -> dict:
    if record.get("sensitivity") != "secret":
        return record
    redacted = dict(record)
    redacted["definition"] = None
    redacted["traits"] = {}
    redacted["definition_redacted"] = True
    return redacted


def _redact_term_explanation(repository: GlyphRepository, text: str) -> dict:
    payload = explain_term(repository, text)
    record = repository.find_term(text)
    if record is None or record.get("sensitivity") != "secret":
        return payload
    for item in payload.get("lexical") or []:
        if isinstance(item, dict):
            item["definition"] = None
            item["traits"] = {}
    limits = list(payload.get("limits") or [])
    limits.append("Secret term definitions are omitted from HTTP responses.")
    payload["limits"] = limits
    return payload


def _redact_normalized_term(repository: GlyphRepository, item: dict) -> dict:
    if item.get("type") == "glyph" or item.get("status") != "matched":
        return item
    record = repository.find_term(item["input"])
    if record is None or record.get("sensitivity") != "secret":
        return item
    redacted = dict(item)
    summary = dict(item.get("summary") or {})
    summary["definition"] = None
    summary["traits"] = {}
    redacted["summary"] = summary
    return redacted


def _strip_local_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_local_paths(item) for key, item in value.items() if key != "local_path"}
    if isinstance(value, list):
        return [_strip_local_paths(item) for item in value]
    return value
