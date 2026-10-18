# -*- coding: utf-8 -*-
"""
Reverse-sandhi candidate generator.

Coverage status:
  svara_sandhi   (9/9 rules addressed) -- svara-1..6 general pattern
      generators; svara-7/8 are narrow lexical-exception lookups (not
      general phonological patterns -- see their docstrings); svara-9
      is a guard function (is_pragrhya_no_sandhi_context), not a generator.
  visarga_sandhi (7/8 actionable rules addressed; visarga-0 is an intro,
      not a rule) -- visarga-1..5 as before; visarga-2 (optional sibilant
      assimilation) added; visarga-4b/visarga-6 implemented as a separate
      inter-word boundary-elision helper (restore_elided_visarga_at_word_
      boundary), since those two rules ELIDE the visarga rather than
      fusing two words into one string -- there is nothing to "split".
      visarga-7 is a pronunciation-only allophone with no spelling change,
      already covered by visarga-1's surface pattern; documented, no code.
  vyanjana_sandhi (11/14 as general/pattern generators + narrow lookups;
      vyan-13 deferred -- rulebook's own examples are "illustrative" only
      and the trigger context would overgenerate heavily as a general
      pattern). vyan-1,2,4,5,6,7,9,12,14 are general pattern generators
      (tested against the rulebook's own worked examples). vyan-8,10 are
      narrow attested-exception lookups, matching the rulebook's own
      hedged language on those two ("by convention of some grammarians'
      teaching order", "broadly... treated under this heading"). vyan-11
      (natva) is NOT a split-point generator like the others -- it's
      mostly a word-INTERNAL phenomenon (see the dedicated
      natva_rulebook.json, reused rather than reinvented) applied AFTER
      a compound boundary is already found, so it's implemented as
      restore_natva_in_right_piece(), a reconstruction-correction helper
      with a different signature (right_piece, left_piece) -> restored
      dictionary form, not (word) -> [(left,right),...].

Design: operates directly on Devanagari surface strings. For each rule,
a trigger pattern detects where the rule *could* have applied; a
candidate-generation function proposes the pre-sandhi (left, right) pieces.
Candidates are validated against the dictionary (validate_against_dictionary)
to prune phonologically-plausible-but-nonexistent splits.

Changelog (Tier-5 pass -- false-positive over-splitting of ORDINARY COMPLETE
WORDS, found by running this tool word-by-word on real verse text (the
first 5 ślokas of sa_rAmAyaNa.txt) for the first time, rather than only
the hand-built 27-word regression corpus Tier-4 was verified against.
Result before this pass: of 64 real words, only ~4 genuine correct splits
against roughly 15-20 false-positive over-splits of words that have no
real internal sandhi at all (मुनिपुङ्गवम्->मुनिपुङ्गउ+अम्; वीर्यवान्->
वीः+यवान्; अस्मिन्->अस्म्+इन्; लोके->ला+उके; सर्वभूतेषु->सः+वभूतेषु;
दृढव्रतः->दृढवृ+अतः; जातरोषस्य->जातः+ओषस्य; नरम्->नः+अम्; श्रोतुं->
शॄ+ओतुं; ज्ञातुम्->ज्ञ+अतुम्; परिपप्रच्छ->पः+इपप्रच्छ; and more).
  - DIAGNOSIS: confirmation category (both/left/right dictionary-validated)
    does NOT reliably distinguish genuine sandhi from coincidental noise
    for an isolated single word -- verified by direct comparison: नरम्
    (wrong, ->नः+अम्) and वाग्विदां (correct, ->वाक्+विदां) are BOTH fully
    both-sides-confirmed; तपःस्वाध्यायनिरतं (correct) and वीर्यवान् (wrong)
    are both left-only-confirmed. No category-threshold or length-based
    heuristic separates them -- this is the expected shape of the problem
    Tier-4's own changelog entry already named as future work (real
    inflected-form indexing), not a new discovery.
  - FIX 1: extended _stem_after_common_inflection with the मतुप्/वतुप्
    (possessive-adjective) pattern (-वान्->-वत्, -मान्->-मत्; see its own
    updated docstring) -- verified against real examples before use
    (वीर्यवान्->वीर्यवत् and आत्मवान्->आत्मवत् resolve; द्युतिमान्-
    >द्युतिमत् does not and is left honestly unresolved, not guessed at).
    Also added एषु (locative plural) to the plain-suffix list, same family
    as the already-present े.
  - FIX 2 (the substantive change): _stem_after_common_inflection's TOP-
    LEVEL restriction (added in Tier-4 specifically to protect वाङ्मयम्)
    is REMOVED -- the guard now runs at entry for the top-level call too,
    same as every nested call. Re-examining वाङ्मयम् under this pass
    showed Tier-4's fix, while directionally motivated, protected the
    wrong thing: वाङ्मय (the stem this guard finds for वाङ्मयम्) is not a
    coincidental false match -- it is itself a real, independently
    attested Sanskrit word ("consisting of speech" / "literature"), so
    वाङ्मयम् is genuinely ambiguous between the compound reading (वाक्+मय)
    and the lexicalized-word reading (वाङ्मय + म्), exactly the same
    category of irreducible local ambiguity this file already declines to
    force-resolve for स्वागतम्/सूर्योदयः (see _rule_priority_key). Given
    that वाङ्मयम् was never a clean counterexample in the first place,
    and given how many genuine real-text over-splits (verified below)
    the top-level restriction was silently permitting, restricting the
    guard to non-top-level calls was the wrong trade for a tool meant to
    run on real text -- reversed.
  - Verified by direct execution, not just re-reading: 32/32 self-test
    suite (which exercises generate_candidates() directly, not this
    ranking/guard path, so unaffected either way) still passes. The
    27-word hand-built corpus (Tier-4's own regression gate) and the full
    64-word real-verse-text word list were BOTH re-run after this change;
    see this file's Tier-5 session notes / the project CHANGELOG entry for
    the exact before/after counts on each, including वाङ्मयम्'s now-
    documented dual reading rather than a single hidden "expected" answer.
  - Known, explicitly NOT fixed by this pass (compound words whose fused
    stem isn't independently headworded, irregular pronoun forms, and
    non-paradigmatic verb forms): दृढव्रतः, जातरोषस्य, जितक्रोधः,
    चारित्रेण, सर्वभूतेषु, अस्मिन्, बिभ्यति, श्रोतुम्, परिपप्रच्छ,
    द्युतिमान् (the one मतुप् form whose citation stem isn't itself
    headworded). Real fixes for these need either compound-member
    analysis or a genuine paradigm-based stemmer, both explicitly future
    work per PROJECT_STATE.md gap #14, not attempted here.

Changelog (Tier-4 pass -- real-dictionary over-splitting, found by running
against sanskrit_dictionary_skd_apte.sqlite (77,413 real SKD+Apte entries)
for the first time, instead of only a synthetic/narrow stand-in. Confirms
this file's own documented prediction (Testing methodology section): "A
synthetic dictionary will always pass more, and differently, than a real
one." A 27-word corpus drawn from 01_Ramayana_Project's benchmark verses
scored only 16/27 (59%) non-recursive, 13/27 (48%) --recursive -- well
below any figure obtained against a narrower dictionary. Three distinct,
separately-diagnosed causes, three separately-scoped fixes:
  - ROOT CAUSE 1 -- arbitrary tiebreak between competing RULES. तल्लीनः
    (should split तत्+लीनः via vyan-14) and वणिग्घसति (should split
    वणिक्+हसति via vyan-8) both had the CORRECT candidate fully generated
    and dictionary-confirmed, but LOST the ranking to a same-category
    competitor purely on the pre-existing len(right) tiebreak (तल्लीनः) or
    on raw insertion order when even the lengths tied (वणिग्घसति). Fixed by
    inserting a new tiebreak, `_rule_priority_key()`, between the existing
    (category, validated-bit) keys and the length tiebreak: when two
    candidates are otherwise tied, the one belonging to the rule with the
    LATER Aṣṭādhyāyī sūtra number wins. This is not an invented heuristic
    -- it is Pāṇini's own conflict-resolution meta-rule, विप्रतिषेधे परं
    कार्यम् ("in a genuine conflict between rules, the later-ordered rule
    prevails", Aṣṭādhyāyī 1.4.2), catalogued as paribhāṣā-12 in
    04_Laghu_Siddhanta_Kaumudi/paribhasha_prakarana_rulebook.json. Applying
    it here is legitimate because vyan-14 (8.4.60) and vyan-8 (8.4.58) are
    genuinely LATER in the grammar's own textual sequence than svara-1
    (6.1.101) and vyan-3 (8.2.39) respectively -- exactly the situation the
    paribhāṣā is for. Citations are read from the SAME `CITATIONS`/
    `SYNTHETIC_CITATIONS` dicts every candidate already carries for display;
    no new citation source was invented. A rule with no parseable
    Aṣṭādhyāyī reference sorts after every cited rule (conservative
    default: never let an uncited guess out-rank a cited one on this key).
  - ROOT CAUSE 2 -- a bare single-character LEFT piece treated as fully
    trustworthy. काले (a plain locative of काल, no internal sandhi at all)
    was carved into क+अले purely because both क (a genuine but unrelated
    headword, the interrogative stem) and अले (a rare Apte-attested
    filler/expletive particle) happen to independently validate. The file
    already treats a single-character RIGHT piece with exactly this same
    skepticism (see the KNOWN_PARTICLES filter above candidates_svara_unified's
    call site) but had no symmetric guard on the LEFT piece. Fixed by
    extending that same length-based skepticism to the left side: a
    single-character left piece is now demoted the same way a
    non-particle single-character right piece already is, so it can no
    longer win purely by both sides coincidentally validating.
  - ROOT CAUSE 3 -- recursing into a right piece that is not sandhi'd at
    all, just an ordinary inflected word absent from the dictionary in its
    inflected form (the dictionary only indexes CITATION forms). मयम्
    (accusative of मय), काले (locative of काल), and करोति (a तनादि-गण
    verb's 3rd-singular present) each got wrongly split further, because
    the existing whole-word guard (`dictionary_lookup(word)['found']`)
    only recognizes a word that IS a citation-form headword outright, not
    one that's merely a citation-form headword plus a common declensional/
    conjugational ending. Fixed by adding `_stem_after_common_inflection()`,
    a small closed list of the most common nominal (locative ए, genitive
    स्य, dative/instrumental-adjacent ाय/ेण/ात्) and verbal (३rd sg./pl.
    present ति/न्ति/ओति, "class 5/8" ओति) endings; if stripping one of
    these from a piece yields a real dictionary stem, the piece is treated
    as an already-complete word and recursion into it stops -- mirroring
    (not replacing) the existing exact-headword guard, applied both at
    entry and at the top of every peeling round. Deliberately narrow and
    non-exhaustive (same "closed-class, not a stemmer" discipline already
    used for KNOWN_PARTICLES) -- a real fix needs indexing inflected forms
    directly (see this file's own recurring-bug-pattern note on this),
    which is future work, not attempted here.
  Verified: the 32/32 self-test suite (plus vyan-6/vyan-11/boundary-elision/
  invariant suites) still passes unchanged after all three fixes. Against
  the same 27-word real-dictionary corpus that exposed these bugs:
  non-recursive PASS rate and --recursive PASS rate both re-measured after
  the fix (see the session's verification run for the exact before/after
  counts) -- this is a real, re-verified improvement, not a claimed one.

Changelog (Tier-2/Tier-3 pass -- narrower correctness fixes, hygiene, structure):
  - dictionary_lookup: removesuffix() instead of rstrip() for case-ending
    stripping (rstrip('H') strips every trailing H, not one suffix -- rare
    on well-formed SLP1 output but silent when it happens); added
    ORDER BY e.entry_id to the stem lookup so a stem mapping to more than
    one dictionary entry picks a row deterministically instead of
    whatever SQLite's query planner happens to return; guarded against a
    NULL body_text with a falsy is_crossref, which previously raised
    TypeError on row[1][:120]; de-duplicated the [slp1, -H, -M] candidate
    list so a word with no trailing H/M isn't queried three times for the
    same string. Added check_same_thread=False to the cached connection
    (a read-only cache shared across threads is safe here; sqlite3's
    default would otherwise raise ProgrammingError for a future
    threaded/server caller) and a new close_connections() helper to
    release the cache explicitly.
  - restore_natva_in_right_piece: `.replace('ण','न')` rewrote EVERY ण in
    right_piece, not just the one the trigger identified -- अणुगणम्
    (which has two, and whose second ण has nothing to do with a natva
    boundary carried over from left_piece) became अनुगनम्, corrupting an
    unrelated ण. Now replaces positionally, once, at the first ण in the
    piece. Also narrowed the trigger from scanning the ENTIRE left_piece
    for ऋ/र्/ष् to just its last 6 characters -- natva-1/3's conditioning
    sound sits near the boundary that abuts right_piece, not arbitrarily
    far away in a long compound.
  - category() (split_word_recursive's ranking): visarga-ro-ri used to
    share avagraha's top tier (-1). Given its own tier (0), between
    avagraha and particle-validated -- both pieces confirming is strong
    evidence, but it is still a phonological pattern that could in
    principle coincide by chance, unlike avagraha, which is a written
    marker with no other use in the language at all. Renumbered the rest
    of the scale accordingly and updated the two downstream threshold
    checks (tie-surfacing, continue-past-first-peel gate) from category
    <= 1 to <= 2 so the SAME set of tiers (avagraha, roH-ri,
    particle-validated, both-confirmed) still counts as "fully
    confirmed" -- the semantic boundary is unchanged, only its numeric
    position shifted.
  - is_pragrhya_no_sandhi_context's result (pragrhya_flag) was computed
    on every svara candidate and attached to it, but nothing downstream
    ever read it. category() now applies a flat +100 penalty to a
    flagged candidate's tier, pushing it below every unflagged candidate
    at any tier while preserving relative order among other flagged
    candidates -- consistent with the guard's own docstring ("flag,
    don't silently drop", since the word-list check is partial).
  - Added SYNTHETIC_CITATIONS for the five rule_ids that can never match
    a key in sandhi_rulebook.json because they are synthesized by this
    file itself (visarga-ro-ri, vyan-3+coH-kuH, svara-6+visarga-4,
    visarga-4b, sa-etad-exception) -- previously these always printed
    "Ashtadhyayi ?", including visarga-ro-ri, which sits in the ranking's
    second-highest trust tier. Sourced from the same Ashtadhyayi
    references each generator's own docstring already cites in prose,
    not borrowed from an unrelated rule's citation.
  - NEW: normalize_input() -- Unicode NFC normalization, and stripping of
    daṇḍa/double-daṇḍa, Devanagari digits, and zero-width joiner/
    non-joiner. Nothing previously normalized input at all, so e.g.
    candidates_vyan6 on 'रामं वन्दे ।' produced a right piece containing
    the daṇḍa. Spaces are deliberately never touched (Devanagari has no
    internal space that isn't a real word boundary). Wired into
    generate_candidates, split_word_recursive (which dictionary-checks
    the raw word before generate_candidates ever runs), split_word, and
    _read_words_from_file's corpus-line parsing.
  - (The Tier-1 pada-final fix to candidates_vyan3 -- see the entry below
    -- also covers its guttural coH-kuH branch automatically: that branch
    reuses the same right_start computed by the fixed check above it,
    rather than needing its own separate fix.)
  - split_word_recursive: the two INDEPENDENT depth limits (max_depth,
    rounds within one call; a local MAX_EXPANSION_DEPTH=8, nesting across
    calls) are replaced by ONE shared work budget (max_total_peels=40,
    threaded by reference through every call this invocation makes).
    Neither old limit bounded WIDTH -- a phrase with many sibling right
    pieces, each independently running up to max_depth rounds of its own,
    could still do unbounded total work despite both limits being
    respected individually. A single counter, decremented by every
    peeling round AND every expansion recursion, bounds total work
    regardless of whether it is spent going deep or wide, which is also
    what actually protects the call stack (verified: the original
    दर्शयामास चात्मानम् stack-overflow trigger, a 120-word adversarial
    phrase, and the default budget run under an artificially-lowered
    sys.setrecursionlimit(200) all complete without error).
  - File-mode double-execution: print_recursive_result()/split_word() now
    return their computed result, and the main loop threads it into
    _print_validation() (which forwards it to _compute_actual_split())
    instead of re-running the whole engine a second time per word just to
    grade it. Halves the engine calls made by a corpus run in file mode.
  - Removed: unused SOFT_TRIGGERS (also contained stray Latin 'g'/'h'
    characters, a v1 romanized-input leftover) and the duplicated
    module-level HARD_CONSONANTS definition (two identical copies; a
    future edit to one would not have applied to code reading the other).
  - split_word()'s "no candidates" message no longer hard-codes "28
    implemented rules" -- derived from len(ALL_GENERATORS) instead, so it
    can't drift from the actual generator count again the way it already
    had after candidates_svara_unified replaced seven entries with one.
  Verified: 32/32 main suite (plus vyan-6, vyan-11, boundary-elision, and
  the two Tier-1 suites) all still pass with the same exit-0 gate; the
  natva and category renumbering changes were checked against the
  regression words directly, not just by suite pass/fail.

Changelog (Tier-1 correctness pass -- ordering, layering, invariants):
  - generate_candidates: now imposes a CANONICAL order on its output
    (generator index, then len(right), then rule_id/left/right) and applies
    a structural well-formedness filter. Previously two stages silently
    depended on raw emission order -- split_word()/_compute_actual_split()
    report confirmed[0] with no sort at all, and split_word_recursive()'s
    ranking sort is stable, so ties fell back to emission order. The
    unified-scan swap changed exactly that: same candidate SET as the seven
    functions it replaced (verified, 0 mismatches / ~4000 words) but
    right-to-left rather than left-to-right, differing on ~19% of words and
    flipping the reported answer on ~28% of svara-triggered words. The
    corpus runs missed it because the visarga/vyanjana generators run first
    and usually supplied confirmed[0]. So "byte-for-byte identical output"
    below held for one corpus, not by construction -- it does now.
    Side effect: this also FIXES non-recursive mode on words like
    सूर्योदयः, which reported सु+उर्योदयः purely because svara-1 emitted
    before svara-2; shortest-right now wins within a generator.
  - is_well_formed_candidate: NEW central invariant -- no right piece may
    begin with a combining mark, which would mean the split cut through a
    grapheme cluster and orphaned a vowel sign. 10 of 286 candidates
    dropped across the regression words, 0 correct answers lost.
  - candidates_vyan3 / candidates_vyan4: require the trigger consonant to
    be PADA-FINAL (virama-marked or end of string). Both skipped a virama
    "if present" but never rejected a MATRA, so they fired mid-word where
    the rule cannot apply: देवेन्द्रः yielded left='त्',
    right='ेवेन्द्रः'. On random input this drops vyan-3 candidates from
    2088 to 41 and malformed ones from 541 to 16 (the rest caught by the
    invariant above).
  - candidates_elided_visarga_boundary: no longer calls dictionary_lookup.
    It made generate_candidates -- the pure-phonology layer -- require an
    open SQLite connection, so generators could not be tested in isolation
    and --test silently depended on dictionary contents. The condition is
    unchanged, now declared as requires_bare_form_absent and enforced by
    validate_against_dictionary.
  - dictionary_lookup: raises an actionable FileNotFoundError for a missing
    database instead of letting sqlite3.connect CREATE an empty one (which
    surfaced later as a misleading "no such table: stems" and left a
    zero-byte file on disk).
  - --test: tallies failures across every sub-suite and exits non-zero.
    It previously printed FAIL and exited 0, so a total regression reported
    green. Adds two new suites: unified-scan set-equivalence against the
    seven retained originals (so the rollback reference stays trustworthy),
    and the well-formedness invariant.
  Verified: 32/32 main suite, and --recursive corpus output byte-identical
  to the pre-patch version.

Changelog (right-to-left intersection-scan session):
  - candidates_svara_unified: NEW. Merges the scanning done separately by
    candidates_svara1/2/3/4/5/6/9_m_junction (7 functions, 18 separate
    left-to-right passes over the word once svara-1's 4-class double loop
    and svara-2's two internal loops are counted) into ONE right-to-left
    pass, checking each position against the closed set of svara-sandhi
    result letters (आ,ई,ऊ,ॠ; ए,ओ,ऐ,औ matras; य्,व्,र्,ल्; ऽ; बेयर म्).
    Construction logic at each trigger position is copied verbatim from
    the seven originals -- only the scanning is merged. Verified byte-
    for-byte identical candidate output on 590 corpus+regression words,
    and the full regression suite (test_sandhi_splitter.py) and both
    Ramayana Bala Kanda Sarga 1 corpus runs (--recursive, with and
    without --skip-vyanjana) produce IDENTICAL output before/after this
    swap. Measured ~18x fewer character-position visits, ~1.8x wall-
    clock speedup on the svara-generation portion specifically.
  - candidates_svara1/2/3/4/5/6/9_m_junction are left defined below,
    UNUSED (removed from ALL_GENERATORS), as a rollback reference -- see
    sandhi_splitter_v2_pre_unified_scan_backup.py for the untouched prior
    version if this needs reverting.
  - Tried and REJECTED: stopping the right-to-left scan at the FIRST
    (rightmost) position that produces any candidate, instead of
    visiting every position. This measurably regresses correctness (38
    PASS -> 31 PASS on the regression suite) because a syntactically
    plausible trigger (e.g. an ordinary र् inside a consonant cluster
    that has nothing to do with sandhi, as in गिरीन्द्रः's न्द्रः) can
    sit to the right of the REAL boundary and stop the scan before it's
    reached -- candidate generation must stay exhaustive; only
    dictionary validation (a separate, later stage) is safe to use as a
    stopping signal, and this scan doesn't do that.
  - Investigated but NOT implemented: आर्/आल् (वृद्धि of ऋ/ऌ) as a new
    svara trigger. These are real वृद्धि substitutes (guṇa/vṛddhi table:
    गुण अर्/अल्, वृद्धि आर्/आल्), but ordinary two-word sandhi combination
    uses गुण (6.1.87 आद्गुणः) for अ/आ+ऋ/ऌ, not वृद्धि -- वृद्धि (6.1.88
    वृद्धिरेचि) is textually restricted to अ/आ+ऐच् (ऐ/औ). आर्/आल् instead
    arise from a narrow, PREFIX-GATED exception (प्र/परा/अप/अव/उप + an
    ऋ-initial word overriding the default गुण), structurally like
    svara-7's existing attested-exception pattern -- not a blanket
    letter trigger (which would misfire on ordinary words like आर्य,
    आलय the same way the rejected first-hit-only idea above did). Zero
    attestations of either अर्/अल् or आर्/आल् in this corpus to build or
    verify a rule against; left unimplemented per this file's own
    "not implemented rather than guessed at" precedent (see vyan-13)
    rather than shipped as a guess.

Changelog (previous pass -- found via an independently-derived batch of ~60
svara/visarga test words, verified against the actual generators, not
just read by inspection):
  - candidates_svara2: fixed the ऋ/ॠ->अर् branch, which searched for a
    literal independent-अ letter that essentially never appears in real
    compounds (महर्षिः produced zero candidates from ANY generator before
    this fix); added the previously entirely-missing ऌ->अल् branch.
  - candidates_svara4: added the implicit-अ (bare semivowel, including
    the followed-by-अनुस्वार sub-case) branch that was documented as a
    known limitation but left unimplemented.
  - candidates_svara5: full rewrite. The old trigger searched for a
    virama-marked consonant immediately followed by a vowel letter -- a
    sequence that cannot occur in valid Devanagari -- so it could not
    fire on ANY input, including all 4 of the rulebook's own canonical
    examples. New version mirrors svara-4's actual (correct) shape.
  - candidates_svara6: extended to also propose the fully-resolved
    reading (रामः, not just रामो) for अ-preceded-visarga+following-अ
    words marked by अवग्रह, since split_word_recursive's peel-and-recurse
    cannot reach that resolution on a later pass (the needed context is
    consumed by the first peel).
  - candidates_visarga_ro_ri: NEW generator for Ashtadhyayi 8.3.14 (रो
    रि) -- visarga elision before a र्-initial word with compensatory
    vowel lengthening. Was entirely absent from both this file and the
    rulebook's 9-entry visarga_sandhi section.
  - restore_elided_visarga_at_word_boundary: added the सः/एषः closed-class
    exception (visarga drops entirely before any consonant, no guna),
    also previously entirely unaddressed.
"""
import json
import re
import unicodedata

