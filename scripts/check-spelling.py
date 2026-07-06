#!/usr/bin/env python3
"""Spell-check for EC blog posts: British English + Traditional Chinese.

Usage:
  python3 scripts/check-spelling.py
  python3 scripts/check-spelling.py --fix
  python3 scripts/check-spelling.py --post SLUG
  python3 scripts/check-spelling.py --drafts
  python3 scripts/check-spelling.py --staged
  python3 scripts/check-spelling.py --file tools/blog-publisher/input/slug.md
  python3 scripts/check-spelling.py --json --report-file report.md

Rules reference: scripts/spellcheck-references/
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

POSTS_DIR = REPO_ROOT / "content" / "posts"
DRAFTS_DIR = REPO_ROOT / "content" / "drafts"
PUBLISHER_INPUT_DIR = REPO_ROOT / "tools" / "blog-publisher" / "input"

DRAFT_GLOBS = ("index.md", "outline-cursor.md", "data-table.md")

AE_BE_PAIRS: list[tuple[str, str]] = [
    ("organizations", "organisations"),
    ("organization", "organisation"),
    ("organizing", "organising"),
    ("organized", "organised"),
    ("organize", "organise"),
    ("recognizing", "recognising"),
    ("recognized", "recognised"),
    ("recognize", "recognise"),
    ("realizing", "realising"),
    ("realized", "realised"),
    ("realize", "realise"),
    ("behavioral", "behavioural"),
    ("behaviors", "behaviours"),
    ("behavior", "behaviour"),
    ("coloring", "colouring"),
    ("colored", "coloured"),
    ("colors", "colours"),
    ("color", "colour"),
    ("favorites", "favourites"),
    ("favorite", "favourite"),
    ("data centers", "data centres"),
    ("data center", "data centre"),
    ("centering", "centring"),
    ("centered", "centred"),
    ("centers", "centres"),
    ("center", "centre"),
    ("defenses", "defences"),
    ("defense", "defence"),
    ("analyzing", "analysing"),
    ("analyzed", "analysed"),
    ("analyze", "analyse"),
    ("traveling", "travelling"),
    ("traveled", "travelled"),
    ("traveler", "traveller"),
    ("modeling", "modelling"),
    ("modeled", "modelled"),
    ("labeling", "labelling"),
    ("labeled", "labelled"),
    ("canceling", "cancelling"),
    ("canceled", "cancelled"),
    ("honoring", "honouring"),
    ("honored", "honoured"),
    ("honor", "honour"),
    ("neighbors", "neighbours"),
    ("neighbor", "neighbour"),
    ("fulfillment", "fulfilment"),
    ("labor", "labour"),
]

EN_PHRASE_FIXES: list[tuple[str, str]] = [
    ("full driving license", "full driving licence"),
    ("driving license", "driving licence"),
    ("full license", "full licence"),
]

PHRASE_ALLOWLIST: list[str] = [
    "Update Management Center",
    "Update management center",
    "Management Center",
    "Managment Center",
    "Azure Update Management Center",
    "Azure Update Managment Center",
    "Cost Center",
]

FLAG_PATTERNS: list[tuple[str, str]] = [
    (r"\blicense\b", "UK noun may be `licence`; verb stays `license`"),
    (r"\blicenses\b", "UK noun plural may be `licences`"),
    (r"\bprogramme\b", "Computing contexts often use `program` — confirm if intentional"),
]

# Longest first to avoid partial overlaps
ZH_LITERAL_FIXES: list[tuple[str, str]] = [
    ("該放倉庫的的放", "該放倉庫的放"),
    ("寫程式的的女孩", "寫程式的女孩"),
    ("詳請請參考", "詳情請參考"),
    ("詳請請見", "詳情請見"),
    ("詳請可以", "詳情可以"),
    ("匯入工的退休金", "匯入員工的退休金"),
    ("不段上漲", "不斷上漲"),
    ("不段扛著", "不斷扛著"),
    ("回隨之增高", "會隨之增高"),
    ("跟本", "根本"),
    ("不段", "不斷"),
    ("做為", "作為"),
    ("澳元", "澳幣"),
    ("0050 正 2", "0050正2"),
]

# Standalone 正2 product shorthand — applied after CJK spacing (spacing must not split 正2)
ZH_LITERAL_FIXES_AFTER: list[tuple[str, str]] = [
    ("正 2", "正2"),
]

CMP_PLACEHOLDER = "\x00CMP{idx}\x00"

# ISO currency code → Traditional Chinese (prose)
CURRENCY_CODE_TO_ZH: dict[str, str] = {
    "NZD": "紐幣",
    "AUD": "澳幣",
    "USD": "美元",
    "NTD": "台幣",
    "TWD": "台幣",
    "FJD": "斐濟幣",
}

ZH_REGEX_FIXES: list[tuple[str, str, str]] = [
    (r"([\u4e00-\u9fff])的的([\u4e00-\u9fff])", r"\1的\2", "重複用字"),
]

# Chinese punctuation — no extra space when adjacent to Latin/digits (e.g. ，NSW / (約 / /年)
ZH_PUNCT_FOR_SPACING = frozenset(
    "，。、；：？！「」『』（）【】《》…—·〈〉""''（）《》【】/\\"
)

# Latin / number token (decimals, currency, percents, hyphenated words)
LATIN_NUM_TOKEN = (
    r"(?:\$[\d,]+(?:\.\d+)?|"
    r"[A-Za-z]{2,}(?:[-'][A-Za-z]+)*|"
    r"[A-Za-z]|"
    r"\d+(?:\.\d+)?%|"
    r"\d+(?:\.\d+)?)"
)

# Product / ticker compounds — no internal CJK↔Latin spacing (e.g. 0050正2, 正2)
COMPOUND_TOKEN = re.compile(r"\d+正2|正2")

# EC voice emoticons — no space before (e.g. 啊XD, 社交XDD, 折磨QAQ, 真難lol)
EC_EMOTICON_PATTERN = r"X[D]+|QAQ|lol|LOL"
EC_EMOTICON = re.compile(EC_EMOTICON_PATTERN, re.IGNORECASE)

# Currency names for amount normalisation
CURRENCY_ZH_NAMES = ("澳幣", "紐幣", "台幣", "美元", "斐濟幣")
CURRENCY_ZH_ALT = r"澳幣|紐幣|台幣|美元|斐濟幣"

DIGIT_ZH: dict[str, str] = {
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
}

PLACEHOLDER = "\x00SPELLPROT{idx}\x00"


@dataclass
class Change:
    line: int
    before: str
    after: str
    lang: str
    applied: bool = False


@dataclass
class Flag:
    line: int
    text: str
    reason: str
    lang: str = "en"


@dataclass
class FileResult:
    path: Path
    changes: list[Change] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)
    skipped_regions: list[str] = field(default_factory=list)


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def split_front_matter(text: str) -> tuple[str, str, str]:
    if not text.startswith("---"):
        return "", text, "body"
    end = text.find("\n---", 3)
    if end == -1:
        return "", text, "body"
    fm_end = end + 4
    if fm_end <= len(text) and text[fm_end : fm_end + 1] == "\n":
        fm_end += 1
    return text[:fm_end], text[fm_end:], "front matter"


def protect_regions(body: str) -> tuple[str, list[str], list[str]]:
    regions: list[str] = []
    labels: list[str] = []

    def mask(pattern: str, label: str, text: str) -> str:
        def repl(m: re.Match[str]) -> str:
            idx = len(regions)
            regions.append(m.group(0))
            labels.append(label)
            return PLACEHOLDER.format(idx=idx)

        return re.sub(pattern, repl, text, flags=re.DOTALL | re.MULTILINE)

    out = body
    out = mask(r"```[\s\S]*?```", "code block", out)
    out = mask(r"`[^`\n]+`", "inline code", out)
    out = mask(r"\{\{<[^>]+>\}\}", "Hugo shortcode", out)
    out = mask(r"\{\{%[\s\S]*?\%\}\}", "Hugo shortcode", out)
    out = mask(r"!\[[^\]]*\]\([^)]+\)", "image markdown", out)
    out = mask(r"\[[^\]]*\]\([^)]+\)", "link (url preserved)", out)
    out = mask(r"https?://[^\s)>\]]+", "URL", out)
    return out, regions, labels


def restore_regions(text: str, regions: list[str]) -> str:
    for idx, region in enumerate(regions):
        text = text.replace(PLACEHOLDER.format(idx=idx), region)
    return text


def line_number_at(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def in_phrase_allowlist(text: str, start: int, end: int) -> bool:
    for phrase in PHRASE_ALLOWLIST:
        for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
            if not (end <= m.start() or start >= m.end()):
                return True
    return False


def record_literal_replacements(
    text: str,
    old: str,
    new: str,
    lang: str,
    fix: bool,
    changes: list[Change],
) -> str:
    start = 0
    while True:
        idx = text.find(old, start)
        if idx == -1:
            break
        changes.append(
            Change(
                line=line_number_at(text, idx),
                before=old,
                after=new,
                lang=lang,
                applied=fix,
            )
        )
        if fix:
            text = text[:idx] + new + text[idx + len(old) :]
            start = idx + len(new)
        else:
            start = idx + len(old)
    return text


def apply_en_phrases(text: str, fix: bool, changes: list[Change]) -> str:
    for american, british in EN_PHRASE_FIXES:
        text = record_literal_replacements(text, american, british, "en", fix, changes)
    return text


def apply_ae_be(text: str, fix: bool, changes: list[Change]) -> str:
    for american, british in AE_BE_PAIRS:
        pattern = re.compile(r"\b" + re.escape(american) + r"\b", re.IGNORECASE)
        if not fix:
            for m in pattern.finditer(text):
                orig = m.group(0)
                if in_phrase_allowlist(text, m.start(), m.end()):
                    continue
                new = preserve_case(orig, british)
                if orig != new:
                    changes.append(
                        Change(
                            line=line_number_at(text, m.start()),
                            before=orig,
                            after=new,
                            lang="en",
                            applied=False,
                        )
                    )
            continue

        def repl(m: re.Match[str], _british: str = british) -> str:
            orig = m.group(0)
            if in_phrase_allowlist(text, m.start(), m.end()):
                return orig
            new = preserve_case(orig, _british)
            if orig != new:
                changes.append(
                    Change(
                        line=line_number_at(text, m.start()),
                        before=orig,
                        after=new,
                        lang="en",
                        applied=True,
                    )
                )
            return new

        text = pattern.sub(repl, text)
    return text


def _is_ec_emoticon(text: str) -> bool:
    return bool(EC_EMOTICON.fullmatch(text))


def _is_colloquial_wan_token_boundary(left: str, right: str) -> bool:
    """六萬五 — no space inside Chinese-digit 萬 compounds."""
    colloquial_digits = frozenset("一二三四五六七八九兩")
    if right.startswith("萬") and left and left[-1] in colloquial_digits:
        return True
    if left.endswith("萬") and right and right[0] in colloquial_digits:
        return True
    return False


def _needs_cjk_latin_space(left: str, right: str) -> bool:
    """True when a space should sit between a CJK char and a Latin/digit token."""
    if not left or not right:
        return False
    if _is_ec_emoticon(right) or _is_ec_emoticon(left):
        return False
    if _is_colloquial_wan_token_boundary(left, right):
        return False
    left_last = left[-1]
    right_first = right[0]
    if left_last in ZH_PUNCT_FOR_SPACING or right_first in ZH_PUNCT_FOR_SPACING:
        return False
    left_is_cjk = "\u4e00" <= left_last <= "\u9fff"
    right_is_cjk = "\u4e00" <= right_first <= "\u9fff"
    if left_is_cjk and not right_is_cjk:
        return right_first.isascii() and (right_first.isalnum() or right_first in "$")
    if right_is_cjk and not left_is_cjk:
        return left_last.isascii() and (left_last.isalnum() or left_last in "$%")
    return False


def apply_currency_zh(text: str, fix: bool, changes: list[Change]) -> str:
    """Convert ISO currency codes to Chinese names; normalise 約台幣 → 約 X 台幣."""
    twd_patterns: list[tuple[str, str]] = [
        (r"（約台幣\s*\$?([^）]+)）", r"（約 \1 台幣）"),
        (r"\(約台幣\s*\$?([^)]+)\)", r"(約 \1 台幣)"),
        (r"約台幣\s*\$?([\d,]+(?:\.\d+)?(?:\s*萬(?:\s*[\d]+)?)?)", r"約 \1 台幣"),
        (r"\$([\d,]+(?:\.\d+)?)\s*台幣", r"\1 台幣"),
    ]
    for pattern, repl in twd_patterns:
        regex = re.compile(pattern)
        if not fix:
            for m in regex.finditer(text):
                orig = m.group(0)
                new_val = m.expand(repl)
                if orig != new_val:
                    changes.append(
                        Change(
                            line=line_number_at(text, m.start()),
                            before=orig,
                            after=new_val,
                            lang="zh",
                            applied=False,
                        )
                    )
            continue

        def sub_twd(m: re.Match[str], _repl: str = repl) -> str:
            orig = m.group(0)
            new_val = m.expand(_repl)
            if orig != new_val:
                changes.append(
                    Change(
                        line=line_number_at(text, m.start()),
                        before=orig,
                        after=new_val,
                        lang="zh",
                        applied=True,
                    )
                )
            return new_val

        text = regex.sub(sub_twd, text)

    for code, zh_name in sorted(CURRENCY_CODE_TO_ZH.items(), key=lambda x: -len(x[0])):
        if code in ("NTD", "TWD"):
            continue
        patterns: list[tuple[str, str]] = [
            (rf"{code}\s*\$?([\d,]+(?:\.\d+)?)", rf"\1 {zh_name}"),
            (rf"\$?([\d,]+(?:\.\d+)?)\s*{code}\b", rf"\1 {zh_name}"),
            (rf"([\d,]+(?:\.\d+)?){code}\b", rf"\1 {zh_name}"),
        ]
        for pattern, repl in patterns:
            regex = re.compile(pattern)
            if not fix:
                for m in regex.finditer(text):
                    orig = m.group(0)
                    new_val = m.expand(repl)
                    if orig != new_val:
                        changes.append(
                            Change(
                                line=line_number_at(text, m.start()),
                                before=orig,
                                after=new_val,
                                lang="zh",
                                applied=False,
                            )
                        )
                continue

            def sub_cur(m: re.Match[str], _repl: str = repl) -> str:
                orig = m.group(0)
                new_val = m.expand(_repl)
                if orig != new_val:
                    changes.append(
                        Change(
                            line=line_number_at(text, m.start()),
                            before=orig,
                            after=new_val,
                            lang="zh",
                            applied=True,
                        )
                    )
                return new_val

            text = regex.sub(sub_cur, text)
    return text


def apply_zh_fixes_after_spacing(text: str, fix: bool, changes: list[Change]) -> str:
    for old, new in ZH_LITERAL_FIXES_AFTER:
        text = record_literal_replacements(text, old, new, "zh", fix, changes)

    # Collapse errant space before EC emoticons (啊 XD → 啊XD, 折磨 QAQ → 折磨QAQ)
    emo_collapse = re.compile(
        rf"([\u4e00-\u9fff])\s+({EC_EMOTICON_PATTERN})",
        re.IGNORECASE,
    )
    if not fix:
        for m in emo_collapse.finditer(text):
            orig = m.group(0)
            new_val = m.group(1) + m.group(2)
            if orig != new_val:
                changes.append(
                    Change(
                        line=line_number_at(text, m.start()),
                        before=orig,
                        after=new_val,
                        lang="zh",
                        applied=False,
                    )
                )
        return text

    def collapse_emo(m: re.Match[str]) -> str:
        orig = m.group(0)
        new_val = m.group(1) + m.group(2)
        if orig != new_val:
            changes.append(
                Change(
                    line=line_number_at(text, m.start()),
                    before=orig,
                    after=new_val,
                    lang="zh",
                    applied=True,
                )
            )
        return new_val

    return emo_collapse.sub(collapse_emo, text)


def _colloquial_wan_zh(wan: str, tail: str) -> str:
    return f"{DIGIT_ZH[wan]}萬{DIGIT_ZH[tail]}"


def _record_regex_sub(
    text: str,
    pattern: str,
    repl_fn,
    fix: bool,
    changes: list[Change],
) -> str:
    regex = re.compile(pattern)
    if not fix:
        for m in regex.finditer(text):
            new_val = repl_fn(m)
            orig = m.group(0)
            if orig != new_val:
                changes.append(
                    Change(
                        line=line_number_at(text, m.start()),
                        before=orig,
                        after=new_val,
                        lang="zh",
                        applied=False,
                    )
                )
        return text

    def sub_fn(m: re.Match[str]) -> str:
        orig = m.group(0)
        new_val = repl_fn(m)
        if orig != new_val:
            changes.append(
                Change(
                    line=line_number_at(text, m.start()),
                    before=orig,
                    after=new_val,
                    lang="zh",
                    applied=True,
                )
            )
        return new_val

    return regex.sub(sub_fn, text)


def apply_chinese_amount_format(text: str, fix: bool, changes: list[Change]) -> str:
    """Colloquial 6 萬 5 → 六萬五 (Chinese digits only). Arabic amounts keep spaced 萬 style."""
    cur = CURRENCY_ZH_ALT

    # 澳幣 6 萬 5 / 澳幣6萬5 → 澳幣六萬五
    text = _record_regex_sub(
        text,
        rf"({cur})\s*(\d)\s*萬\s*(\d)(?![0-9])",
        lambda m: f"{m.group(1)}{_colloquial_wan_zh(m.group(2), m.group(3))}",
        fix,
        changes,
    )

    # 約 5 萬 6 台幣 / 約5萬6台幣 → 約五萬六台幣
    text = _record_regex_sub(
        text,
        rf"約\s*(\d)\s*萬\s*(\d)\s+({cur})",
        lambda m: f"約{_colloquial_wan_zh(m.group(1), m.group(2))}{m.group(3)}",
        fix,
        changes,
    )

    # 5 萬 6 台幣 / 5萬6台幣 → 五萬六台幣
    text = _record_regex_sub(
        text,
        rf"(?<![\d.])(\d)\s*萬\s*(\d)\s+({cur})",
        lambda m: f"{_colloquial_wan_zh(m.group(1), m.group(2))}{m.group(3)}",
        fix,
        changes,
    )

    # 2 萬 5 / 2萬5 (no currency suffix) → 二萬五
    text = _record_regex_sub(
        text,
        r"(?<![\d.])(\d)\s*萬\s*(\d)(?![0-9])",
        lambda m: _colloquial_wan_zh(m.group(1), m.group(2)),
        fix,
        changes,
    )

    return text


def apply_cjk_latin_spacing(text: str, fix: bool, changes: list[Change]) -> str:
    """Insert spaces between CJK and Latin/number tokens unless touching ZH punctuation."""
    token_re = re.compile(LATIN_NUM_TOKEN)
    cjk_re = re.compile(r"[\u4e00-\u9fff]+")

    cmp_ph_re = re.compile(r"\x00CMP\d+\x00")

    def split_segments(line: str) -> list[tuple[str, str]]:
        segs: list[tuple[str, str]] = []
        pos = 0
        while pos < len(line):
            m = cmp_ph_re.match(line, pos)
            if m:
                segs.append(("compound", m.group(0)))
                pos = m.end()
                continue
            m = COMPOUND_TOKEN.match(line, pos)
            if m:
                segs.append(("compound", m.group(0)))
                pos = m.end()
                continue
            m = EC_EMOTICON.match(line, pos)
            if m:
                segs.append(("emoticon", m.group(0)))
                pos = m.end()
                continue
            m = token_re.match(line, pos)
            if m:
                segs.append(("tok", m.group(0)))
                pos = m.end()
                continue
            m = cjk_re.match(line, pos)
            if m:
                segs.append(("cjk", m.group(0)))
                pos = m.end()
                continue
            segs.append(("other", line[pos]))
            pos += 1
        return segs

    def spaced_line(line: str) -> str:
        compounds: list[str] = []

        def mask_compound(m: re.Match[str]) -> str:
            idx = len(compounds)
            compounds.append(m.group(0))
            return CMP_PLACEHOLDER.format(idx=idx)

        masked = re.sub(r"\d+正2|正2", mask_compound, line)
        segs = split_segments(masked)
        if len(segs) < 2:
            return line
        out: list[str] = []
        for i, (kind, chunk) in enumerate(segs):
            if i == 0:
                out.append(chunk)
                continue
            prev_kind, prev_chunk = segs[i - 1]
            if kind == "other" and chunk == " ":
                out.append(chunk)
                continue
            gap = ""
            pair = (prev_kind, kind)
            if pair in {
                ("cjk", "tok"),
                ("tok", "cjk"),
                ("cjk", "compound"),
                ("compound", "cjk"),
                ("tok", "compound"),
                ("compound", "tok"),
                ("cjk", "emoticon"),
            }:
                if _needs_cjk_latin_space(prev_chunk, chunk):
                    gap = " "
            elif prev_kind == "other" and kind in {"cjk", "tok", "compound", "emoticon"}:
                if _needs_cjk_latin_space(prev_chunk, chunk):
                    gap = " "
            out.append(gap)
            out.append(chunk)
        result = "".join(out)
        result = re.sub(r"(\d)\s+%", r"\1%", result)
        for idx, compound in enumerate(compounds):
            result = result.replace(CMP_PLACEHOLDER.format(idx=idx), compound)
        return result

    lines = text.split("\n")
    new_lines: list[str] = []
    for line_no, line in enumerate(lines, start=1):
        new_line = spaced_line(line)
        if new_line != line:
            snippet = line.strip()
            new_snippet = new_line.strip()
            if len(snippet) > 80:
                snippet = snippet[:80] + "…"
            if len(new_snippet) > 80:
                new_snippet = new_snippet[:80] + "…"
            changes.append(
                Change(
                    line=line_no,
                    before=snippet,
                    after=new_snippet,
                    lang="zh",
                    applied=fix,
                )
            )
        new_lines.append(new_line)

    return "\n".join(new_lines)


def apply_zh_fixes(text: str, fix: bool, changes: list[Change]) -> str:
    for old, new in ZH_LITERAL_FIXES:
        text = record_literal_replacements(text, old, new, "zh", fix, changes)

    for pattern, repl, _reason in ZH_REGEX_FIXES:
        regex = re.compile(pattern)
        if not fix:
            for m in regex.finditer(text):
                orig = m.group(0)
                new_val = m.expand(repl)
                if orig != new_val:
                    changes.append(
                        Change(
                            line=line_number_at(text, m.start()),
                            before=orig,
                            after=new_val,
                            lang="zh",
                            applied=False,
                        )
                    )
            continue

        def sub_fn(m: re.Match[str], _repl: str = repl) -> str:
            orig = m.group(0)
            new_val = m.expand(_repl)
            if orig != new_val:
                changes.append(
                    Change(
                        line=line_number_at(text, m.start()),
                        before=orig,
                        after=new_val,
                        lang="zh",
                        applied=True,
                    )
                )
            return new_val

        text = regex.sub(sub_fn, text)
    return text


BOLD_SPAN_RE = re.compile(r"\*\*([^*\n]+)\*\*")  # never span lines: stray ** would swallow paragraphs


def _cjk_char_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def _should_unwrap_bold(inner: str) -> bool:
    """Numbers, amounts, English tokens — never markdown-bold."""
    s = inner.strip()
    if not s:
        return True
    if re.fullmatch(r"[A-Za-z][A-Za-z\s\-]{0,40}", s):
        return True
    if re.search(r"\d", s) and re.search(r"(萬|倍|%|年|澳幣|台幣|美元|紐幣)", s):
        return True
    if "%" in s and re.search(r"\d", s):
        return True
    if re.fullmatch(r"[\d.,\s%]+", s):
        return True
    return False


def _bold_to_guillemets_if_needed(inner: str) -> str | None:
    """Return 「…」 form only for rhetorical emphasis; None = unwrap to plain."""
    s = inner.strip()
    if s.startswith("「") and s.endswith("」"):
        return s
    cjk = _cjk_char_count(s)
    if cjk < 2:
        return None
    if "？" in s or "?" in s:
        return f"「{s}」"
    if "（" in s or "(" in s:
        return f"「{s}」"
    if cjk >= 8:
        return f"「{s}」"
    return None


def _emphasis_replacement(inner: str) -> tuple[str, str]:
    s = inner.strip()
    if _should_unwrap_bold(s):
        return s, "unwrap ** (number/English — no emphasis)"
    guillemet = _bold_to_guillemets_if_needed(s)
    if guillemet:
        return guillemet, "bold → 「」 (rhetorical emphasis)"
    return s, "unwrap ** (short keyword — use plain text)"


def _is_structural_bold(text: str, start: int, end: int) -> bool:
    """A bold span that is an entire line, or an entire list-item label, is deliberate
    structure (Medium pseudo-heading, pull quote, bold bullet label) — never auto-modify;
    promote to a real heading manually if needed."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    prefix = text[line_start:start]
    suffix = text[end:line_end]
    if re.fullmatch(r"\s*(?:[-*+]\s+|\d+[.)]\s+)?", prefix) and re.fullmatch(r"[:：]?\s*", suffix):
        return True
    # bold label opening a list item, content after a colon: `* **預算多少** : …`
    if re.fullmatch(r"\s*(?:[-*+]|\d+[.)])\s+", prefix) and re.match(r"\s*[:：]", suffix):
        return True
    return False


