# -*- coding: utf-8 -*-
changelog_path = "CHANGELOG.md"
state_path = "PROJECT_STATE.md"

with open(changelog_path, encoding="utf-8") as f:
    ch = f.read()

anchor = "# Changelog\n"
assert ch.startswith(anchor), "changelog anchor missing"

new_entry = """
## v0.18 — Stage 47 Three new deterministic dictionary-lookup normalizations, closing known gap #15

- Opened at the user's request ("#15") to take up "the broader spelling-normalization item" next: gap #15's two long-documented, empirically-observed-but-unaddressed SKD/Apte spelling conventions (guttural/anusvāra alternation; Bengali-typesetting consonant gemination), plus the वीर्य/आत्म citation-form mismatch Stage 45 found while wiring Pratyaya attestation.
- **Empirically verified all three, and their real impact, against the actual Library files before writing any engine code** (per the project's standing methodology): confirmed in `skd_entries.json`/`apte_entries.json` that SKD spells the guttural nasal explicitly before a class stop (e.g. "puNgavaH", not "puMgavaH" — matching the classical Pāṇinian parasavarṇa rule 8.4.58) and geminates the non-र् member of any र्-adjacent conjunct (e.g. "DarmmaH"/"puttraH" — and, newly confirmed this cycle, "vIryyaH"-family spellings of वीर्य itself); and traced वीर्य's Apte-side gap to a third, narrower pattern: Apte cites it "vIryaM" (an anusvāra-spelled neuter-singular "-am" ending), one of two interchangeable spellings of the same citation ending the Stage-42 visarga-only strip did not yet cover.
- **Added three module-level, symmetric, deterministic SLP1 transforms** (`_slp1_citation_ending_stripped`, `_slp1_guttural_normalized`, `_slp1_gemination_normalized`) and rewired `_dictionary_attest_word` to try, per dictionary, up to six ordered candidates (exact; citation-ending-normalized; guttural-normalized; guttural+citation; gemination-normalized; gemination+citation), each checked against both a dictionary's raw headword index and its citation-ending-normalized index (both loaders' former visarga-only stripped index widened from stripping only trailing {H} to stripping one trailing {H, m, or M} — the same category of nominal-ending equivalence as the original Stage-42 visarga strip, not new guesswork). None of the three transforms infers gender, stem class, or declension: `_slp1_citation_ending_stripped` only ever removes a single trailing H/m/M already present; the other two are fixed, symmetric letter substitutions that don't depend on what the word means.
- **Result, verified by direct execution against the real 5-verse benchmark**: Component 9 (Samāsa) constituent attestation rose from 8/11 (72.73%) to **10/11 (90.91%)**; Component 8 (Sandhi) rose from 22/33 (66.67%) to **24/33 (72.73%)**; Component 7 (Pratyaya) rose from 9/12 (75%) to **10/12 (83.33%)** — closing the Stage-45-found वीर्य gap (now attested in both SKD, via gemination, and Apte, via the widened citation-ending strip). आत्मन्'s own citation form ("AtmA", a stem-class-specific nominative lengthening no general rule here covers without guessing) and multi-character declensional suffixes (e.g. genitive "-sya", seen on रोषस्य) were deliberately left unresolved — confirmed by direct testing of each, not merely assumed — as still outside this scope.
- Five-śloka structural validation: **PASS for all five verses**, verified by direct execution.
- Evidence coverage: **unchanged at 87.27% (48/55)** — expected and required, since this cycle deepens existing dictionary-attestation sub-evidence rather than promoting any component slot (same category of depth-only gain as Stages 38–45; see known gap #9).
- Rulebook citation count unaffected (still 26).
- **Closes known gap #15 as originally scoped** (both documented conventions — guttural/anusvāra alternation, Bengali-typesetting gemination — are now handled) **and closes its Stage-45 वीर्य/आत्म addendum for वीर्य specifically**. आत्म's own, distinct stem-class-citation-form issue is split out as a new, narrower, explicitly open item (see gap #15 below) rather than left conflated with the now-closed conventions.

"""

ch2 = ch.replace(anchor, anchor + new_entry, 1)
assert ch2 != ch
with open(changelog_path, "w", encoding="utf-8") as f:
    f.write(ch2)
print("CHANGELOG.md updated, new size:", len(ch2))

with open(state_path, encoding="utf-8") as f:
    st = f.read()

