from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def _truthy(v: str | None) -> bool:
    return (v or "").strip() in ("1", "true", "True", "yes", "YES", "on", "ON")


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    runner = base_dir / "run_clawhealth.py"
    test_db = base_dir / "_test_empty.db"
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass

    if not runner.exists():
        print("FAIL: run_clawhealth.py not found")
        return 2

    src_dir = _src_dir(base_dir)
    if not _src_ready(src_dir):
        if _truthy(os.environ.get("CLAWHEALTH_TEST_AUTO_FETCH", "1")):
            proc = subprocess.run([sys.executable, str(base_dir / "fetch_src.py")])
            if proc.returncode != 0:
                print("FAIL: fetch_src.py failed")
                return 2
        else:
            print("FAIL: clawhealth src missing (run fetch_src.py)")
            return 2

    # 1) CLI help should work
    env = dict(os.environ)
    env["CLAWHEALTH_DB"] = str(test_db)
    env["CLAWHEALTH_USE_VENV"] = env.get("CLAWHEALTH_USE_VENV", "1")
    env["CLAWHEALTH_AUTO_FETCH"] = "0"
    env["CLAWHEALTH_AUTO_BOOTSTRAP"] = "0"

    proc = subprocess.run([sys.executable, str(runner), "--help"], capture_output=True, text=True, env=env)
    code, out, err = proc.returncode, proc.stdout, proc.stderr
    if code != 0:
        print("FAIL: CLI --help failed")
        print(err)
        return 2

    # 2) daily-summary should return DB_NOT_FOUND if DB missing (expected)
    proc = subprocess.run(
        [
            sys.executable,
            str(runner),
            "daily-summary",
            "--date",
            "2000-01-01",
            "--json",
        ]
        ,
        capture_output=True,
        text=True,
        env=env,
    )
    code, out, err = proc.returncode, proc.stdout, proc.stderr
    try:
        payload = json.loads(out or "{}")
    except json.JSONDecodeError:
        payload = {}
    if payload.get("error_code") != "DB_NOT_FOUND":
        print("FAIL: expected DB_NOT_FOUND from daily-summary")
        print("stdout:", out)
        print("stderr:", err)
        return 2

    if code not in (0, 1):
        print("FAIL: unexpected exit code from daily-summary:", code)
        return 2

    print("OK: minimal tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