def apply_emphasis_hygiene(
    text: str, fix: bool, changes: list[Change], flags: list[Flag]
) -> str:
    """Normalise markdown bold in Chinese prose. See references/emphasis-rules.md."""

    def repl(m: re.Match[str]) -> str:
        orig = m.group(0)
        if _is_structural_bold(text, m.start(), m.end()) and not _should_unwrap_bold(
            m.group(1)
        ):
            return orig
        if "「" in m.group(1) or "」" in m.group(1):
            # converting to 「…」 would nest quotes — leave the bold alone
            return orig
        line_start = text.rfind("\n", 0, m.start()) + 1
        if text[line_start:m.start()].lstrip().startswith("#"):
            # bold inside a heading: heading already carries emphasis — just unwrap
            new_val = m.group(1)
            if orig != new_val:
                changes.append(
                    Change(
                        line=line_number_at(text, m.start()),
                        before=orig,
                        after=new_val,
                        lang="zh",
                        applied=fix,
                    )
                )
            return new_val if fix else orig
        new_val, _reason = _emphasis_replacement(m.group(1))
        if orig != new_val:
            changes.append(
                Change(
                    line=line_number_at(text, m.start()),
                    before=orig,
                    after=new_val,
                    lang="zh",
                    applied=fix,
                )
            )
        return new_val if fix else orig

    text = BOLD_SPAN_RE.sub(repl, text)

    if fix:
        text = re.sub(r"([\u4e00-\u9fff]) 「", r"\1「", text)
        text = re.sub(r"」 ([\u4e00-\u9fff])", r"」\1", text)

    for m in BOLD_SPAN_RE.finditer(text):
        if _is_structural_bold(text, m.start(), m.end()):
            continue
        flags.append(
            Flag(
                line=line_number_at(text, m.start()),
                text=m.group(0),
                reason="residual markdown ** — review manually",
                lang="zh",
            )
        )
    return text


