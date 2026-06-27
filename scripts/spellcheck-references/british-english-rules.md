# British English rules (EC blog)

Applies to **Latin-script segments** in post body and draft markdown. Implemented by [`../check-spelling.py`](../check-spelling.py).

---

## Auto-fix (high confidence)

Word-boundary AE → BE replacements, case-preserving:

| American | British |
|---|---|
| organize, organized, organizing | organise, organised, organising |
| organization, organizations | organisation, organisations |
| recognize, recognized, recognizing | recognise, recognised, recognising |
| realize, realized, realizing | realise, realised, realising |
| behavior, behaviors, behavioral | behaviour, behaviours, behavioural |
| color, colors, colored, coloring | colour, colours, coloured, colouring |
| favorite, favorites | favourite, favourites |
| center, centers, centered, centering | centre, centres, centred, centring |
| defense, defenses | defence, defences |
| analyze, analyzed, analyzing | analyse, analysed, analysing |
| traveling, traveled, traveler | travelling, travelled, traveller |
| modeling, modeled | modelling, modelled |
| labeling, labeled | labelling, labelled |
| canceling, canceled | cancelling, cancelled |
| honor, honored, honoring | honour, honoured, honouring |
| labor | labour |
| neighbor, neighbors | neighbour, neighbours |
| fulfillment | fulfilment |
| data center, data centers | data centre, data centres |

Phrase replacements (EC prose):

| American | British |
|---|---|
| driving license | driving licence |
| full license | full licence |
| full driving license | full driving licence |

---

## Never auto-fix (allowlist)

Computing and established terms:

- `program`, `programming`, `pair programming`, `programmer`
- Language and framework names
- Cloud product names as published (AWS, Azure, GCP official spelling)
- File paths, slugs, URLs, code identifiers

---

## Never auto-fix (phrase allowlist)

Do not change `center` inside product / brand names:

- `Management Center`
- `Update Management Center`
- `Update management center`
- `Managment Center`
- `Azure Update Management Center`
- `Cost Center`

---

## Flag only (do not auto-fix)

| Pattern | Notes |
|---|---|
| `license` (other contexts) | UK noun = `licence`; verb = `license` |
| `program` vs `programme` | Computing = `program`; TV/events = `programme` |
| `-ize` in proper nouns | e.g. company names |

---

## Protected regions

Never modify text inside:

- YAML front matter
- Fenced / inline code
- Markdown link URLs, raw URLs
- Hugo shortcodes

Link **anchor text** is checked if English.

---

## Examples from corpus

| File | Before | After | Action |
|---|---|---|---|
| `devops-interview-1` | organization culture | organisation culture | auto-fix |
| `ms-csa-5` | data center | data centre | auto-fix |
| `ms-csa-4` | Update management center | — | skip (product name in link) |
| `bribie-island` | driving license | driving licence | auto-fix |
