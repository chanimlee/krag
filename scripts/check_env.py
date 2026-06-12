#!/usr/bin/env python
"""Print the local Python environment for the KRAG project."""

from __future__ import annotations

import importlib.metadata
import os
import platform
import sys


PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "sklearn": "scikit-learn",
    "joblib": "joblib",
}


def package_version(import_name: str, dist_name: str) -> str:
    try:
        __import__(import_name)
        return importlib.metadata.version(dist_name)
    except Exception as exc:
        return f"not installed ({exc.__class__.__name__})"


def main() -> int:
    print("KRAG Python environment")
    print("=======================")
    print(f"Python executable: {sys.executable}")
    print(f"Python version:    {platform.python_version()}")
    print(f"Working directory: {os.getcwd()}")
    print()
    print("Packages")
    print("--------")
    for import_name, dist_name in PACKAGES.items():
        print(f"{dist_name:14} {package_version(import_name, dist_name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