def find_flags(text: str) -> list[Flag]:
    flags: list[Flag] = []
    seen: set[tuple[int, str]] = set()
    for pattern, reason in FLAG_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            key = (line_number_at(text, m.start()), m.group(0).lower())
            if key in seen:
                continue
            seen.add(key)
            flags.append(
                Flag(
                    line=line_number_at(text, m.start()),
                    text=m.group(0),
                    reason=reason,
                    lang="en",
                )
            )
    return flags


def process_file(path: Path, fix: bool) -> FileResult:
    original = path.read_text(encoding="utf-8")
    fm, body, fm_label = split_front_matter(original)
    masked, regions, region_labels = protect_regions(body)

    unique_labels = sorted(set(region_labels))
    skipped = [fm_label] if fm else []
    skipped.extend(unique_labels)

    changes: list[Change] = []
    new_masked = apply_en_phrases(masked, fix=fix, changes=changes)
    new_masked = apply_ae_be(new_masked, fix=fix, changes=changes)
    new_masked = apply_zh_fixes(new_masked, fix=fix, changes=changes)
    new_masked = apply_currency_zh(new_masked, fix=fix, changes=changes)
    new_masked = apply_cjk_latin_spacing(new_masked, fix=fix, changes=changes)
    new_masked = apply_zh_fixes_after_spacing(new_masked, fix=fix, changes=changes)
    new_masked = apply_chinese_amount_format(new_masked, fix=fix, changes=changes)
    flags: list[Flag] = []
    new_masked = apply_emphasis_hygiene(new_masked, fix=fix, changes=changes, flags=flags)
    flags.extend(find_flags(new_masked))

    new_body = restore_regions(new_masked, regions)
    new_content = fm + new_body

    if fix and new_content != original:
        path.write_text(new_content, encoding="utf-8")

    return FileResult(path=path, changes=changes, flags=flags, skipped_regions=skipped)


