"""zh-TW punctuation hygiene in hand-authored templates, data and i18n strings.

Full-width punctuation carries its own left sidebearing, so a space in front of
it is always wrong in zh-TW — 「歡迎預約 ：」 renders with a visible gap. These
slip in through repo-wide find-and-replace: editing one phrase in a post also
rewrites the same phrase in `data/`, where nothing was proofreading it (that is
exactly how `portfolio.yaml` picked one up on 2026-08-02).

Deliberately NOT a `check-spelling.py` rule. That script only scans posts and
drafts, so it would have missed the data-file case entirely; and over the post
corpus the same pattern fires ~146 times, ~two thirds of them EC's habitual
`* **項目** ：說明` list style rather than typos. Prose needs a judgement call
and a baseline file. Templates and data don't: they are short strings with no
markdown, so any hit here is a genuine accident.

Opening marks (（「『【) are excluded on purpose — in markdown a space before
them is usually required syntax (`### 「大學」`, `* 「A Cloud Guru」`).
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
