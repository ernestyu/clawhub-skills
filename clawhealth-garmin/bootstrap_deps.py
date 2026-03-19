from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path


REQS = [
    "garminconnect>=0.2.1,<0.3.0",
    "garth>=0.5.0,<0.6.0",
]



def _venv_python(base_dir: Path) -> Path:
    venv_dir = base_dir / ".venv"
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _truthy(v: str | None) -> bool:
    return (v or "").strip() in ("1", "true", "True", "yes", "YES", "on", "ON")


def _ensure_src(base_dir: Path) -> None:
    script = base_dir / "fetch_src.py"
    if not script.exists():
        raise SystemExit("fetch_src.py not found; cannot download clawhealth src")
    cmd = [sys.executable, str(script)]
    if _truthy(os.environ.get("CLAWHEALTH_SRC_REFRESH")):
        cmd.append("--refresh")
    _run(cmd)


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / ".venv"
    vpy = _venv_python(base_dir)

    if not vpy.exists():
        print("Creating venv at", venv_dir)
        venv.EnvBuilder(with_pip=True).create(venv_dir)

    print("Upgrading pip/setuptools/wheel")
    _run([str(vpy), "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])

    print("Installing dependencies:", ", ".join(REQS))
    _run([str(vpy), "-m", "pip", "install", *REQS])

    print("Fetching clawhealth src (if missing)")
    _ensure_src(base_dir)

    print("OK: dependencies installed. Run the skill with:")
    print(f"  {sys.executable} {base_dir / 'run_clawhealth.py'} --help")
    print("Tip: run_clawhealth.py will re-exec into .venv automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
