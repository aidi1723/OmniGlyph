import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLICY_PACK_SCHEMA = "omniglyph.policy_pack:0.1"
POLICY_FILENAME = "policy.json"
INTENTS_FILENAME = "intents.csv"
ALLOWED_DECISIONS = {"allow", "review", "block"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
REQUIRED_POLICY_FIELDS = {
    "schema",
    "policy_id",
    "namespace",
    "name",
    "version",
    "owner_type",
    "license",
    "visibility",
}
REQUIRED_INTENT_FIELDS = {
    "intent_id",
    "canonical_phrase",
    "decision",
    "risk_level",
    "requires_approval",
    "allowed_roles",
    "audit_required",
    "parameters_schema",
}
TRUE_VALUES = {"true", "yes", "1"}
FALSE_VALUES = {"false", "no", "0"}


@dataclass(frozen=True)
class PolicyPack:
    metadata: dict[str, Any]
    intents: list[dict[str, Any]]

    def to_manifest(self) -> dict[str, Any]:
        return {
            "policy": {
                "policy_id": self.metadata["policy_id"],
                "namespace": self.metadata["namespace"],
                "name": self.metadata["name"],
                "version": self.metadata["version"],
            },
            "intents": [dict(intent) for intent in self.intents],
        }


def init_policy_pack(path: Path | str, namespace: str, policy_id: str, name: str) -> None:
    pack_dir = Path(path)
    pack_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema": POLICY_PACK_SCHEMA,
        "policy_id": policy_id,
        "namespace": namespace,
        "name": name,
        "version": "0.1.0",
        "owner_type": "personal",
        "license": "private",
        "visibility": "private",
        "description": "Starter OmniGlyph policy pack.",
    }
    (pack_dir / POLICY_FILENAME).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (pack_dir / INTENTS_FILENAME).write_text(
        "\n".join(
            [
                "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema",
                'example.review,review example request,review,medium,true,admin,true,"{}"',
                'example.allow,allow example request,allow,low,false,admin;operator,true,"{}"',
                'example.block,block example request,block,high,false,,true,"{}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def load_policy_pack(path: Path | str) -> PolicyPack:
    pack_dir = Path(path)
    metadata = _read_metadata(pack_dir)
    intents = _read_intents(pack_dir)
    return PolicyPack(metadata=metadata, intents=intents)


def validate_policy_pack(path: Path | str) -> dict:
    pack_dir = Path(path)
    errors = []
    metadata: dict[str, Any] = {}
    intents: list[dict[str, Any]] = []
    if not pack_dir.exists():
        errors.append(f"policy pack directory not found: {pack_dir}")
    elif not pack_dir.is_dir():
        errors.append(f"policy pack path must be a directory: {pack_dir}")
    if not errors:
        metadata, metadata_errors = _validate_metadata(pack_dir)
        errors.extend(metadata_errors)
        intents, intent_errors = _validate_intents(pack_dir)
        errors.extend(intent_errors)
    if errors:
        intents = []
    return {
        "schema": POLICY_PACK_SCHEMA,
        "status": "pass" if not errors else "fail",
        "policy": {
            "policy_id": metadata.get("policy_id"),
            "namespace": metadata.get("namespace"),
            "name": metadata.get("name"),
            "version": metadata.get("version"),
        },
        "summary": {
            "intent_count": len(intents),
            "allow_count": sum(1 for intent in intents if intent["decision"] == "allow"),
            "review_count": sum(1 for intent in intents if intent["decision"] == "review"),
            "block_count": sum(1 for intent in intents if intent["decision"] == "block"),
        },
        "errors": errors,
        "warnings": [],
    }


def ensure_allowed_policy_pack_path(path: str, root: Path | None) -> None:
    if root is None:
        return
    pack_path = Path(path).resolve()
    allowed_root = root.resolve()
    if pack_path != allowed_root and allowed_root not in pack_path.parents:
        raise ValueError("policy pack path is outside OMNIGLYPH_POLICY_PACK_ROOT")


def _read_metadata(pack_dir: Path) -> dict[str, Any]:
    metadata = json.loads((pack_dir / POLICY_FILENAME).read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError(f"{POLICY_FILENAME}: metadata must be a JSON object")
    return metadata


def _read_intents(pack_dir: Path) -> list[dict[str, Any]]:
    with (pack_dir / INTENTS_FILENAME).open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return [
            _parse_intent_row(row)
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def _validate_metadata(pack_dir: Path) -> tuple[dict[str, Any], list[str]]:
    metadata_path = pack_dir / POLICY_FILENAME
    if not metadata_path.exists():
        return {}, [f"{POLICY_FILENAME} is required"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{POLICY_FILENAME}: invalid JSON at line {exc.lineno} column {exc.colno}"]
    if not isinstance(metadata, dict):
        return {}, [f"{POLICY_FILENAME}: metadata must be a JSON object"]
    errors = []
    missing = sorted(field for field in REQUIRED_POLICY_FIELDS if not metadata.get(field))
    for field in missing:
        errors.append(f"{POLICY_FILENAME}: missing required field {field}")
    if metadata.get("schema") != POLICY_PACK_SCHEMA:
        errors.append(f"{POLICY_FILENAME}: schema must be {POLICY_PACK_SCHEMA}")
    if metadata.get("namespace") and not str(metadata["namespace"]).startswith("private_"):
        errors.append(f"{POLICY_FILENAME}: namespace should start with private_ for user policy packs")
    return metadata, errors


def _validate_intents(pack_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    intents_path = pack_dir / INTENTS_FILENAME
    if not intents_path.exists():
        return [], [f"{INTENTS_FILENAME} is required"]
    errors = []
    intents = []
    intent_rows: dict[str, int] = {}
    with intents_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return [], [f"{INTENTS_FILENAME}: missing header row"]
        missing = sorted(field for field in REQUIRED_INTENT_FIELDS if field not in reader.fieldnames)
        for field in missing:
            errors.append(f"{INTENTS_FILENAME}: missing required column {field}")
        for row_number, row in enumerate(reader, 2):
            if not any((value or "").strip() for value in row.values()):
                continue
            for field in REQUIRED_INTENT_FIELDS:
                if field != "allowed_roles" and not (row.get(field) or "").strip():
                    errors.append(f"{INTENTS_FILENAME} row {row_number}: missing required field {field}")
            parsed, row_errors = _validate_intent_row(row, row_number)
            errors.extend(row_errors)
            if not row_errors:
                intent_id = parsed["intent_id"]
                first_row = intent_rows.get(intent_id)
                if first_row is not None:
                    errors.append(
                        f"{INTENTS_FILENAME} row {row_number}: duplicate intent_id {intent_id} "
                        f"(first defined at row {first_row})"
                    )
                else:
                    intent_rows[intent_id] = row_number
                    intents.append(parsed)
    return intents, errors


def _validate_intent_row(row: dict[str, str | None], row_number: int) -> tuple[dict[str, Any], list[str]]:
    errors = []
    decision = (row.get("decision") or "").strip()
    if decision not in ALLOWED_DECISIONS:
        errors.append(f"{INTENTS_FILENAME} row {row_number}: decision must be one of allow, block, review")
    risk_level = (row.get("risk_level") or "").strip()
    if risk_level not in ALLOWED_RISK_LEVELS:
        errors.append(f"{INTENTS_FILENAME} row {row_number}: risk_level must be one of critical, high, low, medium")
    requires_approval_raw = (row.get("requires_approval") or "").strip()
    audit_required_raw = (row.get("audit_required") or "").strip()
    requires_approval = _parse_bool(requires_approval_raw)
    audit_required = _parse_bool(audit_required_raw)
    if requires_approval is None:
        errors.append(f"{INTENTS_FILENAME} row {row_number}: requires_approval must be a boolean string")
    if audit_required is None:
        errors.append(f"{INTENTS_FILENAME} row {row_number}: audit_required must be a boolean string")
    parameters_schema = _parse_json_object(row.get("parameters_schema") or "{}")
    if parameters_schema is None:
        errors.append(f"{INTENTS_FILENAME} row {row_number}: parameters_schema must be a JSON object")
    if errors:
        return {}, errors
    assert parameters_schema is not None
    return _intent_payload(row, decision, risk_level, bool(requires_approval), bool(audit_required), parameters_schema), []


def _parse_intent_row(row: dict[str, str | None]) -> dict[str, Any]:
    decision = (row.get("decision") or "").strip()
    risk_level = (row.get("risk_level") or "").strip()
    requires_approval = _parse_bool((row.get("requires_approval") or "").strip())
    audit_required = _parse_bool((row.get("audit_required") or "").strip())
    parameters_schema = _parse_json_object(row.get("parameters_schema") or "{}")
    if requires_approval is None or audit_required is None or parameters_schema is None:
        raise ValueError(f"{INTENTS_FILENAME}: invalid intent row")
    return _intent_payload(row, decision, risk_level, requires_approval, audit_required, parameters_schema)


def _intent_payload(
    row: dict[str, str | None],
    decision: str,
    risk_level: str,
    requires_approval: bool,
    audit_required: bool,
    parameters_schema: dict[str, Any],
) -> dict[str, Any]:
    return {
        "intent_id": (row.get("intent_id") or "").strip(),
        "canonical_phrase": (row.get("canonical_phrase") or "").strip(),
        "decision": decision,
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "allowed_roles": _parse_roles(row.get("allowed_roles") or ""),
        "audit_required": audit_required,
        "parameters_schema": parameters_schema,
    }


def _parse_roles(raw: str) -> list[str]:
    return [role.strip() for role in raw.split(";") if role.strip()]


def _parse_bool(raw: str) -> bool | None:
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    return None


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    return value
