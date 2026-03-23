#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runtime entry for the clawknowledge skill.

This script expects to be invoked by the ClawHub skill runtime with a JSON
payload on stdin and returns a JSON response on stdout.

It is intentionally a thin, auditable wrapper around the public
`clawsqlite` package and its `knowledge` CLI.
"""
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Dict


def _run_knowledge_cli(args: list[str]) -> Dict[str, Any]:
    """Run `clawsqlite knowledge ...` and return parsed JSON when applicable.

    This relies on the `clawsqlite` package being installed in the same
    Python environment as this skill (typically via `bootstrap_deps.py`).
    It uses `python -m clawsqlite_cli knowledge ...` so that imports are
    resolved from the installed package, not from any local source tree.

    NOTE: `--json` should be part of *args* when JSON output is desired.
    """
    cmd = [sys.executable, "-m", "clawsqlite_cli", "knowledge"] + args
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": "knowledge_cli_failed",
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    # Try to parse JSON; fall back to raw text
    try:
        data = json.loads(proc.stdout)
    except Exception:
        data = {"raw": proc.stdout}
    return {"ok": True, "data": data}


def handle_ingest_url(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = payload["url"]
    title = payload.get("title")
    category = payload.get("category", "web")
    tags = payload.get("tags")
    gen_provider = payload.get("gen_provider", "openclaw")
    root = payload.get("root")  # optional override

    args: list[str] = ["ingest", "--url", url, "--category", category, "--gen-provider", gen_provider, "--json"]
    if title:
        args += ["--title", title]
    if tags:
        args += ["--tags", tags]
    if root:
        args += ["--root", root]

    return _run_knowledge_cli(args)


def handle_ingest_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload["text"]
    title = payload.get("title")
    category = payload.get("category", "note")
    tags = payload.get("tags")
    gen_provider = payload.get("gen_provider", "openclaw")
    root = payload.get("root")

    args: list[str] = [
        "ingest",
        "--text",
        text,
        "--category",
        category,
        "--gen-provider",
        gen_provider,
        "--json",
    ]
    if title:
        args += ["--title", title]
    if tags:
        args += ["--tags", tags]
    if root:
        args += ["--root", root]

    return _run_knowledge_cli(args)


def handle_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = payload["query"]
    mode = payload.get("mode", "hybrid")
    topk = int(payload.get("topk", 10))
    category = payload.get("category")
    tag = payload.get("tag")
    include_deleted = bool(payload.get("include_deleted", False))
    root = payload.get("root")

    args: list[str] = [
        "search",
        query,
        "--mode",
        mode,
        "--topk",
        str(topk),
        "--json",
    ]
    if category:
        args += ["--category", category]
    if tag:
        args += ["--tag", tag]
    if include_deleted:
        args.append("--include-deleted")
    if root:
        args += ["--root", root]

    return _run_knowledge_cli(args)


def handle_show(payload: Dict[str, Any]) -> Dict[str, Any]:
    article_id = str(payload["id"])
    full = bool(payload.get("full", True))
    root = payload.get("root")

    args: list[str] = [
        "show",
        "--id",
        article_id,
        "--json",
    ]
    if full:
        args.append("--full")
    if root:
        args += ["--root", root]

    return _run_knowledge_cli(args)


HANDLERS = {
    "ingest_url": handle_ingest_url,
    "ingest_text": handle_ingest_text,
    "search": handle_search,
    "show": handle_show,
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        json.dump({"ok": False, "error": "invalid_json", "detail": str(e)}, sys.stdout)
        return 1

    action = payload.get("action")
    if not action:
        json.dump({"ok": False, "error": "missing_action"}, sys.stdout)
        return 1

    handler = HANDLERS.get(action)
    if not handler:
        json.dump({"ok": False, "error": "unknown_action", "action": action}, sys.stdout)
        return 1

    result = handler(payload)
    json.dump(result, sys.stdout, ensure_ascii=False)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
