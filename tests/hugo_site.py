"""Shared Hugo build helpers for HTML and browser smoke tests."""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
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


def wait_for_port(
    host: str,
    port: int,
    timeout: float = 15.0,
    proc: subprocess.Popen | None = None,
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        # Fail fast instead of burning the whole timeout on a server that is
        # already dead (e.g. it could not bind the port).
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"server process exited with code {proc.returncode}")
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"server not ready on {host}:{port}")


def _drain(log) -> str:
    """Read back a server log captured to a temp file (best effort)."""
    try:
        log.seek(0)
        return log.read().strip()
    except (OSError, ValueError):
        return ""


def start_static_server(public_dir: Path, port: int = STATIC_SERVER_PORT) -> subprocess.Popen:
    # http.server logs every request to stderr, so a PIPE would fill its buffer and
    # stall the server mid-suite. Buffer to a temp file we can read back on failure
    # instead of discarding it — the "Address already in use" line lives here.
    log = tempfile.TemporaryFile(mode="w+")
    proc = subprocess.Popen(
        # -u: without it the child block-buffers stdout into the log file and the
        # "Serving HTTP" readiness banner never reaches us until the buffer fills.
        [sys.executable, "-u", "-m", "http.server", str(port), "--directory", str(public_dir)],
        cwd=public_dir,
        stdout=log,
        stderr=log,
    )

    def fail(reason: str) -> RuntimeError:
        proc.terminate()
        details = _drain(log)
        return RuntimeError(
            f"static server for {public_dir} failed on 127.0.0.1:{port} — {reason}."
            f"\nIs a previous run's server still holding the port?"
            + (f"\n--- server stderr ---\n{details}" if details else "")
        )

    try:
        wait_for_port("127.0.0.1", port, proc=proc)
    except RuntimeError as exc:
        raise fail(str(exc)) from None

    # A port that answers is NOT proof that *we* own it: a previous run's server may
    # still be shutting down on it. Our own bind then fails and every request starts
    # refusing once the old one finishes dying — a cascade of ERR_CONNECTION_REFUSED
    # across unrelated tests. So wait for http.server's own "Serving HTTP" banner,
    # which only prints once it holds the socket.
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if proc.poll() is not None:
            raise fail(f"process exited with code {proc.returncode} while the port answered")
        if "Serving HTTP" in _drain(log):
            return proc
        time.sleep(0.05)
    raise fail("server never reported 'Serving HTTP'")
