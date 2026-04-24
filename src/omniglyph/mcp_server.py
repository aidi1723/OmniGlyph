import json
import sys
from typing import Any, TextIO

from omniglyph.config import settings
from omniglyph.normalization import compact_normalize, normalize_tokens
from omniglyph.repository import GlyphRepository

JSONRPC_VERSION = "2.0"


def build_tools_list() -> list[dict[str, Any]]:
    return [
        {
            "name": "lookup_glyph",
            "description": "Look up a single glyph in the local OmniGlyph symbol fact base.",
            "inputSchema": {
                "type": "object",
                "properties": {"char": {"type": "string", "description": "Exactly one Unicode character to look up."}},
                "required": ["char"],
            },
        },
        {
            "name": "lookup_term",
            "description": "Look up a private or curated lexical/domain term.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Term text or alias to look up."}},
                "required": ["text"],
            },
        },
        {
            "name": "normalize_tokens",
            "description": "Normalize glyphs and known domain terms into canonical IDs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tokens": {"type": "array", "items": {"type": "string"}},
                    "mode": {"type": "string", "enum": ["full", "compact"]},
                },
                "required": ["tokens"],
            },
        },
    ]


def handle_mcp_request(request: dict[str, Any], repository: GlyphRepository | None = None) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    glyph_repository = repository or GlyphRepository(settings.sqlite_path)

    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "omniglyph", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _result(request_id, {"tools": build_tools_list()})

    if method == "tools/call":
        params = request.get("params") or {}
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if tool_name == "lookup_glyph":
            char = arguments.get("char")
            if not isinstance(char, str) or len(char) != 1:
                return _error(request_id, -32602, "lookup_glyph requires exactly one Unicode character")
            record = glyph_repository.find_by_glyph(char)
            if record is None:
                return _result(request_id, {"content": [{"type": "text", "text": f"Glyph not found: {char}"}], "isError": True})
            return _result(request_id, {"content": [{"type": "json", "json": record}]})

        if tool_name == "lookup_term":
            text = arguments.get("text")
            if not isinstance(text, str) or not text.strip():
                return _error(request_id, -32602, "lookup_term requires non-empty text")
            record = glyph_repository.find_term(text)
            if record is None:
                return _result(request_id, {"content": [{"type": "text", "text": f"Term not found: {text}"}], "isError": True})
            return _result(request_id, {"content": [{"type": "json", "json": record}]})

        if tool_name == "normalize_tokens":
            tokens = arguments.get("tokens")
            mode = arguments.get("mode", "full")
            if not isinstance(tokens, list) or not all(isinstance(item, str) for item in tokens):
                return _error(request_id, -32602, "normalize_tokens requires a list of string tokens")
            results = normalize_tokens(glyph_repository, tokens)
            payload = compact_normalize(results) if mode == "compact" else {"results": results}
            return _result(request_id, {"content": [{"type": "json", "json": payload}]})

        return _error(request_id, -32601, f"Unknown tool: {tool_name}")

    return _error(request_id, -32601, f"Unknown method: {method}")


def serve_stdio(input_stream: TextIO = sys.stdin, output_stream: TextIO = sys.stdout) -> None:
    for line in input_stream:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
        except json.JSONDecodeError as exc:
            response = _error(None, -32700, f"Parse error: {exc.msg}")
        except Exception as exc:  # pragma: no cover - defensive stdio server boundary
            response = _error(None, -32603, f"Internal error: {exc}")
        if response is not None:
            output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
            output_stream.flush()


def main() -> None:
    serve_stdio()


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": {"code": code, "message": message}}

if __name__ == "__main__":
    main()
