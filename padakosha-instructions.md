# Padakosha Build Instructions
*(Paninian word-level Sanskrit grammar lexicon — JSON data + standalone HTML viewer)*

This document supersedes the original one-paragraph brief (`Claude-instruction.txt`). It
folds in everything learned building the **Ramayana Padakosha** (Valmiki Ramayana, Bala
Kanda, Sarga 1 — 79 shlokas, 643 words) so the same workflow can be replicated cleanly
for a new text or a new sarga, without re-discovering the same bugs.

---

## 1. Goal

Turn a classical Sanskrit text (padapatha-style verse JSON, a scanned PDF, or pasted
source) into:
1. A **single master JSON file** — one entry per unique word-form, covering every verse
   processed so far.
2. A **standalone HTML viewer** that loads that JSON (via same-folder auto-fetch or a
   file picker) and lets a reader browse by verse, search, and click through to
   Ashtadhyayi.com for grammar references.

## 2. Naming & file convention

- **One JSON file per text**, named descriptively (e.g. `Ramayana Padakosha.json`).
  Always **append/extend** the single file as more verses are processed — never create
  per-verse-range files (no `sarga1-verse-041-060.json`). The viewer is generic and
  reads `corpus_meta` + `words`, so it stays correct automatically as the file grows.
- Keep a working copy in `/home/claude/lexicon.json` mirroring the output file; copy to
  `/mnt/user-data/outputs/<Name>.json` only once a batch is fully validated.
- `corpus_meta.verses_covered` (e.g. `"1-40"`, `"1-79"`) must be updated on every merge —
  the viewer's title/header render from this field, not from a hardcoded string.

## 3. Word schema

Every entry needs exactly these keys (no more, no fewer — validate this mechanically
before merging):

```json
{
 "word": "तपःस्वाध्यायनिरतम्",
 "iast": "tapaḥsvādhyāyaniratam",
 "verses": [1],
 "word_type": "समासः (कर्मधारय-सप्तमीतत्पुरुषः)",
 "pratipadika": "तपःस्वाध्यायनिरत",
 "dhatu": "",
 "dhatu_gana": "",
 "meaning_en": "devoted/absorbed in penance and Vedic self-study",
 "gender": "पुंल्लिङ्गम्",
 "number": "एकवचनम्",
 "case": "द्वितीया",
 "paradigm": "रामशब्दवत् (अकारान्त पुंल्लिङ्ग)",
 "samasa_type": "सप्तमीतत्पुरुषः (तपसि स्वाध्याये च निरतः)",
 "samasa_split": "तपः + स्वाध्याय + निरतः",
 "samasa_component_meanings": {
   "तपः": "penance/austerity",
   "स्वाध्यायः": "Vedic self-recitation/study",
   "निरतः": "absorbed in, devoted to"
 },
 "pratyaya": "क्त (निरत में)",
 "ashtadhyayi_ref": "2.1.40",
 "ashtadhyayi_url": "https://ashtadhyayi.com/sutraani/2/1/40",
 "notes": ""
}
```

**Language policy:** `meaning_en` is English; every other field is Sanskrit
(Devanagari). Keep this in `corpus_meta.language_policy` too.

**`verses` is a list, not a set.** If a word occurs twice in one verse, list that verse
number twice (`[46, 46]`) — occurrence-counting during validation (§6) depends on this.

**Dedup rule:** one entry per unique *inflected form*. Rama in nominative/accusative/
genitive/instrumental are **four separate entries** (रामः / रामम् / रामस्य / रामेण), each
extended with more verse numbers as that exact form recurs. Do not collapse inflections
into one lemma — the whole point is word-level grammar, not lemma frequency.

**Polysemy:** if the same surface form recurs with a genuinely different sense (e.g.
वरम् = "the best" in one verse vs. "a boon" in another), keep it as **one entry** with
both verse numbers, and flag the two senses in `notes` rather than duplicating the word.

**`ashtadhyayi_ref`/`ashtadhyayi_url`:** best-effort category-level reference (samasa
type, krt/taddhita affix governing rule), using the confirmed URL pattern
`https://ashtadhyayi.com/sutraani/{adhyaya}/{pada}/{sutra}`. State plainly in
`corpus_meta.important_disclaimer` that exact sutra numbers for complex derivations
should be cross-verified on the site, since not every word gets a live lookup.

## 4. Processing workflow (per batch of ~10 verses)

1. **Extract raw verse text** from the source JSON (`data[kanda][sarga][shloka]`),
   tokenize by whitespace.