def collect_post_files(post_slug: str | None) -> list[Path]:
    if post_slug:
        p = POSTS_DIR / post_slug / "index.md"
        if not p.exists():
            matches = list(POSTS_DIR.glob(f"*{post_slug}*/index.md"))
            if not matches:
                print(f"❌ Post not found: {post_slug}", file=sys.stderr)
                sys.exit(1)
            return matches
        return [p]
    return sorted(POSTS_DIR.glob("*/index.md"))


def collect_draft_files() -> list[Path]:
    files: list[Path] = []
    if not DRAFTS_DIR.exists():
        return files
    for name in DRAFT_GLOBS:
        files.extend(sorted(DRAFTS_DIR.glob(f"*/{name}")))
    return files


def collect_staged_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        print("❌ git diff failed", file=sys.stderr)
        sys.exit(1)
    paths: list[Path] = []
    for line in out.stdout.splitlines():
        p = REPO_ROOT / line.strip()
        if p.suffix != ".md":
            continue
        if p.parts[-3:-1] == ("content", "posts") and p.name == "index.md":
            paths.append(p)
        elif p.parts[-4:-1] == ("content", "drafts") and p.name in DRAFT_GLOBS:
            paths.append(p)
        elif p.parts[-3:-1] == ("blog-publisher", "input") and p.suffix == ".md":
            paths.append(p)
    return paths


