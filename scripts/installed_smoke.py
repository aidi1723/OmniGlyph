#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    cli, mcp = sys.argv[1:3]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    version_output = run([cli, "--version"], env)
    if not version_output.startswith("omniglyph "):
        raise SystemExit("installed CLI version check failed")
    source = Path(tempfile.mkdtemp(prefix="omniglyph-installed-source-")) / "terms.csv"
    source.write_text("term,canonical_id,entry_type,language,aliases,definition,traits\nFOB,trade:fob,term,en,,Free On Board,{}\n", encoding="utf-8")
    run([cli, "ingest-domain-pack", "--source", str(source), "--namespace", "private_smoke"], env)
    lookup = run([cli, "lookup", "FOB"], env)
    if json.loads(lookup)["canonical_id"] != "trade:fob":
        raise SystemExit("installed CLI lookup failed")
    mcp_output = subprocess.run(
        [mcp], input='{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n', text=True,
        capture_output=True, check=True, env=env,
    ).stdout
    tools = json.loads(mcp_output)["result"]["tools"]
    expected = {"lookup_glyph", "lookup_term", "validate_policy_pack", "enforce_intent"}
    names = {item["name"] for item in tools}
    if not expected <= names or len(names) != len(tools):
        raise SystemExit("installed MCP tool listing failed")
    from fastapi.testclient import TestClient

    from omniglyph.api import create_app
    from omniglyph.repository import GlyphRepository

    client = TestClient(create_app(GlyphRepository(Path(env["OMNIGLYPH_SQLITE_PATH"]))))
    if client.get("/api/v1/health").status_code != 200:
        raise SystemExit("installed HTTP health failed")
    if client.get("/api/v1/term", params={"text": "FOB"}).json()["canonical_id"] != "trade:fob":
        raise SystemExit("installed HTTP term lookup failed")
    print("installed smoke ok")


def run(command: list[str], env: dict[str, str]) -> str:
    return subprocess.run(command, text=True, capture_output=True, check=True, env=env).stdout


if __name__ == "__main__":
    main()