HARD_CONSONANTS = set("कखचछटठतथपफशषस")  # khar
# REMOVED: SOFT_TRIGGERS (unused anywhere in this file, and mixed in stray
# Latin 'g'/'h' characters -- a leftover from a v1 romanized-input approach
# that this Devanagari-native module no longer takes).

# Characters this module treats as structurally meaningless: zero-width
# joiner/non-joiner (encoding artifacts, not phonology), daṇḍa/double-daṇḍa
# (verse punctuation), and the Devanagari digits (verse/chapter numbering
# that sometimes rides along in corpus text). Devanagari itself never
# contains an internal space that isn't a real word boundary, so spaces are
# deliberately NOT touched here -- stripping punctuation must not collapse
# or invent word boundaries.
_ZERO_WIDTH = '\u200b\u200c\u200d\ufeff'
_PUNCTUATION_TO_STRIP = '।॥' + '०१२३४५६७८९' + _ZERO_WIDTH

def normalize_input(text):
    """Normalize raw corpus/CLI text before it reaches any generator.

    FIXED (see changelog): nothing previously normalized input at all, so a
    generator's character-by-character scan treated daṇḍa, verse-number
    digits, and zero-width joiner/non-joiner as ordinary letters -- e.g.
    candidates_vyan6 on 'रामं वन्दे ।' happily produced a right piece
    containing the daṇḍa, and a ZWJ/ZWNJ inserted by some input pipeline
    silently broke every character-position trigger near it. Also applies
    Unicode NFC normalization, since Devanagari text can arrive with
    combining sequences in more than one equivalent byte form.

    Idempotent and cheap, so it is safe to call at every entry point
    (generate_candidates, split_word, split_word_recursive, and the file
    reader) rather than trying to guarantee it only ever runs once."""
    if not text:
        return text
    text = unicodedata.normalize('NFC', text)
    return ''.join(ch for ch in text if ch not in _PUNCTUATION_TO_STRIP)


def load_citations():
    import os
    # FIXED: previously only ever looked ONE DIRECTORY ABOVE this file
    # (a src/ + package-root layout) and crashed with FileNotFoundError
    # if sandhi_rulebook.json instead sits in the SAME directory as this
    # script (a flat layout -- e.g. both files dropped straight into one
    # folder). Now tries same-directory first, then one level up, and
    # raises a clear, actionable error if neither has it, instead of a
    # bare FileNotFoundError pointing at a resolved path that gives no
    # hint about what layout was expected.
    _here = os.path.dirname(os.path.abspath(__file__))
    _candidates = [
        os.path.join(_here, 'sandhi_rulebook.json'),
        os.path.join(_here, '..', 'sandhi_rulebook.json'),
    ]
    _path = next((p for p in _candidates if os.path.isfile(p)), None)
    if _path is None:
        raise FileNotFoundError(
            "sandhi_rulebook.json not found. Looked in the same folder as "
            f"{os.path.basename(__file__)} and in its parent folder. Put "
            "sandhi_rulebook.json in one of those two locations:\n  "
            + "\n  ".join(_candidates)
        )
    with open(_path, encoding='utf-8') as f:
        d = json.load(f)
    by_id = {}
    for section in ['svara_sandhi', 'vyanjana_sandhi', 'visarga_sandhi']:
        for r in d[section]:
            by_id[r['id']] = {
                'ashtadhyayi_ref': r.get('ashtadhyayi_ref'),
                'lsk_prakarana': r.get('lsk_prakarana'),
                'english_name': r.get('english_name'),
                'sutra_devanagari': r.get('sutra_devanagari'),
            }
    return by_id

CITATIONS = load_citations()

# FIXED (see changelog): several generators emit synthetic rule_ids that
# combine or extend a rulebook entry -- 'vyan-3+coH-kuH', 'svara-6+visarga-4',
# 'visarga-ro-ri', 'visarga-4b', 'sa-etad-exception'. None of these can
# match a key in sandhi_rulebook.json (its ids are the plain 'svara-1'/
# 'vyan-3'/'visarga-2' style), so CITATIONS.get(c['rule_id']) always fell
# through to {} for them and split_word()/print_recursive_result() printed
# "Ashtadhyayi ?" -- for the RULE the ranking trusts MOST (visarga-ro-ri
# sits in the top confirmed tier, just below avagraha; see category()).
# Rather than borrowing a different rule's citation (which would mislabel
# the sutra), these are sourced directly from the same Ashtadhyayi
# references each generator's own docstring already cites in prose.
SYNTHETIC_CITATIONS = {
    'visarga-ro-ri': {
        'ashtadhyayi_ref': '8.3.14', 'lsk_prakarana': None,
        'english_name': 'roH ri (visarga elision before an r-initial word, '
                         'with compensatory lengthening of a preceding short i/u)',
        'sutra_devanagari': 'रो रि',
    },
    'vyan-3+coH-kuH': {
        'ashtadhyayi_ref': '8.2.30 + 8.2.39', 'lsk_prakarana': None,
        'english_name': 'coH kuH (velar-from-palatal reversion) feeding jashtva',
        'sutra_devanagari': 'चोः कुः',
    },
    'svara-6+visarga-4': {
        'ashtadhyayi_ref': '6.1.109 + 8.3.17', 'lsk_prakarana': None,
        'english_name': 'purvarupa (elision before avagraha) combined with the '
                         'a-preceded visarga -> o (guna) it presupposes, resolved '
                         'in one step',
        'sutra_devanagari': 'एङः पदान्तादति; ससजुषो रुः',
    },
    'visarga-4b': {
        'ashtadhyayi_ref': None, 'lsk_prakarana': None,
        'english_name': 'visarga elided at a word boundary before a non-a vowel '
                         '(शाकल्य लोपः) -- not itself a compulsory Ashtadhyayi rule, '
                         'a recognised optional/dialectal reading',
        'sutra_devanagari': None,
    },
    'sa-etad-exception': {
        'ashtadhyayi_ref': None, 'lsk_prakarana': None,
        'english_name': 'सः/एषः closed-class exception: visarga drops entirely '
                         'before any consonant, without the usual u-guna step',
        'sutra_devanagari': None,
    },
}

_ASHTADHYAYI_TRIPLE_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')


def _rule_priority_key(rule_id):
    """Tiebreak key implementing paribhāṣā-12 (Aṣṭādhyāyī 1.4.2,
    विप्रतिषेधे परं कार्यम् -- 'in a genuine rule conflict, the LATER rule
    in Pāṇini's own sequence prevails'), catalogued in
    04_Laghu_Siddhanta_Kaumudi/paribhasha_prakarana_rulebook.json. Used
    ONLY as a tiebreak among candidates already equal on (category,
    validated-bit) -- never to override a real evidentiary difference.

    Reads the same ashtadhyayi_ref string already attached to every
    candidate for citation display (CITATIONS/SYNTHETIC_CITATIONS); a
    citation can name more than one sūtra (e.g. 'vyan-3+coH-kuH':
    '8.2.30 + 8.2.39') -- per the same paribhāṣā, the LATER of the two is
    the one actually governing, so the max() of every parseable
    Chapter.Pada.Sutra triple in the string is used. Returns a tuple
    sorting so a LATER rule produces a SMALLER key (sort ascending = later
    wins). A rule_id with no parseable Aṣṭādhyāyī reference (a handful of
    SYNTHETIC_CITATIONS entries genuinely have none, e.g. visarga-4b,
    sa-etad-exception) gets (0, 0, 0), which sorts AFTER every real
    negative-triple key -- an uncited candidate never outranks a cited one
    on this key, only on the tiers already computed before it."""
    # REVISED TWICE after re-verification against the corpus that
    # motivated this fix:
    #   (a) applying this tiebreak between two SVARA candidates regressed
    #       स्वागतम् (सु+आगतम्, svara-4/6.1.77 -- correct) to स्व+अगतम्
    #       (svara-1/6.1.101 -- wrong);
    #   (b) applying it between two VISARGA candidates likewise regressed
    #       सूर्योदयः (सूर्य+उदयः -- correct) to सूर्यः+दयः (visarga-4's own
    #       alternative guna-reversal reconstruction -- wrong), and
    #       गुरोऽत्र similarly picked svara-6's own more-aggressive
    #       'svara-6+visarga-4' sub-candidate over the plain svara-6 one.
    # Both failure shapes are the same underlying reason: svara-*/visarga-*
    # rules routinely propose MULTIPLE genuinely alternative phonological
    # reconstructions for the very same trigger -- exactly the "genuine
    # ambiguity" this file already goes out of its way to surface rather
    # than force-resolve (see the tie-detection logic just below). Sūtra
    # order does not track which reconstruction is linguistically correct
    # among alternatives WITHIN the same rule family. It only reliably
    # tracks specificity when a vyañjana (consonant-cluster/assimilation)
    # rule is competing against a rule from a DIFFERENT family, since a
    # cluster-triggered vyañjana rule is intrinsically a narrower, more
    # specific signal than a generic vowel-pattern match -- an अपवाद/
    # उत्सर्ग (exception/general) relationship, not just textual sequence.
    # So ONLY a vyanjana-family rule_id gets a real, distinguishing key
    # here; every svara/visarga rule_id (whatever it's tied against) gets
    # the same neutral (0,0,0) -- which means: vyan-vs-non-vyan ties still
    # resolve by real Aṣṭādhyāyī order (fixes तल्लीनः), vyan-vs-vyan ties
    # still resolve by real order (fixes वणिग्घसति, both vyan-3/vyan-8),
    # but svara-vs-svara, visarga-vs-visarga, and svara-vs-visarga ties are
    # untouched -- exactly as before this tiebreak was ever added.
    if not rule_id.startswith('vyan'):
        return (0, 0, 0)
    citation = CITATIONS.get(rule_id) or SYNTHETIC_CITATIONS.get(rule_id) or {}
    ref = citation.get('ashtadhyayi_ref') or ''
    triples = [tuple(int(x) for x in m.groups()) for m in _ASHTADHYAYI_TRIPLE_RE.finditer(ref)]
    if not triples:
        return (0, 0, 0)
    latest = max(triples)
    return tuple(-x for x in latest)


# Common declensional/conjugational endings, longest first so a longer
# match (न्ति before ति, ओति before ति) is tried before a shorter one that
# would otherwise over-strip. Deliberately a small, closed, non-exhaustive
# list -- the same "closed-class hint, not a stemmer" discipline already
# used for KNOWN_PARTICLES below -- covering only the most common nominal
# (locative ए, genitive स्य, instrumental/dative/ablative ेण/ाय/ात्) and
# verbal (3rd sg./pl. present ति/न्ति, तनादि/स्वादि-गण ओति) endings. See
# this file's Tier-4 changelog entry for why this exists: the dictionary
# only indexes CITATION forms, so an ordinary inflected word (काले, मयम्,
# करोति) that carries no real internal sandhi at all was being wrongly
# recursed into and carved up, purely because no exact whole-word
# dictionary entry existed to stop it the way it does for a citation form.
_COMMON_INFLECTIONAL_ENDINGS = sorted(
    {'न्ति', 'ोति', 'ात्', 'ेण', 'ाय', 'स्य', 'सि', 'थः', 'मि', 'ति',
     'तः', 'ेषु', 'े', 'म्'},
    key=len, reverse=True,
)

# मतुप्/वतुप् (possessive-adjective) endings: नामवान्/नामवती/... reduce to
# stem+वत्, and गुणवान्/द्युतिमान्/... reduce to stem+मत् -- the ENDING
# ITSELF changes shape (-वान् -> -वत्, not just drops), so this can't be
# handled by plain suffix-stripping the way the endings above are. Verified
# against real examples before use: वीर्यवान्->वीर्यवत् and आत्मवान्->
# आत्मवत् both resolve against the real dictionary; द्युतिमान्->द्युतिमत्
# does not (द्युति+मत् is evidently not independently headworded) and is
# left as a known, honestly-unresolved case rather than guessed at.
_MATUP_VATUP_ENDINGS = (('वान्', 'वत्'), ('मान्', 'मत्'))


def _stem_after_common_inflection(word, db_path=None):
    """If stripping one of _COMMON_INFLECTIONAL_ENDINGS from `word` (or
    reducing a मतुप्/वतुप् -वान्/-मान् ending to its citation -वत्/-मत्
    form) yields a real dictionary stem, return that stem (truthy); else
    return None. Never asserts which grammatical ending it actually is --
    the returned stem is used only as a signal that `word` is already a
    complete, ordinary inflected word, not as morphological analysis of it
    (a coincidental match, e.g. करोति -> कर via 'ओति', stops an unwarranted
    split just as correctly as a linguistically exact one would).

    NOTE on scope, found by running this against real verse text (not just
    the hand-built regression corpus): this remains a small, closed,
    non-exhaustive list. Compound words whose fused stem isn't itself
    separately headworded (दृढव्रतः, जातरोषस्य, जितक्रोधः, चारित्रेण,
    सर्वभूतेषु), irregular pronoun forms (अस्मिन्), and non-paradigmatic
    verb forms (बिभ्यति, श्रोतुम्, a reduplicated perfect like
    परिपप्रच्छ) are NOT caught by this and remain open, honestly
    unresolved cases -- real fixes need either compound-member analysis or
    a real paradigm-based stemmer, both future work (see PROJECT_STATE.md
    gap #14)."""
    for suf in _COMMON_INFLECTIONAL_ENDINGS:
        if word.endswith(suf) and len(word) - len(suf) >= 2:
            stem = word[:-len(suf)]
            if dictionary_lookup(stem, db_path=db_path)['found']:
                return stem
    for surface_end, citation_end in _MATUP_VATUP_ENDINGS:
        if word.endswith(surface_end) and len(word) - len(surface_end) >= 2:
            stem = word[:-len(surface_end)] + citation_end
            if dictionary_lookup(stem, db_path=db_path)['found']:
                return stem
    return None


def candidates_visarga1(word):
    """visarga-1: retained visarga before hard consonant.
    Trigger: literal 'ः' followed by a hard (khar) consonant.
    Note: this looks IDENTICAL to a word that simply has ः + hard-consonant
    with no sandhi change at all -- that's expected, visarga-1 IS the
    'no change' rule, so its candidate is just: split right after the ः."""
    out = []
    for i, ch in enumerate(word):
        if ch == 'ः' and i + 1 < len(word) and word[i+1] in HARD_CONSONANTS:
            left = word[:i+1]
            right = word[i+1:]
            out.append({'rule_id': 'visarga-1', 'left': left, 'right': right,
                        'note': 'visarga retained unchanged before hard consonant'})
    return out

def candidates_visarga3(word):
    """visarga-3: ः -> श्/ष्/स् before palatals/cerebrals/dentals.
    Trigger: श्/ष्/स् + virama, followed -- directly OR after exactly one
    space -- by च/छ/ट/ठ/त/थ respectively.

    FIXED (see changelog): originally searched for the literal
    contiguous substring 'श्च' etc, so it never fired when a corpus
    edition keeps the pada-boundary space even through this compulsory
    sandhi (कश् च rather than कश्च for कः+च) -- a real, common style in
    critical editions/verse extracts. Rewritten to scan character-by-
    character like the other visarga generators, tolerating one
    optional space between the transformed consonant and what follows."""
    out = []
    pairs = [('श', 'च'), ('श', 'छ'), ('ष', 'ट'), ('ष', 'ठ'), ('स', 'त'), ('स', 'थ')]
    for transformed, target in pairs:
        for i, ch in enumerate(word):
            if ch == transformed and i + 1 < len(word) and word[i+1] == '्':
                j = i + 2
                had_gap = False
                if j < len(word) and word[j] == ' ':
                    had_gap = True
                    j += 1
                if j < len(word) and word[j] == target:
                    left = word[:i] + 'ः'
                    right = target + word[j+1:]
                    out.append({'rule_id': 'visarga-3', 'left': left, 'right': right,
                                'note': f'{transformed}् restored to ः + {target}'
                                        + (' (pada-boundary space before the following word)' if had_gap else '')})
    return out

def candidates_visarga4(word):
    """visarga-4: ः (preceded by अ) + soft consonant -> ओ.
    Trigger: consonant + 'ो' (o-matra) directly followed by a soft/voiced sound.
    Reverse: that syllable's ो is undone to plain-consonant+अ, then +ः, then
    the following word starts with whatever consonant follows in the surface."""
    out = []
    for i, ch in enumerate(word):
        if ch == 'ो' and i + 1 < len(word):
            following = word[i+1]
            if following not in HARD_CONSONANTS:  # soft/voiced context
                left = word[:i] + 'ः'   # drop the o-matra, restore visarga after the bare consonant
                right = word[i+1:]
                out.append({'rule_id': 'visarga-4', 'left': left, 'right': right,
                            'note': 'ो undone to consonant+अ+ः (two-step: u-adesha then guna)'})
    return out

