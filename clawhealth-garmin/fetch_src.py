from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError


DEFAULT_REPO_URL = "https://github.com/ernestyu/clawhealth"
DEFAULT_REPO_REF = "main"
SUBDIR = Path("src") / "clawhealth"


def _src_dir(base_dir: Path, override: str | None = None) -> Path:
    raw = override or os.environ.get("CLAWHEALTH_SRC_DIR")
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


def _temp_root(base_dir: Path) -> Path:
    raw = os.environ.get("CLAWHEALTH_TMP_DIR")
    if raw:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = base_dir / p
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()
    tmp = base_dir / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp.resolve()


def _make_temp_dir(temp_root: Path) -> Path:
    temp_root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=str(temp_root)))


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _git_available() -> bool:
    return shutil.which("git") is not None


def _normalize_github_owner_repo(url: str) -> str | None:
    if "github.com/" not in url:
        return None
    owner_repo = url.split("github.com/", 1)[1].strip().strip("/")
    if owner_repo.endswith(".git"):
        owner_repo = owner_repo[:-4]
    if "/" not in owner_repo:
        return None
    return owner_repo


def _copy_subdir(src_repo: Path, dest_root: Path) -> None:
    pkg_src = src_repo / SUBDIR
    if not pkg_src.exists():
        raise SystemExit(f"expected path not found in repo: {pkg_src}")
    if dest_root.exists():
        shutil.rmtree(dest_root, ignore_errors=True)
    dest_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(pkg_src, dest_root / "clawhealth")


def _fetch_with_git(url: str, ref: str, dest_root: Path, temp_root: Path) -> None:
    td = _make_temp_dir(temp_root)
    try:
        repo_dir = Path(td) / "repo"
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
        ]
        if ref:
            cmd.extend(["--branch", ref])
        cmd.extend([url, str(repo_dir)])
        _run(cmd)
        _run(["git", "-C", str(repo_dir), "sparse-checkout", "set", str(SUBDIR).replace("\\", "/")])
        _copy_subdir(repo_dir, dest_root)
    finally:
        shutil.rmtree(td, ignore_errors=True)


def _download_zip(owner_repo: str, ref: str, dest_root: Path, temp_root: Path) -> None:
    def _try(kind: str) -> None:
        zip_url = f"https://github.com/{owner_repo}/archive/refs/{kind}/{ref}.zip"
        td = _make_temp_dir(temp_root)
        try:
            zip_path = Path(td) / "repo.zip"
            urllib.request.urlretrieve(zip_url, zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(td)
            extracted = [p for p in Path(td).iterdir() if p.is_dir()]
            if not extracted:
                raise RuntimeError("zip extraction failed")
            _copy_subdir(extracted[0], dest_root)
        finally:
            shutil.rmtree(td, ignore_errors=True)

    try:
        _try("heads")
        return
    except HTTPError as exc:
        if exc.code != 404:
            raise

    _try("tags")


def main() -> int:
    base_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Fetch clawhealth src/ into this skill folder")
    parser.add_argument("--url", default=os.environ.get("CLAWHEALTH_REPO_URL", DEFAULT_REPO_URL))
    parser.add_argument("--ref", default=os.environ.get("CLAWHEALTH_REPO_REF", DEFAULT_REPO_REF))
    parser.add_argument("--dest", default=os.environ.get("CLAWHEALTH_SRC_DIR"))
    parser.add_argument("--refresh", action="store_true", help="Re-download even if src exists")
    args = parser.parse_args()

    dest_root = _src_dir(base_dir, args.dest)
    temp_root = _temp_root(base_dir)

    if dest_root.exists():
        if args.refresh:
            shutil.rmtree(dest_root, ignore_errors=True)
        else:
            if _src_ready(dest_root):
                print("OK: src already present at", dest_root)
                return 0
            print("Src folder exists but is incomplete:", dest_root)
            print("Tip: run with --refresh to re-download.")
            return 2

    prefer_git = _truthy(os.environ.get("CLAWHEALTH_USE_GIT", "1"))
    if prefer_git and _git_available():
        try:
            print("Fetching src via git sparse-checkout:", args.url, "@", args.ref)
            _fetch_with_git(args.url, args.ref, dest_root, temp_root)
            print("OK: src ready at", dest_root)
            return 0
        except SystemExit as exc:
            print("WARN: git fetch failed, falling back to zip:", exc)

    owner_repo = _normalize_github_owner_repo(args.url)
    if not owner_repo:
        raise SystemExit("git not found and URL is not a GitHub repo; cannot download")

    try:
        print("Fetching src via GitHub zip:", owner_repo, "@", args.ref)
        _download_zip(owner_repo, args.ref, dest_root, temp_root)
        print("OK: src ready at", dest_root)
        return 0
    except (HTTPError, URLError) as exc:
        raise SystemExit(f"download failed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
