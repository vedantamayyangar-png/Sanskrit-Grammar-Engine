# Dhaturupa Manjari & Sabdamanjari Extraction — Project State

## Current state — Sabdamanjari track (ACTIVE as of this session)

- Target file: `sabdamanjari.json` (same folder as this doc's parent).
- Source: `E:\Downloads\Sabdamanjari.pdf`, 116 pages, no text layer.
- **Section 1 (अजन्त पुंलिङ्ग साधारण शब्दाः): COMPLETE.** 11 words (राम, देव, हरि, मुनि, शम्भु, गुरु, धातृ, पितृ, भ्रातृ, गो, ग्लौ), PDF pp.6-12.
- **Section 2 (अजन्त स्त्रीलिङ्ग साधारण शब्दाः): COMPLETE.** 10 words (रमा, मति, गौरी, नदी, धेनु, वधू, मातृ, स्वसृ, द्यो, नौ), PDF pp.12-17.
- **Section 3 (अजन्त नपुंसकलिङ्ग साधारण शब्दाः): COMPLETE.** 8 words (वन, नगर, दधि, वारि, शुचि, मधु, मृदु, कर्तृ), PDF pp.17-21.
- **MILESTONE: भाग-1 "साधारण शब्दाः" (ordinary words) fully closed — 29 words total.**
- **Section 4 (अजन्त पुंलिङ्ग विशेषशब्दाः — भाग-2 "विशेष शब्दाः" begins): COMPLETE.** 20 words (ऐक्ष्वाक, निर्जर, दन्त, पाद, यूष, मास, विश्वपा, हाहा, औडुलोमि, पति, सखि, प्रधी, वातप्रमी, सुधी, सेनानी, क्रोष्टु, वर्षाभू, स्वभू, नृ, रै), PDF pp.22-33. See CHANGELOG.md for detail — several two-track irregular words, one corrected cell (औडुलोमि), one reconstructed cell (नृ), one illegible grouped-name (वर्षाभू).
- **Next: Section 5 (अथ अजन्त स्त्रीलिङ्ग विशेष शब्दाः, special feminine words), starting word #50 अम्बा, PDF p.34.**
- Schema: top-level `sections` key, each section an object with `words[]`; each word has `declension_table` (8 rows: 7 विभक्तिs + संबोधनम्, ×3 numbers), Tamil+English meaning, `grouping_note`, optional `rule_note`/`note`. See `sabdamanjari.json` itself for the worked template — do not assume it matches `dhaturupa_manjari.json`'s गण-based shape, this is a different book with a different structure (numbered words, not गणs).
- Note: a separate, pre-existing `vibhakti_table.json` already exists in this folder (used by `generate_10component_quality_report.py`) — independently authored, NOT to be merged with `sabdamanjari.json`. See that file's own `related_files` block.
- Rendering/reading method identical to the Dhaturupa Manjari track below (pypdfium2 via `D:\python\python.exe`, scale 3.0 normal / up to 10.0 for disputed glyphs).

## Dhaturupa Manjari track (PAUSED — resume when asked; not superseded)

- Target file: `dhaturupa_manjari.json` (same folder as this doc's parent)
- **All 10 गणs (सार्वधातुकप्रकरण) are complete** — see prior CHANGELOG entries.
- **आर्धधातुकप्रकरण: IN PROGRESS**, new top-level JSON key `ardhadhatuka_prakarana` (a sibling of `ganas`, NOT nested inside it — this section is organized लकार-by-लकार across all गणs together, not गण-by-गण, per the book's own structure).
  - **लुट् (First Future): COMPLETE.**
  - **लृट् (Second Future): COMPLETE**, including a valuable 32-root comparison table (लुट्/लृट्/लृङ् 3rd-sg. side by side).
  - **लृङ् (Conditional): COMPLETE.**
  - **आशीर्लिङ् (Benedictive): COMPLETE**, including 5 special root-change rules.
  - **लिट् (Perfect): PARTIAL.** Its own 7 rules (द्वित्वलिट् vs अनुप्रयोगलिट् distinction) captured. द्वित्वलिट् (reduplicative): प्रत्यय table + भू/भाष् examples + **16 numbered special-root-groups** (each a full 3×3 table + "एवं...रूपाणि" grouping note) captured — PDF pp.131-135. **The book's own sequence continues past group #16** (root #16 चि is marked "प्रथमं रूपम्", implying more follows) — not yet reached. **अनुप्रयोगलिट् (periphrastic) has NOT been captured at all.**
  - **लुङ् (Aorist, 7 traditional प्रकरणs): NOT STARTED.**

## Where things are (PDF page ranges, confirmed by direct reading)

- PDF p.120 closes गण 7 AND the whole सार्वधातुकप्रकरण ("इति रुधादिः" + "इति सार्वधातुकप्रकरणम्").
- PDF p.121 opens आर्धधातुकप्रकरण directly after, with सेट्/अनिट्/वेट् इट्-आगम rules, then लुट्.
- लुट्: PDF p.121-122. लृट्: PDF p.122-124 (includes the comparison table spanning several pages). लृङ्: PDF p.125-126 (shares the comparison table). आशीर्लिङ्: PDF p.126-128 (ब्रेक्स into special rules on what would be book p.124, printed mid-section). लिट् starts PDF p.130, द्वित्वलिट् examples run PDF pp.131-135+ and continue further.

## Schema note for this new section

`ardhadhatuka_prakarana` uses a different shape than `ganas`: no गण subdivision, instead one object per लकार (`lut_prathama_bhavishyat`, `lrt_dvitiya_bhavishyat`, `lrn_sanketa`, `ashirlin_benedictive`, `lit_paroksha_bhuta`, `lun_aorist`), each with its own `pratyaya` (general personal-ending table, both पदs) and `examples` (root-specific forms, tagged with `sanjna`: सेट्/अनिट्/वेट्). लिट् additionally nests `dvitva_lit`/`anuprayoga_lit`. This mirrors how the book itself organizes the section — verify against the book's own layout before assuming any other लकार follows exactly the same shape (आशीर्लिङ् and लिट् already needed extra fields: `special_root_rules`, `rules`, `special_root_groups`).

## Known gaps / flagged low-confidence cells

1. PDF page 83 (गण 3, root #8 दा's परस्मैपद table) — confirmed missing page.
2. गण 4 root list #17 (फुल्ल्) — degraded scan, reconstructed with a flag.
3. गण 7's अञ्ज्/तृह् — a few cells read at moderate confidence.
4. **New this session**: लृट् comparison table's root #2 (कृप्) cells, and लिट् group #13 (कृप्, second root of same name in this section) — both read at moderate confidence from dense/small-print scan regions, flagged in their own `note` fields. Group #2's (अर्च्) grouped-root list also had some partially-illegible names.

## Next-cycle protocol

1. Read this file, `README.md`, `CHANGELOG.md`, and `dhaturupa_manjari.json`'s `ardhadhatuka_prakarana` key as the schema template.
2. **Continue द्वित्वलिट्'s special-root-groups past #16** (PDF p.135+) until it concludes.
3. **Capture अनुप्रयोगलिट्** (its own प्रत्यय table + examples, likely using कथ्/भू/अस्/कृ per the rules already captured).
4. **Start लुङ् (Aorist)** — 7 traditional प्रकरणs (formation varieties), likely a substantial task comparable in scope to लिट्. Render forward from wherever अनुप्रयोगलिट् ends to locate it (previous, now-superseded estimate was book pp.140-159 — re-confirm against actual content, don't assume the old estimate still holds precisely given this session's page-range findings).
5. Follow the established schema; deliver incrementally; update this file and `CHANGELOG.md`; validate the JSON:
   ```powershell
   $obj = Get-Content -Raw -Encoding UTF8 "dhaturupa_manjari.json" | ConvertFrom-Json
   ```

## Open items

1. **द्वित्वलिट् groups #17+ and अनुप्रयोगलिट् — the immediate next task.**
2. **लुङ् (Aorist) — after लिट् is fully closed.**
3. गण 2's remaining 19 परस्मैपदी roots (optional completeness pass).
4. The flagged low-confidence cells listed above (optional re-verification pass).
5. End matter (book p.160+ / PDF pp.~161-167) — not examined.
6. Sabdamanjari.pdf — **STARTED** (user explicitly asked to switch this
   session). See the "Sabdamanjari track" section at the top of this file
   and CHANGELOG.md for current status (section 1 of many complete).