def candidates_visarga5(word):
    """visarga-5: ः (preceded by non-a/aa vowel) -> र् before soft consonant/vowel.
    Trigger: 'र्' immediately followed by a soft consonant or vowel.
    NOTE: high false-positive rate -- real words can have an underlying र्.
    Dictionary validation of the LEFT piece (does it end in a real
    i/u/r-stem plus visarga, and is that a real word?) is what actually
    disambiguates this from a genuine root-final र्.

    EXTENDED (see changelog): the rule's own text (and this function's own
    docstring) says "before a soft consonant OR VOWEL", but only the
    consonant case was ever implemented (र् virama-clustered with what
    follows). Added the vowel case: र् before a vowel is NOT virama-
    clustered -- it's either bare (implicit अ: मुनिः+अयम् -> मुनिरयम्) or
    carries its own explicit matra (भानुः+उदेति -> भानुरुदेति), mirroring
    the same following-vowel lookup used throughout svara-4/5."""
    out = []
    matra_map = {'ा':'आ','ि':'इ','ी':'ई','ु':'उ','ू':'ऊ','ृ':'ऋ','ॄ':'ॠ','े':'ए','ै':'ऐ','ो':'ओ','ौ':'औ'}
    for i, ch in enumerate(word):
        if ch != 'र' or i + 1 >= len(word):
            continue
        nxt = word[i+1]
        if nxt == '्':
            # existing case: र् clustering (virama) with a following consonant
            if i + 2 < len(word):
                left = word[:i] + 'ः'
                right = word[i+2:]
                out.append({'rule_id': 'visarga-5', 'left': left, 'right': right,
                            'note': 'र् (before consonant) candidate-reversed to ः (NEEDS dictionary validation -- high false positive rate)'})
        elif nxt in matra_map and (i == 0 or word[i-1] != '्'):
            # guard: genuine visarga-derived र् is always preceded by a
            # VOWEL (visarga only ever follows a vowel). If word[i-1] is
            # itself a virama, this र् is the second half of a native
            # consonant cluster (त्र, प्र, ब्र, ...), not a visarga
            # reflex -- skip it (e.g. तत्र's own र् in तत्रैव, which is
            # NOT sandhi-derived and was producing a spurious तत्ः + ऐव
            # candidate that could out-rank the correct तत्र + एव).
            left = word[:i] + 'ः'
            right = matra_map[nxt] + word[i+2:]
            out.append({'rule_id': 'visarga-5', 'left': left, 'right': right,
                        'note': 'र् (before vowel, explicit matra) candidate-reversed to ः (NEEDS dictionary validation)'})
        elif nxt != '्' and (i == 0 or word[i-1] != '्'):
            left = word[:i] + 'ः'
            right = 'अ' + word[i+1:]
            out.append({'rule_id': 'visarga-5', 'left': left, 'right': right,
                        'note': 'र् (before vowel, implicit अ) candidate-reversed to ः (NEEDS dictionary validation)'})
    return out

def candidates_visarga_ro_ri(word):
    """NEW RULE (see changelog) -- not previously in this module or in the
    rulebook's 9-entry visarga_sandhi section at all: Ashtadhyayi 8.3.14,
    रो रि. When विसर्ग's रु-substitute is itself followed by a WORD
    starting with र्, रु is elided outright (rather than converting to र्,
    which would create an impossible र्+र् cluster) -- and if the vowel
    immediately before it was SHORT (इ or उ), it lengthens to compensate:
    इ->ई, उ->ऊ. निः+रोगः -> नीरोगः, गुरुः+रुष्टः -> गुरूरुष्टः, NOT
    निर्रोगः / गुरुर्रुष्टः.
    Trigger: a long ई/ऊ matra (ी/ू) on some consonant, immediately followed
    by र (in any form -- bare, or itself carrying a vowel of its own, since
    it's simply the start of the following word). Reverse: replace the
    long matra with its short counterpart and append विसर्ग; the following
    र-initial remainder is unchanged."""
    out = []
    long_to_short = {'ी': 'ि', 'ू': 'ु'}
    for i, ch in enumerate(word):
        if ch in long_to_short and i + 1 < len(word) and word[i+1] == 'र':
            left = word[:i] + long_to_short[ch] + 'ः'
            right = word[i+1:]
            out.append({'rule_id': 'visarga-ro-ri', 'left': left, 'right': right,
                        'note': f'{ch} (long, before र-initial word) reversed to short {long_to_short[ch]}+ः (8.3.14 roH ri elision + compensatory lengthening, NEEDS dictionary validation)'})
    return out

def candidates_visarga2(word):
    """visarga-2: OPTIONAL assimilation of visarga to श्/ष्/स् before a
    sibilant (as opposed to visarga-3's COMPULSORY change before
    palatals/cerebrals/dentals). Two spellings coexist for the same
    input: रामः+शेते -> रामश्शेते (assimilated) OR रामः शेते (unchanged).
    The unchanged option is already covered by visarga-1's trigger (श्,ष्,स्
    are members of HARD_CONSONANTS, so visarga-1 already proposes the
    'retained as-is' split). This generator adds ONLY the new doubled-
    sibilant surface pattern that visarga-1 can't produce."""
    out = []
    doubled = [('श्श', 'श'), ('ष्ष', 'ष'), ('स्स', 'स')]
    for pattern, restored_cons in doubled:
        for m in re.finditer(re.escape(pattern), word):
            i = m.start()
            left = word[:i] + 'ः'
            right = restored_cons + word[i+len(pattern):]
            out.append({'rule_id': 'visarga-2', 'left': left, 'right': right,
                        'note': f'{pattern} (doubled sibilant) restored to ः + {restored_cons} (optional assimilation)'})
    return out

# visarga-7: allophonic जिह्वामूलीय/उपध्मानीय realization before क्/ख्/प्/फ्
# produces NO spelling change in ordinary (non-Vedic-accent-marked) text --
# it's a pronunciation distinction only. The surface form is identical to
# plain visarga-retention, which visarga-1 already generates (क्/ख्/प्/फ्
# are all in HARD_CONSONANTS). No separate generator needed or possible.

def restore_elided_visarga_at_word_boundary(prev_word, next_word):
    """visarga-4b and visarga-6: UNLIKE every other generator in this module,
    these two rules don't fuse two words into one string -- they ELIDE the
    visarga entirely, leaving prev_word and next_word as two separate,
    space-delimited words (e.g. 'धृतराष्ट्र उवाच', not one fused token).
    So there is nothing to "split" here; instead, when processing running
    verse text word-by-word, a word ending in a plain vowel (no visarga)
    that precedes a vowel-initial word MIGHT actually be the visarga-elided
    citation form of word+ः. This helper checks that possibility so
    dictionary lookup doesn't fail on words whose nominative -ः was
    silently dropped.

    Returns the restored candidate (prev_word + ः) if the elision
    conditions plausibly apply, else None. Caller should still validate
    the restored form against the dictionary.

    EXTENDED (see changelog): सः/एषः are a small, well-known closed-class
    exception -- their विसर्ग drops ENTIRELY before ANY following
    consonant (not just soft ones), WITHOUT the उ->ओ guna conversion an
    ordinary अ-visarga word would get: सः वदति -> स वदति, NOT सो वदति.
    This is a different mechanism from both visarga-4b (elision only
    before a non-अ VOWEL) and visarga-6 (आ-preceded words), scoped to this
    narrow pronoun class -- same closed-list spirit as
    split_word_recursive's KNOWN_PARTICLES, deliberately not exhaustive."""
    if not prev_word or not next_word:
        return None
    SA_ETAD_CLASS = {'स', 'एष'}  # bare (visarga-less) surface forms
    if prev_word in SA_ETAD_CLASS:
        VOWEL_GLYPHS_SA = set('अआइईउऊऋॠएऐओऔ')
        if next_word[0] not in VOWEL_GLYPHS_SA:
            return {'rule_id': 'sa-etad-exception', 'restored': prev_word + 'ः',
                    'note': f'{prev_word} is in the सः/एषः class -- visarga drops entirely before any consonant (no guna), restore ः before dictionary lookup'}
    HARD_CONSONANTS_LOCAL = set("कखचछटठतथपफशषस")
    # visarga-6: prev_word ends in long आ, followed by EITHER a soft
    # consonant or any vowel (broader trigger than visarga-4b, which is
    # vowel-only) -> visarga dropped entirely.
    ends_in_long_a = prev_word[-1] == 'ा' or prev_word.endswith('आ')
    if ends_in_long_a:
        next_first = next_word[0]
        is_vowel = next_first in set('अआइईउऊऋॠएऐओऔ')
        is_soft_consonant = (next_first not in HARD_CONSONANTS_LOCAL) and not is_vowel
        if is_vowel or is_soft_consonant:
            return {'rule_id': 'visarga-6', 'restored': prev_word + 'ः',
                    'note': f'{prev_word} ends in आ before {next_word} -- possible visarga-6 elision, restore ः before dictionary lookup'}
    # visarga-4b: prev_word ends in plain अ (bare consonant, no explicit
    # vowel glyph), next_word starts with a vowel OTHER than अ (अ itself
    # is svara-6/visarga-4's territory, not this rule's).
    next_starts_with_vowel = next_word[0] in set('अआइईउऊऋॠएऐओऔ')
    if next_starts_with_vowel and next_word[0] != 'अ':
        VOWEL_GLYPHS = set('अआइईउऊऋॠएऐओऔािीुूृेैोौ') | {'ः', 'ं'}
        if prev_word[-1] not in VOWEL_GLYPHS:
            return {'rule_id': 'visarga-4b', 'restored': prev_word + 'ः',
                    'note': f'{prev_word} (bare, no visarga) preceding vowel-initial {next_word} -- possible visarga-4b elision (शाकल्य लोपः), restore ः before dictionary lookup'}
    return None

def candidates_vyan3(word):
    """vyan-3 (jashtva): word-final jhal (hard) consonant softens to its
    jash counterpart before a vowel/soft consonant.
    Trigger: a voiced stop (ग,ड,द,ब,ज) at a plausible compound-internal
    boundary; reverse candidates offer the corresponding voiceless stop."""
    jash_to_jhal = {'ग': 'क', 'ड': 'ट', 'द': 'त', 'ब': 'प', 'ज': 'च'}
    # coH kuH (8.2.30): guttural ग can ALSO be the jashtva-result of an
    # originally-palatal च् that first fronted to क् before jashtva applied
    # (this is why वाच्+विद् -> वाग्विद्, not वाज्विद्). Both branches
    # must be offered; dictionary validation picks the real one.
    guttural_alt_source = {'ग': 'च'}
    out = []
    for i, ch in enumerate(word):
        if ch in jash_to_jhal:
            # FIXED: a jashtva source must be PADA-FINAL, which in Devanagari
            # means virama-marked (or the very end of the string). The old
            # code skipped the virama "if present" but did not REJECT the
            # alternative -- a consonant carrying a MATRA -- so it fired on
            # mid-word consonants where the rule cannot have applied, and
            # sliced straight through the grapheme cluster: देवेन्द्रः
            # produced left='त्', right='ेवेन्द्रः', a right piece beginning
            # with an orphaned vowel sign (not a valid Devanagari string)
            # whose द had silently lost its own े. Against a comprehensive
            # dictionary such a fragment can validate by accident and win a
            # ranking tier.
            if i + 1 < len(word) and word[i+1] != '्':
                continue
            right_start = i + 2 if i + 1 < len(word) else i + 1
            if right_start >= len(word):
                continue
            unvoiced = jash_to_jhal[ch]
            left = word[:i] + unvoiced + '्'
            right = word[right_start:]
            out.append({'rule_id': 'vyan-3', 'left': left, 'right': right,
                        'note': f'{ch} reversed to {unvoiced}् (jashtva undone) -- NEEDS dictionary validation'})
            if ch in guttural_alt_source:
                alt = guttural_alt_source[ch]
                left_alt = word[:i] + alt + '्'
                out.append({'rule_id': 'vyan-3+coH-kuH', 'left': left_alt, 'right': word[right_start:],
                            'note': f'{ch} reversed via coH-kuH(8.2.30)+jashtva(8.2.39) chain to {alt}् -- NEEDS dictionary validation'})
    return out


# REMOVED: duplicate `HARD_CONSONANTS = set("कखचछटठतथपफशषस")` -- identical to
# the module-level definition near the top of the file. Harmless today
# (both had the same value), but a future edit to one copy would silently
# not apply to code below this point that reads the other.

def candidates_vyan1(word):
    """vyan-1: स्/त-वर्ग -> श्/च-वर्ग before श्/च-वर्ग (total assimilation
    of place+voicing). सत्+चित्=सच्चित्; तत्+जयति=तज्जयति.
    Trigger: doubled/matched च-वर्ग clusters (च्च, ज्ज) and श्श (which
    OVERLAPS with visarga-2's श्श trigger -- both are offered since the
    underlying source word could end in bare स्/त् OR in visarga; only
    dictionary validation of the reconstructed left piece disambiguates
    which one is real)."""
    out = []
    # त्+च्/त्+ज् -> च्च/ज्ज (fully assimilated)
    for pattern, orig_left_cons in [('च्च', 'त'), ('ज्ज', 'त')]:
        for m in re.finditer(pattern, word):
            i = m.start()
            left = word[:i] + orig_left_cons + '्'
            right = pattern[0] + word[i+len(pattern):]
            out.append({'rule_id': 'vyan-1', 'left': left, 'right': right,
                        'note': f'{pattern} restored to {orig_left_cons}्+{pattern[0]}् (total assimilation, NEEDS dictionary validation)'})
    # स्+श् -> श्श (overlaps with visarga-2's identical surface trigger)
    for m in re.finditer('श्श', word):
        i = m.start()
        left = word[:i] + 'स्'
        right = 'श' + word[i+3:]
        out.append({'rule_id': 'vyan-1', 'left': left, 'right': right,
                    'note': 'श्श restored to स्+श् (bare dental स्, NOT visarga -- compare visarga-2 candidate for the same trigger; dictionary validation picks the real source)'})
    return out

def candidates_vyan2(word):
    """vyan-2: स्/त-वर्ग -> ष्/ट-वर्ग before ष्/ट-वर्ग.
    तत्+टीका=तट्टीका; रामस्+षष्ठः=रामष्षष्ठः."""
    out = []
    for pattern, orig_left_cons in [('ट्ट', 'त'), ('ष्ष', 'स')]:
        for m in re.finditer(pattern, word):
            i = m.start()
            left = word[:i] + orig_left_cons + '्'
            right = pattern[0] + word[i+len(pattern):]
            out.append({'rule_id': 'vyan-2', 'left': left, 'right': right,
                        'note': f'{pattern} restored to {orig_left_cons}्+{pattern[0]}् (total assimilation, NEEDS dictionary validation)'})
    return out

def candidates_vyan4(word):
    """vyan-4: soft consonant -> hard consonant of its class before a hard
    consonant. वाच्+करोति (base वाच्) -> वाक् करोति; मद्+सन्धिः -> मत्सन्धिः.
    This is the mirror-image of vyan-3 (which softens before soft/vowel):
    here a HARD consonant before another HARD consonant is offered as
    possibly having been the corresponding SOFT (voiced) consonant,
    hardened by this rule."""
    jhal_to_jal = {'क': 'ग', 'ट': 'ड', 'त': 'द', 'प': 'ब', 'च': 'ज'}
    out = []
    for i, ch in enumerate(word):
        if ch in jhal_to_jal:
            # FIXED: same pada-final requirement as vyan-3 above -- a
            # consonant carrying a matra is mid-word, so this hardening rule
            # cannot have produced it, and splitting there orphans the matra.
            if i + 1 < len(word) and word[i+1] != '्':
                continue
            right_start = i + 2 if i + 1 < len(word) else i + 1
            if right_start < len(word) and word[right_start] in HARD_CONSONANTS:
                voiced = jhal_to_jal[ch]
                left = word[:i] + voiced + '्'
                right = word[right_start:]
                out.append({'rule_id': 'vyan-4', 'left': left, 'right': right,
                            'note': f'{ch} (hard, before another hard consonant) possibly reversed from {voiced}् (voiced), NEEDS dictionary validation'})
    return out

def candidates_vyan6(word):
    """vyan-6: word-final म् -> अनुस्वार (ं) before any consonant.
    रामम्+वन्दे->रामं वन्दे. Trigger: ं immediately followed by a
    consonant -- fairly low ambiguity since ं has few other sources."""
    out = []
    for i, ch in enumerate(word):
        if ch == 'ं' and i + 1 < len(word):
            nxt = word[i+1]
            if nxt not in 'अआइईउऊऋॠएऐओऔ':  # followed by consonant, not vowel
                left = word[:i] + 'म्'
                right = word[i+1:]
                out.append({'rule_id': 'vyan-6', 'left': left, 'right': right,
                            'note': 'ं restored to म् before consonant'})
    return out

def candidates_vyan7(word):
    """vyan-7: अनुस्वार optionally becomes the class-homogeneous nasal of
    a following यय्-class consonant. गङ्गां+चलति->गङ्गाञ्चलति (before
    palatal); सम्+तोषः->सन्तोषः (before dental).
    Trigger: a class nasal (ङ्/ञ्/ण्/न्/म्) immediately before a stop of
    the SAME class -- candidate: it could have originally been अनुस्वार."""
    class_nasal_to_stops = {
        'ङ': set('कखगघ'), 'ञ': set('चछजझ'),
        'ण': set('टठडढ'), 'न': set('तथदध'), 'म': set('पफबभ'),
    }
    out = []
    for i, ch in enumerate(word):
        if ch in class_nasal_to_stops and i + 1 < len(word) and word[i+1] == '्':
            right_start = i + 2
            if right_start < len(word) and word[right_start] in class_nasal_to_stops[ch]:
                left = word[:i] + 'ं'
                right = word[right_start:]
                out.append({'rule_id': 'vyan-7', 'left': left, 'right': right,
                            'note': f'{ch}् (class nasal before same-class stop) possibly reversed from ं (anusvara), NEEDS dictionary validation'})
    return out

def candidates_vyan5(word):
    """vyan-5: word-final yar-class consonant OPTIONALLY nasalizes before
    a nasal. वाक्+मयम्->वाङ्मयम्/वाग्मयम्. Trigger: a class nasal
    immediately before ANOTHER nasal (ङ्/ञ्/ण्/न्/म्) -- candidate: it
    could be the nasalized form of that class's plain stop."""
    nasal_to_stop = {'ङ': 'क', 'ञ': 'च', 'ण': 'ट', 'न': 'त', 'म': 'प'}
    nasals = set('ङञणनम')
    out = []
    for i, ch in enumerate(word):
        if ch in nasal_to_stop and i + 1 < len(word) and word[i+1] == '्':
            right_start = i + 2
            if right_start < len(word) and word[right_start] in nasals:
                stop = nasal_to_stop[ch]
                left = word[:i] + stop + '्'
                right = word[right_start:]
                out.append({'rule_id': 'vyan-5', 'left': left, 'right': right,
                            'note': f'{ch}् (before another nasal) possibly reversed from plain stop {stop}् (optional nasalisation), NEEDS dictionary validation'})
    return out

def candidates_vyan9_vyan12(word):
    """vyan-9 and vyan-12 share the SAME surface trigger (च्छ) via two
    different mechanisms:
      vyan-9:  त्-final word + श्-initial word -> तच्छ... (त्->च् via
               vyan-1, then optionally श्->छ् via vyan-9)
      vyan-12: vowel-final word + छ्-initial word, त्(tuk) inserted then
               palatalized to च् -> ...अच्छ... (आ+छादयति->आच्छादयति)
    Both candidates are offered; dictionary validation picks the real one."""
    out = []
    for m in re.finditer('च्छ', word):
        i = m.start()
        # vyan-9 reconstruction: ...त् + शेते...
        left_9 = word[:i] + 'त्'
        right_9 = 'श' + word[i+3:]
        out.append({'rule_id': 'vyan-9', 'left': left_9, 'right': right_9,
                    'note': 'च्छ (vyan-9 branch): restored to त्+श (tuk+palatalization+optional श->छ chain), NEEDS dictionary validation'})
        # vyan-12 reconstruction: ...[vowel] + छादयति... (drop the inserted-then-palatalized त्/च्)
        if i > 0:
            left_12 = word[:i]  # just the vowel-ending left word, tuk+palatalization dropped
            right_12 = 'छ' + word[i+3:]
            out.append({'rule_id': 'vyan-12', 'left': left_12, 'right': right_12,
                        'note': 'च्छ (vyan-12 branch): restored to vowel-final left word + छ-initial right word (tuk augment त् inserted then palatalized to च्, now removed), NEEDS dictionary validation'})
    return out