old_header = """- Engine version: **0.17**
- Stage: **45 complete"""
assert old_header in st, "header anchor missing"
new_header = """- Engine version: **0.18**
- Stage: **47 complete — three new deterministic SLP1 normalizations (citation-ending strip generalized from visarga-only to H/m/M; guttural/anusvāra-before-stop; Bengali-typesetting r-adjacent gemination) wired into `_dictionary_attest_word`, closing known gap #15 and its वीर्य addendum; Samāsa constituent attestation 8/11→10/11, Sandhi 22/33→24/33, Pratyaya 9/12→10/12; आत्म split out as a new, narrower, still-open item; see Stage-47 result below**
- Stage: **45 complete"""
st2 = st.replace(old_header, new_header, 1)
assert st2 != st

old_gap15 = "15. **(Stage 42; still open, now affects Apte too as of Stage 43)** Dictionary constituent attestation currently normalizes exactly one systematic spelling convention (a trailing visarga). Two others were observed but deliberately NOT normalized: guttural/anusvāra alternation (the v8.1 breakdown's पुंगवम् vs. SKD's own मुनिपुङ्गवः-family entries, which use ङ्, not ं) and Bengali-typesetting consonant gemination (SKD frequently doubles a consonant after certain conjuncts, e.g. `DarmmaH` for धर्मः, `puttraH` for पुत्रः). Both are real, inspectable, folder-evidenced conventions (not guesses) and would be legitimate, narrowly-scoped candidates for a future cycle. Stage 43 confirmed this gap applies identically to Apte lookups (पुंगवम्, रोषस्य, विधं remain unattested in both dictionaries) — adding a second dictionary did not, and structurally could not, close this category of gap; only a normalization pass would. Deliberately left undone across both Stage 42 and Stage 43 (see README's \"no fuzzy matching\" and the project's standing preference for one well-scoped change per cycle). **Stage 45 update**: a third, distinct citation-form convention was found affecting Component 7 (वीर्य/आत्म not matching these dictionaries' own citation forms) — same category of gap, a different specific convention, still open."
assert old_gap15 in st2, "gap15 anchor missing"
new_gap15 = ("15. ~~Dictionary constituent attestation normalized only a trailing visarga; guttural/anusvāra alternation (पुंगवम् vs. पुङ्गव-spellings) and Bengali-typesetting consonant gemination (DarmaH/DarmmaH, putraH/puttraH) were observed but not normalized~~ — "
             "**closed in Stage 47**: three new deterministic SLP1 transforms (`_slp1_citation_ending_stripped` — the old visarga-only strip generalized to any trailing H, m, or M; `_slp1_guttural_normalized`; `_slp1_gemination_normalized`) now cover both conventions, verified against the real SKD/Apte data (see Stage-47 CHANGELOG entry for the exact before/after attestation counts). "
             "**Also closes, for वीर्य specifically, the Stage-45 addendum below.** रोषस्य (genitive `-sya`) remains an open, out-of-scope multi-character declensional suffix, confirmed unresolved by direct testing, not merely assumed.")
st3 = st2.replace(old_gap15, new_gap15, 1)
assert st3 != st2

# New, narrower item for what Stage 47 deliberately left open (आत्म's own
# citation form) -- appended as its own numbered continuation of the gap
# list rather than left folded into the now-closed gap #15/#16 text.
old_gap16_tail = "**New sub-finding from Stage 45**: वीर्य (1.1.2) and आत्म (1.1.4) — ordinary, unremarkable stems — failed to attest, apparently because these dictionaries cite them in an inflected/stem-final form a bare query doesn't match (distinct from the visarga-stripping already handled since Stage 42). Recorded as a further instance of gap #15 (citation-form/spelling normalization), not fixed this cycle."
assert old_gap16_tail in st3, "gap16 tail anchor missing"
new_gap16_tail = ("**Sub-finding from Stage 45, updated Stage 47**: वीर्य and आत्म — ordinary, unremarkable stems — initially failed to attest. "
                  "**वीर्य is now resolved** (Stage 47, via the widened citation-ending strip and the new gemination normalization — see gap #15). "
                  "**आत्म remains open** as new gap #17: SKD cites it \"AtmA\" (a masc. n-stem-specific nominative lengthening, आत्मन् → आत्मा), which is a genuine stem-class-specific citation form, not a spelling-convention alternation — resolving it would require guessing declension class from the bare stem alone, which this project's no-fuzzy-matching / no-gender-guessing policy (see `_dictionary_attest_word`'s own docstring) deliberately does not do. A legitimate candidate for a future cycle only if a non-guessing approach is found (e.g. an explicit stem-class annotation already present elsewhere in the Library data).")
st4 = st3.replace(old_gap16_tail, new_gap16_tail, 1)
assert st4 != st3

with open(state_path, "w", encoding="utf-8") as f:
    f.write(st4)
print("PROJECT_STATE.md updated, new size:", len(st4))
