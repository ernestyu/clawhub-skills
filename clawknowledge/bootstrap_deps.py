#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Install dependencies for the clawknowledge skill.

This skill is a thin wrapper around the public `clawsqlite` PyPI package.
It does **not** vendor source code or clone git repositories.
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    cmd = [sys.executable, "-m", "pip", "install", "clawsqlite>=0.1.0"]
    proc = subprocess.run(cmd)
    return proc.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