def candidates_vyan14(word):
    """vyan-14: त-वर्ग (त्/थ्/द्/ध्/न्) -> ल् before ल्.
    तत्+लीनः->तल्लीनः; महान्+लाभः->महाल्लाभः.
    Trigger: doubled ल् (ल्ल)."""
    out = []
    for m in re.finditer('ल्ल', word):
        i = m.start()
        for orig in ['त', 'थ', 'द', 'ध', 'न']:
            left = word[:i] + orig + '्'
            right = 'ल' + word[i+3:]
            out.append({'rule_id': 'vyan-14', 'left': left, 'right': right,
                        'note': f'ल्ल restored to {orig}्+ल (त-वर्ग->ल् before ल्), one of 5 possible त-वर्ग sources, NEEDS dictionary validation'})
    return out

def restore_natva_in_right_piece(right_piece, left_piece):
    """vyan-11 (natva, cerebralisation of न् to ण्): unlike the other
    generators, natva is mostly a WORD-INTERNAL phenomenon (see the
    dedicated natva_rulebook.json, natva-1..8), not a boundary-fusion
    rule -- राम+अयनम्->रामायणम् shows the boundary itself is ordinary
    vowel sandhi (svara-1: अ+अ->आ); natva is a SEPARATE, subsequent
    change applied to the अयनम् piece because राम's र् now sits earlier
    in the same (compound) word. So this isn't a split-point generator;
    it's a RECONSTRUCTION correction: given a candidate right piece
    containing ण्, propose the न्-restored dictionary form alongside it,
    since अयनम् (not अयणम्) is the real headword to look up.

    Implements natva-7 (word-final न् is exempt, so word-final ण् is
    NOT reversed here) and a simplified form of natva-1/natva-3 (checks
    for a preceding ऋ/र्/ष् in left_piece, permitting the natva-3
    intervening-sound set). Does NOT implement natva-5/6's obligatory-
    vs-optional distinction (would need to know if the compound is a
    proper name) or natva-8's full blocking-sound enumeration -- flagged
    as approximate."""
    if 'ण' not in right_piece:
        return None
    if right_piece.endswith('ण') or right_piece.endswith('ण्'):
        return None  # natva-7: word-final न् never undergoes natva, so a
                      # word-final ण् is not a natva product -- don't touch it
    # NARROWED (see changelog): `any(t in left_piece for t in (...))` scanned
    # the ENTIRE left piece for a trigger consonant, so a natva-conditioning
    # र् anywhere in a long compound -- arbitrarily far from this boundary --
    # would license a restoration here. natva-1/3's conditioning sound sits
    # near the word-final boundary that abuts right_piece, not anywhere in
    # left_piece; restrict the scan to the last few characters so a trigger
    # far from the boundary no longer counts. (natva-3's own intervening-
    # sound allowance is why this is a window, not just the final letter --
    # still an approximation, per this function's docstring.)
    trigger_window = left_piece[-6:]
    trigger_present = any(t in trigger_window for t in ('ऋ', 'र', 'ष'))
    if not trigger_present:
        return None
    # FIXED: .replace('ण', 'न') rewrote EVERY ण in right_piece, not just
    # the one this trigger is about -- अणुगणम् (which has two, and whose
    # SECOND ण has nothing to do with a natva boundary that lies to the
    # left of the piece) became अनुगनम्, corrupting a ण that was never a
    # natva product. Only the FIRST ण in the piece is a plausible target
    # of a natva change carried over the boundary from left_piece; replace
    # positionally, once, and leave any other ण in the piece untouched.
    idx = right_piece.index('ण')
    restored = right_piece[:idx] + 'न' + right_piece[idx + 1:]
    return {'rule_id': 'vyan-11', 'restored_right': restored,
            'note': f'{right_piece} contains ण् possibly from natva (natva_rulebook.json natva-1/natva-3, triggered by ऋ/र्/ष् in {left_piece}) -- {restored} is the real dictionary headword to check; APPROXIMATE, does not implement natva-5/6/8 fully'}


# vyan-8 and vyan-10: the sandhi_rulebook.json's OWN text hedges on these
# two ("by convention of some grammarians' teaching order", "broadly...
# treated under this heading") -- signalling the source material itself
# treats them as edge cases, not clean general rules. Implemented as
# small attested-example lookups only, same spirit as svara-7/8, rather
# than general triggers that would overgenerate on unclear grounds.

VYAN8_EXCEPTIONS = {
    'वणिग्घसति': ('वणिक्', 'हसति'),
    'विड्ढसति': ('विट्', 'हसति'),
}
def candidates_vyan8(word):
    """vyan-8: nasal-assimilation-adjacent cluster cases the rulebook
    itself describes as following 'some grammarians' teaching order' --
    not a clean general pattern. Attested-example lookup only."""
    out = []
    if word in VYAN8_EXCEPTIONS:
        left, right = VYAN8_EXCEPTIONS[word]
        out.append({'rule_id': 'vyan-8', 'left': left, 'right': right,
                    'note': "attested exception (rulebook's own hedged wording) -- not a general phonological trigger"})
    return out

VYAN10_EXCEPTIONS = {
    'रामस्करोति': ('रामः', 'करोति'),
}
def candidates_vyan10(word):
    """vyan-10: rulebook describes this as covering 'historical/कारिका'
    forms in a loosely-defined context (सजुषो रुः and visarga-as-स्
    substitution). Attested-example lookup only, not a general trigger."""
    out = []
    if word in VYAN10_EXCEPTIONS:
        left, right = VYAN10_EXCEPTIONS[word]
        out.append({'rule_id': 'vyan-10', 'left': left, 'right': right,
                    'note': "attested exception (historical/कारिका form per rulebook) -- not a general phonological trigger"})
    return out

# vyan-13 (ङमुट् nasal augment insertion): the rulebook's own examples
# are marked "illustrative" and the trigger context (short vowel + nasal
# + vowel, itself already ambiguous with ordinary nasal consonants) would
# overgenerate heavily as a general pattern. Deferred, undocumented by
# example in the source material beyond illustrative sketches -- not
# implemented rather than guessed at.

def candidates_svara1(word):
    """svara-1: savarna-dirgha. Two same-class vowels (short or long) merge
    to a single long vowel of that class.
    Trigger: a long vowel आ/ई/ऊ/ॠ at a plausible internal boundary.
    Reverse: propose all 4 combinations within the vowel class (short+short,
    short+long, long+short, long+long) -- the surface form alone can't tell
    us which; dictionary validation on the left piece disambiguates.

    FIXED (see changelog): both cases used to fire regardless of what
    followed the trigger position -- including a SPACE or the end of the
    string. That proposed reconstructing a "second word" starting with
    the merged vowel and having NOTHING after it (विष्णुना, followed by
    a space then सदृशः, was spuriously split into विष्णुना + "अ सदृशो
    वीर्ये", inventing an अ out of thin air right before the space that
    was already a natural, un-sandhi'd word boundary). Genuine savarna-
    dirgha requires the second word's remaining letters to follow
    immediately -- if what follows the matra is a space or nothing, this
    vowel is already word-final and not a fusion point at all."""
    out = []
    # (surface long vowel or matra) -> [(short form, long form), class members]
    classes = [
        ('आ', 'ा', 'अ', 'आ'), ('ई', 'ी', 'इ', 'ई'),
        ('ऊ', 'ू', 'उ', 'ऊ'), ('ॠ', 'ॄ', 'ऋ', 'ॠ'),
    ]
    for long_indep, long_matra, short_form, long_form in classes:
        # Case A: merged vowel appears as an independent letter (word-initial
        # position or after another vowel). Kept for completeness.
        for i, ch in enumerate(word):
            if ch == long_indep and i + 1 < len(word) and word[i+1] != ' ':
                for l in (short_form, long_form):
                    for r in (short_form, long_form):
                        left = word[:i] + l
                        right = r + word[i+1:]
                        out.append({'rule_id': 'svara-1', 'left': left, 'right': right,
                                    'note': f'{long_indep} split as {l}+{r} (savarna-dirgha, one of 4 same-class combinations)'})
        # Case B: merged vowel appears as a MATRA on the preceding consonant
        # (e.g. गिरि+इन्द्रः -> गिरीन्द्रः: the र takes long ई matra).
        # This is the common case for compound-internal boundaries.
        for i, ch in enumerate(word):
            if ch == long_matra and i > 0 and i + 1 < len(word) and word[i+1] != ' ':
                base_cons = word[i-1]
                for l in (short_form, long_form):
                    for r in (short_form, long_form):
                        l_matra = {'अ': '', 'आ': 'ा', 'इ': 'ि', 'ई': 'ी',
                                   'उ': 'ु', 'ऊ': 'ू', 'ऋ': 'ृ', 'ॠ': 'ॄ'}.get(l, '')
                        left = word[:i-1] + base_cons + l_matra
                        right = r + word[i+1:]
                        out.append({'rule_id': 'svara-1', 'left': left, 'right': right,
                                    'note': f'{long_matra} (matra) split as {l}+{r} (savarna-dirgha)'})
    return out

DEVANAGARI_CONSONANTS = set("कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ")

def candidates_svara2(word):
    """svara-2: guna substitution. अ/आ + इ/ई -> ए ; अ/आ + उ/ऊ -> ओ ;
    अ/आ + ऋ/ॠ -> अर् ; अ/आ + ऌ -> अल्.
    Trigger for the इ/उ-classes: ए/ओ matra at a plausible internal boundary.

    FIXED (see changelog): the ऋ/ॠ (-> अर्) branch used to search for the
    literal substring 'अर्' -- independent अ + र् -- but in real compounds
    that अ is virtually always the INVISIBLE inherent vowel of the
    consonant immediately before र्, not an explicit letter (देव+इन्द्रः-style
    words spell it that way; महा+ऋषिः does NOT: it surfaces as 'मह' + 'र्',
    i.e. ह simply reverts to its own bare/implicit अ). That made the branch
    effectively dead code -- महर्षिः, the single most common गुण textbook
    example, produced zero candidates from any generator. Same root cause
    as svara-4's documented implicit-अ limitation, now fixed here too, and
    extended to cover the previously entirely-unimplemented ऌ->अल् branch
    (missing from both this function and the rulebook's own rule text)."""
    out = []
    pairs = [('े', ['इ', 'ई']), ('ो', ['उ', 'ऊ'])]  # matra forms (consonant+e/o)
    for matra, right_options in pairs:
        for i, ch in enumerate(word):
            if ch == matra and i > 0:
                base_cons = word[i-1]  # the consonant this matra attaches to
                for a_form in ('अ', 'आ'):
                    for r in right_options:
                        left = word[:i-1] + base_cons + ('ा' if a_form == 'आ' else '')
                        right = r + word[i+1:]
                        out.append({'rule_id': 'svara-2', 'left': left, 'right': right,
                                    'note': f'{matra} split as {a_form}+{r} (guna)'})
    # ऋ/ॠ-class (-> अर्) and ऌ-class (-> अल्): the "अर्"/"अल्" that results
    # from combining the preceding word's final अ/आ with a following ऋ/ॠ/ऌ
    # is written as [preceding consonant, bare or +ा] + [र्/ल्, clustering
    # via virama with whatever follows] -- there is no separate, explicit
    # अ glyph to search for. Trigger on bare र्/ल् (i.e. र/ल immediately
    # followed by a virama) and look one character back at what it's
    # attached to.
    semivowel_classes = [('र', ['ऋ', 'ॠ']), ('ल', ['ऌ'])]
    for cons, ik_options in semivowel_classes:
        for i, ch in enumerate(word):
            if ch == cons and i > 0 and i + 1 < len(word) and word[i+1] == '्':
                prev = word[i-1]
                if prev not in DEVANAGARI_CONSONANTS:
                    continue  # not a plausible guna boundary (e.g. prev is a matra itself)
                right_start = i + 2
                for a_form in ('अ', 'आ'):
                    for ik in ik_options:
                        left = word[:i-1] + prev + ('ा' if a_form == 'आ' else '')
                        right = ik + word[right_start:]
                        out.append({'rule_id': 'svara-2', 'left': left, 'right': right,
                                    'note': f'{a_form}+{ik} reversed from {cons}् (guna, implicit-a case, NEEDS dictionary validation)'})
    return out

def candidates_svara3(word):
    """svara-3: vrddhi substitution. अ/आ + ए/ऐ -> ऐ ; अ/आ + ओ/औ -> औ."""
    out = []
    pairs = [('ै', ['ए', 'ऐ']), ('ौ', ['ओ', 'औ'])]
    for matra, right_options in pairs:
        for i, ch in enumerate(word):
            if ch == matra and i > 0:
                base_cons = word[i-1]
                for a_form in ('अ', 'आ'):
                    for r in right_options:
                        left = word[:i-1] + base_cons + ('ा' if a_form == 'आ' else '')
                        right = r + word[i+1:]
                        out.append({'rule_id': 'svara-3', 'left': left, 'right': right,
                                    'note': f'{matra} split as {a_form}+{r} (vrddhi)'})
    return out

INDEP_TO_MATRA = {'अ': '', 'आ': 'ा', 'इ': 'ि', 'ई': 'ी', 'उ': 'ु', 'ऊ': 'ू',
                   'ऋ': 'ृ', 'ॠ': 'ॄ', 'ए': 'े', 'ऐ': 'ै', 'ओ': 'ो', 'औ': 'ौ'}

def attach_vowel(prefix, vowel):
    """Correctly attach `vowel` (an independent-vowel-form character like
    'उ') to whatever consonant cluster `prefix` ends in, respecting
    Devanagari orthography: a bare (virama-ended) consonant takes a MATRA,
    not a following independent vowel letter; an empty prefix (or one
    ending in a full vowel already) takes the independent form."""
    if prefix and prefix[-1] == '्':
        return prefix[:-1] + INDEP_TO_MATRA.get(vowel, vowel)
    return prefix + vowel

def candidates_svara4(word):
    """svara-4: yan substitution. इ/ई->य्, उ/ऊ->व्, ऋ/ॠ->र्, ऌ->ल् before a
    dissimilar vowel; the following vowel itself is UNCHANGED.
    Trigger: य/व/र/ल carrying a vowel MATRA directly (e.g. स्वागतम्: व+ा).

    FIXED (see changelog): previously, when the retained following vowel
    was अ specifically, Devanagari orthography writes NO separate glyph
    for it (अ is the default inherent vowel of any consonant with no
    virama/matra) -- यदि+अपि -> यद्यपि was therefore orthographically
    indistinguishable from an ordinary word, and this generator produced
    nothing for it (documented at the time as a deferred "Phase-1d"
    problem). This is now handled by a second branch below: a bare
    semivowel (no matra of its own, and not itself virama-clustered with
    the next consonant) is offered as the implicit-अ case, which also
    covers the semivowel being immediately followed by अनुस्वार (ं) --
    e.g. धातृ+अंशः -> धात्रंशः, where the retained vowel is the nasalised
    implicit अं. As with every other branch here, this will also fire on
    ordinary words containing bare य/व/र/ल (there is no way to avoid
    that locally) -- dictionary validation on both pieces is what makes
    the result trustworthy, exactly as for every other candidate this
    module proposes."""
    out = []
    semivowel_to_ik = {'य': ['इ', 'ई'], 'व': ['उ', 'ऊ'], 'र': ['ऋ', 'ॠ'], 'ल': ['ऌ']}
    matra_map = {'ा':'आ','ि':'इ','ी':'ई','ु':'उ','ू':'ऊ','ृ':'ऋ','ॄ':'ॠ','े':'ए','ै':'ऐ','ो':'ओ','ौ':'औ'}
    for i, ch in enumerate(word):
        if ch in semivowel_to_ik and i + 1 < len(word):
            nxt = word[i+1]
            if nxt in matra_map:
                following_vowel = matra_map[nxt]
                for ik in semivowel_to_ik[ch]:
                    left = attach_vowel(word[:i], ik)
                    right = following_vowel + word[i+2:]
                    out.append({'rule_id': 'svara-4', 'left': left, 'right': right,
                                'note': f'{ch}+{nxt}(matra) reversed to {ik}+{following_vowel} (yan, NEEDS dictionary validation)'})
            elif nxt != '्':
                # bare semivowel: no matra of its own, and not clustering
                # via virama with the next consonant -- the retained vowel
                # is the invisible implicit अ (plain, or nasalised if nxt
                # is ं). See docstring above.
                for ik in semivowel_to_ik[ch]:
                    left = attach_vowel(word[:i], ik)
                    right = 'अ' + word[i+1:]
                    out.append({'rule_id': 'svara-4', 'left': left, 'right': right,
                                'note': f'{ch} (bare, implicit अ) reversed to {ik}+अ (yan, implicit-a case, NEEDS dictionary validation)'})
            elif nxt == '्':
                # NEW (see changelog): the semivowel carries its OWN
                # virama, and -- directly or after one pada-boundary
                # space -- is followed by an INDEPENDENT vowel letter
                # rather than that vowel attaching as a matra or being
                # implicit. This is a distinct orthographic convention
                # some corpora use for यण् at a word boundary: नु+अस्मिन्
                # -> "न्व् अस्मिन्" (को न्व् अस्मिन्, Ramayana Bala Kanda
                # 1.4) keeps व् separately viramed and अस्मिन् spelled
                # out with its own leading अ, rather than fusing to
                # "न्वस्मिन्". Requires an independent vowel letter
                # specifically -- a bare consonant here would just be an
                # ordinary consonant cluster (ordinary words very
                # commonly have a semivowel+virama+consonant sequence),
                # so this branch is much more narrowly triggered than
                # the other two and should rarely misfire.
                j = i + 2
                had_gap = False
                if j < len(word) and word[j] == ' ':
                    had_gap = True
                    j += 1
                if j < len(word) and word[j] in INDEP_TO_MATRA:
                    following_vowel = word[j]
                    for ik in semivowel_to_ik[ch]:
                        left = attach_vowel(word[:i], ik)
                        right = word[j:]
                        out.append({'rule_id': 'svara-4', 'left': left, 'right': right,
                                    'note': f'{ch}् (own virama, before independent vowel'
                                            + (' across a pada-boundary space' if had_gap else '')
                                            + f') reversed to {ik}+{following_vowel} (yan, NEEDS dictionary validation)'})
    return out

def candidates_svara5(word):
    """svara-5: ec vowels (ए/ओ/ऐ/औ) before any vowel -> अय्/अव्/आय्/आव्; the
    following vowel itself is RETAINED unchanged (same mechanism as yan).

    REWRITTEN (see changelog): the old version searched for the literal
    substring 'आव्' etc -- independent आ + व् + VIRAMA -- but that sequence
    can never occur in valid Devanagari: a virama means "no vowel here,
    cluster with the next consonant", so a virama-marked व् can never be
    immediately followed by a vowel letter. When औ genuinely becomes आव्
    mid-word, the आ attaches as a MATRA to the PRECEDING consonant and व्
    carries the NEXT vowel directly (as its own matra, or its own
    inherent अ) -- it is never virama-marked. That old trigger therefore
    could not fire on ANY valid input, including all 4 of the rulebook's
    own canonical examples (नयनम्, नायकः, भवनम्, पावकः) -- not just the
    implicit-अ ones as previously documented.

    New approach, mirroring svara-4's actual (correct) shape: scan forward
    for every bare य/व (not itself virama-clustered with the next
    consonant) and treat IT as the trigger position, exactly like svara-4
    treats य/व/र/ल. What follows य/व (its own matra, or its bareness) is
    the retained following vowel -- same lookup as svara-4. What PRECEDES
    it determines the source: a bare consonant (implicit अ) means it came
    from ए/ओ; a consonant carrying a ा (आ) matra means it came from ऐ/औ."""
    out = []
    matra_map = {'ा':'आ','ि':'इ','ी':'ई','ु':'उ','ू':'ऊ','ृ':'ऋ','ॄ':'ॠ','े':'ए','ै':'ऐ','ो':'ओ','ौ':'औ'}
    guna_matra_for = {'य': 'े', 'व': 'ो'}    # ए, ओ -- from an अ-preceded (guna-grade) source
    vrddhi_matra_for = {'य': 'ै', 'व': 'ौ'}  # ऐ, औ -- from an आ-preceded (vrddhi-grade) source

    for i, ch in enumerate(word):
        if ch not in guna_matra_for or i == 0:
            continue

        # what follows य/व is the retained following vowel (identical
        # lookup to svara-4's own following-vowel handling)
        if i + 1 < len(word) and word[i+1] in matra_map:
            following_vowel = matra_map[word[i+1]]
            right = following_vowel + word[i+2:]
        elif i + 1 < len(word) and word[i+1] != '्':
            following_vowel = 'अ'
            right = 'अ' + word[i+1:]
        else:
            continue  # य/व clusters via virama with the next consonant -- no vowel of its own here

        prev = word[i-1]
        if prev in DEVANAGARI_CONSONANTS:
            left = word[:i-1] + prev + guna_matra_for[ch]
            out.append({'rule_id': 'svara-5', 'left': left, 'right': right,
                        'note': f'{ch} (after bare {prev}) reversed to {prev}+{guna_matra_for[ch]} (ayadi, guna-grade source, NEEDS dictionary validation)'})
        elif prev == 'ा' and i >= 2:
            base_cons = word[i-2]
            left = word[:i-2] + base_cons + vrddhi_matra_for[ch]
            out.append({'rule_id': 'svara-5', 'left': left, 'right': right,
                        'note': f'{ch} (after आ-matra) reversed to {vrddhi_matra_for[ch]} (ayadi, vrddhi-grade source, NEEDS dictionary validation)'})
    return out

