import argparse
import json
from pathlib import Path

from omniglyph import __version__
from omniglyph.audit import build_audit_event
from omniglyph.code_linter import format_json_report, format_text_report, scan_path
from omniglyph.config import settings
from omniglyph.explanation import explain_for_audit
from omniglyph.guardrail import enforce_grounded_output, validate_output_terms
from omniglyph.language_security import enforce_intent_manifest, scan_language_input, scan_output_dlp
from omniglyph.lexicon_pack import entries_from_source, init_lexicon_pack, source_paths, validate_lexicon_pack
from omniglyph.normalizer import parse_unicode_data
from omniglyph.policy_pack import init_policy_pack, load_policy_pack, validate_policy_pack
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.sources import download_source, register_local_source
from omniglyph.unihan import parse_unihan_data

UNICODE_LICENSE = "Unicode Terms of Use"
UNIHAN_LICENSE = "Unicode Terms of Use"


def download_unicode(expected_sha256: str | None = None) -> Path:
    artifact = download_source(
        settings.unicode_data_url,
        settings.raw_dir / "UnicodeData.txt",
        source_version="latest",
        license=UNICODE_LICENSE,
        expected_sha256=expected_sha256,
    )
    print(f"Downloaded {artifact.path} sha256={artifact.sha256}")
    return artifact.path


def ingest_unicode(source_path: Path, source_version: str = "local", expected_sha256: str | None = None) -> int:
    artifact = register_local_source(
        source_path,
        source_url=source_path.as_uri() if source_path.is_absolute() else f"file://{source_path}",
        source_version=source_version,
        license=UNICODE_LICENSE,
        expected_sha256=expected_sha256,
    )
    records = list(parse_unicode_data(source_path))
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name="Unicode Character Database",
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    repository.insert_glyph_records(records, source_id=source_id)
    return len(records)


def ingest_unihan(source_path: Path, source_version: str = "local", expected_sha256: str | None = None) -> int:
    artifact = register_local_source(
        source_path,
        source_url=source_path.as_uri() if source_path.is_absolute() else f"file://{source_path}",
        source_version=source_version,
        license=UNIHAN_LICENSE,
        expected_sha256=expected_sha256,
    )
    properties = list(parse_unihan_data(source_path))
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name="Unihan Database",
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    return repository.insert_unihan_properties(properties, source_id=source_id)


def ingest_domain_pack(
    source_path: Path,
    namespace: str | None = None,
    source_version: str = "local",
    expected_sha256: str | None = None,
    dry_run: bool = False,
    replace_namespace: bool = False,
) -> int:
    entries, metadata = entries_from_source(source_path, namespace=namespace)
    terms_path, _ = source_paths(source_path)
    source_namespace = metadata["namespace"] if metadata is not None else namespace
    if source_namespace is None:
        raise ValueError("namespace is required when importing a CSV file")
    source_version = metadata["version"] if metadata is not None else source_version
    source_name = metadata["name"] if metadata is not None else "Private Domain Pack"
    if dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "namespace": source_namespace,
                    "source_version": source_version,
                    "entry_count": len(entries),
                    "alias_count": sum(len(entry.aliases) for entry in entries),
                    "secret_count": sum(1 for entry in entries if entry.sensitivity == "secret"),
                },
                ensure_ascii=False,
            )
        )
        return len(entries)
    artifact = register_local_source(
        terms_path,
        source_url=terms_path.as_uri() if terms_path.is_absolute() else f"file://{terms_path}",
        source_version=source_version,
        license="private",
        expected_sha256=expected_sha256,
    )
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    if replace_namespace:
        repository.delete_lexical_namespace(source_namespace)
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name=source_name,
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    return repository.insert_lexical_entries(entries, source_id=source_id)