def collect_converter_input_files() -> list[Path]:
    if not PUBLISHER_INPUT_DIR.exists():
        return []
    return sorted(PUBLISHER_INPUT_DIR.glob("*.md"))


def collect_file_args(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = REPO_ROOT / p
        if not p.exists():
            print(f"❌ File not found: {raw}", file=sys.stderr)
            sys.exit(1)
        if p.suffix != ".md":
            print(f"❌ Not a markdown file: {raw}", file=sys.stderr)
            sys.exit(1)
        files.append(p)
    return files


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _changes_section(results: list[FileResult], lang: str, fix: bool) -> list[str]:
    action = "applied" if fix else "would fix"
    items = [(r, c) for r in results for c in r.changes if c.lang == lang]
    if not items:
        return [f"_No {lang.upper()} changes._", ""]
    lines = [f"#### Changes {action} ({lang})"]
    for r, c in items:
        lines.append(f"- `{rel(r.path)}:{c.line}` — `{c.before}` → `{c.after}`")
    lines.append("")
    return lines


def build_report(results: list[FileResult], fix: bool, scope: str) -> str:
    files_scanned = len(results)
    files_changed = sum(1 for r in results if r.changes)
    en_changed = sum(1 for c in (c for r in results for c in r.changes) if c.lang == "en")
    zh_changed = sum(1 for c in (c for r in results for c in r.changes) if c.lang == "zh")

    lines = [
        "## Spell check summary",
        "",
        f"**Scope:** {scope} | **Files scanned:** {files_scanned} | **Files changed:** {files_changed}",
        "",
        f"### English (British) — {'auto-fix applied' if fix else 'dry run'} ({en_changed} changes)",
        "",
    ]

    changed = [r for r in results if r.changes or r.flags]
    if changed:
        lines.append("| File | EN fixed | ZH fixed | Flagged | Skipped regions |")
        lines.append("|------|----------|----------|---------|-----------------|")
        for r in changed:
            en_n = sum(1 for c in r.changes if c.lang == "en")
            zh_n = sum(1 for c in r.changes if c.lang == "zh")
            skip = ", ".join(sorted(set(r.skipped_regions))) or "—"
            lines.append(
                f"| `{rel(r.path)}` | {en_n} | {zh_n} | {len(r.flags)} | {skip} |"
            )
        lines.append("")

    lines.extend(_changes_section(results, "en", fix))

    all_flags = [(r, f) for r in results for f in r.flags]
    if all_flags:
        lines.append("#### Flagged (needs human decision)")
        for r, f in all_flags:
            lines.append(f"- `{rel(r.path)}:{f.line}` — `{f.text}` — {f.reason}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"### Traditional Chinese — {'auto-fix applied' if fix else 'dry run'} ({zh_changed} changes)")
    lines.append("")
    lines.extend(_changes_section(results, "zh", fix))

    if not any(r.changes for r in results) and not all_flags:
        lines.append("_No issues found._")
        lines.append("")

    return "\n".join(lines)


def build_json(results: list[FileResult], fix: bool, scope: str) -> dict:
    return {
        "scope": scope,
        "fix": fix,
        "files_scanned": len(results),
        "files_changed": sum(1 for r in results if r.changes),
        "files": [
            {
                "path": rel(r.path),
                "changes": [
                    {
                        "line": c.line,
                        "before": c.before,
                        "after": c.after,
                        "lang": c.lang,
                        "applied": c.applied,
                    }
                    for c in r.changes
                ],
                "flags": [
                    {"line": f.line, "text": f.text, "reason": f.reason, "lang": f.lang}
                    for f in r.flags
                ],
                "skipped_regions": r.skipped_regions,
            }
            for r in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Spell-check EC blog posts (EN + zh-TW)")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes to files")
    parser.add_argument("--post", metavar="SLUG", help="Single post directory name or slug")
    parser.add_argument("--drafts", action="store_true", help="Include content/drafts/")
    parser.add_argument("--staged", action="store_true", help="Git staged post/draft files only")
    parser.add_argument(
        "--file",
        metavar="PATH",
        action="append",
        help="Single markdown file (repeatable); e.g. tools/blog-publisher/input/slug.md",
    )
    parser.add_argument(
        "--posts-only",
        action="store_true",
        help="content/posts/ only (skip drafts + converter input); used by dev-check.sh",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--report-file", metavar="PATH", help="Write Markdown report to file")
    args = parser.parse_args()

    if args.file:
        files = collect_file_args(args.file)
        scope = ", ".join(args.file)
    elif args.staged:
        files = collect_staged_files()
        scope = "staged"
    else:
        files = collect_post_files(args.post)
        scope = args.post or "all posts"
        if (args.drafts or not args.post) and not args.posts_only:
            files = sorted(set(files + collect_draft_files()))
            if args.drafts and not args.post:
                scope = "drafts"
            elif not args.post:
                scope = "all posts + drafts"
        if not args.post and not args.posts_only:
            files = sorted(set(files + collect_converter_input_files()))
            if scope == "all posts + drafts":
                scope = "all posts + drafts + converter input"

    if not files:
        print("No files to check.", file=sys.stderr)
        return 0

    results = [process_file(p, fix=args.fix) for p in files]
    report = build_report(results, fix=args.fix, scope=scope)

    if args.json:
        payload = build_json(results, fix=args.fix, scope=scope)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(report)

    if args.report_file:
        Path(args.report_file).write_text(report, encoding="utf-8")

    has_changes = any(r.changes for r in results)
    has_flags = any(r.flags for r in results)
    if not args.fix and has_changes:
        return 1
    if has_flags:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