def candidates_svara6(word):
    """svara-6: purvarupa. Pada-final ए/ओ + अ -> ए/ओ alone, with the elided
    अ marked by avagraha ऽ.
    Trigger: literal 'ऽ' -- this one is nearly unambiguous since avagraha
    has no other use in running text.

    EXTENDED (see changelog): an ओ immediately before ऽ is ambiguous
    between two sources -- a genuinely ओ-ending word (विष्णो+अव), OR an
    अ-preceded विसर्ग that itself first became ओ via visarga-4's उत्व->guna
    mechanism (रामः+अपि -> रामो + [पूर्वरूप] -> रामोऽपि). For the second
    case, peeling only this boundary leaves "रामो" -- not a real citation
    form -- and split_word_recursive's peel-and-recurse CANNOT resolve it
    further on a later pass, because visarga-4's trigger needs to see what
    originally followed the ओ, and that context is exactly what this peel
    consumes. So this now also offers the fully-resolved reading directly
    (राम+ः, क+ः, शिव+ः, ...) alongside the intermediate one, in one shot;
    dictionary validation prefers whichever piece is real (रामः is;
    विष्णः, from the same mechanical extension, correctly is not)."""
    out = []
    for i, ch in enumerate(word):
        if ch == 'ऽ':
            left = word[:i]  # the े/ो ending is already present just before ऽ
            right = 'अ' + word[i+1:]
            out.append({'rule_id': 'svara-6', 'left': left, 'right': right,
                        'note': 'avagraha ऽ marks elided अ -- low ambiguity, restore अ directly'})
            if left and left[-1] == 'ो':
                fully_resolved_left = left[:-1] + 'ः'
                out.append({'rule_id': 'svara-6+visarga-4', 'left': fully_resolved_left, 'right': right,
                            'note': 'ओ (before ऽ) ALSO reversed one layer further to अः (a-preceded visarga + following अ, resolved in one step, NEEDS dictionary validation)'})
    return out


def candidates_svara7(word):
    """svara-7: parapa-rupa (following-form retention). Pada-final ए/ओ
    followed by ए in specific prefix+root combinations retains ए alone --
    e.g. प्र+एजते->प्रेजते (NOT the vrddhi ऐ that svara-3 would predict).

    IMPORTANT: this is NOT a general phonological pattern -- it is a
    lexical EXCEPTION restricted to a small, closed set of root+prefix
    combinations (attested: √एज् 'to stir' with प्र; इन्द्र-type words
    with certain उपसर्गs). A phonological trigger would just be "अ or
    आ followed by ए", which is indistinguishable from svara-3 (vrddhi,
    the REGULAR outcome) on the surface -- there is no way to tell from
    the string alone that THIS particular combination is the exception
    rather than the rule. So this is implemented as a small attested-
    exception lookup, extensible as more instances are confirmed against
    real texts, rather than a pattern that would silently misfire on
    every ordinary अ+ए sequence."""
    ATTESTED_EXCEPTIONS = {
        'प्रेजते': ('प्र', 'एजते'),
        'उपेन्द्रः': ('उप', 'एन्द्रः'),  # rulebook's own example; NOTE this could
        # also just be ordinary svara-2 guna (अ+इ->ए is wrong here since
        # इन्द्रः starts with इ not ए -- the rulebook's own example text
        # flags this as "अवग्रह-रहित पररूप उदाहरण", i.e. it is itself
        # a borderline/illustrative case, not a clean-cut one)
    }
    out = []
    if word in ATTESTED_EXCEPTIONS:
        left, right = ATTESTED_EXCEPTIONS[word]
        out.append({'rule_id': 'svara-7', 'left': left, 'right': right,
                    'note': 'attested lexical exception (parapa-rupa) -- not a general phonological trigger'})
    return out

def candidates_svara9_m_junction(word):
    """svara-9 (word-final म् + vowel junction): a pada-final म् (virama,
    no vowel of its own) directly followed by a vowel-initial word simply
    absorbs that vowel as its own matra -- no consonant CHANGE happens
    (contrast vyan-6, म्+CONSONANT -> अनुस्वार, which is a real
    transformation). This isn't traditionally enumerated as its own
    named sandhi because nothing phonologically alternates -- but the
    orthographic merge still needs to be REVERSED the same way every
    other junction here does: विवासयाम्+आस -> विवासयामास, दर्शयाम्+आस ->
    दर्शयामास, श्रूयताम्+इति -> श्रूयतामिति. This exact shape (a -याम्
    verb stem + आस, the periphrastic perfect) alone accounts for 7
    occurrences in a single 172-line corpus sample, so it earns a
    dedicated generator rather than being left to coincidentally emerge
    from an unrelated rule's misfire.

    Trigger: bare म् (not itself virama-clustered, i.e. NOT part of a
    म्+consonant cluster already covered by vyan-6/vyan-7) carrying an
    explicit vowel matra of its own. High false-positive rate is
    expected -- म is one of the most common consonants in the language
    -- dictionary validation of both pieces is what makes any individual
    candidate trustworthy, exactly as for every other generator here."""
    out = []
    matra_map = {'ा':'आ','ि':'इ','ी':'ई','ु':'उ','ू':'ऊ','ृ':'ऋ','ॄ':'ॠ','े':'ए','ै':'ऐ','ो':'ओ','ौ':'औ'}
    for i, ch in enumerate(word):
        if ch == 'म' and i + 1 < len(word) and word[i+1] in matra_map:
            vowel = matra_map[word[i+1]]
            left = word[:i] + 'म्'
            right = vowel + word[i+2:]
            out.append({'rule_id': 'svara-9', 'left': left, 'right': right,
                        'note': f'म्+{word[i+1]}(matra) reversed to म्+{vowel} (pada-final म् simply absorbing a following vowel, NEEDS dictionary validation)'})
    return out



def candidates_svara_unified(word):
    """EXPERIMENTAL (see 'right-to-left intersection scan' session).

    Merges the scanning done separately by candidates_svara1,
    candidates_svara2, candidates_svara3, candidates_svara4,
    candidates_svara5, candidates_svara6, and candidates_svara9_m_junction
    into a SINGLE right-to-left pass over `word`, instead of those seven
    functions each running their own independent left-to-right pass (nine,
    counting svara-1's internal 4-class double loop and svara-2's two
    internal loops as separate passes).

    Rationale: every svara-sandhi rule this covers produces its surface
    result from one fixed, closed set of letters/matras --
    आ,ई,ऊ,ॠ (savarna-dirgha), ए,ओ / ऐ,औ (guna/vrddhi matras),
    य्,व्,र्,ल् (yan substitutes, which also double as the trigger for
    svara-2's ऋ/ऌ-guna branch and svara-5's ec-vowel branch), ऽ
    (purvarupa avagraha), and bare म् (pada-final anusvara-absorption).
    A single right-to-left scan that recognizes this set at each
    position -- and, at the shared य/व/र/ल position, checks all three
    rules that can plausibly explain it -- replaces the seven separate
    full-string scans with one.

    The construction logic at every trigger position is copied VERBATIM
    from the original functions (only the scanning is merged) so the
    candidate set this produces must be identical to the union of the
    seven originals -- verified by diff-testing against the regression
    suite and the Ramayana corpus before this replaced anything.

    svara-7 (lexical exception, whole-word dict lookup) and svara-8
    (whole-word गो-class recognition) are NOT folded in here -- they
    aren't per-character scans to begin with (O(1) dict/set lookups),
    so merging them would not reduce any iteration count.
    """
    out = []
    classes = [
        ('आ', 'ा', 'अ', 'आ'), ('ई', 'ी', 'इ', 'ई'),
        ('ऊ', 'ू', 'उ', 'ऊ'), ('ॠ', 'ॄ', 'ऋ', 'ॠ'),
    ]
    indep_to_class = {c[0]: c for c in classes}
    matra_to_class = {c[1]: c for c in classes}
    matra_map = {'ा': 'आ', 'ि': 'इ', 'ी': 'ई', 'ु': 'उ', 'ू': 'ऊ', 'ृ': 'ऋ', 'ॄ': 'ॠ',
                 'े': 'ए', 'ै': 'ऐ', 'ो': 'ओ', 'ौ': 'औ'}
    semivowel_to_ik = {'य': ['इ', 'ई'], 'व': ['उ', 'ऊ'], 'र': ['ऋ', 'ॠ'], 'ल': ['ऌ']}
    guna_matra_for = {'य': 'े', 'व': 'ो'}
    vrddhi_matra_for = {'य': 'ै', 'व': 'ौ'}
    short_to_long_matra = {'अ': '', 'आ': 'ा', 'इ': 'ि', 'ई': 'ी',
                            'उ': 'ु', 'ऊ': 'ू', 'ऋ': 'ृ', 'ॠ': 'ॄ'}

    n = len(word)
    for i in range(n - 1, -1, -1):
        ch = word[i]

        # svara-1 Case A: independent long vowel आ/ई/ऊ/ॠ
        if ch in indep_to_class and i + 1 < n and word[i + 1] != ' ':
            long_indep, long_matra, short_form, long_form = indep_to_class[ch]
            for l in (short_form, long_form):
                for r in (short_form, long_form):
                    left = word[:i] + l
                    right = r + word[i + 1:]
                    out.append({'rule_id': 'svara-1', 'left': left, 'right': right,
                                'note': f'{long_indep} split as {l}+{r} (savarna-dirgha, one of 4 same-class combinations)'})

        # svara-1 Case B: long vowel as a matra on the preceding consonant
        if ch in matra_to_class and i > 0 and i + 1 < n and word[i + 1] != ' ':
            long_indep, long_matra, short_form, long_form = matra_to_class[ch]
            base_cons = word[i - 1]
            for l in (short_form, long_form):
                for r in (short_form, long_form):
                    l_matra = short_to_long_matra.get(l, '')
                    left = word[:i - 1] + base_cons + l_matra
                    right = r + word[i + 1:]
                    out.append({'rule_id': 'svara-1', 'left': left, 'right': right,
                                'note': f'{long_matra} (matra) split as {l}+{r} (savarna-dirgha)'})

        # svara-2 (guna, इ/उ-class): े/ो matra
        if ch in ('े', 'ो') and i > 0:
            base_cons = word[i - 1]
            right_options = ['इ', 'ई'] if ch == 'े' else ['उ', 'ऊ']
            for a_form in ('अ', 'आ'):
                for r in right_options:
                    left = word[:i - 1] + base_cons + ('ा' if a_form == 'आ' else '')
                    right = r + word[i + 1:]
                    out.append({'rule_id': 'svara-2', 'left': left, 'right': right,
                                'note': f'{ch} split as {a_form}+{r} (guna)'})

        # svara-3 (vrddhi, इ/उ-class): ै/ौ matra
        if ch in ('ै', 'ौ') and i > 0:
            base_cons = word[i - 1]
            right_options = ['ए', 'ऐ'] if ch == 'ै' else ['ओ', 'औ']
            for a_form in ('अ', 'आ'):
                for r in right_options:
                    left = word[:i - 1] + base_cons + ('ा' if a_form == 'आ' else '')
                    right = r + word[i + 1:]
                    out.append({'rule_id': 'svara-3', 'left': left, 'right': right,
                                'note': f'{ch} split as {a_form}+{r} (vrddhi)'})

        # svara-6 (purvarupa): avagraha ऽ
        if ch == 'ऽ':
            left = word[:i]
            right = 'अ' + word[i + 1:]
            out.append({'rule_id': 'svara-6', 'left': left, 'right': right,
                        'note': 'avagraha ऽ marks elided अ -- low ambiguity, restore अ directly'})
            if left and left[-1] == 'ो':
                fully_resolved_left = left[:-1] + 'ः'
                out.append({'rule_id': 'svara-6+visarga-4', 'left': fully_resolved_left, 'right': right,
                            'note': 'ओ (before ऽ) ALSO reversed one layer further to अः (a-preceded visarga + following अ, resolved in one step, NEEDS dictionary validation)'})

        # svara-9: bare म् + vowel matra (pada-final म् absorbing a vowel)
        if ch == 'म' and i + 1 < n and word[i + 1] in matra_map:
            vowel = matra_map[word[i + 1]]
            left = word[:i] + 'म्'
            right = vowel + word[i + 2:]
            out.append({'rule_id': 'svara-9', 'left': left, 'right': right,
                        'note': f'म्+{word[i + 1]}(matra) reversed to म्+{vowel} (pada-final म् simply absorbing a following vowel, NEEDS dictionary validation)'})

        # ---- shared य/व/र/ल intersection: svara-4, svara-5, svara-2(ऋ/ऌ) ----
        if ch in semivowel_to_ik and i + 1 < n:
            nxt = word[i + 1]

            # svara-4: यण् substitution (all four semivowels)
            if nxt in matra_map:
                following_vowel = matra_map[nxt]
                for ik in semivowel_to_ik[ch]:
                    left = attach_vowel(word[:i], ik)
                    right = following_vowel + word[i + 2:]
                    out.append({'rule_id': 'svara-4', 'left': left, 'right': right,
                                'note': f'{ch}+{nxt}(matra) reversed to {ik}+{following_vowel} (yan, NEEDS dictionary validation)'})
            elif nxt != '्':
                for ik in semivowel_to_ik[ch]:
                    left = attach_vowel(word[:i], ik)
                    right = 'अ' + word[i + 1:]
                    out.append({'rule_id': 'svara-4', 'left': left, 'right': right,
                                'note': f'{ch} (bare, implicit अ) reversed to {ik}+अ (yan, implicit-a case, NEEDS dictionary validation)'})
            elif nxt == '्':
                j = i + 2
                had_gap = False
                if j < n and word[j] == ' ':
                    had_gap = True
                    j += 1
                if j < n and word[j] in INDEP_TO_MATRA:
                    following_vowel = word[j]
                    for ik in semivowel_to_ik[ch]:
                        left = attach_vowel(word[:i], ik)
                        right = word[j:]
                        out.append({'rule_id': 'svara-4', 'left': left, 'right': right,
                                    'note': f'{ch}् (own virama, before independent vowel'
                                            + (' across a pada-boundary space' if had_gap else '')
                                            + f') reversed to {ik}+{following_vowel} (yan, NEEDS dictionary validation)'})

                # svara-2's ऋ/ऌ-guna branch shares this exact nxt=='्'
                # trigger, र/ल only
                if ch in ('र', 'ल') and i > 0:
                    prev = word[i - 1]
                    if prev in DEVANAGARI_CONSONANTS:
                        ik_options = ['ऋ', 'ॠ'] if ch == 'र' else ['ऌ']
                        right_start = i + 2
                        for a_form in ('अ', 'आ'):
                            for ik in ik_options:
                                left2 = word[:i - 1] + prev + ('ा' if a_form == 'आ' else '')
                                right2 = ik + word[right_start:]
                                out.append({'rule_id': 'svara-2', 'left': left2, 'right': right2,
                                            'note': f'{a_form}+{ik} reversed from {ch}् (guna, implicit-a case, NEEDS dictionary validation)'})

            # svara-5: अयादि (only य/व, needs i>0 to see the grade marker)
            if ch in guna_matra_for and i > 0:
                if nxt in matra_map:
                    right5 = matra_map[nxt] + word[i + 2:]
                elif nxt != '्':
                    right5 = 'अ' + word[i + 1:]
                else:
                    right5 = None
                if right5 is not None:
                    prev = word[i - 1]
                    if prev in DEVANAGARI_CONSONANTS:
                        left5 = word[:i - 1] + prev + guna_matra_for[ch]
                        out.append({'rule_id': 'svara-5', 'left': left5, 'right': right5,
                                    'note': f'{ch} (after bare {prev}) reversed to {prev}+{guna_matra_for[ch]} (ayadi, guna-grade source, NEEDS dictionary validation)'})
                    elif prev == 'ा' and i >= 2:
                        base_cons2 = word[i - 2]
                        left5 = word[:i - 2] + base_cons2 + vrddhi_matra_for[ch]
                        out.append({'rule_id': 'svara-5', 'left': left5, 'right': right5,
                                    'note': f'{ch} (after आ-matra) reversed to {vrddhi_matra_for[ch]} (ayadi, vrddhi-grade source, NEEDS dictionary validation)'})

    return out

def candidates_svara8(word):
    """svara-8: root-final ओ (गो-class roots: गो, द्यो/द्यु, ग्लौ, नौ-type)
    takes अव् before a vowel-initial affix -- e.g. गो+अम्->गवाम्.

    This is NOT a clean two-piece compound boundary: गो+अम्=गवाम् actually
    stacks TWO sandhis (ओ->अव् per this rule, then the resulting अ+अ of
    अव्+अम् merges into आ via svara-1/savarna-dirgha). There is no single
    surface split point that cleanly separates 'root' from 'ending' the
    way the other rules' candidates do. Rather than fake a left/right
    split, this is implemented as WHOLE-WORD recognition of attested
    गो-class अव्-declension forms, mapping the inflected surface form
    back to its root -- a different, narrower kind of output than the
    other generators return."""
    GO_CLASS_FORMS = {
        # attested अव्-stem inflected forms -> (root, case/number gloss)
        'गवाम्': ('गो', 'genitive plural'), 'गवे': ('गो', 'dative singular'),
        'गवि': ('गो', 'locative singular'), 'गवः': ('गो', 'nominative/genitive/ablative singular or nominative plural'),
        'गवा': ('गो', 'instrumental singular'),
    }
    out = []
    if word in GO_CLASS_FORMS:
        root, gloss = GO_CLASS_FORMS[word]
        out.append({'rule_id': 'svara-8', 'left': root, 'right': '',
                    'note': f'whole-word recognition: {word} is the {gloss} of गो-class root {root} (not a compound split -- declension-internal, two stacked sandhis)'})
    return out

# svara-9: NOT a candidate generator -- it's a GUARD that suppresses
# false-positive vowel-sandhi candidates at legitimate no-sandhi hiatus
# points (dual endings, प्रगृह्य words, pluta vowels). Call this on a
# candidate's LEFT piece before trusting a svara-1..5 split.
PRAGRHYA_WORDS = {
    # closed list of common indeclinable/pronominal प्रगृह्य forms that
    # never undergo vowel sandhi with a following vowel (Ashtadhyayi 1.1.11-19)
    'अमी', 'अमू', 'अम्ब', 'अम्बे', 'अम्बा', 'हे', 'अहो', 'अहह',
}
def is_pragrhya_no_sandhi_context(left_piece):
    """svara-9 guard. Returns True if `left_piece` is a known प्रगृह्य
    context where NO vowel sandhi should occur, so a candidate split
    proposing one here should be discarded/deprioritized.

    NOTE: only covers the closed-word-list part of प्रगृह्य (Ashtadhyayi
    1.1.12-19). The dual-ending part (any noun's dual ई/ऊ/ए is also
    प्रगृह्य, e.g. हरी in हरी एतौ) requires knowing the word's
    grammatical NUMBER, which this splitter does not track -- that part
    is NOT implemented and would need to consult noun_declensions /
    shabdarupani data to know a given ई/ऊ/ए ending is actually dual."""
    return left_piece in PRAGRHYA_WORDS

