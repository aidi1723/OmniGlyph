import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACK_SCHEMA = "omniglyph.protocol_pack:0.1"
CHECK_SCHEMA = "omniglyph.protocol_check:0.1"
PROTOCOL_FILENAME = "protocol.json"

ALLOWED_LAYERS = {"root", "jurisdiction", "industry", "enterprise", "scenario"}
ALLOWED_CATEGORIES = {"physical_reality", "life_safety", "social_coordination", "symbolic_cognition"}
ALLOWED_SEVERITIES = {"info", "warn", "block"}
ALLOWED_DECISIONS = {"allow", "warn", "block", "unknown"}
ALLOWED_KINDS = {"goal", "action", "output", "intent"}
ALLOWED_MATCH_TYPES = {"keyword_any", "keyword_all", "exact_intent"}

REQUIRED_PACK_FIELDS = {"schema", "protocol_id", "name", "version", "layer", "owner", "license", "rules"}
REQUIRED_RULE_FIELDS = {"rule_id", "category", "severity", "statement", "match", "decision", "confidence", "source"}
REQUIRED_SOURCE_FIELDS = {"source_id", "source_name", "source_version", "license"}

LIMITS = [
    "World Protocol Pack v0.1 checks only configured deterministic rules.",
    "An unknown decision is not a permission grant; the host runtime must choose review, block, or fallback.",
    "The host runtime remains responsible for extraction, tool permissions, and human review.",
]


@dataclass(frozen=True)
class ProtocolRule:
    rule_id: str
    category: str
    severity: str
    statement: str
    match: dict[str, Any]
    decision: str
    confidence: float
    source: dict[str, Any]


@dataclass(frozen=True)
class ProtocolPack:
    metadata: dict[str, Any]
    rules: list[ProtocolRule]


def init_protocol_pack(path: Path | str, protocol_id: str, name: str) -> None:
    pack_dir = Path(path)
    pack_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": PACK_SCHEMA,
        "protocol_id": protocol_id,
        "name": name,
        "version": "0.1.0",
        "layer": "root",
        "owner": "local",
        "license": "private",
        "description": "Starter OmniGlyph protocol pack.",
        "rules": [
            {
                "rule_id": "symbolic.truth.no_unsupported_reference",
                "category": "symbolic_cognition",
                "severity": "block",
                "statement": "Do not present unsupported references as verified facts.",
                "match": {"type": "keyword_any", "keywords": ["unsupported reference"]},
                "decision": "block",
                "confidence": 0.8,
                "source": {
                    "source_id": "source:local:protocol",
                    "source_name": name,
                    "source_version": "0.1.0",
                    "license": "private",
                },
            }
        ],
    }
    (pack_dir / PROTOCOL_FILENAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_protocol_pack(path: Path | str) -> ProtocolPack:
    payload = _read_protocol_json(Path(path))
    rules = [
        ProtocolRule(
            rule_id=rule["rule_id"],
            category=rule["category"],
            severity=rule["severity"],
            statement=rule["statement"],
            match=rule["match"],
            decision=rule["decision"],
            confidence=float(rule["confidence"]),
            source=rule["source"],
        )
        for rule in payload["rules"]
    ]
    metadata = {key: value for key, value in payload.items() if key != "rules"}
    return ProtocolPack(metadata=metadata, rules=rules)


def validate_protocol_pack(path: Path | str) -> dict[str, Any]:
    pack_dir = Path(path)
    errors: list[str] = []
    payload: dict[str, Any] = {}
    if not pack_dir.exists():
        errors.append(f"pack directory not found: {pack_dir}")
    elif not pack_dir.is_dir():
        errors.append(f"pack path must be a directory: {pack_dir}")
    if not errors:
        payload, payload_errors = _validate_payload(pack_dir)
        errors.extend(payload_errors)
    rules = payload.get("rules") if isinstance(payload.get("rules"), list) else []
    return {
        "schema": PACK_SCHEMA,
        "status": "pass" if not errors else "fail",
        "protocol": {
            "protocol_id": payload.get("protocol_id"),
            "name": payload.get("name"),
            "version": payload.get("version"),
            "layer": payload.get("layer"),
        },
        "summary": {
            "rule_count": len(rules) if not errors else 0,
            "block_count": sum(1 for rule in rules if rule.get("decision") == "block") if not errors else 0,
            "warn_count": sum(1 for rule in rules if rule.get("decision") == "warn") if not errors else 0,
        },
        "errors": errors,
        "warnings": [],
    }


def check_protocol(path: Path | str, text: str, kind: str, actor_id: str | None = None) -> dict[str, Any]:
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"kind must be one of {', '.join(sorted(ALLOWED_KINDS))}")
    pack = load_protocol_pack(path)
    matched = [rule for rule in pack.rules if _matches(rule, text, kind)]
    decision = _aggregate_decision(matched)
    sources = _unique_sources(matched)
    payload = {
        "schema": CHECK_SCHEMA,
        "decision": decision,
        "status": "pass" if decision == "allow" else "warn",
        "kind": kind,
        "matched_rules": [_rule_to_result(rule) for rule in matched],
        "unknown": [] if matched else [text],
        "sources": sources,
        "limits": LIMITS,
    }
    if actor_id:
        payload["audit"] = {"actor": {"id": actor_id}, "action": "check_protocol"}
    return payload


def _read_protocol_json(pack_dir: Path) -> dict[str, Any]:
    return json.loads((pack_dir / PROTOCOL_FILENAME).read_text(encoding="utf-8"))


