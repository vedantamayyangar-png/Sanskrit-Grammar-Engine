# -*- coding: utf-8 -*-
changelog_path = "CHANGELOG.md"
state_path = "PROJECT_STATE.md"

with open(changelog_path, encoding="utf-8") as f:
    ch = f.read()

anchor = "# Changelog\n"
assert ch.startswith(anchor), "changelog anchor missing"

new_entry = """
## (no engine version change) — Stage 46 Exhaustive search for the missing v0.2 template file, closing known gap #5 as confirmed-absent rather than leaving it open

- Opened at the user's request ("#5") to continue the 10-component setup work by chasing the last remaining item on the open-gaps list: Stage 33's flagged possibility that `Ramayana_BalaKanda_1.1.2-1.1.5_template_test_v0.2_library_only.json` — cited by name only in some very early, since-cleaned-up `KNOWN_FORM_EVIDENCE` citation strings — might exist somewhere and could resolve the v0.1 template file's 1.1.2 padaccheda undercount (13 words vs the authoritative 15).
- **Searched exhaustively, not just re-asserted the prior finding.** Checked both connected locations in full: `E:\\Sanskrit & Tamil Scholarship` and `D:\\python`, by exact filename, by every plausible variant (`*v0.2*`, `*library_only*`, `*template_test*`, `*BalaKanda*`, `*1.1.2-1.1.5*`), and — new this cycle — by listing the contents of every one of the ~90 zip archives reachable in either location (the Stage 16–19/32 engine-history zips, the Sanskrit_Relational_Corpus Stage 1–14 zips, and `Sanskrit_Interactive_Corpus_Source_Package.zip`) rather than assuming Stage 36's zip check (which only tested whether those zips *used* the rulebooks) also covered this. Zero matches anywhere.
- **Traced the citation's origin** to confirm it isn't quietly still influencing live evidence: the only surviving reference to this filename in `sanskrit_grammar_engine.py` is a single historical comment (near `LIBRARY_TEMPLATE_FILENAME`) explaining that *earlier-stage* citation strings once named it; no `KNOWN_FORM_EVIDENCE` entry or Library loader currently cites or depends on it. Confirmed the file's absence is not silently degrading anything currently in use.
- **Re-examined what the gap actually affects.** Component 1 (Padaccheda) — the project's authoritative word inventory per its own principles — is sourced from `sa_rAmAyaNa.txt`, not from the v0.1 template file, and is already correct for 1.1.2 (15 words, `SOURCE_ASSERTION`). The template file's own internal Component-1 copy being short by one word only affects a secondary, informational cross-validation check, which the engine already reports as a non-fatal warning ("likely a stale/incomplete padaccheda in the template artifact itself, not an engine defect") rather than an error — confirmed by re-running the benchmark and reading that warning directly rather than assuming its severity.
- **Conclusion: this is a confirmed-absent artifact affecting a cosmetic secondary discrepancy, not an open content gap blocking real evidence.** No code change was made — there is nothing to safely wire in, and per this project's no-fabrication policy a missing file is reported as missing, not guessed at or reconstructed. Recommended next step, if the user wants this fully closed rather than just downgraded: check any old local backups/drives outside the two locations this session can currently reach, since both connected locations and every reachable archive are now confirmed clear.
- No engine code changed this cycle; `ENGINE_VERSION` remains **0.17**. This entry exists to record a completed, verified investigation so it is not re-attempted from scratch in a future cycle.

"""

ch2 = ch.replace(anchor, anchor + new_entry, 1)
assert ch2 != ch
with open(changelog_path, "w", encoding="utf-8") as f:
    f.write(ch2)
print("CHANGELOG.md updated, new size:", len(ch2))

with open(state_path, encoding="utf-8") as f:
    st = f.read()

old_gap5 = "5. Resolving the 1.1.2 padaccheda undercount in the v0.1 template file (see Stage-33 result above), ideally by locating the referenced v0.2 template file."
assert old_gap5 in st, "gap5 anchor missing"
new_gap5 = ("5. ~~Resolving the 1.1.2 padaccheda undercount in the v0.1 template file, ideally by locating the referenced v0.2 template file~~ — "
            "**searched exhaustively in Stage 46: confirmed absent everywhere reachable** (both connected locations in full, plus every zip archive in either, by exact name and every plausible variant). "
            "**Downgraded, not closed as fixed**: this does not affect any live evidence — Component 1 for 1.1.2 is already correct from its true authoritative source (`sa_rAmAyaNa.txt`), and the template file's own short internal copy only affects a secondary cross-validation check already reported as a non-fatal warning. "
            "Would need a source outside this session's two currently-reachable locations (e.g. an old local backup) to fully close.")
st2 = st.replace(old_gap5, new_gap5, 1)
assert st2 != st

with open(state_path, "w", encoding="utf-8") as f:
    f.write(st2)
print("PROJECT_STATE.md updated, new size:", len(st2))
