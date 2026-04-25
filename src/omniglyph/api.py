from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from omniglyph import __version__
from omniglyph.config import settings
from omniglyph.guardrail import validate_output_terms
from omniglyph.normalization import compact_normalize, normalize_tokens
from omniglyph.repository import GlyphRepository


class NormalizeRequest(BaseModel):
    tokens: list[str]


class GuardrailRequest(BaseModel):
    terms: list[str]


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

    @app.post("/api/v1/normalize")
    def normalize(request: NormalizeRequest, mode: str = Query("full")) -> dict:
        results = normalize_tokens(glyph_repository, request.tokens)
        if mode == "compact":
            return compact_normalize(results)
        return {"results": results}


    @app.post("/api/v1/guardrail/validate-output")
    def validate_output(request: GuardrailRequest) -> dict:
        return validate_output_terms(glyph_repository, request.terms)

    return app


app = create_app()
