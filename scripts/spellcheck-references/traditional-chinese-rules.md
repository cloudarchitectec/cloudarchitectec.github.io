# Traditional Chinese typo rules (EC blog)

Implemented by [`../check-spelling.py`](../check-spelling.py) — **auto-fix high-confidence patterns**; flag uncertain cases in report.

---

## What to scan

- Post body markdown (below front matter)
- Draft files: `index.md`, `outline-cursor.md`, `data-table.md`

**Skip:** front matter, URLs, code blocks, Hugo shortcodes.

---

## Auto-fix (high confidence)

Literal replacements and patterns validated on EC corpus:

| Before | After | Category |
|---|---|---|
| 不段 | 不斷 | 形近字 |
| 詳請請 | 詳情請 | 重複用字 |
| 詳請可以 | 詳情可以 | 音近/形近 |
| 跟本 | 根本 | 音近字 |
| 的的 | 的 | 重複用字（中文字間） |
| 匯入工的 | 匯入員工的 | 漏字 |
| 回隨之 | 會隨之 | 形近字 |
| 做為 | 作為 | 做/作（= as） |
| 澳元 | 澳幣 | Established 用語（AUD 中文） |
| 寫程式的的女孩 | 寫程式的女孩 | 重複用字 |

### CJK ↔ Latin/digit spacing (auto-fix)

Insert a space between Chinese characters and adjacent English words or numbers. **Skip** when the touching character is Chinese punctuation (e.g. `，NSW`、`(約`、`/年`).

| Before | After |
|---|---|
| `NSW約9.5萬` | `NSW 約 9.5 萬` |
| `，NSW約` | `，NSW 約` |
| `(約186萬台幣)/年` | `(約 186 萬台幣)/年` |
| `9.3萬澳幣` | `9.3 萬澳幣` |

### Product / ticker compounds (no internal spacing)

- `0050正2`, `正2`, `00631L` — treat as atomic tokens in spacing pass

### Foreign currency (auto-fix to Chinese)

Prose format: `{amount} {幣別}(約 {TWD} 台幣)` — e.g. `699 紐幣 (約 7100 台幣)`

| Before | After |
|---|---|
| `699NZD` | `699 紐幣` |
| `NZD $17` | `17 紐幣` |
| `$49NZD` | `49 紐幣` |
| `40FJD` | `40 斐濟幣` |
| `(約台幣 7100)` | `(約 7100 台幣)` |
| `約台幣 240 萬` | `約 240 萬台幣` |
| `$280 台幣` | `280 台幣` |

Codes mapped: NZD→紐幣, AUD→澳幣, USD→美元, NTD/TWD→台幣, FJD→斐濟幣. Official data tables with `$` may stay as-is when no code suffix.

### EC emoticons (no space before)

`XD`, `XDD`, `QAQ`, `lol`, `LOL`, … — treat as atomic; no space after preceding Chinese (e.g. `啊XD`, `折磨QAQ`, `真難lol`).

### Colloquial 萬 amounts (auto-fix)

Oral shorthand `{digit} 萬 {digit}` → Chinese digits without spaces (e.g. `澳幣 6 萬 5` → `澳幣六萬五`, `5 萬 6 台幣` → `五萬六台幣`).

**Arabic numeral amounts keep spaces** (see CJK ↔ Latin/digit spacing): `9.3 萬澳幣`, `約 186 萬台幣`, `22.5 萬澳幣 (約 450 萬台幣)` — do **not** compact to `9.3萬澳幣` or `約450萬台幣`.

Agent may add new patterns here after EC confirms a recurring typo.

---

## Flag only (do not auto-fix)

- Intentional 口語、諧音、自嘲（估狗、棄了了）
- Nicknames and persona labels
- EC voice choices（XD、lol、括號碎念）
- 的/得/地、在/再 when context-dependent
- 簡體字 — flag only

---

## Report

After `--fix`, report lists **Changes applied (Chinese)** and any **待確認** items. Same mandatory report as English pass.

---

## Corpus examples (auto-fix)

| File:line | Before | After |
|---|---|---|
| `2023-09-23-qld-first-home-1/index.md:39` | 不段上漲 | 不斷上漲 |
| `2023-09-23-qld-first-home-1/index.md:45` | 詳請請參考 | 詳情請參考 |
| `2019-09-20-my-portfolio-website/index.md:27` | 跟本超難 | 根本超難 |
| `2019-09-20-my-portfolio-website/index.md:85` | 首頁的的 | 首頁的 |
| `2024-09-01-nz-day3/index.md:68` | 不段扛著 | 不斷扛著 |
| `2024-12-16-will/index.md:23` | 詳請請見 | 詳情請見 |
| `2024-02-19-devops-2023-2024-salary/index.md:70` | 詳請請參考 / 匯入工的 / 回隨之 | 詳情請參考 / 匯入員工的 / 會隨之 |
| `2023-05-07-2023-life/index.md:26` | 詳請可以 | 詳情可以 |
| `2026-06-17-retirement-plan/index.md:91` | 該放倉庫的的放 | 該放倉庫的放 |
| `2023-01-21-eng-interview/index.md:64` | 做為 | 作為 |