def _validate_payload(pack_dir: Path) -> tuple[dict[str, Any], list[str]]:
    protocol_path = pack_dir / PROTOCOL_FILENAME
    if not protocol_path.exists():
        return {}, [f"{PROTOCOL_FILENAME} is required"]
    try:
        payload = json.loads(protocol_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{PROTOCOL_FILENAME}: invalid JSON at line {exc.lineno} column {exc.colno}"]
    errors: list[str] = []
    for field in sorted(REQUIRED_PACK_FIELDS):
        if field not in payload or payload[field] in (None, "", []):
            errors.append(f"{PROTOCOL_FILENAME}: missing required field {field}")
    if payload.get("schema") != PACK_SCHEMA:
        errors.append(f"{PROTOCOL_FILENAME}: schema must be {PACK_SCHEMA}")
    if payload.get("layer") and payload["layer"] not in ALLOWED_LAYERS:
        errors.append(f"{PROTOCOL_FILENAME}: layer must be one of {', '.join(sorted(ALLOWED_LAYERS))}")
    rules = payload.get("rules")
    if rules is not None and not isinstance(rules, list):
        errors.append(f"{PROTOCOL_FILENAME}: rules must be a list")
    elif isinstance(rules, list):
        for index, rule in enumerate(rules, 1):
            errors.extend(_validate_rule(rule, index))
    return payload, errors


def _validate_rule(rule: Any, index: int) -> list[str]:
    if not isinstance(rule, dict):
        return [f"{PROTOCOL_FILENAME} rule {index}: rule must be an object"]
    errors: list[str] = []
    for field in sorted(REQUIRED_RULE_FIELDS):
        if field not in rule or rule[field] in (None, "", []):
            errors.append(f"{PROTOCOL_FILENAME} rule {index}: missing required field {field}")
    if rule.get("category") and rule["category"] not in ALLOWED_CATEGORIES:
        errors.append(f"{PROTOCOL_FILENAME} rule {index}: category must be one of {', '.join(sorted(ALLOWED_CATEGORIES))}")
    if rule.get("severity") and rule["severity"] not in ALLOWED_SEVERITIES:
        errors.append(f"{PROTOCOL_FILENAME} rule {index}: severity must be one of {', '.join(sorted(ALLOWED_SEVERITIES))}")
    if rule.get("decision") and rule["decision"] not in ALLOWED_DECISIONS:
        errors.append(f"{PROTOCOL_FILENAME} rule {index}: decision must be one of {', '.join(sorted(ALLOWED_DECISIONS))}")
    if "confidence" in rule:
        try:
            confidence = float(rule["confidence"])
        except (TypeError, ValueError):
            errors.append(f"{PROTOCOL_FILENAME} rule {index}: confidence must be a number between 0 and 1")
        else:
            if confidence < 0 or confidence > 1:
                errors.append(f"{PROTOCOL_FILENAME} rule {index}: confidence must be a number between 0 and 1")
    errors.extend(_validate_match(rule.get("match"), index))
    errors.extend(_validate_source(rule.get("source"), index))
    return errors


def _validate_match(match: Any, index: int) -> list[str]:
    if not isinstance(match, dict):
        return [f"{PROTOCOL_FILENAME} rule {index}: match must be an object"]
    match_type = match.get("type")
    errors: list[str] = []
    if match_type not in ALLOWED_MATCH_TYPES:
        errors.append(f"{PROTOCOL_FILENAME} rule {index}: match.type must be one of exact_intent, keyword_all, keyword_any")
    if match_type in {"keyword_any", "keyword_all"}:
        keywords = match.get("keywords")
        if not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item.strip() for item in keywords):
            errors.append(f"{PROTOCOL_FILENAME} rule {index}: match.keywords must be a non-empty string list")
    if match_type == "exact_intent" and not isinstance(match.get("intent"), str):
        errors.append(f"{PROTOCOL_FILENAME} rule {index}: match.intent must be a string")
    return errors


def _validate_source(source: Any, index: int) -> list[str]:
    if not isinstance(source, dict):
        return [f"{PROTOCOL_FILENAME} rule {index}: source must be an object"]
    errors: list[str] = []
    for field in sorted(REQUIRED_SOURCE_FIELDS):
        if not source.get(field):
            errors.append(f"{PROTOCOL_FILENAME} rule {index}: source missing required field {field}")
    return errors


def _matches(rule: ProtocolRule, text: str, kind: str) -> bool:
    match = rule.match
    match_type = match.get("type")
    candidate = text.casefold()
    if match_type == "keyword_any":
        return any(keyword.casefold() in candidate for keyword in match.get("keywords", []))
    if match_type == "keyword_all":
        return all(keyword.casefold() in candidate for keyword in match.get("keywords", []))
    if match_type == "exact_intent":
        return kind == "intent" and text.strip() == match.get("intent")
    return False


def _aggregate_decision(rules: list[ProtocolRule]) -> str:
    decisions = {rule.decision for rule in rules}
    if "block" in decisions:
        return "block"
    if "warn" in decisions:
        return "warn"
    if not rules:
        return "unknown"
    return "allow"


def _rule_to_result(rule: ProtocolRule) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "category": rule.category,
        "severity": rule.severity,
        "decision": rule.decision,
        "statement": rule.statement,
        "confidence": rule.confidence,
        "source_id": rule.source["source_id"],
    }


def _unique_sources(rules: list[ProtocolRule]) -> list[dict[str, Any]]:
    sources = {}
    for rule in rules:
        source = rule.source
        sources[source["source_id"]] = {
            "source_id": source["source_id"],
            "source_name": source["source_name"],
            "source_version": source["source_version"],
            "license": source["license"],
        }
    return list(sources.values())
