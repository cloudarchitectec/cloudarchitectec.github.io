"""Small Hugo build helper for rendered-output regression tests."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
HUGO_BUILD_ARGS = ["--gc", "--minify", "--cleanDestinationDir", "--logLevel", "warn"]
HUGO_WARNING_PATTERN = re.compile(r"(duplicate path|(^|\s)WARN:)", re.IGNORECASE | re.MULTILINE)


def ensure_built_site() -> Path:
    if os.environ.get("HUGO_SKIP_REBUILD") == "1" and (PUBLIC_DIR / "index.html").is_file():
        return PUBLIC_DIR
    if not shutil.which("hugo"):
        raise RuntimeError("hugo not installed")
    result = subprocess.run(
        ["hugo", *HUGO_BUILD_ARGS], cwd=REPO_ROOT, capture_output=True, text=True
    )
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode or HUGO_WARNING_PATTERN.search(output):
        raise RuntimeError(f"hugo build failed or warned:\n{output}")
    return PUBLIC_DIR