2. **Identify sandhi-fused tokens** and split each into citation-form (undo-sandhi)
   constituents. Common patterns seen in this build:
   - विसर्ग/जश्त्व changes before voiced sounds: `वाक्यम् सम्यक् रामः` etc. resolve to the
     dictionary form (`सम्यक्` not `सम्यग्`).
   - vowel sandhi: `चैव`→च+एव, `चाप्य्`→च+अपि, `तत्रैव`→तत्र+एव, `नैच्छत्`→न+ऐच्छत्,
     `सप्तैकेन`→सप्त+एकेन, `अस्त्रेणोन्मुहम्`→अस्त्रेण+उन्मुहम्.
   - nasal/other nuances: त्→न् before nasals (`आयान्`→आयात्), त्→द्/ज् before voiced
     stops (`ईयाज्`→ईयात्, `वचनाद् धत्वा`→वचनात् हत्वा).
   - **A raw token that splits into N parts contributes N to that verse's expected
     occurrence count** — this matters for validation (§6).
   - Editorial calls (stray spacing merged into one compound, apparent transcription
     anomalies normalized) are legitimate — just record the reasoning in `notes` rather
     than silently guessing.
3. **Cross-check every token against the existing word list** (exact string match,
   case-sensitive) before writing a new entry:
   - Already exists → note it for the **extend pass** (§5), don't create a duplicate.
   - New surface form → write a full entry per §3.
4. **Author new entries in batches** as Python `list[dict]` files
   (`build_words_N.py`), not by hand-editing the JSON directly — this keeps entries
   diffable and re-runnable.
5. **Validate schema mechanically** before merging: every entry has exactly the 19
   required keys, no extras, no missing.

## 5. The extend pass — the step that's easy to skip

**This is where nearly every bug in this build came from**, across multiple rounds.
Function words (सः, च, एव, तेन, ततः, तदा, तत्, तस्य, ह, आस, इति, नाम, तत्र, पुनः, यथा, तथा,
न...) recur constantly, and a batch of new verses will re-use dozens of words that were
already created in earlier verse ranges. A merge script's automatic collision detection
**only catches a repeat if it appears twice within the same merge run** — it does
**not** know that सः already has verses `[16]` from three batches ago and needs `21`
appended now.

So: after merging new-word batches, do a **separate, explicit extend pass** —
a plain Python dict of `{word: [verses_to_append]}`, built by re-reading your own
verse-by-verse token analysis and asking, for every function word and every recurring
content word: *does this word already exist, and does it appear again in this batch?*

Do this pass **before** trusting anything is done — never skip straight to validation
assuming the merge script caught everything.

## 6. Validation — the mechanical safety net

Manual bookkeeping *will* have errors (this build needed 2–3 correction rounds per
batch, every time). Catch them automatically instead of trusting the plan:

1. For each verse, compute the **expected occurrence count** = raw token count +
   (number of extra words produced by sandhi splits in that verse). Derive this
   directly from your token/split analysis in §4, not from memory.
2. After merging + extending, use a `Counter` over every `verses` list in the lexicon
   to get the **actual** occurrence count per verse.
3. Any mismatch pinpoints exactly which verse has a missing extend, a duplicate, or a
   wrongly-attributed verse number. Print expected vs. actual per verse; fix; re-run.
4. Also check: **no duplicate `word` keys** anywhere in the file, and **full schema
   conformance** (all 19 keys, nothing extra) on every entry, including old ones.
5. Only copy to the output path once every verse in the batch shows `OK`.

This check is non-negotiable — every batch in this build had real errors that only this
counting method surfaced (wrong verse attributions, forgotten extends, double-counts
from a word being combined in its own batch definition *and* separately extended).

## 7. Viewer (HTML)

- Single self-contained HTML file, generic across texts — reads `corpus_meta` (title,
  kanda/sarga, verses_covered, disclaimer) and `words` from the JSON at runtime, so nothing
  needs to be hardcoded or regenerated as the lexicon grows.
- Supports both same-folder auto-fetch and a file-picker fallback (for portability/
  sharing outside the sandbox).
- Verse filter chips, free-text search (should match `word` and `iast` at minimum),
  and a header status line reporting words-loaded count — useful as an eyeball sanity
  check alongside the mechanical validator.
- Ashtadhyayi references should be live outbound links (`ashtadhyayi_url`), not just
  displayed text.

**Test before presenting:** serve the test folder locally
(`python3 -m http.server PORT`) and drive it headlessly (Playwright:
`chromium.launch()`), in the **same bash call** as the server launch — each
`bash_tool` invocation is a fresh shell, so a server started in one call is dead by the
next. Check: word count matches the JSON, a verse-filter chip returns the right count,
a search hits the expected entries, and `page.on('pageerror')` is empty.

## 8. Output

- Copy the validated `lexicon.json` to `/mnt/user-data/outputs/<Name>.json`, present it
  via `present_files`.
- Keep the working copy and all `build_words_N.py` / merge / validation scripts in
  `/home/claude/` for the next session to resume from — the next batch just needs the
  next verse range, not a rebuild from scratch.
