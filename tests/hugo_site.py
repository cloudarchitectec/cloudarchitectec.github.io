"""Shared Hugo build helpers for HTML and browser smoke tests."""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
STATIC_SERVER_PORT = 8765


def hugo_available() -> bool:
    return shutil.which("hugo") is not None


HUGO_BUILD_ARGS = [
    "--gc",
    "--minify",
    "--cleanDestinationDir",
    "--printPathWarnings",
    "--logLevel",
    "warn",
]

HUGO_WARNING_PATTERN = re.compile(
    r"(duplicate path|(^|\s)WARN:)",
    re.IGNORECASE | re.MULTILINE,
)


def run_hugo_build(extra_args: list[str] | None = None) -> None:
    cmd = ["hugo", *HUGO_BUILD_ARGS, *(extra_args or [])]
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        raise RuntimeError(f"hugo build failed:\n{combined}")
    if HUGO_WARNING_PATTERN.search(combined):
        raise RuntimeError(f"hugo build produced warnings:\n{combined}")


def ensure_built_site() -> Path:
    if os.environ.get("HUGO_SKIP_REBUILD") == "1" and (PUBLIC_DIR / "index.html").is_file():
        return PUBLIC_DIR
    if not hugo_available():
        raise RuntimeError("hugo not installed")
    run_hugo_build()
    return PUBLIC_DIR


def wait_for_port(host: str, port: int, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"server not ready on {host}:{port}")


def start_static_server(public_dir: Path, port: int = STATIC_SERVER_PORT) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", str(public_dir)],
        cwd=public_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wait_for_port("127.0.0.1", port)
    return proc