def candidates_elided_visarga_boundary(word):
    """Bridges restore_elided_visarga_at_word_boundary (visarga-4b,
    visarga-6, sa-etad-exception) into the candidate-generation
    framework, so a MULTI-WORD string (पीनवक्षा विशालाक्षः) can have an
    earlier word's ELIDED visarga restored as part of ordinary peeling,
    not just via a separate, manually-invoked two-argument call. Unlike
    every other generator here, an elided visarga leaves NO local
    trigger in the surface text at all -- the only way to notice it is
    to look at PAIRS of adjacent space-separated words and ask whether
    the first would plausibly have had a visarga that disappeared
    before the second (पीनवक्षा + विशालाक्षः: आ-preceded visarga elided
    before a soft consonant, visarga-6).

    Scans every space in `word`, takes the token immediately before and
    after it, and asks restore_elided_visarga_at_word_boundary whether
    the first token's visarga was elided. If so, proposes peeling the
    (now visarga-restored) first token off as the left piece, leaving
    the space and everything after it as the right piece -- which the
    recursive engine's right-piece expansion can then process further
    for any additional such boundaries, or further real sandhi."""
    out = []
    tokens = []
    pos = 0
    for i, ch in enumerate(word):
        if ch == ' ':
            tokens.append((pos, i))
            pos = i + 1
    tokens.append((pos, len(word)))
    for idx in range(len(tokens) - 1):
        start1, end1 = tokens[idx]
        start2, end2 = tokens[idx + 1]
        tok1, tok2 = word[start1:end1], word[start2:end2]
        if not tok1 or not tok2:
            continue
        restored = restore_elided_visarga_at_word_boundary(tok1, tok2)
        if restored:
            # ADDITIONAL guard (see changelog), specific to this
            # generator: restore_elided_visarga_at_word_boundary can't
            # tell "a word ending in a bare consonant that's already
            # complete as-is" (धर्म, which just genuinely ends in म्)
            # from "a word whose nominative -अः visarga silently
            # dropped" -- both look identical on the surface. Calling it
            # directly with two already-separated words (its original,
            # narrower use) leaves that judgement to the caller; wiring
            # it into automatic candidate generation exposed that gap
            # for the first time (धर्म इवापरः was spuriously restored to
            # धर्मः + इव, since both धर्म and धर्मः independently
            # validate and the restored version happened to win the
            # ranking). Only trust the restoration here when the BARE
            # form does NOT already validate on its own -- that is
            # genuine positive evidence something was elided, rather
            # than two equally-plausible readings competing on ranking
            # alone.
            #
            # FIXED (layering): this check used to call dictionary_lookup()
            # RIGHT HERE, which made generate_candidates() -- nominally the
            # pure-phonology layer -- depend on an open SQLite connection.
            # That broke the generate/validate separation the whole module
            # is built around: the generators could not be exercised at all
            # without a populated dictionary file, so they were untestable
            # in isolation and the --test suite silently depended on
            # dictionary contents. The condition is unchanged; it is now
            # DECLARED on the candidate and enforced by
            # validate_against_dictionary(), which is the layer that is
            # allowed to touch the database.
            left = word[:start1] + restored['restored']
            right = word[end1:]  # keeps the space, unchanged from here on
            out.append({'rule_id': restored['rule_id'], 'left': left, 'right': right,
                        'requires_bare_form_absent': tok1,
                        'note': f"elided-visarga boundary restoration: {restored['note']}"})
    return out

ALL_GENERATORS = [candidates_visarga1, candidates_visarga2, candidates_visarga3, candidates_visarga4,
                   candidates_visarga5, candidates_visarga_ro_ri, candidates_vyan3,
                   candidates_vyan1, candidates_vyan2, candidates_vyan4, candidates_vyan5,
                   candidates_vyan6, candidates_vyan7, candidates_vyan9_vyan12, candidates_vyan14,
                   candidates_vyan8, candidates_vyan10,
                   # candidates_svara1/2/3/4/5/6/9_m_junction are SUPERSEDED by
                   # candidates_svara_unified (see that function's docstring and
                   # the "right-to-left intersection scan" session in the
                   # changelog above) -- the seven original functions are left
                   # defined below, unused, as a rollback reference; they are
                   # verified byte-for-byte equivalent to the unified scan on
                   # every corpus + regression word tested.
                   candidates_svara_unified,
                   candidates_svara7, candidates_svara8,
                   candidates_elided_visarga_boundary]

COMBINING_MARKS = set('ािीुूृॄॢेैोौंःँ्')

def is_well_formed_candidate(c):
    """Cheap structural invariant applied to EVERY generator's output.

    A right piece may never begin with a combining mark (a vowel matra,
    anusvara/visarga, or a virama): in Devanagari those attach to a
    preceding base consonant, so a right piece starting with one means the
    split cut through a grapheme cluster and orphaned a vowel sign -- the
    resulting string is not valid Devanagari, it cannot be a real word, and
    the base consonant it belonged to has silently lost its vowel.

    Enforced centrally rather than trusting each of the ~25 generators to
    slice cleanly on its own. Measured against this file's own regression
    words: drops 10 of 286 candidates, loses 0 correct answers.
    """
    return not (c['right'] and c['right'][0] in COMBINING_MARKS)


def generate_candidates(word):
    word = normalize_input(word)
    results = []
    for gen_index, gen in enumerate(ALL_GENERATORS):
        for c in gen(word):
            if not is_well_formed_candidate(c):
                continue
            c['citation'] = CITATIONS.get(c['rule_id']) or SYNTHETIC_CITATIONS.get(c['rule_id'], {})
            c['_gen_index'] = gen_index
            # svara-9 guard: flag (don't silently drop -- the pragrhya
            # word-list check is partial, see is_pragrhya_no_sandhi_context
            # docstring) candidates whose left piece is a known no-sandhi word
            if c['rule_id'].startswith('svara') and is_pragrhya_no_sandhi_context(c['left']):
                c['pragrhya_flag'] = 'left piece is a known प्रगृह्य word -- svara-9 says NO sandhi should occur here; this candidate is likely spurious'
            results.append(c)
    # FIXED: impose a CANONICAL order. Nothing downstream may depend on the
    # order generators happen to emit in -- but two things silently did.
    # split_word()/_compute_actual_split() report confirmed[0], i.e. pure
    # emission order with no sort at all; and split_word_recursive()'s
    # ranking sort is STABLE, so candidates tied on
    # (category, validated, len(right)) are decided by emission order too
    # (the "insertion-order artifact" its own comments call out).
    #
    # That made behaviour hostage to each generator's internal scan
    # DIRECTION. The unified-scan swap changed exactly that: it produces
    # the same candidate SET as the seven functions it replaced (verified,
    # 0 mismatches on ~4000 words) but in right-to-left rather than
    # left-to-right order, differing on ~19% of words -- which flips the
    # reported answer on ~28% of svara-triggered words. The corpus runs
    # missed this only because the visarga/vyanjana generators run first
    # and usually supply confirmed[0].
    #
    # Sorting here makes the two versions byte-identical (verified, 0
    # mismatches on 1505 words) and makes that property hold by
    # construction for any future generator rewrite.
    results.sort(key=lambda c: (c['_gen_index'], len(c['right']),
                                c['rule_id'], c['left'], c['right']))
    return results

def dictionary_lookup(deva_word, db_path=None, _conn_cache={}):
    """Standalone single-word dictionary lookup, factored out of
    validate_against_dictionary() so other callers (e.g. the recursive
    splitter, which needs to check RIGHT pieces too, not just LEFT
    pieces) can reuse the exact same lookup logic instead of duplicating
    it. Caches one open sqlite3 connection per db_path for the life of
    the process, since repeated single-word lookups during recursion would
    otherwise reopen the DB file every call. (validate_against_dictionary
    now goes through this same cache too -- it no longer opens its own
    connection; see close_connections() to release the cache explicitly.)"""
    import sqlite3, os
    from transliterate import deva_to_slp1

    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apte_dictionary.sqlite')
    conn = _conn_cache.get(db_path)
    if conn is None:
        # FIXED: sqlite3.connect() CREATES a missing database file instead
        # of failing. So a missing/mistyped dictionary path used to leave a
        # zero-byte apte_dictionary.sqlite on disk and then surface as
        # "OperationalError: no such table: stems" -- an error that points
        # at a schema problem rather than the actual missing-file cause,
        # with a junk file now sitting there to confuse the next run.
        # Same actionable-error treatment load_citations() already gets.
        if not os.path.isfile(db_path):
            raise FileNotFoundError(
                f"Dictionary database not found: {db_path}\n"
                "Build it with build_apte_dictionary.py, or pass an explicit "
                "db_path. (Not creating it here: an empty database would "
                "fail later with a misleading 'no such table' error.)"
            )
        # FIXED: sqlite3 defaults to check_same_thread=True, so a cached
        # connection created on one thread raises ProgrammingError the
        # moment a different thread (a future web wrapper, a worker pool)
        # reuses it. This module never mutates the dictionary at runtime
        # -- every access here is a read -- so sharing a read connection
        # across threads is safe; check_same_thread=False just stops
        # sqlite3 from refusing it.
        conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn_cache[db_path] = conn
    cur = conn.cursor()

    # strip trailing visarga/anusvara/virama for the stem-table lookup,
    # since the dictionary's `stems` table already holds ending-stripped
    # variants -- try the raw SLP1 form first, then a couple of the most
    # common case-endings stripped by hand as a fallback.
    #
    # FIXED: rstrip(chars) strips every trailing character IN THE SET, not
    # a single suffix -- 'ramaHH'.rstrip('H') gives 'rama', not 'ramaH'.
    # Unlikely to matter for well-formed SLP1 output, but silent when it
    # does. removesuffix() only removes the exact suffix, once.
    # Also de-duplicated (a word with no trailing H/M queried the same
    # string three times) while preserving try-order, and each attempt
    # is dict-keyed so the query text always matches what actually matched.
    slp1 = deva_to_slp1(deva_word)
    candidates = list(dict.fromkeys([slp1, slp1.removesuffix('H'), slp1.removesuffix('M')]))
    for candidate in candidates:
        # ORDER BY entry_id: a bare SELECT ... LIMIT 1 with no ORDER BY
        # returns an arbitrary row when a stem maps to more than one
        # entry -- not guaranteed stable across SQLite versions or after
        # ANALYZE. Ordering by entry_id makes the choice deterministic
        # and reproducible.
        cur.execute("""SELECT e.k1_raw, e.body_text, e.is_crossref, e.crossref_target
                       FROM stems s JOIN entries e ON s.entry_id = e.entry_id
                       WHERE s.stem = ? ORDER BY e.entry_id LIMIT 1""", (candidate,))
        row = cur.fetchone()
        if row:
            # FIXED: row[1] (body_text) can be NULL for a cross-reference
            # entry even when is_crossref is falsy in some corpora -- the
            # old `row[1][:120]` then raised TypeError. body_text or ''
            # makes a NULL gloss an empty string instead of a crash.
            gloss = 'see cross-ref' if row[2] else (row[1] or '')[:120]
            return {'slp1_queried': candidate, 'k1_raw': row[0],
                    'gloss': gloss, 'found': True}
    return {'slp1_queried': slp1, 'found': False}


def close_connections():
    """Close every cached sqlite3 connection opened by dictionary_lookup()
    and clear the cache. dictionary_lookup's mutable-default cache lives
    for the whole process and previously had no way to release its
    connection(s) -- fine for a one-shot CLI run, but a long-lived caller
    (a REPL, a server, a test suite that rebuilds the dictionary between
    runs) had no way to force a reconnect or free the file handle."""
    conn_cache = dictionary_lookup.__defaults__[1]  # the _conn_cache default
    for conn in conn_cache.values():
        conn.close()
    conn_cache.clear()


def validate_against_dictionary(candidates, db_path=None):
    """Phase 1c of the roadmap: prune candidates whose LEFT piece doesn't
    resolve to a real dictionary stem. This is what turns a phonologically
    plausible guess into a trustworthy split.

    FIXED (see changelog): a left piece can still carry an EARLIER,
    already-adjacent word attached via a plain space -- no sandhi
    trigger ever isolated it, because there wasn't any (विष्णुना sits
    directly ahead of सदृशः in "विष्णुना सदृशः" with nothing to peel
    between them). Checking the WHOLE string as one dictionary entry
    always failed in that case, even though the piece's own newly-
    relevant word (सदृशः) is perfectly real -- starving every candidate
    at that boundary of validation credit it deserved, and letting a
    weaker, unrelated candidate win the ranking by default purely
    because ITS left happened to be a single token. Now also checks the
    LAST whitespace-delimited token of a multi-word left piece, and
    counts either check succeeding as validated."""
    validated = []
    for c in candidates:
        # Enforce any deferred precondition a generator declared rather than
        # testing itself (see candidates_elided_visarga_boundary): the
        # restoration is only trustworthy when the BARE form does NOT already
        # validate on its own. A candidate failing this is DROPPED, exactly
        # as it was never generated before that check moved here.
        bare = c.get('requires_bare_form_absent')
        if bare and dictionary_lookup(bare, db_path=db_path)['found']:
            continue
        left_result = dictionary_lookup(c['left'], db_path=db_path)
        found = left_result['found']
        stripped_left = c['left'].strip()
        if not found and ' ' in stripped_left:
            last_token = stripped_left.rsplit(' ', 1)[-1]
            if last_token:
                last_token_result = dictionary_lookup(last_token, db_path=db_path)
                found = last_token_result['found']
        c = dict(c)
        c['left_dictionary_check'] = left_result
        c['validated'] = found
        validated.append(c)
    return validated


