"""zh-TW punctuation hygiene in hand-authored templates, data and i18n strings.

Full-width punctuation carries its own left sidebearing, so a space in front of
it is always wrong in zh-TW — 「歡迎預約 ：」 renders with a visible gap. These
arrive via repo-wide find-and-replace, which reaches data files that no other
check proofreads.

Posts are out of scope, and this is not a `check-spelling.py` rule: that script
never scans `data/`, and over the post corpus the pattern fires ~146 times with
roughly two thirds being the `* **項目** ：說明` list style rather than typos.
Prose would need a baseline file; templates and data are short strings with no
markdown, so a hit here is always an accident.

Opening marks (（「『【) are excluded — in markdown a space before them is
usually required syntax (`### 「大學」`, `* 「A Cloud Guru」`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Closing / terminal full-width punctuation only.
TERMINAL_PUNCT = "，。、；：？！）」』】》〉…"

# A space is only an error when it follows visible content on the same line;
# the \S lookbehind keeps leading indentation (YAML block scalars, wrapped
# template lines) from being reported.
SPACE_BEFORE_PUNCT = re.compile(rf"(?<=\S)[ \t　]+[{TERMINAL_PUNCT}]")

SCAN_GLOBS = (
    "data/*.yaml",  # .json is generated (analytics) — hand-authored data only
    "i18n/*.yaml",
    "layouts/**/*.html",
    "hugo.toml",
)


def scanned_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in SCAN_GLOBS:
        files.update(p for p in REPO_ROOT.glob(pattern) if p.is_file())
    return sorted(files)


@pytest.mark.parametrize("path", scanned_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_space_before_full_width_punctuation(path: Path) -> None:
    offences: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for match in SPACE_BEFORE_PUNCT.finditer(line):
            offences.append(f"{path.relative_to(REPO_ROOT)}:{lineno} — …{match.group(0)!r}… in {line.strip()!r}")

    assert not offences, "Remove the space before the full-width punctuation:\n" + "\n".join(offences)