def main() -> None:
    parser = argparse.ArgumentParser(prog="omniglyph")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    download = subcommands.add_parser("download-unicode")
    download.add_argument("--expected-sha256")

    ingest = subcommands.add_parser("ingest-unicode")
    ingest.add_argument("--source", type=Path, required=True)
    ingest.add_argument("--source-version", default="local")
    ingest.add_argument("--expected-sha256")

    ingest_unihan_parser = subcommands.add_parser("ingest-unihan")
    ingest_unihan_parser.add_argument("--source", type=Path, required=True)
    ingest_unihan_parser.add_argument("--source-version", default="local")
    ingest_unihan_parser.add_argument("--expected-sha256")

    domain = subcommands.add_parser("ingest-domain-pack")
    domain.add_argument("--source", type=Path, required=True)
    domain.add_argument("--namespace")
    domain.add_argument("--source-version", default="local")
    domain.add_argument("--expected-sha256")
    domain.add_argument("--dry-run", action="store_true")
    domain.add_argument("--replace-namespace", action="store_true")

    init_pack = subcommands.add_parser("init-lexicon-pack")
    init_pack.add_argument("path", type=Path)
    init_pack.add_argument("--namespace", required=True)
    init_pack.add_argument("--pack-id", required=True)
    init_pack.add_argument("--name", required=True)

    validate_pack = subcommands.add_parser("validate-domain-pack")
    validate_pack.add_argument("path", type=Path)

    init_policy = subcommands.add_parser("init-policy-pack")
    init_policy.add_argument("path", type=Path)
    init_policy.add_argument("--namespace", required=True)
    init_policy.add_argument("--policy-id", required=True)
    init_policy.add_argument("--name", required=True)

    validate_policy = subcommands.add_parser("validate-policy-pack")
    validate_policy.add_argument("path", type=Path)

    enforce_intent = subcommands.add_parser("enforce-intent")
    enforce_intent.add_argument("intent_id")
    enforce_intent.add_argument("--policy-pack", type=Path, required=True)
    enforce_intent.add_argument("--actor-role")
    enforce_intent.add_argument("--parameters", default="{}")

    enforce_output = subcommands.add_parser("enforce-output")
    enforce_output.add_argument("--term", action="append", required=True)
    enforce_output.add_argument("--actor-id")
    enforce_output.add_argument("--policy")

    validate_output = subcommands.add_parser("validate-output")
    validate_output.add_argument("--term", action="append", required=True)

    scan_language_input_parser = subcommands.add_parser("scan-language-input")
    scan_language_input_parser.add_argument("--text", required=True)
    scan_language_input_parser.add_argument("--source-name", default="<cli-input>")

    scan_output_dlp_parser = subcommands.add_parser("scan-output-dlp")
    scan_output_dlp_parser.add_argument("--text", required=True)
    scan_output_dlp_parser.add_argument("--secret-term", action="append", default=[])
    scan_output_dlp_parser.add_argument("--include-lexicon-secrets", action="store_true")
    scan_output_dlp_parser.add_argument("--source-name", default="<cli-output>")

    audit_explain = subcommands.add_parser("audit-explain")
    audit_explain.add_argument("--actor-id", required=True)
    audit_explain.add_argument("--kind", choices=["glyph", "term", "code"], required=True)
    audit_explain.add_argument("--text", required=True)
    audit_explain.add_argument("--source-name", default="<cli-text>")

    lookup = subcommands.add_parser("lookup")
    lookup.add_argument("text")

    scan_code = subcommands.add_parser("scan-code")
    scan_code.add_argument("path", type=Path)
    scan_code.add_argument("--format", choices=["text", "json"], default="text")
    scan_code.add_argument("--fail-on", choices=["never", "warning"], default="never")

    args = parser.parse_args()
    if args.command == "download-unicode":
        download_unicode(args.expected_sha256)
    elif args.command == "ingest-unicode":
        count = ingest_unicode(args.source, args.source_version, args.expected_sha256)
        print(f"Ingested {count} glyph records")
    elif args.command == "ingest-unihan":
        count = ingest_unihan(args.source, args.source_version, args.expected_sha256)
        print(f"Ingested {count} Unihan properties")
    elif args.command == "ingest-domain-pack":
        count = ingest_domain_pack(
            args.source,
            namespace=args.namespace,
            source_version=args.source_version,
            expected_sha256=args.expected_sha256,
            dry_run=args.dry_run,
            replace_namespace=args.replace_namespace,
        )
        if not args.dry_run:
            print(f"Ingested {count} domain entries")
    elif args.command == "init-lexicon-pack":
        init_lexicon_pack(args.path, namespace=args.namespace, pack_id=args.pack_id, name=args.name)
        print(f"Created lexicon pack at {args.path}")
    elif args.command == "validate-domain-pack":
        report = validate_lexicon_pack(args.path)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["status"] != "pass":
            raise SystemExit(1)
    elif args.command == "init-policy-pack":
        init_policy_pack(args.path, namespace=args.namespace, policy_id=args.policy_id, name=args.name)
        print(f"Created policy pack at {args.path}")
    elif args.command == "validate-policy-pack":
        report = validate_policy_pack(args.path)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["status"] != "pass":
            raise SystemExit(1)
    elif args.command == "enforce-intent":
        try:
            parameters = json.loads(args.parameters)
        except json.JSONDecodeError as exc:
            parser.error(f"--parameters must be a JSON object: {exc.msg}")
        if not isinstance(parameters, dict):
            parser.error("--parameters must be a JSON object")
        manifest = load_policy_pack(args.policy_pack).to_manifest()
        report = enforce_intent_manifest(
            args.intent_id,
            manifest,
            actor_role=args.actor_role,
            parameters=parameters,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "enforce-output":
        policy = None
        if args.policy is not None:
            try:
                policy = json.loads(args.policy)
            except json.JSONDecodeError as exc:
                parser.error(f"--policy must be a JSON object: {exc.msg}")
            if not isinstance(policy, dict):
                parser.error("--policy must be a JSON object")
        repository = GlyphRepository(settings.sqlite_path)
        repository.initialize()
        report = enforce_grounded_output(repository, args.term, actor_id=args.actor_id, policy=policy)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "validate-output":
        repository = GlyphRepository(settings.sqlite_path)
        repository.initialize()
        report = validate_output_terms(repository, args.term)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "scan-language-input":
        report = scan_language_input(args.text, source_name=args.source_name)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "scan-output-dlp":
        secret_terms = list(args.secret_term)
        if args.include_lexicon_secrets:
            repository = GlyphRepository(settings.sqlite_path)
            repository.initialize()
            secret_terms.extend(repository.list_secret_terms())
        report = scan_output_dlp(args.text, secret_terms=secret_terms, source_name=args.source_name)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "audit-explain":
        repository = GlyphRepository(settings.sqlite_path)
        repository.initialize()
        result, action = explain_for_audit(repository, args.kind, args.text, args.source_name)
        print(json.dumps({"result": result, "audit": build_audit_event(args.actor_id, action, result)}, ensure_ascii=False, indent=2))
    elif args.command == "lookup":
        repository = GlyphRepository(settings.sqlite_path)
        repository.initialize()
        lookup_result = repository.find_by_glyph(args.text) if len(args.text) == 1 else repository.find_term(args.text)
        if lookup_result is None:
            print(json.dumps({"error": "not found", "text": args.text}, ensure_ascii=False))
            raise SystemExit(1)
        print(json.dumps(lookup_result, ensure_ascii=False, indent=2))
    elif args.command == "scan-code":
        report = scan_path(args.path)
        if args.format == "json":
            print(format_json_report(report))
        else:
            print(format_text_report(report))
        if args.fail_on == "warning" and report["status"] in {"warn", "error"}:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