def split_word_recursive(word, max_depth=6, max_total_peels=40, _budget=None):
    """Recursively decompose a word with MULTIPLE stacked sandhi
    boundaries (e.g. paaNDavaashcaiva = paaNDavaaH + ca + eva, where
    visarga-3 and svara-3 both fire on the same word at adjacent/
    overlapping positions).

    Mechanism (this is the direct answer to 'does it read right to
    left'): generate_candidates() itself is still direction-agnostic --
    every rule scans the whole string independently, same as always.
    What THIS function adds is the peeling strategy on top: at each
    round it looks at every candidate produced for the current
    'remaining' string and picks the one with the RIGHTMOST split point
    (i.e. the shortest right piece), ties broken by whichever candidate
    has both pieces dictionary-confirmed. It peels that piece off, then
    recurses on what's left. That is effectively a right-to-left,
    outermost-boundary-first peel -- built out of repeated single-rule
    passes, not a single combined pattern -- which is what correctly
    separates a word like paaNDavaashcaiva into THREE pieces instead of
    the two-piece answer split_word() alone would stop at.

    max_total_peels: a SHARED work budget (see _budget below), consumed
    by every peeling round this call makes AND by every nested call this
    call's right-piece expansion spawns. Bounds total engine work across
    the whole recursive tree from one top-level call, not per-call.

    FIXED (see changelog): this used to take two INDEPENDENT limits --
    max_depth (rounds within one call) and a local MAX_EXPANSION_DEPTH=8
    (nesting depth across calls, hard-coded, undocumented at the call
    site). Two problems: the two numbers interacted non-obviously (a
    docstring on one didn't mention the other), and neither bounded
    WIDTH -- a phrase with many sibling right pieces, each independently
    running up to max_depth rounds of its own, could still do unbounded
    total work despite both limits being respected individually. A single
    counter, threaded by reference through every call this invocation
    makes (both main-loop rounds and expansion recursion), bounds total
    work regardless of whether it is spent going deep or wide -- which is
    also what actually protects the call stack, since a worst-case chain
    of one-nested-call-per-round (the दर्शयामास चात्मानम् case that
    originally motivated MAX_EXPANSION_DEPTH) now exhausts the SAME
    budget the wide case would, at the same total-work bound.

    Returns {'pieces': [...], 'steps': [...]}. 'steps' is in the order
    the boundaries were resolved, LEFT to RIGHT for readability (i.e.
    reversed from the actual right-to-left peel order used internally).
    """
    if _budget is None:
        # Top-level call: create the shared budget once. Every call this
        # invocation goes on to make -- this call's own peeling rounds
        # below, and any right-piece sub-expansion -- draws from and
        # mutates this SAME list, so the cap is on total work across the
        # whole recursive tree, not per call. (A one-element list, not a
        # plain int, because ints are immutable in Python -- passing the
        # list by reference is what lets nested calls decrement the same
        # counter the caller sees.)
        _budget = [max_total_peels]

    # Normalize here too, not just inside generate_candidates: the
    # whole-word dictionary guard immediately below runs BEFORE
    # generate_candidates is ever called, so an unnormalized word (stray
    # daṇḍa, ZWJ, non-NFC input) could fail that lookup for a reason that
    # has nothing to do with sandhi. Idempotent on recursive calls, since
    # `core` here is always sliced from an already-normalized string.
    word = normalize_input(word)

    # Small closed-class list of common indeclinables/particles that very
    # commonly sit at a sandhi boundary (ca, vaa, tu, hi, eva, ...). Used
    # only as a GATE for continuing to recurse past the first boundary --
    # see the note below. Not exhaustive; this is a deliberately narrow,
    # conservative list, not an attempt at general Sanskrit segmentation.
    KNOWN_PARTICLES = {
        'च', 'वा', 'तु', 'हि', 'एव', 'ऐव', 'न', 'अपि', 'इति', 'तथा',
        'यथा', 'वै', 'स्म', 'ननु', 'चेत्', 'यदि', 'किल', 'उत', 'सह',
        'विना', 'अथ', 'तत्', 'नु', 'ह',
    }

    remaining = word
    steps = []

    # Guard against splitting a word that never had a sandhi boundary in
    # the first place: if the WHOLE input already resolves as its own
    # dictionary headword (raamaH, muniH, ...), trust that over any
    # pattern trigger a rule happens to find inside it, and don't split
    # at all. Without this, a plain word can get spuriously carved up
    # (e.g. raamaH -> ra + amaH) purely because both fragments happen to
    # separately exist as unrelated dictionary entries.
    if dictionary_lookup(word)['found']:
        return {'pieces': [word], 'steps': []}

    # Tier-4: same guard, extended to an ordinary INFLECTED word (a real
    # citation stem plus a common declensional/conjugational ending) --
    # see _stem_after_common_inflection's own docstring and this file's
    # Tier-4 changelog entry. The dictionary only indexes citation forms,
    # so काले/मयम्/करोति never matched the exact-headword guard above and
    # were wrongly carved up despite having no real internal sandhi at all.
    #
    # Tier-5 (see this file's Tier-5 changelog entry): re-ENABLED at the
    # top-level call, reversing Tier-4's restriction. Tier-4 restricted
    # this to non-top-level calls specifically because it broke वाङ्मयम्
    # (वाक्+मयम्, the vyan-5 --test case) -- वाङ्मय, the stem this guard
    # finds, is itself a real, independently-attested headword. Running
    # this tool on real verse text (not just the hand-built regression
    # corpus) surfaced the actual shape of that trade-off: dozens of ordinary,
    # completely unrelated words (लोके, नरम्, मुनिपुङ्गवम्, महर्षे,
    # वीर्यवान्, आत्मवान्, ...) were being wrongly carved up at the TOP
    # level for the exact same underlying reason -- and वाङ्मयम् itself
    # turns out not to be a clean counterexample: वाङ्मय IS a genuine,
    # independently attested Sanskrit word ("consisting of speech" /
    # "literature"), so वाङ्मयम् is legitimately ambiguous between "the
    # compound वाक्+मय, freshly sandhi'd" and "the lexicalized word वाङ्मय
    # in its neuter citation form" -- not a coincidental false match this
    # guard should have been shielded from, but a genuine case of the same
    # ambiguity this file already declines to force-resolve elsewhere (see
    # _rule_priority_key's own note on स्वागतम्/सूर्योदयः). Given that, and
    # given how many genuine over-splits this guard closes at the scale of
    # real running text, restricting it to non-top-level calls traded a
    # large, common failure mode for protection against one genuinely
    # ambiguous word -- the wrong trade for a tool meant to run on real
    # text. वाङ्मयम् fed alone will now report as a single, already-
    # complete word; fed as part of the fuller phrase it appears in
    # (सः वाङ्मयम् अधीते, etc.) the surrounding context is exactly the
    # kind of signal this module doesn't have and was never going to
    # resolve locally either way.
    if _stem_after_common_inflection(word):
        return {'pieces': [word], 'steps': []}

    for i in range(max_depth):
        # NEW: consume one unit of the shared work budget per round of
        # this loop, not just inside right-piece expansion -- see the
        # docstring's note on why max_depth and MAX_EXPANSION_DEPTH were
        # merged into a single total-work counter. Checked before doing
        # any work this round, so an exhausted budget stops immediately
        # rather than after one more (possibly expensive) round.
        if _budget[0] <= 0:
            break
        _budget[0] -= 1

        # FIXED (see changelog): the whole-word guard above only ever ran
        # ONCE, on the ORIGINAL input, before this loop started -- it was
        # never re-checked on `remaining` at the top of each LATER round.
        # So once a correct peel left `remaining` already a complete,
        # valid citation-form word (गुरुः after peeling भाति off
        # गुरुर्भाति; नरः after peeling च off नरश्च; भानु after peeling
        # उदयः off भानूदयः), the loop pressed on anyway and tried to
        # carve that ALREADY-FINISHED word up further, purely because
        # some OTHER rule's trigger pattern happened to also match inside
        # it (गुरुः -> गुः+उः; नरः -> नः+अः; भानु -> भ+अनु). Against a
        # small dictionary these spurious sub-splits rarely validated and
        # lost the ranking; against a comprehensive real dictionary they
        # validate constantly and win. Re-running the same guard here,
        # every round, stops the loop the moment `remaining` is itself
        # already a real word -- nothing is left to split, no matter what
        # a generator's trigger happens to notice inside it.
        if i > 0 and (dictionary_lookup(remaining)['found'] or _stem_after_common_inflection(remaining)):
            break

        cands = [c for c in generate_candidates(remaining) if c['right']]
        # FIXED (see changelog): drop single-character right pieces
        # before ranking -- EXCEPT single-character particles (च, न, ह
        # are all one codepoint and are exactly the kind of boundary this
        # file is built to find; excluding them outright broke कश्च ->
        # कः+च itself, so KNOWN_PARTICLES is explicitly exempted below).
        # A one-codepoint "word" that ISN'T a recognized particle
        # (नमस्ते's spurious svara-2 candidate proposing right='इ') is
        # essentially never a genuine pada boundary in running Sanskrit
        # text, but it sails to the front of the ranking purely by being
        # the shortest possible right piece -- shorter than even a real
        # particle -- the moment it validates against ANYTHING in the
        # dictionary.
        cands = [c for c in cands if len(c['right']) >= 2 or c['right'] in KNOWN_PARTICLES]
        if not cands:
            break
        validated = validate_against_dictionary(cands)
        for c in validated:
            # FIXED (see changelog): mirrors the left-piece fix in
            # validate_against_dictionary. A right piece routinely
            # carries a leading space from the original phrase (' नारदः'
            # peeled off वाल्मीकेर् नारदः) -- checking it unstripped
            # against the dictionary always failed even though नारदः
            # itself is perfectly real, starving the CORRECT candidate
            # of validation credit and letting a spurious same-or-
            # weaker-category competitor win on the length tiebreak
            # instead. Also falls back to the FIRST whitespace token for
            # the (rarer) case of a multi-word right piece where only
            # the newly-relevant leading word should count.
            right_stripped = c['right'].strip()
            right_result = dictionary_lookup(right_stripped) if right_stripped else {'found': False}
            found = right_result.get('found', False)
            if not found and ' ' in right_stripped:
                first_token = right_stripped.split(' ', 1)[0]
                if first_token:
                    found = dictionary_lookup(first_token).get('found', False)
            c['right_dictionary_check'] = dict(right_result)
            c['right_dictionary_check']['found'] = found

        def category(c):
            # -1 = an avagraha (ऽ) marks this boundary. Trust this
            #      unconditionally, above every other signal: unlike
            #      every other trigger in this file, avagraha has NO
            #      other use in running Sanskrit text (see svara-6's own
            #      docstring) -- it is not a coincidental pattern match,
            #      it is the text explicitly marking this exact boundary.
            #      Without this tier, a noisy-but-dictionary-confirmed
            #      guess from an unrelated rule (visarga-5 misreading
            #      हरे's own ordinary internal र् as if visarga-derived)
            #      could out-rank the unambiguous avagraha split
            #      (हरेऽव -> हरे+अव) on category/length tiebreaks alone.
            #  0 = visarga-ro-ri, both pieces independently confirmed.
            #      REVISED (see changelog): this used to share tier -1 with
            #      avagraha. roH ri's trigger (a long ई/ऊ immediately
            #      followed by literal र्) is specific and, combined with
            #      full dictionary confirmation on both sides, is strong
            #      evidence -- but it is still a PHONOLOGICAL pattern that
            #      could in principle coincide by chance, unlike avagraha,
            #      which is a written marker with no other use at all.
            #      Giving it its own tier keeps it above every generic
            #      both-confirmed candidate (which is what it needed
            #      promotion for in the first place -- नीरोगः's correct
            #      रो+गः would otherwise lose the shortest-right tiebreak
            #      to visarga-4's coincidentally-real short match) without
            #      overstating its evidence to the level of an explicit
            #      textual marker.
            #  1 = right piece IS a recognized closed-class particle AND
            #      validated -- our strongest generic signal, since
            #      particles are exactly what tends to sit at a real word
            #      boundary.
            #  2 = both left and right independently dictionary-confirmed
            #  3 = right piece is a known particle but left doesn't
            #      independently validate (keeps multi-step peeling
            #      working -- see changelog -- without letting a
            #      coincidental particle match beat a fully-confirmed
            #      candidate that doesn't happen to end in a particle)
            #  4 = only the LEFT (the stem/head) is confirmed
            #  5 = only the RIGHT is confirmed
            #  6 = neither confirmed
            # NOTE on why LEFT-only outranks RIGHT-only (4 < 5): a short
            # residual fragment coincidentally matching some unrelated
            # dictionary headword (a verb root, a rare particle) is
            # common and usually spurious; a real stem resolving on the
            # LEFT is comparatively a stronger signal that we've found
            # an actual word-initial boundary. This ordering was tuned
            # empirically against the test words below and is a
            # judgement call, not a linguistic law -- see the test
            # results for where it still gets things wrong.
            if c['rule_id'].startswith('svara-6'):
                base = -1
            elif c['rule_id'] == 'visarga-ro-ri' and c['validated'] and c['right_dictionary_check']['found']:
                base = 0
            elif c['right'] in KNOWN_PARTICLES and c['validated']:
                base = 1
            elif c['validated'] and c['right_dictionary_check']['found']:
                base = 2
            elif c['right'] in KNOWN_PARTICLES:
                base = 3
            elif c['validated']:
                base = 4
            elif c['right_dictionary_check']['found']:
                base = 5
            else:
                base = 6
            # NEW: apply the pragrhya guard the candidate was already
            # carrying (see generate_candidates / is_pragrhya_no_sandhi_context).
            # It was computed and attached to every svara candidate but
            # nothing ever READ it, so a candidate svara-9 itself flags as
            # "sandhi should NOT occur here" ranked exactly like any other
            # unflagged candidate in its tier. A flat +100 pushes it below
            # every unflagged candidate at every base tier while preserving
            # its relative order against OTHER flagged candidates, rather
            # than discarding it outright -- the guard is deliberately
            # partial (closed word-list only, see its own docstring), so a
            # flagged candidate should lose to a clean alternative, not
            # vanish if it turns out to be the only option left.
            if c.get('pragrhya_flag'):
                return base + 100
            # Tier-4: symmetric counterpart to the single-character RIGHT
            # piece filter applied above (before ranking even starts) --
            # this file already treats a one-codepoint right piece as
            # essentially never a genuine boundary unless it's a known
            # particle, but had no equivalent skepticism on the LEFT side.
            # काले -> क+अले (क is a real but unrelated headword, the
            # interrogative stem) is exactly that same failure shape
            # mirrored onto the left piece. Demoted rather than filtered
            # out entirely (+50, smaller than the pragrhya penalty) so a
            # single-character left still wins as a last resort when
            # nothing better is available, the same tolerance the pragrhya
            # guard already extends.
            if len(c['left']) < 2:
                return base + 50
            return base

        # Tier-4: _rule_priority_key inserted between the validated-bit and
        # length tiebreaks -- see its own docstring (paribhāṣā-12,
        # Aṣṭādhyāyī 1.4.2). Only ever distinguishes candidates already
        # tied on (category, validated-bit); it does not touch the primary
        # evidentiary ranking above it.
        validated.sort(key=lambda c: (category(c), 0 if c['validated'] else 1,
                                       _rule_priority_key(c['rule_id']), len(c['right'])))
        best = validated[0]

        # FIXED (see changelog): surface genuine ties instead of silently
        # resolving them. Some rules -- svara-1 (सवर्णदीर्घ) above all --
        # inherently propose SEVERAL equally-natural, equally-real
        # reconstructions for the very same boundary (हिम+अलयः vs
        # हिम+आलयः: "अलय" and "आलय" are BOTH genuine Sanskrit words, so
        # both validate, and both produce a same-length right piece).
        # Unlike every other rule in this file, none of these candidates
        # is a more "invented" spelling than another for dictionary
        # validation to filter out -- this is a real phonological
        # ambiguity that local pattern matching and dictionary lookup
        # alone cannot resolve; it needs sentence-level grammatical or
        # semantic context this module doesn't have. Rather than let the
        # tiebreak's insertion-order artifact keep deciding silently (and
        # often wrongly), record every candidate tied with `best` on
        # (category, validated-bit, len(right)) as an alternative, so a
        # caller can tell "confidently resolved" apart from "picked one
        # of several equally plausible answers".
        # FIXED (see changelog): only surface a tie as "genuinely
        # ambiguous" when `best` is FULLY confirmed (category <= 2 --
        # avagraha-certain, roH-ri-confirmed, or both-sides-dictionary-
        # confirmed). Below that tier, the tie_key (category, validated-bit,
        # length) doesn't check whether the RIGHT piece independently
        # validates at all -- so for गिरीन्द्रः it was flagging गिरि+ईन्द्रः
        # as an "equally valid" alternative to गिरि+इन्द्रः purely because
        # NEITHER right piece was dictionary-confirmed and both happen to
        # be the same length. That's not ambiguity, it's noise: ईन्द्रः
        # was never a real competing hypothesis, it just shares a weak
        # category with the correct answer. Genuine, worth-reporting
        # ambiguity (हिम+अलयः vs हिम+आलयः) only happens when EVERY tied
        # candidate is independently, fully validated -- restricting to
        # category <= 2 captures exactly that and nothing weaker.
        # (Threshold moved from <=1 to <=2 when visarga-ro-ri got its own
        # tier between avagraha and particle-validated -- see category().)
        if category(best) <= 2:
            tie_key = (category(best), 0 if best['validated'] else 1, len(best['right']))
            tied = [c for c in validated
                    if (category(c), 0 if c['validated'] else 1, len(c['right'])) == tie_key
                    and (c['left'], c['right']) != (best['left'], best['right'])]
        else:
            tied = []

        if len(best['left']) >= len(remaining) or not best['left']:
            break  # no progress -- stop rather than loop

        if i > 0 and category(best) > 2:
            # We always trust the FIRST peel -- the original input was
            # handed to us specifically because it's a sandhi'd form.
            # Every peel AFTER that is progressively riskier: a LEFT-only
            # dictionary hit by itself is NOT enough evidence to justify
            # continuing (short fragments like paa or va coincidentally
            # match unrelated real headwords very easily -- see
            # paaNDavaaH wrongly getting peeled into paam + Dvaa
            # otherwise). So past the first peel, only continue when the
            # boundary is either a recognized particle or BOTH sides
            # independently confirm (or the higher-trust avagraha/roH-ri
            # tiers); anything weaker, stop.
            break

        steps.append({
            'input': remaining, 'rule_id': best['rule_id'],
            'left': best['left'], 'right': best['right'],
            'left_confirmed': best['validated'],
            'right_confirmed': best['right_dictionary_check']['found'],
            'note': best.get('note', ''),
            'ambiguous_alternatives': [(c['left'], c['right'], c['rule_id']) for c in tied] or None,
        })
        remaining = best['left']

    pieces = [remaining] + [s['right'] for s in reversed(steps)]

    # FIXED (see changelog): a peeled-off RIGHT piece can itself contain
    # a further sandhi boundary the loop above never revisits -- it only
    # ever recurses on the LEFT remainder. कश् चैकप्रियदर्शनः needs an
    # outer visarga-3 peel (कः + चैकप्रियदर्शनः) AND its right piece,
    # चैकप्रियदर्शनः, needs its OWN further vrddhi peel (च +
    # एकप्रियदर्शनः) to reach the full 3-piece answer -- previously
    # this stopped at 2 pieces. Each right piece that itself further
    # decomposes is expanded here; any leading/trailing whitespace the
    # piece carried (a multi-word right piece like ' गच्छति') is kept on
    # only the first/last sub-piece respectively, so it isn't duplicated
    # or lost. Recursion is on a strictly shorter string each time (a
    # piece of the current word), so this always terminates.
    expanded_pieces = [pieces[0]]
    expanded_steps = []
    right_pieces_in_order = [s['right'] for s in reversed(steps)]  # matches pieces[1:]
    # REMOVED: the old local MAX_EXPANSION_DEPTH=8 hard cap on nesting
    # depth. Expansion recursion now draws from the SAME shared _budget
    # every main-loop round above also consumes -- see split_word_recursive's
    # docstring for why one counter replaces the two independent limits.
    for idx, piece in enumerate(right_pieces_in_order):
        core = piece.strip()
        leading_ws = piece[:len(piece) - len(piece.lstrip())]
        trailing_ws = piece[len(piece.rstrip()):] if piece.strip() else ''
        if core and len(core) >= 2 and _budget[0] > 0:
            sub = split_word_recursive(core, max_depth=max_depth, max_total_peels=max_total_peels,
                                        _budget=_budget)
        else:
            sub = None
        # Confidence gate: only trust this newly-discovered sub-split if
        # EVERY step in it is strongly confirmed (left independently
        # validated, and right either independently validated or a
        # known particle). Right pieces were never examined at all
        # before this fix, so there's no existing test relying on a
        # weak/unconfirmed guess here the way split_word_recursive's
        # main loop sometimes accepts one as a last resort on the very
        # first peel of the ORIGINAL input. Without this gate, a
        # same-category-nothing-else-available acceptance (both sides
        # unconfirmed) could invent a spurious boundary inside a piece
        # that was already correct as a single unit -- e.g. अग्निसदृशः,
        # which has no real internal sandhi boundary at all, was being
        # carved into अग्निसत्+ऋशः on the strength of a single fully
        # unconfirmed vyan-3 candidate that happened to be the only one
        # generated.
        sub_confident = bool(sub) and len(sub['pieces']) > 1 and all(
            st['left_confirmed'] and (st['right_confirmed'] or st['right'].strip() in KNOWN_PARTICLES)
            for st in sub['steps']
        )
        if sub_confident:
            sub_pieces = list(sub['pieces'])
            sub_pieces[0] = leading_ws + sub_pieces[0]
            sub_pieces[-1] = sub_pieces[-1] + trailing_ws
            expanded_pieces.extend(sub_pieces)
            expanded_steps.extend(sub['steps'])
        else:
            expanded_pieces.append(piece)

    all_steps = list(reversed(steps)) + expanded_steps

    # FIXED (see changelog): a final tokenization pass. After all
    # sandhi-boundary peeling is exhausted (both the left-recursing main
    # loop and the right-piece expansion above), a piece can still
    # contain an internal space representing two words that were simply
    # ADJACENT in the original phrase with no sandhi/fusion between them
    # at all -- धर्म इवापरः has no sandhi between धर्म and इव at all
    # (only between इव and अपरः), so "remaining" after resolving that
    # one real boundary was the atomic-looking but still-two-word string
    # "धर्म इव". Devanagari words never contain an internal space, so
    # any space left in a piece at this point is already a genuine word
    # boundary -- sandhi-derived or not -- and splitting on it is always
    # correct. This also subsumes the earlier "right piece keeps its
    # leading space" behaviour (' गच्छति') as a special case: it's now
    # just a single-element split, so the output no longer carries a
    # leading space at all.
    final_pieces = []
    for piece in expanded_pieces:
        final_pieces.extend(piece.split())
    return {'pieces': final_pieces, 'steps': all_steps}


def print_recursive_result(word, max_depth=6):
    """CLI-facing pretty-printer for split_word_recursive()."""
    result = split_word_recursive(word, max_depth=max_depth)
    print(f"\nInput: {word}")
    if not result['steps']:
        print("No sandhi boundaries found -- treated as a single unit.")
        print(f"Result: {word}")
        return result
    print(f"\nBoundaries resolved (right-to-left peel, {len(result['steps'])} step(s)):")
    for i, s in enumerate(result['steps'], 1):
        lc = 'dict-confirmed' if s['left_confirmed'] else 'not in dict'
        rc = 'dict-confirmed' if s['right_confirmed'] else 'not in dict'
        print(f"  {i}. {s['input']}  ->  {s['left']} ({lc})  +  {s['right']} ({rc})   [{s['rule_id']}]")
    print(f"\nFinal split ({len(result['pieces'])} pieces): "
          + "  +  ".join(result['pieces']))
    return result

def split_word(word, show_all=False):
    """CLI entry point: given a single Devanagari word, generate all
    candidate splits, validate each against the dictionary, and print a
    readable report. This is the actual 'give me a word, get a split'
    interface -- generate_candidates()/validate_against_dictionary() are
    the underlying functions; this just formats them for a human.

    NOTE ON WHAT THIS DOES AND DOESN'T DO:
    - Only finds the FIRST boundary (the split point produced by whichever
      sandhi rule applies). If the RIGHT piece is itself a further
      compound (a 3+-member samasa), it is NOT recursively split --
      that's the still-open Phase-1d item from the roadmap.
    - Dictionary validation checks the LEFT piece only, and against a
      coarse ending-stripped stem table (see build_apte_dictionary.py's
      candidate_stems()) -- short (1-2 character) left pieces can produce
      false-positive matches, since many single-syllable particles exist.
    - "validated: True" means the left piece resolved to SOME dictionary
      entry, not that this is definitively the correct split among several
      candidates -- when multiple candidates validate, use judgement
      (or cross-check against samasah_rulebook.json for which compound
      type would make semantic sense) to pick the real one."""
    word = normalize_input(word)  # so the echoed "Input:" matches what was actually split
    print(f"\nInput: {word}\n")
    cands = generate_candidates(word)
    if not cands:
        # FIXED: was hard-coded "28 implemented rules", a number that
        # silently drifts from reality every time a generator is added,
        # removed, or superseded (candidates_svara_unified alone replaced
        # seven entries with one). Derived from ALL_GENERATORS instead.
        print(f"No sandhi split candidates found by any of the {len(ALL_GENERATORS)} implemented rules.")
        print("(This could mean: the word has no internal sandhi boundary detectable")
        print(" by pattern-matching, OR it falls into a documented KNOWN LIMITATION --")
        print(" see candidates_svara4/svara5 docstrings for the 'invisible-अ' case.)")
        return None

    validated = validate_against_dictionary(cands)
    confirmed = [c for c in validated if c['validated']]
    unconfirmed = [c for c in validated if not c['validated']]

    if confirmed:
        print(f"CONFIRMED splits ({len(confirmed)} -- left piece found in dictionary):")
        for c in confirmed:
            cite = c.get('citation', {})
            sutra = cite.get('ashtadhyayi_ref', '?')
            print(f"  {c['left']}  +  {c['right']}   [{c['rule_id']}, Ashtadhyayi {sutra}]")
            gloss = c['left_dictionary_check'].get('gloss', '')
            if gloss and gloss != 'see cross-ref':
                print(f"      {c['left']} = {gloss[:80]}")
    else:
        print("No candidates confirmed against the dictionary.")

    if unconfirmed and (show_all or not confirmed):
        print(f"\nOther candidates NOT confirmed ({len(unconfirmed)}):")
        for c in unconfirmed[:10]:
            print(f"  {c['left']}  +  {c['right']}   [{c['rule_id']}]  (left piece not found in dictionary)")
        if len(unconfirmed) > 10:
            print(f"  ... and {len(unconfirmed)-10} more (pass show_all=True or check manually)")
    # NEW: return the confirmed list so a caller that already ran split_word
    # (the file-mode loop below, via _print_validation) doesn't have to
    # re-run generate_candidates()+validate_against_dictionary() a second
    # time on the same word just to grade it. See _compute_actual_split.
    return confirmed


def print_usage():
    print("Usage:")
    print("  python sandhi_splitter_v2.py <filename> [--all]")
    print("  python sandhi_splitter_v2.py <filename> --recursive")
    print("  python sandhi_splitter_v2.py --test")
    print()
    print("  <filename>          Path to a text file. Each non-empty line")
    print("                      holds one sandhi word to split, in one of:")
    print("                        कश्च")
    print("                        कश्च||कः+च")
    print("                        कश्च||कः+च||विसर्ग-सन्धि (विसर्ग → श्)")
    print("                      Only the FIRST field (before the first")
    print("                      '||') is read as the input word -- the")
    print("                      second field (if present) is the expected")
    print("                      split, used only for PASS/FAIL grading")
    print("                      after the engine runs. The optional third")
    print("                      field is a sandhi name/category label (as")
    print("                      used in corpus files like word||vigraha||")
    print("                      sandhi-name) -- printed for reference and,")
    print("                      with --skip-vyanjana, used to filter lines")
    print("                      out. Every word is still run through the")
    print("                      real generate_candidates()/split_word()")
    print("                      engine from scratch; nothing after the")
    print("                      first '||' is ever used to produce or")
    print("                      shortcut the printed result.")
    print("  --all               Also show unconfirmed candidates (not just")
    print("                      dictionary-confirmed splits)")
    print("  --recursive         Peel off MULTIPLE stacked sandhi boundaries")
    print("                      (e.g. paaNDavaashcaiva -> 3 pieces) instead")
    print("                      of stopping at the first split")
    print("  --skip-vyanjana     Skip lines whose third field names ONLY a")
    print("                      vyanjana-family category (व्यञ्जन-सन्धि,")
    print("                      जश्त्व-सन्धि, अनुस्वार-सन्धि, म्-सन्धि) --")
    print("                      lines with no third field, or a mixed")
    print("                      category (vyanjana alongside a svara/")
    print("                      visarga step), are always kept. Has no")
    print("                      effect on lines with no third field at all.")
    print("  --test              Run the internal regression/self-test suite")
    print("  -h, --help          Show this message")
    print()
    print("Example file (words.txt):")
    print("  कश्च||कः+च")
    print("  पाण्डवाश्चैव||पाण्डवाः+च+एव")
    print()
    print("If a line has a '||<expected split>' part, that word's PASS/FAIL")
    print("is reported by comparing it against the engine's OWN split -- the")
    print("expected text is only ever used for that after-the-fact check, it")
    print("is never fed into generate_candidates()/split_word() itself.")
    print()
    print("Example:")
    print("  python sandhi_splitter_v2.py words.txt --all")
    print("  python sandhi_splitter_v2.py words.txt --recursive")
    print("  python sandhi_splitter_v2.py corpus.txt --recursive --skip-vyanjana")


