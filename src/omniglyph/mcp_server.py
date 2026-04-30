import json
import sys
from pathlib import Path
from typing import Any, TextIO

from omniglyph import __version__
from omniglyph.audit import build_audit_event
from omniglyph.code_linter import scan_text
from omniglyph.config import settings
from omniglyph.explanation import explain_code_security, explain_glyph, explain_term
from omniglyph.guardrail import enforce_grounded_output, validate_output_terms
from omniglyph.language_security import enforce_intent_manifest, scan_language_input, scan_output_dlp
from omniglyph.lexicon_pack import validate_lexicon_pack
from omniglyph.logos.loader import load_policy_file
from omniglyph.logos.validator import validate_action
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
            "name": "explain_glyph",
            "description": "Explain one Unicode character using the OmniGlyph Explanation Standard.",
            "inputSchema": {
                "type": "object",
                "properties": {"char": {"type": "string", "description": "Exactly one Unicode character to explain."}},
                "required": ["char"],
            },
        },
        {
            "name": "explain_term",
            "description": "Explain a lexical/domain term using the OmniGlyph Explanation Standard.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Term text or alias to explain."}},
                "required": ["text"],
            },
        },
        {
            "name": "explain_code_security",
            "description": "Explain Unicode source-code security findings using the OmniGlyph Explanation Standard.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Source code text to scan and explain."},
                    "source_name": {"type": "string", "description": "Optional source label for findings."},
                },
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
        {
            "name": "list_namespaces",
            "description": "List loaded lexical namespaces and their entry, alias, pack, and source summaries.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "validate_lexicon_pack",
            "description": "Validate an OmniGlyph Lexicon Pack directory with pack.json and terms.csv.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to a Lexicon Pack directory."},
                },
                "required": ["path"],
            },
        },
        {
            "name": "validate_output_terms",
            "description": "Validate generated output terms against the local fact base.",
            "inputSchema": {
                "type": "object",
                "properties": {"terms": {"type": "array", "items": {"type": "string"}}},
                "required": ["terms"],
            },
        },
        {
            "name": "validate_action_policy",
            "description": "Validate an agent action plan against a local LogosGate JSON policy file and return allow, warn, review, or block.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "policy_path": {"type": "string", "description": "Path to a local LogosGate JSON policy file."},
                    "text": {"type": "string", "description": "Agent action plan text to validate."},
                },
                "required": ["policy_path", "text"],
            },
        },
        {
            "name": "enforce_grounded_output",
            "description": "Apply strict source-grounding policy to generated output terms and return allow/block decision evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "terms": {"type": "array", "items": {"type": "string"}},
                    "actor_id": {"type": "string", "description": "Optional user, service, or agent identifier for audit evidence."},
                },
                "required": ["terms"],
            },
        },
        {
            "name": "scan_code_symbols",
            "description": "Scan source code text for invisible Unicode controls and cross-script homoglyph risks.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Source code text to scan."},
                    "source_name": {"type": "string", "description": "Optional source label for findings."},
                },
                "required": ["text"],
            },
        },
        {
            "name": "scan_unicode_security",
            "description": "Scan source code text with developer-friendly Unicode Security Pack findings.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Source code text to scan."},
                    "source_name": {"type": "string", "description": "Optional source label for findings."},
                },
                "required": ["text"],
            },
        },
        {
            "name": "scan_language_input",
            "description": "Scan natural-language input for prompt-injection directives and hidden Unicode attacks.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Natural-language input to scan before model ingestion."},
                    "source_name": {"type": "string", "description": "Optional source label for findings."},
                },
                "required": ["text"],
            },
        },
        {
            "name": "scan_output_dlp",
            "description": "Scan model output for sensitive data and return redacted text.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Model output to inspect before external delivery."},
                    "secret_terms": {"type": "array", "items": {"type": "string"}},
                    "include_lexicon_secrets": {"type": "boolean", "description": "Include approved secret terms from loaded lexicon packs."},
                    "source_name": {"type": "string", "description": "Optional source label for findings."},
                },
                "required": ["text"],
            },
        },
        {
            "name": "enforce_intent",
            "description": "Apply an intent sandbox manifest and return allow, review, or block without executing commands.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "intent_id": {"type": "string", "description": "Canonical intent requested by the agent."},
                    "manifest": {"type": "object", "description": "Intent manifest with allowed roles and commands."},
                    "actor_role": {"type": "string", "description": "Optional role requesting the intent."},
                    "parameters": {"type": "object", "description": "Optional structured intent parameters."},
                },
                "required": ["intent_id", "manifest"],
            },
        },
        {
            "name": "audit_explain",
            "description": "Return an OES explanation together with an audit event showing actor, sources, and unknowns.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "actor_id": {"type": "string", "description": "User, service, or agent identifier."},
                    "kind": {"type": "string", "enum": ["glyph", "term", "code"]},
                    "text": {"type": "string", "description": "Glyph, term, or source-code text to explain."},
                    "source_name": {"type": "string", "description": "Optional source label for code explanations."},
                },
                "required": ["actor_id", "kind", "text"],
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
                "serverInfo": {"name": "omniglyph", "version": __version__},
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

        if tool_name == "explain_glyph":
            char = arguments.get("char")
            if not isinstance(char, str) or len(char) != 1:
                return _error(request_id, -32602, "explain_glyph requires exactly one Unicode character")
            return _result(request_id, {"content": [{"type": "json", "json": explain_glyph(glyph_repository, char)}]})

        if tool_name == "explain_term":
            text = arguments.get("text")
            if not isinstance(text, str) or not text.strip():
                return _error(request_id, -32602, "explain_term requires non-empty text")
            return _result(request_id, {"content": [{"type": "json", "json": explain_term(glyph_repository, text)}]})

        if tool_name == "explain_code_security":
            text = arguments.get("text")
            source_name = arguments.get("source_name", "<mcp-text>")
            if not isinstance(text, str):
                return _error(request_id, -32602, "explain_code_security requires source code text")
            if not isinstance(source_name, str) or not source_name.strip():
                return _error(request_id, -32602, "explain_code_security source_name must be a string")
            return _result(request_id, {"content": [{"type": "json", "json": explain_code_security(text, source_name=source_name)}]})

        if tool_name == "normalize_tokens":
            tokens = arguments.get("tokens")
            mode = arguments.get("mode", "full")
            if not isinstance(tokens, list) or not all(isinstance(item, str) for item in tokens):
                return _error(request_id, -32602, "normalize_tokens requires a list of string tokens")
            results = normalize_tokens(glyph_repository, tokens)
            payload = compact_normalize(results) if mode == "compact" else {"results": results}
            return _result(request_id, {"content": [{"type": "json", "json": payload}]})

        if tool_name == "list_namespaces":
            return _result(
                request_id,
                {
                    "content": [
                        {
                            "type": "json",
                            "json": {
                                "schema": "omniglyph.lexicon_namespaces:0.1",
                                "namespaces": glyph_repository.list_lexical_namespaces(),
                            },
                        }
                    ]
                },
            )

        if tool_name == "validate_lexicon_pack":
            path = arguments.get("path")
            if not isinstance(path, str) or not path.strip():
                return _error(request_id, -32602, "validate_lexicon_pack requires path")
            return _result(request_id, {"content": [{"type": "json", "json": validate_lexicon_pack(path)}]})

        if tool_name == "validate_output_terms":
            terms = arguments.get("terms")
            if not isinstance(terms, list) or not all(isinstance(item, str) for item in terms):
                return _error(request_id, -32602, "validate_output_terms requires a list of string terms")
            return _result(request_id, {"content": [{"type": "json", "json": validate_output_terms(glyph_repository, terms)}]})

        if tool_name == "validate_action_policy":
            policy_path = arguments.get("policy_path")
            text = arguments.get("text")
            if not isinstance(policy_path, str) or not policy_path.strip():
                return _error(request_id, -32602, "validate_action_policy requires policy_path")
            if not isinstance(text, str) or not text.strip():
                return _error(request_id, -32602, "validate_action_policy requires text")
            try:
                policy = load_policy_file(Path(policy_path))
            except FileNotFoundError as error:
                return _error(request_id, -32602, f"validate_action_policy policy_path not found: {error}")
            except PermissionError as error:
                return _error(request_id, -32602, f"validate_action_policy policy_path not readable: {error}")
            except json.JSONDecodeError as error:
                return _error(request_id, -32602, f"validate_action_policy policy file is not valid JSON: {error}")
            except ValueError as error:
                return _error(request_id, -32602, f"validate_action_policy invalid policy file: {error}")
            return _result(request_id, {"content": [{"type": "json", "json": validate_action(text, policy)}]})

        if tool_name == "enforce_grounded_output":
            terms = arguments.get("terms")
            actor_id = arguments.get("actor_id")
            if not isinstance(terms, list) or not all(isinstance(item, str) for item in terms):
                return _error(request_id, -32602, "enforce_grounded_output requires a list of string terms")
            if actor_id is not None and (not isinstance(actor_id, str) or not actor_id.strip()):
                return _error(request_id, -32602, "enforce_grounded_output actor_id must be a string")
            return _result(request_id, {"content": [{"type": "json", "json": enforce_grounded_output(glyph_repository, terms, actor_id=actor_id)}]})

        if tool_name == "scan_code_symbols":
            text = arguments.get("text")
            source_name = arguments.get("source_name", "<mcp-text>")
            if not isinstance(text, str):
                return _error(request_id, -32602, "scan_code_symbols requires source code text")
            if not isinstance(source_name, str) or not source_name.strip():
                return _error(request_id, -32602, "scan_code_symbols source_name must be a string")
            return _result(request_id, {"content": [{"type": "json", "json": scan_text(text, source_name=source_name)}]})

        if tool_name == "scan_unicode_security":
            text = arguments.get("text")
            source_name = arguments.get("source_name", "<mcp-text>")
            if not isinstance(text, str):
                return _error(request_id, -32602, "scan_unicode_security requires source code text")
            if not isinstance(source_name, str) or not source_name.strip():
                return _error(request_id, -32602, "scan_unicode_security source_name must be a string")
            return _result(request_id, {"content": [{"type": "json", "json": scan_text(text, source_name=source_name)}]})

        if tool_name == "scan_language_input":
            text = arguments.get("text")
            source_name = arguments.get("source_name", "<mcp-input>")
            if not isinstance(text, str):
                return _error(request_id, -32602, "scan_language_input requires text")
            if not isinstance(source_name, str) or not source_name.strip():
                return _error(request_id, -32602, "scan_language_input source_name must be a string")
            return _result(request_id, {"content": [{"type": "json", "json": scan_language_input(text, source_name=source_name)}]})

        if tool_name == "scan_output_dlp":
            text = arguments.get("text")
            secret_terms = arguments.get("secret_terms", [])
            include_lexicon_secrets = arguments.get("include_lexicon_secrets", False)
            source_name = arguments.get("source_name", "<mcp-output>")
            if not isinstance(text, str):
                return _error(request_id, -32602, "scan_output_dlp requires text")
            if not isinstance(secret_terms, list) or not all(isinstance(item, str) for item in secret_terms):
                return _error(request_id, -32602, "scan_output_dlp secret_terms must be a list of strings")
            if not isinstance(include_lexicon_secrets, bool):
                return _error(request_id, -32602, "scan_output_dlp include_lexicon_secrets must be a boolean")
            if not isinstance(source_name, str) or not source_name.strip():
                return _error(request_id, -32602, "scan_output_dlp source_name must be a string")
            if include_lexicon_secrets:
                secret_terms = list(secret_terms) + glyph_repository.list_secret_terms()
            return _result(request_id, {"content": [{"type": "json", "json": scan_output_dlp(text, secret_terms=secret_terms, source_name=source_name)}]})

        if tool_name == "enforce_intent":
            intent_id = arguments.get("intent_id")
            manifest = arguments.get("manifest")
            actor_role = arguments.get("actor_role")
            parameters = arguments.get("parameters")
            if not isinstance(intent_id, str) or not intent_id.strip():
                return _error(request_id, -32602, "enforce_intent requires intent_id")
            if not isinstance(manifest, dict):
                return _error(request_id, -32602, "enforce_intent requires manifest object")
            if actor_role is not None and (not isinstance(actor_role, str) or not actor_role.strip()):
                return _error(request_id, -32602, "enforce_intent actor_role must be a string")
            if parameters is not None and not isinstance(parameters, dict):
                return _error(request_id, -32602, "enforce_intent parameters must be an object")
            return _result(
                request_id,
                {
                    "content": [
                        {
                            "type": "json",
                            "json": enforce_intent_manifest(intent_id, manifest, actor_role=actor_role, parameters=parameters),
                        }
                    ]
                },
            )

        if tool_name == "audit_explain":
            actor_id = arguments.get("actor_id")
            kind = arguments.get("kind")
            text = arguments.get("text")
            source_name = arguments.get("source_name", "<mcp-text>")
            if not isinstance(actor_id, str) or not actor_id.strip():
                return _error(request_id, -32602, "audit_explain requires actor_id")
            if not isinstance(kind, str) or kind not in {"glyph", "term", "code"}:
                return _error(request_id, -32602, "audit_explain kind must be glyph, term, or code")
            if not isinstance(text, str) or not text.strip():
                return _error(request_id, -32602, "audit_explain requires text")
            if kind == "glyph" and len(text) != 1:
                return _error(request_id, -32602, "audit_explain glyph text must contain exactly one Unicode character")
            if not isinstance(source_name, str) or not source_name.strip():
                return _error(request_id, -32602, "audit_explain source_name must be a string")
            result, action = _explain_for_audit(glyph_repository, kind, text, source_name)
            return _result(request_id, {"content": [{"type": "json", "json": {"result": result, "audit": build_audit_event(actor_id, action, result)}}]})

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


def _explain_for_audit(repository: GlyphRepository, kind: str, text: str, source_name: str) -> tuple[dict, str]:
    if kind == "glyph":
        if len(text) != 1:
            raise ValueError("audit_explain glyph text must contain exactly one Unicode character")
        return explain_glyph(repository, text), "explain_glyph"
    if kind == "term":
        return explain_term(repository, text), "explain_term"
    return explain_code_security(text, source_name=source_name), "explain_code_security"

if __name__ == "__main__":
    main()
