from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


def _read_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter start '---'")
    try:
        end_idx = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md missing frontmatter end '---'") from exc
    fm_lines = lines[1:end_idx]
    frontmatter: dict[str, str] = {}
    for line in fm_lines:
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def _parse_manifest(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    non_empty = [
        ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")
    ]
    if len(non_empty) == 1:
        # Inline format: "name: x version: y ..."
        line = non_empty[0]
        parts = list(re.finditer(r"(\w+):", line))
        for idx, match in enumerate(parts):
            key = match.group(1)
            start = match.end()
            end = parts[idx + 1].start() if idx + 1 < len(parts) else len(line)
            value = line[start:end].strip()
            data[key] = value
        return data

    current_list_key: str | None = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if current_list_key:
                data.setdefault(current_list_key, [])
                if isinstance(data[current_list_key], list):
                    data[current_list_key].append(line[2:].strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = value
                current_list_key = None
    return data


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _truthy(v: str | None) -> bool:
    return (v or "").strip() in ("1", "true", "True", "yes", "YES", "on", "ON")


def _src_dir(base_dir: Path) -> Path:
    raw = os.environ.get("CLAWHEALTH_SRC_DIR")
    if raw:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = base_dir / p
        return p.resolve()
    return (base_dir / "clawhealth_src").resolve()


def _src_ready(src_dir: Path) -> bool:
    return (src_dir / "clawhealth" / "cli.py").exists()


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    skill_md = base_dir / "SKILL.md"
    env_example = base_dir / "ENV_EXAMPLE.md"
    runner = base_dir / "run_clawhealth.py"
    publish_doc = base_dir / "PUBLISH.md"
    bootstrap = base_dir / "bootstrap_deps.py"
    manifest = base_dir / "manifest.yaml"
    readme = base_dir / "README.md"
    fetch_src = base_dir / "fetch_src.py"

    _require(skill_md.exists(), "SKILL.md not found")
    _require(env_example.exists(), "ENV_EXAMPLE.md not found")
    _require(runner.exists(), "run_clawhealth.py not found")
    _require(publish_doc.exists(), "PUBLISH.md not found")
    _require(bootstrap.exists(), "bootstrap_deps.py not found")
    _require(manifest.exists(), "manifest.yaml not found")
    _require(readme.exists(), "README.md not found (used for listing)")
    _require(fetch_src.exists(), "fetch_src.py not found")

    # Validate manifest.yaml (minimal schema)
    mf = _parse_manifest(manifest)
    for key in ("name", "version", "description", "author", "license", "entry"):
        _require(key in mf, f"manifest.yaml missing '{key}'")
    version = str(mf.get("version", "")).strip()
    _require(
        bool(SEMVER_RE.match(version)),
        "manifest.yaml version must be semver (e.g. 0.1.0)",
    )

    # Validate SKILL.md frontmatter
    text = skill_md.read_text(encoding="utf-8")
    fm = _read_frontmatter(text)

    _require("name" in fm, "frontmatter missing 'name'")
    _require("description" in fm, "frontmatter missing 'description'")
    _require("metadata" in fm, "frontmatter missing 'metadata'")

    metadata_raw = fm["metadata"]
    if isinstance(metadata_raw, dict):
        metadata = metadata_raw
    else:
        try:
            metadata = json.loads(metadata_raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "frontmatter 'metadata' must be a YAML mapping or valid single-line JSON"
            ) from exc

    requires = metadata.get("openclaw", {}).get("requires", {})
    bins = requires.get("bins", [])
    _require(
        isinstance(bins, list) and "python" in bins,
        "metadata requires bins must include 'python'",
    )

    # Basic sanity check: run CLI help if src is available (or allow auto-fetch)
    validate_with_fetch = _truthy(os.environ.get("CLAWHEALTH_VALIDATE_WITH_FETCH"))
    if _src_ready(_src_dir(base_dir)) or validate_with_fetch:
        env = dict(os.environ)
        if not validate_with_fetch:
            env["CLAWHEALTH_AUTO_FETCH"] = "0"
        proc = subprocess.run(
            [sys.executable, str(runner), "--help"],
            capture_output=True,
            text=True,
            env=env,
        )
        _require(proc.returncode == 0, "CLI help failed to run via run_clawhealth.py")
    else:
        print(
            "SKIP: clawhealth src not present; set CLAWHEALTH_VALIDATE_WITH_FETCH=1 to allow auto-fetch."
        )

    print("OK: Skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