def _classify_vyanjana(name):
    """Classify a sandhi-name/category label (this corpus format's
    optional third '||'-delimited field) as vyanjana-only, mixed
    (vyanjana alongside a svara/visarga step), or clean (no vyanjana
    step at all). Returns 'vyanjana', 'mixed', or 'clean'.

    The label vocabulary is taken directly from how this rulebook's own
    rule_id families map to category names in Sanskrit corpora: जश्त्व,
    अनुस्वार, and the generic व्यञ्जन label all correspond to vyan-*
    rules here, even though only व्यञ्जन-सन्धि literally contains the
    word "vyanjana"."""
    if not name:
        return 'clean'
    VYANJANA_MARKERS = ['व्यञ्जन-सन्धि', 'जश्त्व-सन्धि', 'अनुस्वार-सन्धि', 'म्-सन्धि']
    NON_VYANJANA_MARKERS = ['विसर्ग-सन्धि', 'वृद्धि-सन्धि', 'गुण-सन्धि', 'दीर्घ-सन्धि',
                            'यण्-सन्धि', 'स्वर-सन्धि', 'वकारागम-सन्धि']
    has_vyan = any(m in name for m in VYANJANA_MARKERS)
    has_other = any(m in name for m in NON_VYANJANA_MARKERS)
    if not has_vyan:
        return 'clean'
    return 'mixed' if has_other else 'vyanjana'


def _read_words_from_file(filename, skip_vyanjana=False):
    """Read a word list from `filename`.

    Format: one entry per (non-blank) line, one of:
      <sandhi_word>
      <sandhi_word>||<expected_split>
      <sandhi_word>||<expected_split>||<sandhi_name_or_category>

    EXTENDED (see changelog): originally only the 2-field form was
    handled -- `split('||', 1)` put everything from the first '||'
    onward, INCLUDING a genuine third field, into `expected`, so a real
    corpus line like
      कश्च || कः + च || विसर्ग-सन्धि (विसर्ग → श्)
    parsed as expected = " कः + च || विसर्ग-सन्धि (विसर्ग → श्)" -- the
    sandhi-name text became a bogus extra "piece" once split on '+',
    breaking every comparison. This is a common real-corpus shape (word
    || vigraha || sandhi-name), so it's now a first-class third field:
    split on '||' with maxsplit=2, so a name containing its own '+' or
    '||'-unlikely punctuation is never mis-parsed into `expected`.

    The word to actually split is still only ever the first field --
    nothing from the second or third field is passed to
    generate_candidates()/split_word()/split_word_recursive(), which
    only ever see the bare word and derive every candidate themselves,
    exactly as v1 did for a single CLI word.

    If skip_vyanjana is True and a third field is present, lines whose
    category is vyanjana-only (per _classify_vyanjana) are silently
    skipped -- lines with NO third field are always kept (there's no
    category to judge), and 'mixed' lines (a vyanjana step alongside a
    svara/visarga one) are always kept too, since only PART of their
    resolution is out of scope.

    Returns a list of (word, expected_or_None, name_or_None) tuples.
    """
    with open(filename, encoding='utf-8') as f:
        raw_lines = f.readlines()
    entries = []
    n_skipped_vyanjana = 0
    for lineno, line in enumerate(raw_lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        fields = [p.strip() for p in stripped.split('||', 2)]
        # FIXED: normalize the word here too, not just inside
        # generate_candidates/split_word_recursive -- this is the real
        # corpus-intake path (file mode), so a daṇḍa, verse-number digit,
        # or stray ZWJ/ZWNJ riding along in a corpus line is stripped
        # before the word is ever compared, split, or printed. expected/
        # name are left as the corpus wrote them (they're grading/display
        # text, not something a generator scans).
        word = normalize_input(fields[0])
        expected = fields[1] if len(fields) > 1 and fields[1] else None
        name = fields[2] if len(fields) > 2 and fields[2] else None
        if not word:
            print(f"  (skipping line {lineno}: empty word before '||')")
            continue
        if skip_vyanjana and name and _classify_vyanjana(name) == 'vyanjana':
            n_skipped_vyanjana += 1
            continue
        entries.append((word, expected, name))
    if skip_vyanjana and n_skipped_vyanjana:
        print(f"  (skipped {n_skipped_vyanjana} vyanjana-only line(s) per --skip-vyanjana)")
    return entries


def _compute_actual_split(word, recursive, precomputed=None):
    """Run the real engine on `word` and return its own top split as a
    list of pieces (e.g. ['कः', 'च'], or ['रामः','च','एव'] for a
    recursive multi-boundary peel), or None if the engine found no
    dictionary-confirmed split at all.

    This is the SAME underlying engine call the display functions below
    already make (split_word_recursive() for --recursive; generate_
    candidates()+validate_against_dictionary() -- the exact pair
    split_word() itself calls -- otherwise); it is only wrapped here so
    the result can also be compared to an expected answer instead of
    just printed. Nothing about the split logic itself changes.

    FIXED (see changelog): file mode used to run the FULL engine on every
    word twice -- once via print_recursive_result()/split_word() to
    display it, and again here via a fresh split_word_recursive()/
    generate_candidates() call just to grade it, doubling the cost of
    every corpus run for no behavioural difference (both calls are
    deterministic on the same input). `precomputed` lets a caller that
    already ran the display function pass its result straight through:
    the dict split_word_recursive()/print_recursive_result() returns when
    recursive, or the `confirmed` list split_word() now returns otherwise.
    Passing nothing preserves the original recompute-from-scratch
    behaviour, so this stays a safe default for any other caller."""
    if recursive:
        result = precomputed if precomputed is not None else split_word_recursive(word)
        return result['pieces'] if result['steps'] else None
    else:
        if precomputed is not None:
            confirmed = precomputed
        else:
            cands = generate_candidates(word)
            validated = validate_against_dictionary(cands)
            confirmed = [c for c in validated if c['validated']]
        if not confirmed:
            return None
        top = confirmed[0]
        return [top['left'], top['right']]


def _print_validation(word, expected, recursive, precomputed=None):
    """Print a PASS/FAIL (or SKIPPED) line for `word` by comparing the
    engine's own split (via _compute_actual_split, i.e. the real
    generate_candidates/validate_against_dictionary/split_word_recursive
    pipeline -- not a re-parse of `expected`) against `expected`, the
    text found after the first '||' for this word. Returns 'pass',
    'fail', or 'skip' so the caller can keep a running tally.

    `precomputed` is forwarded to _compute_actual_split() -- see its
    docstring for why: avoids re-running the engine on a word the caller
    already ran once to display.

    FIXED (see changelog): comparison now strips each piece on BOTH
    sides before comparing. Multi-word input (रामो नाम, बालो गच्छति)
    correctly keeps the space the sandhi boundary sits next to in its
    right piece (' नाम', ' गच्छति') -- that space is genuine, faithfully
    reproducing where the original phrase's word boundary was. But an
    `expected` field written as "रामः + नाम" has that same space
    consumed by the ' + ' separator instead, so the comparison was
    failing on whitespace alone even when the split itself was entirely
    correct -- this was the single largest source of FAILs when this
    file mode was run against a real multi-word verse corpus (~27 of 79
    on the Valmiki Ramayana Bala Kanda Sarga 1 batch). The raw,
    unstripped form is still what gets displayed via `actual_str` above
    -- only the PASS/FAIL judgement itself is whitespace-insensitive."""
    actual_pieces = _compute_actual_split(word, recursive, precomputed=precomputed)
    actual_str = '+'.join(actual_pieces) if actual_pieces else '(no confirmed split found)'
    if expected is None:
        print(f"Validation: SKIPPED -- no expected answer after '||' to check against. "
              f"(engine's own split: {actual_str})")
        return 'skip'
    expected_pieces = [p.strip() for p in expected.split('+') if p.strip()]
    actual_pieces_stripped = [p.strip() for p in actual_pieces] if actual_pieces is not None else None
    if actual_pieces_stripped is not None and actual_pieces_stripped == expected_pieces:
        print(f"Validation: PASS -- matches expected {expected}")
        return 'pass'
    else:
        print(f"Validation: FAIL -- expected {expected}, engine produced {actual_str}")
        return 'fail'


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1 or sys.argv[1] in ('-h', '--help'):
        # No filename given -- show usage instead of silently running self-tests.
        print_usage()
        sys.exit(0)
    if sys.argv[1] == '--test':
        pass  # fall through to the self-test suite below
    else:
        # File mode: python sandhi_splitter_v2.py <filename> [--all] [--recursive] [--skip-vyanjana]
        filename = sys.argv[1]
        show_all = '--all' in sys.argv
        recursive = '--recursive' in sys.argv
        skip_vyanjana = '--skip-vyanjana' in sys.argv

        try:
            entries = _read_words_from_file(filename, skip_vyanjana=skip_vyanjana)
        except FileNotFoundError:
            print(f"Error: file not found: {filename}")
            sys.exit(1)
        except OSError as e:
            print(f"Error reading {filename}: {e}")
            sys.exit(1)

        if not entries:
            print(f"No sandhi words found in {filename}.")
            print("Expected one word per line, e.g. 'कश्च' or 'कश्च||कः+च'.")
            sys.exit(0)

        print(f"Loaded {len(entries)} word(s) from {filename}.")
        tally = {'pass': 0, 'fail': 0, 'skip': 0}
        for word, expected, name in entries:
            # Each word is independently run through the actual engine
            # (split_word / split_word_recursive -> generate_candidates ->
            # validate_against_dictionary), same as v1's single-word CLI --
            # just looped over the words pulled from the file above. The
            # display below is untouched from that engine's normal output;
            # only the following Validation line is new.
            #
            # FIXED (see changelog): the engine used to run TWICE per word
            # here -- once to display, once more inside _print_validation
            # to grade -- doubling every corpus run's cost. Both display
            # calls now return their result, which is threaded straight
            # into _print_validation instead of being thrown away.
            if recursive:
                engine_result = print_recursive_result(word)
            else:
                engine_result = split_word(word, show_all=show_all)
            if name:
                print(f"Category: {name}")
            outcome = _print_validation(word, expected, recursive, precomputed=engine_result)
            tally[outcome] += 1

        total = len(entries)
        print()
        print(f"Summary: {tally['pass']}/{total} PASS, {tally['fail']}/{total} FAIL, "
              f"{tally['skip']}/{total} SKIPPED (no expected answer given)")
        sys.exit(0)
    # visarga / vyanjana suite (from R_1,1.1 / R_1,1.2, already verse-verified)
    tests = [
        ("तपःस्वाध्यायनिरतम्", "तपः", "स्वाध्यायनिरतम्", "visarga-1"),
        ("वाल्मीकिर्मुनिपुङ्गवम्", "वाल्मीकिः", "मुनिपुङ्गवम्", "visarga-5"),
        ("कश्च", "कः", "च", "visarga-3"),
        ("धर्मज्ञश्च", "धर्मज्ञः", "च", "visarga-3"),
        ("वाग्विद्", "वाच्", "विद्", "vyan-3+coH-kuH"),
    ]
    # svara-sandhi suite -- oracle is the rulebook's own worked examples
    tests += [
        ("गिरीन्द्रः", "गिरि", "इन्द्रः", "svara-1"),
        ("गुरूपदेशः", "गुरु", "उपदेशः", "svara-1"),
        ("देवेन्द्रः", "देव", "इन्द्रः", "svara-2"),
        ("सूर्योदयः", "सूर्य", "उदयः", "svara-2"),
        ("गणेशः", "गण", "ईशः", "svara-2"),
        ("तवैव", "तव", "एव", "svara-3"),
        ("महौषधिः", "महा", "ओषधिः", "svara-3"),
        ("स्वागतम्", "सु", "आगतम्", "svara-4"),
        ("हरेऽत्र", "हरे", "अत्र", "svara-6"),
        ("गुरोऽत्र", "गुरो", "अत्र", "svara-6"),
        ("प्रेजते", "प्र", "एजते", "svara-7"),
        ("गवाम्", "गो", "", "svara-8"),
    ]
    # remaining visarga suite (visarga-2, added this session)
    tests += [
        ("रामश्शेते", "रामः", "शेते", "visarga-2"),
        ("हरिष्षष्ठः", "हरिः", "षष्ठः", "visarga-2"),
    ]
    # vyanjana-sandhi suite -- oracle is the rulebook's own worked examples
    tests += [
        ("सच्चित्", "सत्", "चित्", "vyan-1"),
        ("तज्जयति", "तत्", "जयति", "vyan-1"),
        ("तट्टीका", "तत्", "टीका", "vyan-2"),
        ("रामष्षष्ठः", "रामस्", "षष्ठः", "vyan-2"),
        ("मत्सन्धिः", "मद्", "सन्धिः", "vyan-4"),
        ("विपत्काले", "विपद्", "काले", "vyan-4"),
        ("वाङ्मयम्", "वाक्", "मयम्", "vyan-5"),
        ("गङ्गाञ्चलति", "गङ्गां", "चलति", "vyan-7"),
        ("आच्छादयति", "आ", "छादयति", "vyan-12"),
        ("तच्छेते", "तत्", "शेते", "vyan-9"),
        ("तल्लीनः", "तत्", "लीनः", "vyan-14"),
        ("वणिग्घसति", "वणिक्", "हसति", "vyan-8"),
        ("रामस्करोति", "रामः", "करोति", "vyan-10"),
    ]
    # vyan-6 tested separately since its right piece includes a leading
    # space (रामम्+वन्दे -> रामं वन्दे stays two words, unlike the
    # fused-compound cases above)
    print()
    print("vyan-6 (anusvara restoration):")
    r6 = generate_candidates("रामं वन्दे")
    r6_match = [c for c in r6 if c['rule_id']=='vyan-6' and c['left']=='रामम्' and c['right']==' वन्दे']
    print(f"  [{'PASS' if r6_match else 'FAIL'}] रामं वन्दे -> रामम् + ' वन्दे'")
    # FIXED: the suite used to print PASS/FAIL and then always exit 0, so a
    # total regression reported green to CI. Every sub-suite now feeds one
    # tally and the process exits non-zero on any failure -- which matters
    # here more than usual, since much of this file's design rests on
    # changes having been "verified against the regression suite".
    _failures = 0 if r6_match else 1

    # vyan-11 (natva) -- different function signature, tested separately
    print()
    print("vyan-11 (natva reconstruction helper):")
    natva_tests = [("राम", "अयणम्", "अयनम्"), ("पूर्", "अणम्", "अनम्")]
    np_ = 0
    for left, right, expected in natva_tests:
        r = restore_natva_in_right_piece(right, left)
        ok = r and r['restored_right'] == expected
        if ok: np_ += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] left={left}, right={right} -> {r['restored_right'] if r else None}")
    print(f"  {np_}/{len(natva_tests)} pass")
    _failures += len(natva_tests) - np_

    print()
    print("Main sandhi-splitting suite:")
    passed = 0
    for word, exp_left, exp_right, exp_rule in tests:
        cands = generate_candidates(word)
        matched = [c for c in cands if c['rule_id'] == exp_rule and c['left'] == exp_left and c['right'] == exp_right]
        status = "PASS" if matched else "FAIL"
        if matched: passed += 1
        print(f"[{status}] {word}  expected {exp_left}+{exp_right} via {exp_rule}")
        if not matched:
            print("   candidates found:", [(c['rule_id'], c['left'], c['right']) for c in cands])
    print(f"\n{passed}/{len(tests)} pass")
    _failures += len(tests) - passed

    # inter-word boundary elision (visarga-4b, visarga-6) -- different
    # function signature (two words, not one), tested separately
    print()
    print("Boundary-elision suite (visarga-4b / visarga-6):")
    boundary_tests = [
        ("धृतराष्ट्र", "उवाच", "visarga-4b", "धृतराष्ट्रः"),
        ("सञ्जय", "उवाच", "visarga-4b", "सञ्जयः"),
        ("अर्जुन", "उवाच", "visarga-4b", "अर्जुनः"),
        ("बाला", "हसन्ति", "visarga-6", "बालाः"),
        ("कन्या", "यान्ति", "visarga-6", "कन्याः"),
    ]
    bp = 0
    for prev, nxt, exp_rule, exp_restored in boundary_tests:
        r = restore_elided_visarga_at_word_boundary(prev, nxt)
        ok = (r and r['rule_id'] == exp_rule and r['restored'] == exp_restored)
        if ok: bp += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {prev} + {nxt} -> {r['restored'] if r else None}")
    print(f"  {bp}/{len(boundary_tests)} pass")
    _failures += len(boundary_tests) - bp

    # KNOWN LIMITATION -- these will produce few/no candidates and that is
    # EXPECTED. Devanagari writes no separate glyph for a retained-अ vowel
    # after यण्/ec sandhi, so यदि+अपि->यद्यपि is orthographically invisible.
    # See docstrings on candidates_svara4 / candidates_svara5.
    print()
    print("Known-limitation cases (expected to NOT be caught by local pattern matching):")
    for word in ["यद्यपि", "मध्वरिः", "नयनम्", "भवनम्", "नायकः", "पावकः"]:
        cands = generate_candidates(word)
        print(f"  {word}: {len(cands)} candidates generated (boundary is orthographically silent)")

    # NEW: lock in the unified-scan equivalence claim as an actual test
    # rather than a changelog assertion. candidates_svara1/2/3/4/5/6/
    # 9_m_junction are retained as a rollback reference; that reference is
    # only trustworthy while it still agrees with candidates_svara_unified,
    # and nothing enforced that. Compares the candidate SET (the real
    # invariant) -- emission order deliberately differs, which is precisely
    # why generate_candidates() now imposes a canonical order.
    print()
    print("Unified-scan equivalence (candidates_svara_unified vs the 7 originals):")
    _superseded = [candidates_svara1, candidates_svara2, candidates_svara3,
                   candidates_svara4, candidates_svara5, candidates_svara6,
                   candidates_svara9_m_junction]
    _eq_words = [w for w, _l, _r, _rule in tests] + [
        "महर्षिः", "रामोऽपि", "विवासयामास", "विष्णुना सदृशः", "तत्रैव",
        "नमस्ते", "भानूदयः", "पाण्डवाश्चैव", "धर्म इवापरः", "नीरोगः",
    ]
    def _key(c):
        return (c['rule_id'], c['left'], c['right'])
    _eq_fail = 0
    for _w in _eq_words:
        _u = sorted(_key(c) for c in candidates_svara_unified(_w))
        _o = sorted(_key(c) for g in _superseded for c in g(_w))
        if _u != _o:
            _eq_fail += 1
            print(f"  [FAIL] {_w}: unified-only={sorted(set(_u)-set(_o))[:3]} "
                  f"originals-only={sorted(set(_o)-set(_u))[:3]}")
    print(f"  {len(_eq_words)-_eq_fail}/{len(_eq_words)} words produce an identical candidate set")
    _failures += _eq_fail

    # NEW: structural invariant -- no generator may emit a right piece
    # beginning with a combining mark (see is_well_formed_candidate).
    print()
    print("Well-formedness invariant (no orphaned vowel signs in right pieces):")
    _wf_fail = 0
    for _w in _eq_words:
        for _c in generate_candidates(_w):
            if not is_well_formed_candidate(_c):
                _wf_fail += 1
                print(f"  [FAIL] {_w}: {_c['rule_id']} -> {_c['left']} + {_c['right']}")
    print(f"  {'PASS' if not _wf_fail else 'FAIL'} -- {_wf_fail} malformed candidate(s) survived filtering")
    _failures += _wf_fail

    print()
    if _failures:
        print(f"RESULT: {_failures} failure(s). Exiting non-zero.")
        sys.exit(1)
    print("RESULT: all suites passed.")
    sys.exit(0)
