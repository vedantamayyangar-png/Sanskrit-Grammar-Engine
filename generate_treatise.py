#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_treatise.py
=====================
Standalone command-line pipeline that produces the mandatory 10-component
Sanskrit grammar treatise (Sanskrit-medium components + an English
translation) for a range of verses, from ANY of several source formats.

It is a thin orchestration layer over the engine and data files that
already live in this same directory:

    samasa_splitter.py        -- sandhi/samasa/karaka/pratyaya engine
    build_grammar_json.py     -- mechanically-derived components 1/4/7/8/9
    manual_grammar_data.py    -- hand-authored components 2/3/5/6/10
    combine_grammar_json.py   -- merges the two into one 10-component doc
    comprehensive-10-component-template.json
                               -- a fully hand-verified WORKED EXAMPLE
                                  (currently Bala Kanda 1.1.1). When the
                                  verse being generated matches an
                                  exemplar in this file, its verified
                                  Component 1/8/9 content (padaccheda,
                                  sandhi, samasa) is used IN PLACE of the
                                  raw automatic guess for those
                                  components, since the exemplar has
                                  already been scholarly-checked.
    ap90.txt / mw.txt          -- Apte / Monier-Williams dictionaries
                                  (SLP1 source text), used for gloss
                                  lookup and split validation.

This script does not duplicate any of that logic -- it imports the
modules above directly, so bug-fixes made to any of them are picked up
automatically the next time this script runs.

WHAT IS, AND ISN'T, FULLY AUTOMATIC
------------------------------------
Components 1 (padaccheda), 4 (karaka), 7 (pratyaya), 8 (sandhi) and 9
(samasa) are mechanically derived from the sandhi/samasa engine and the
two dictionaries -- confidence-tagged (dictionary-verified vs
phonology-only/heuristic) so you can see how much to trust each entry.

Components 2 (anvaya), 3 (pada-vigraha prose), 5 (shabdarupani), 6
(dhaturupani) and 10 (chandas/alankara) need real Sanskrit-grammarian
judgement (meter, rhetorical figures, full case/conjugation paradigms,
prose word-order) that cannot be responsibly auto-generated from string
matching alone. For any verse present in manual_grammar_data.py's
MANUAL_DATA dict, this script fills these in from there. For a verse
NOT yet present there, these five components are emitted as a clearly
labeled skeleton (status: SKELETON_NEEDS_MANUAL_AUTHORING) rather than
fabricated -- exactly as build_grammar_json.py already does on its own,
EXCEPT for Component 10 (chandas), which gets a best-effort automatic
meter identification via the optional 'chanda' package if installed
(see install_grammar_validators.py).
To extend coverage to a new verse, add an entry to MANUAL_DATA keyed by
its verse id (e.g. "1.1.2") -- manual_grammar_data.py already has
entries for 1.1.1 through 1.1.5.

SANSKRIT-ONLY GRAMMAR CONTENT
------------------------------
Every field of grammatical content (pos, gender, number, case,
declension/conjugation tables, breakdowns, samasa/sandhi types, etc.) is
rendered in Sanskrit. The only fields left in English are word/verse
MEANINGS ("meaning", "meaning_en", "translation_en") and the
"confidence" field. Fields literally named "description",
"manual_content_status", or any field name starting with "_" (e.g.
"_note") are pipeline/meta documentation about the JSON structure
itself, not grammar content about the verse, and are also left as-is.
See the SANSKRIT LOCALIZATION LAYER section below for the exact
translation tables and the sanskritize_doc() function that applies them.

SUPPORTED SOURCE FORMATS  (--source-type, default: auto-detect from extension)
--------------------------------------------------------------------------
  gretil   A GRETIL-style plain-text file with a "# Text" marker and each
           pada-line tagged "...text... R_KANDA,SARGA.VERSE" (this is
           the format of sa_rAmAyaNa.txt). kanda/sarga are then genuine
           filters into a single big multi-kanda file.

  iast     Any other plain-text file: one verse per block, blocks
           separated by a blank line OR ended by a verse-number marker
           at the end of the line such as "|| 12 ||", "॥ १२ ॥",
           "(12)", or a trailing bare "12". No kanda/sarga structure is
           assumed; verses are numbered in the order they appear
           (offset by verse_start if given). Devanagari or IAST text is
           both fine -- Devanagari input is transliterated to IAST
           internally before analysis (the engine's native scheme).

  json     A JSON file holding either:
             - a flat list of verse strings, or
             - a list of objects, each with a text field (any of
               "text"/"iast"/"devanagari"/"shloka") and, optionally,
               "kanda"/"sarga"/"verse"/"number" fields, or
             - {"verses": [...]} wrapping either of the above.

  pdf      Text is extracted page-by-page (PyPDF2/pypdf, installed on
           demand if missing) and then handled exactly like "iast"
           above. PDF layout extraction is inherently less reliable
           than a clean text source -- inspect the output for
           line-wrap artifacts, especially for scanned/DTP-heavy PDFs.

USAGE
-----
    python generate_treatise.py --source sa_rAmAyaNa.txt \\
        --kanda 1 --sarga 1 --verse-start 1 --verse-end 1 \\
        --output bala_1_1-1_treatise.json

    python generate_treatise.py --source my_verses.json \\
        --verse-start 1 --verse-end 10 --output my_treatise.json

Kanda/sarga are OPTIONAL. Verse-start/verse-end are MANDATORY. If the
source is a multi-kanda GRETIL file and kanda/sarga are omitted, this
script defaults to kanda=1, sarga=1 (Bala Kanda, Sarga 1) and prints a
notice -- pass them explicitly for any other kanda/sarga.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as tl
except ImportError:
    sys.exit(
        "Missing dependency: indic_transliteration.\n"
        "Install it with:\n"
        f"    {sys.executable} -m pip install indic_transliteration sandhi\n"
        "(If pip reports 'Access is denied', run that command from an "
        "elevated/administrator prompt, or use a Python install you have "
        "write access to.)"
    )

try:
    import samasa_splitter as ss
except ImportError:
    sys.exit(
        "Cannot import samasa_splitter.py -- this script must live in the "
        "same directory as samasa_splitter.py, build_grammar_json.py, "
        "combine_grammar_json.py and manual_grammar_data.py."
    )

try:
    import build_grammar_json as bg
except ImportError:
    sys.exit("Cannot import build_grammar_json.py (see samasa_splitter.py note above).")

try:
    from manual_grammar_data import MANUAL_DATA
except ImportError:
    sys.exit("Cannot import manual_grammar_data.py (see samasa_splitter.py note above).")

# =========================================================================== #
# SANSKRIT LOCALIZATION LAYER
# =========================================================================== #
# By request: every field of GRAMMATICAL CONTENT in the output must be in
# Sanskrit. The only fields left in English are: word/verse MEANINGS
# ("meaning", "meaning_en", "translation_en") and the "confidence" field.
# Fields literally named "description", "manual_content_status", or any
# field name starting with "_" (e.g. "_note") are pipeline/meta
# documentation about the JSON structure itself (not grammar content
# about the verse), and are also left as-is.
#
# MANUAL_DATA (manual_grammar_data.py) is written in Sanskrit-in-IAST
# throughout (matching that file's own established convention -- e.g.
# "saptamī-tatpuruṣa", "kvip", "matup" are already Sanskrit terms, just
# romanized); this layer only needs to replace the residual ENGLISH
# grammatical-metalanguage words still present (pos/gender/number/case
# category names, and English glue-words inside etymology/role prose).
# The auto-generated components (build_grammar_json.py, via
# samasa_splitter.py's engine) use Devanagari for grammar terms (see
# CASE_NAME_SA there already), so this layer matches that convention
# for the English left in ITS output (pratyaya "function", samasa/sandhi
# "compound_type"/"sandhi_type" full sentences).
# =========================================================================== #

POS_SA = {
    "noun": "nāma", "noun (compound)": "nāma (samāsaḥ)",
    "adjective": "viśeṣaṇam", "adjective (compound)": "viśeṣaṇam (samāsaḥ)",
    "adjective (compound, bahuvrīhi)": "viśeṣaṇam (samāsaḥ, bahuvrīhiḥ)",
    "adjective (compound, nañ-tatpuruṣa)": "viśeṣaṇam (samāsaḥ, nañtatpuruṣaḥ)",
    "adjective (matup)": "viśeṣaṇam (matup-pratyayāntam)",
    "noun/adjective": "nāma/viśeṣaṇam",
    "proper noun": "saṃjñā-śabdaḥ",
    "verb": "kriyāpadam",
    "pronoun (idam)": "sarvanāma (idam)", "pronoun (etad)": "sarvanāma (etad)",
    "pronoun (aham)": "sarvanāma (aham)",
    "pronoun (aham, enclitic)": "sarvanāma (aham, anudāttam)",
    "pronoun (tvad)": "sarvanāma (tvad)",
    "interrogative pronoun": "praśna-sarvanāma",
    "indeclinable": "avyayam", "indeclinable (adverb)": "avyayam (kriyā-viśeṣaṇam)",
    "indeclinable particle": "avyayam (nipātaḥ)",
    "participle (kvasu)": "kṛdantam (kvasu-pratyayāntam)",
    "infinitive": "tumun-antam",
}
GENDER_SA = {"masc": "puṃliṅgam", "fem": "strīliṅgam", "neut": "napuṃsakaliṅgam",
             "masc/neut": "puṃliṅgam/napuṃsakaliṅgam",
             "neut/masc": "napuṃsakaliṅgam/puṃliṅgam", "-": "—"}
NUMBER_SA = {"sg": "ekavacanam", "pl": "bahuvacanam", "-": "—"}
CASE_SA = {"nominative": "prathamā", "accusative": "dvitīyā", "instrumental": "tṛtīyā",
           "dative": "caturthī", "ablative": "pañcamī", "genitive": "ṣaṣṭhī",
           "locative": "saptamī", "vocative": "sambodhanam", "-": "—"}

# role field: exact-match for fixed terms, else pattern-based for the
# "qualifies X" / "X, qualifies Y" / "role of X" family.
ROLE_EXACT_SA = {
    "karta": "kartā", "karma": "karma", "kriyā": "kriyā",
    "karaṇa": "karaṇam", "adhikaraṇa": "adhikaraṇam", "sambandha": "sambandhaḥ",
    "emphasis": "avadhāraṇam", "conjunction": "samuccayaḥ",
    "sambodhana (address)": "sambodhanam",
    "emphasis/causal connective": "avadhāraṇam/hetu-dyotakaḥ",
    "karta (implied 'asti')": "kartā (adhyāhṛtam 'asti'-padam)",
    "karta (implied 'asti'), repeated 5x": "kartā (adhyāhṛtam 'asti'-padam), pañca-vāram punaruktam",
    "karta (implied 'asti'), repeated 3x": "kartā (adhyāhṛtam 'asti'-padam), tri-vāram punaruktam",
    "kālavācaka (time adverb) -- NOT an accusative object, "
    "despite the -am ending coincidentally matching one":
        "kāla-vācakam (kriyā-viśeṣaṇam) — na tu dvitīyāntaṃ karma, "
        "yadyapi '-am'-pratyayāntatvāt tathā bhrāntiḥ syāt",
}
_ROLE_PATTERNS_SA = [
    (re.compile(r"^sambandha, qualifies (.+)$"), lambda m: f"sambandhaḥ, '{m.group(1)}'-padasya viśeṣaṇam"),
    (re.compile(r"^adhikaraṇa, qualifies (.+)$"), lambda m: f"adhikaraṇam, '{m.group(1)}'-padasya viśeṣaṇam"),
    (re.compile(r"^qualifies (.+?) \((.+)\)$"), lambda m: f"'{m.group(1)}'-padasya ({ROLE_EXACT_SA.get(m.group(2), m.group(2))}) viśeṣaṇam"),
    (re.compile(r"^qualifies (.+)$"), lambda m: f"'{m.group(1)}'-padasya viśeṣaṇam"),
    (re.compile(r"^viśeṣaṇam of (.+)$"), lambda m: f"'{m.group(1)}'-padasya viśeṣaṇam"),
    (re.compile(r"^karma of (.+)$"), lambda m: f"'{m.group(1)}'-padasya karma"),
    (re.compile(r"^sambandha, qualifies (.+)$"), lambda m: f"sambandhaḥ, '{m.group(1)}'-padasya viśeṣaṇam"),
]
ROLE_EXACT_SA.update({
    "karma of icchāmi/śrotum": "'icchāmi'/'śrotum' ityanayoḥ karma",
    "purpose, complements icchāmi": "tumarthaḥ, 'icchāmi'-padasya pūrakaḥ",
    "predicate, qualifies tvam": "vidheyam, 'tvam'-padasya viśeṣaṇam",
    "complements samarthaḥ asi": "'samarthaḥ asi' ityasya pūrakaḥ",
})


def translate_role_sa(role):
    if not role:
        return role
    if role in ROLE_EXACT_SA:
        return ROLE_EXACT_SA[role]
    for pat, fn in _ROLE_PATTERNS_SA:
        m = pat.match(role)
        if m:
            return fn(m)
    return role  # leave untranslated rather than guess wrong


# etymology field: exact-match dict (bounded, hand-verified set drawn
# from manual_grammar_data.py across all 5 authored verses).
ETYM_SA = {
    "tapas + in (possessive taddhita)": "tapas + in (svatva-vācakaḥ taddhitaḥ)",
    "pari + √prach, liṭ (perfect) 3sg parasmaipada":
        "pari + √prach, liṭ (parokṣa-bhūtaḥ), prathama-puruṣa-ekavacanam parasmaipadam",
    "muni + puṅgava -- ṣaṣṭhī-tatpuruṣa w/ embedded upamā":
        "muni + puṅgava — ṣaṣṭhī-tatpuruṣaḥ, upamā-garbhitaḥ",
    "kim + su (masc.)": "kim + su (puṃliṅge)",
    "unanalyzable particle": "avibhajya-nipātaḥ",
    "idam, loc.sg.": "idam, saptamī-ekavacanam",
    "sam+pra+√ap, taddhita -tana, used adverbially":
        "sam+pra+√āp, taddhitaḥ '-tana', kriyā-viśeṣaṇatvena prayuktam",
    "loka + i (loc.sg.)": "loka + i (saptamī-ekavacanam)",
    "satya + vākya (karmadhāraya, bahuvrīhi as a whole)":
        "satya + vākya (karmadhārayaḥ, samastaḥ tu bahuvrīhiḥ)",
    "dṛḍha + vrata (karmadhāraya, bahuvrīhi as a whole)":
        "dṛḍha + vrata (karmadhārayaḥ, samastaḥ tu bahuvrīhiḥ)",
    "particle": "nipātaḥ",
    "√vid + vas (kvasu-pratyaya, perfect active participle) -- NOT the matup "
    "vat/mat suffix, despite the surface resemblance to 'X-vān' words "
    "elsewhere in this verse-set":
        "√vid + vas (kvasu-pratyayaḥ, kartari-liṭi kṛdantam) — na tu "
        "matup-pratyayaḥ (vat/mat), yadyapi asmin śloka-samūhe anyatra "
        "dṛśyamānaiḥ '-vān'-śabdaiḥ sādṛśyaṃ bhāti",
    "eka + priya + darśana (karmadhāraya chain)":
        "eka + priya + darśana (paramparā-karmadhārayaḥ)",
    "kim, gen.sg.": "kim, ṣaṣṭhī-ekavacanam",
    "√bhī, laṭ (present) 3rd pl. parasmaipada":
        "√bhī, laṭ (vartamāna-kālaḥ), prathama-puruṣa-bahuvacanam parasmaipadam",
    "deva + jas (nom.pl.)": "deva + jas (prathamā-bahuvacanam)",
    "sam + √yuj + a, loc.sg.": "sam + √yuj + a, saptamī-ekavacanam",
    "etad, acc.sg.neut.": "etad, dvitīyā-ekavacanam (napuṃsakaliṅge)",
    "√iṣ, laṭ (present) 1st sg. parasmaipada":
        "√iṣ, laṭ (vartamāna-kālaḥ), uttama-puruṣa-ekavacanam parasmaipadam",
    "aham, nom.sg.": "aham, prathamā-ekavacanam",
    "aham, gen.sg. enclitic": "aham, ṣaṣṭhī-ekavacanam (anudāttam)",
    "tvad, nom.sg.": "tvad, prathamā-ekavacanam",
    "√as, laṭ (present) 2nd sg. parasmaipada":
        "√as, laṭ (vartamāna-kālaḥ), madhyama-puruṣa-ekavacanam parasmaipadam",
}


def translate_etymology_sa(etym):
    return ETYM_SA.get(etym, etym)


# shabdarupani gender labels (a few extra combinations not in GENDER_SA)
SHABDA_GENDER_SA = dict(GENDER_SA)
SHABDA_GENDER_SA.update({
    "masc/neut adj.": "puṃliṅgam/napuṃsakaliṅgam (viśeṣaṇam)",
    "masc (interrogative pronoun)": "puṃliṅgam (praśna-sarvanāma)",
})

# shabdarupani/declension-table "note" fields (exact-match, bounded set)
SHABDA_NOTE_SA = {
    "vāgvid (consonant/d-stem) omitted from this generator set -- irregular "
    "root-noun declension (nom.sg. vāgvit via cartva, governed by the root "
    "vid- 'know', not a fixed-vowel-stem pattern) -- needs its own "
    "hand-checked table, not one of the generic paradigms above.":
        "'vāgvid' (vyañjanāntaḥ, d-kārāntaḥ) asmāt jananayantrāt tyaktaḥ — "
        "vaiṣamikam mūla-nāma-rūpam (prathamā-ekavacane 'vāgvit' iti "
        "cartva-dvārā, 'vid'-dhātunā niyantritam, na tu niyata-svarānta-"
        "prakāraḥ) — svakīyam hasta-parīkṣitam kośṭakam apekṣate, na tu "
        "upari-varṇita-sāmānya-prakārāṇām ekam.",
    "masculine forms shown (the verse uses kaḥ throughout, interrogative "
    "pronoun agreeing with an unstated masc. referent)":
        "puṃliṅga-rūpāṇi darśitāni (śloke sarvatra 'kaḥ' prayuktam, "
        "praśna-sarvanāma anuktena puṃliṅga-viṣayeṇa sārdham anvitam)",
    "vidvān (vidvas-stem participle, kvasu) omitted from this generator set "
    "-- an irregular -vas/-vat consonant-stem participle paradigm distinct "
    "from both the a-stem and matup patterns above; needs its own "
    "hand-checked table.":
        "'vidvān' (vidvas-prātipadikam kṛdantam, kvasu-pratyayāntam) asmāt "
        "jananayantrāt tyaktam — vaiṣamikaḥ '-vas/-vat' vyañjanāntaḥ "
        "kṛdanta-prakāraḥ, upari-varṇita-akārānta-prakārāt matup-prakārāc "
        "ca bhinnaḥ; svakīyam hasta-parīkṣitam kośṭakam apekṣate.",
    "neuter forms shown (etat qualifies an unstated neuter referent, "
    "'this [matter]')":
        "napuṃsakaliṅga-rūpāṇi darśitāni ('etat' iti anuktam "
        "napuṃsakaliṅgaṃ viṣayaṃ viśinaṣṭi, 'idam vastu' ityarthe)",
}

# dhaturupani gana/lakara/form/note (exact-match, bounded set)
DHATU_FIELD_SA = {
    "6 (tudādi)": "ṣaṣṭho gaṇaḥ (tudādiḥ)",
    "3 (juhotyādi/reduplicating class)": "tṛtīyo gaṇaḥ (juhotyādiḥ, dvirvacana-gaṇaḥ)",
    "2 (adādi)": "dvitīyo gaṇaḥ (adādiḥ)",
    "liṭ (perfect)": "liṭ (parokṣa-bhūtaḥ)",
    "laṭ (present)": "laṭ (vartamāna-kālaḥ)",
    "paripapraccha = pari + papraccha, 3rd sg. parasmaipada":
        "paripapraccha = pari + papraccha, prathama-puruṣa-ekavacanam parasmaipadam",
    "bibhyati = √bhī, 3rd pl. parasmaipada":
        "bibhyati = √bhī, prathama-puruṣa-bahuvacanam parasmaipadam",
    "icchāmi = √iṣ, 1st sg. parasmaipada":
        "icchāmi = √iṣ, uttama-puruṣa-ekavacanam parasmaipadam",
    "asi = √as, 2nd sg. parasmaipada":
        "asi = √as, madhyama-puruṣa-ekavacanam parasmaipadam",
    "No overt finite verb in this verse -- an elliptical existential 'asti' "
    "(is there) is understood, governing the string of nominative "
    "predicate-adjectives. See COMPONENT_6 of 1.1.5 for the paradigm of √as.":
        "asmin śloke prakaṭaḥ tiṅantaḥ na vidyate — adhyāhṛtam 'asti'-padam "
        "prathamānta-viśeṣaṇa-paramparāṃ niyacchati. √as-dhātoḥ rūpāṇi "
        "1.1.5-COMPONENT_6 ityatra draṣṭavyāni.",
    "No overt finite verb -- same elliptical 'asti' as 1.1.2. vidvān is a "
    "participle (see pada_vigraha), not a finite form.":
        "prakaṭaḥ tiṅantaḥ nāsti — 1.1.2-vat adhyāhṛtam 'asti'-padam. "
        "'vidvān' iti kṛdantam (pada_vigrahe draṣṭavyam), na tu tiṅantam.",
    "śrotum (√śru + tumun) and jñātum (√jñā + tumun) are infinitives, not "
    "finite forms -- no conjugation table applies; see COMPONENT_7 "
    "pratyaya for their derivation.":
        "'śrotum' (√śru+tumun) 'jñātum' (√jñā+tumun) ca tumun-antau, na tu "
        "tiṅantau — dhātu-rūpa-kośṭakam na prayujyate; etayoḥ vyutpattiḥ "
        "COMPONENT_7-pratyaye draṣṭavyā.",
}

# alankara name/definition (exact-match keyed by (name, definition) pair,
# per verse -- bespoke prose, bounded to the 8 entries across 5 verses)
ALANKARA_SA = {
    ("svabhāvokti", "plain, unadorned narration -- the verse's overall style"):
        ("svabhāvokti", "sahaja-varṇanam, alaṅkāra-rahitam — ślokasya sāmānya-śailī"),
    ("rūpaka (minor, embedded)", "munipuṅgavam figures the sage as a bull among sages"):
        ("rūpaka (gauṇam, samāsāntargatam)", "'munipuṅgavam' iti munim puṅgava-rūpeṇa rūpayati"),
    ("praśna (rhetorical question, not a formal alaṅkāra but the verse's "
     "organizing device)",
     "the first of a chain of questions Vālmīki puts to Nārada, continuing through 1.1.4"):
        ("praśnaḥ (arthālaṅkāratvena aprasiddhaḥ, kintu ślokasya vinyāsa-sādhanam)",
         "vālmīkinā nāradaṃ prati pṛṣṭānāṃ praśna-paramparāyāḥ prathamaḥ, 1.1.4-paryantam anuvartate"),
    ("praśna (continued)", "second verse of the question-chain begun in 1.1.2"):
        ("praśnaḥ (anuvṛttaḥ)", "1.1.2-ślokāt ārabdha-praśna-paramparāyāḥ dvitīyaḥ ślokaḥ"),
    ("praśna (concludes the question-chain)",
     "final verse of questions begun in 1.1.2, culminating in the vivid image "
     "of even gods fearing this person's wrath in battle (ativāda/atiśayokti "
     "-- hyperbolic praise)"):
        ("praśnaḥ (praśna-paramparāyāḥ samāpakaḥ)",
         "1.1.2-taḥ ārabdhānāṃ praśnānām antimaḥ ślokaḥ, yuddhe devānām api "
         "asya krodhāt bhaya-darśanena parisamāpyate (ativādaḥ/atiśayoktiḥ — "
         "atiśaya-praśaṃsā)"),
    ("atiśayoktiḥ", "hyperbole -- that even the devas themselves fear this person's anger"):
        ("atiśayoktiḥ", "atiśayoktiḥ — yat svayaṃ devāḥ api asya krodhāt bibhyati"),
    ("svabhāvokti", "plain first-person statement of intent -- closes the "
     "frame Vālmīki opened in 1.1.1, transitioning from the list of "
     "questions (1.1.2-4) back to direct address of Nārada"):
        ("svabhāvokti", "sarala-uttama-puruṣa-vākyena abhiprāya-kathanam — "
         "1.1.1-śloke vālmīkinā ārabdhaṃ prastāva-vṛttaṃ samāpayati, "
         "praśna-paramparātaḥ (1.1.2-4) punaḥ nāradaṃ prati sākṣāt-"
         "sambodhanaṃ prati parivartamānam"),
}

# HEADERS used across every declension_table/conjugation table
HEADERS_SA = {"vibhakti": "vibhaktiḥ", "singular": "ekavacanam",
              "dual": "dvivacanam", "plural": "bahuvacanam", "puruṣa": "puruṣaḥ"}
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")


def sanskritize_table(table):
    """Generic cleanup for any {"headers":[...], "rows":[[label, ...], ...],
    "note": "..."} declension/conjugation table: translate headers via
    HEADERS_SA, strip the trailing English parenthetical gloss from each
    row's first (label) column (e.g. "prathamā (nom.)" -> "prathamā",
    "prathama (3rd)" -> "prathama"), and translate the table's own "note"
    if it's one of the known ones."""
    if not isinstance(table, dict):
        return table
    if "headers" in table:
        table["headers"] = [HEADERS_SA.get(h, h) for h in table["headers"]]
    if "rows" in table:
        for row in table["rows"]:
            if row:
                row[0] = _TRAILING_PAREN_RE.sub("", row[0]).strip()
    if "note" in table:
        table["note"] = SHABDA_NOTE_SA.get(table["note"], table["note"])
    return table


# CASE_ENDING_TABLE_WX notes (21 fixed rows in samasa_splitter.py) -> full
# Sanskrit (Devanagari, matching the auto-generated component's own
# convention) description of the stem-class/case/number, used for
# COMPONENT_7's auto "function" field.
STEM_NOTE_SA = {
    "-mat stem (e.g. buddhimAn)": "मत्-प्रत्ययान्तः, यथा बुद्धिमान्",
    "-vat stem (e.g. balavAn, bhagavAn)": "वत्-प्रत्ययान्तः, यथा बलवान्, भगवान्",
    "fem I-stem/pronoun (iyam)": "स्त्रियाम् ईकारान्तः/सर्वनाम (इयम्)",
    "a-stem masc/neut gen sg (e.g. rAmasya)": "अकारान्तः पुंनपुंसकलिङ्गे षष्ठ्येकवचनम्, यथा रामस्य",
    "a-stem gen pl (e.g. narANAm -- approximate)": "अकारान्तः षष्ठीबहुवचनम्, यथा (सदृशम्) नराणाम्",
    "a-stem loc pl (e.g. narezu)": "अकारान्तः सप्तमीबहुवचनम्, यथा नरेषु",
    "": "अकारान्तः तृतीयाद्विवचनम्",
    "a-stem abl sg (e.g. grAmAw)": "अकारान्तः पञ्चम्येकवचनम्, यथा ग्रामात्",
    "a-stem masc nom pl (ambiguous w/ A-stem fem gen/abl sg)":
        "अकारान्तः पुल्लिङ्गे प्रथमाबहुवचनम् (आकारान्तस्त्रीलिङ्गे षष्ठी/पञ्चम्येकवचनेन सह साम्यम्)",
    "a-stem masc acc pl (ambiguous w/ -mat/-vat nom sg, see above)":
        "अकारान्तः पुल्लिङ्गे द्वितीयाबहुवचनम् (मत्/वत्-प्रत्ययान्तप्रथमैकवचनेन सह साम्यम्)",
    "a-stem masc nom sg (e.g. rAmaH)": "अकारान्तः पुल्लिङ्गे प्रथमैकवचनम्, यथा रामः",
    "a-stem masc acc sg / neut nom-acc sg":
        "अकारान्तः पुल्लिङ्गे द्वितीयैकवचनम् / नपुंसकलिङ्गे प्रथमा-द्वितीयैकवचनम्",
    "a-stem masc/neut inst sg (e.g. rAmeRa)": "अकारान्तः पुंनपुंसकलिङ्गे तृतीयैकवचनम्, यथा रामेण",
    "a-stem masc/neut dat sg": "अकारान्तः पुंनपुंसकलिङ्गे चतुर्थ्येकवचनम्",
    "i-stem masc/fem nom sg (e.g. vAlmIkiH)": "इकारान्तः पुंस्त्रीलिङ्गे प्रथमैकवचनम्, यथा वाल्मीकिः",
    "u-stem masc/fem nom sg (e.g. guruH)": "उकारान्तः पुंस्त्रीलिङ्गे प्रथमैकवचनम्, यथा गुरुः",
    "i-stem acc sg": "इकारान्तः द्वितीयैकवचनम्",
    "u-stem acc sg": "उकारान्तः द्वितीयैकवचनम्",
    "-Am gen pl across several stem classes (e.g. vAgvidAm)":
        "'-आम्' षष्ठीबहुवचनम् (बहुषु प्रातिपदिकवर्गेषु), यथा वाग्विदाम्",
    "-in stem masc / fem I-stem (e.g. wapasvI)": "इन्-कारान्तः पुल्लिङ्गे / स्त्रियाम् ईकारान्तः, यथा तपस्वी",
    "fem A-stem nom sg (highly ambiguous -- also inst sg elsewhere)":
        "स्त्रियाम् आकारान्तः प्रथमैकवचनम् (अतीव सांदिग्धम् — अन्यत्र तृतीयैकवचनमपि)",
}

# The 5 unique kṛt/matup pratyaya glosses (PRATYAYA_SUFFIXES/MATUP_SUFFIXES_WX
# in samasa_splitter.py), used for COMPONENT_7's auto "function" field when
# a word resolves via resolve_pratyaya/resolve_matup rather than a plain
# case ending.
PRATYAYA_GLOSS_SA = {
    "infinitive: 'to (do/be) ...'": "तुमुन्नन्तः (क्रियार्थकः)",
    "infinitive, root-final aspirate assimilated the -t- (buX -> boXXum)":
        "तुमुन्नन्तः (धात्वन्त्यमहाप्राणसन्धिः)",
    "gerund: 'having (done/been) ...'": "क्त्वान्तः (पूर्वकालिकः)",
    "gerund, root-final aspirate assimilated the -t- (buX -> buXXvA)":
        "क्त्वान्तः (धात्वन्त्यमहाप्राणसन्धिः)",
    "matup pratyaya (possessive): 'possessing/having ~'": "मतुप्प्रत्ययः (स्वत्ववाचकः)",
}

# samasa/sandhi "compound_type"/"sandhi_type" auto-generated full-sentence
# values (guess_samasa_type() in samasa_splitter.py, after
# sanskrit_type_label()'s partial Devanagari substitution) -- pattern-based,
# since a specific word is interpolated into the sentence.
_TYPE_SENTENCE_PATTERNS_SA = [
    (re.compile(r"^NOT a samasa -- '(.+?)' is a particle; this is ordinary "
                r"external sandhi fused without a written space$"),
     lambda m: f"न समासः — '{m.group(1)}' इति निपातः; इदं केवलं पदान्तरसन्धिः, "
               f"रिक्तस्थानं विना।"),
    (re.compile(r"^dvigu \(heuristic: numeral first member\)$"),
     lambda m: "द्विगुसमासः (अनुमानम्: पूर्वपदं सङ्ख्यावाचकम्)"),
    (re.compile(r"^तत्पुरुषसमासः \(upasarga-compound: '(.+?)-' is one of the "
                r"22 traditional upasargas\)$"),
     lambda m: f"तत्पुरुषसमासः (उपसर्गसमासः: '{m.group(1)}-' द्वाविंशत्युपसर्गेषु अन्यतमः)"),
    (re.compile(r"^nañ-तत्पुरुषसमासः \(negative compound: '(.+?)-' is the "
                r"negative prefix a-/an-\)$"),
     lambda m: f"नञ्तत्पुरुषसमासः (निषेधार्थकसमासः: '{m.group(1)}-' अकार/अनकार-निषेधोपसर्गः)"),
    (re.compile(r"^avyayibhava\? \(heuristic: indeclinable-looking first "
                r"member\)$"),
     lambda m: "अव्ययीभावसमासः? (अनुमानम्: पूर्वपदम् अव्ययसदृशम्)"),
    (re.compile(r"^तत्पुरुषसमासः / कर्मधारयसमासः / बहुव्रीहिसमासः -- uncertain "
                r"\(needs meaning/dictionary glosses to disambiguate\)$"),
     lambda m: "तत्पुरुषः/कर्मधारयः/बहुव्रीहिः — असंदिग्धम् (निर्णयाय अर्थ-/कोश-सहायता अपेक्षिता)"),
    (re.compile(r"^not a compound \(single member\)$"),
     lambda m: "समासो नास्ति (एकमेव पदम्)"),
    (re.compile(r"^sandhi-free junction \(members concatenate unchanged\)$"),
     lambda m: "सन्धिरहितः सन्धिः (अवयवाः अपरिवर्तितौ मिलितौ)"),
]


def translate_type_sentence_sa(text):
    if not text:
        return text
    for pat, fn in _TYPE_SENTENCE_PATTERNS_SA:
        m = pat.match(text)
        if m:
            return fn(m)
    return text  # already Sanskrit (e.g. real sutra-derived sandhi_type), or unrecognized -- leave as-is


def sanskritize_doc(doc):
    """Walks one verse's merged 10-component doc and converts every field
    of grammatical CONTENT to Sanskrit, leaving meanings/translations/
    confidence/meta-description fields in English (see module-level
    comment above for the exact rule)."""

    # --- COMPONENT_3 pada_vigraha (from MANUAL_DATA, IAST-Sanskrit) -----
    c3 = doc.get("COMPONENT_3_padavigraha", {})
    for w in c3.get("pada_vigraha", []):
        if "pos" in w:
            w["pos"] = POS_SA.get(w["pos"], w["pos"])
        if "gender" in w:
            w["gender"] = GENDER_SA.get(w["gender"], w["gender"])
        if "number" in w:
            w["number"] = NUMBER_SA.get(w["number"], w["number"])
        if "case" in w:
            w["case"] = CASE_SA.get(w["case"], w["case"])
        if "etymology" in w:
            w["etymology"] = translate_etymology_sa(w["etymology"])
        if "role" in w:
            w["role"] = translate_role_sa(w["role"])
        # "meaning" (word meaning) is deliberately left in English.

    # --- COMPONENT_5 shabdarupani ----------------------------------------
    c5 = doc.get("COMPONENT_5_shabdarupani", {}).get("shabdarupani", {})
    if isinstance(c5, dict):
        for key, entry in c5.items():
            if key == "note":
                c5["note"] = SHABDA_NOTE_SA.get(entry, entry)
                continue
            if isinstance(entry, dict):
                if "gender" in entry:
                    entry["gender"] = SHABDA_GENDER_SA.get(entry["gender"], entry["gender"])
                if "declension_table" in entry:
                    sanskritize_table(entry["declension_table"])

    # --- COMPONENT_6 dhaturupani ------------------------------------------
    c6 = doc.get("COMPONENT_6_dhaturupani", {}).get("dhaturupani", {})
    if isinstance(c6, dict):
        def _fix_root_entry(rd):
            for f in ("gana", "lakara", "form"):
                if f in rd:
                    rd[f] = DHATU_FIELD_SA.get(rd[f], rd[f])
            if "conjugation" in rd:
                sanskritize_table(rd["conjugation"])
        if "roots" in c6:  # 1.1.5-style multi-root shape
            for rd in c6["roots"]:
                _fix_root_entry(rd)
        else:
            _fix_root_entry(c6)
        if "note" in c6:
            c6["note"] = DHATU_FIELD_SA.get(c6["note"], c6["note"])

    # --- COMPONENT_10 chandas: alankara name/definition -------------------
    c10 = doc.get("COMPONENT_10_chandas", {})
    new_alankara = []
    for a in c10.get("alankara", []):
        key = (a.get("name", ""), a.get("definition", ""))
        if key in ALANKARA_SA:
            name_sa, def_sa = ALANKARA_SA[key]
            new_alankara.append({"name": name_sa, "definition": def_sa})
        else:
            new_alankara.append(a)
    if "alankara" in c10:
        c10["alankara"] = new_alankara

    # --- COMPONENT_7 pratyaya (auto-generated) -----------------------------
    for p in doc.get("COMPONENT_7_pratyaya", {}).get("pratyaya", []):
        if "breakdown" in p:
            p["breakdown"] = (p["breakdown"].replace("(stem)", "प्रातिपदिकम्")
                               .replace(" vibhakti", " विभक्तिः"))
        if "function" in p:
            p["function"] = STEM_NOTE_SA.get(
                p["function"], PRATYAYA_GLOSS_SA.get(p["function"], p["function"]))
        # "confidence" deliberately left in English.

    # --- COMPONENT_8 sandhi / COMPONENT_9 samasa (auto full sentences) ----
    for s in doc.get("COMPONENT_8_sandhi", {}).get("sandhi", []):
        if "sandhi_type" in s:
            s["sandhi_type"] = translate_type_sentence_sa(s["sandhi_type"])
    for s in doc.get("COMPONENT_9_samasa", {}).get("samasa", []):
        if "compound_type" in s:
            s["compound_type"] = translate_type_sentence_sa(s["compound_type"])
        # "meaning" (word/compound meaning) deliberately left in English.

    return doc


# Optional: automatic meter identification via the 'chanda' package
# (Chandojnanam, https://github.com/hrishikeshrt/chanda) for verses that
# have no MANUAL_DATA entry yet. Soft dependency -- if not installed
# (see install_grammar_validators.py), Component 10 just falls back to
# the existing SKELETON_NEEDS_MANUAL_AUTHORING placeholder as before.
try:
    import chanda as _chanda_lib
except ImportError:
    _chanda_lib = None


def auto_identify_chandas(verse_lines):
    """Best-effort automatic meter identification for a verse that has no
    MANUAL_DATA entry, using the chanda (Chandojnanam) package if it's
    installed. Returns a COMPONENT_10-shaped dict, or None if chanda
    isn't installed or couldn't identify anything."""
    if _chanda_lib is None:
        return None
    full_text = "\n".join(line["text"] for line in verse_lines)
    try:
        result = _chanda_lib.analyze_text(full_text)
    except Exception as e:
        print(f"[chanda meter identification failed: {e}]", file=sys.stderr)
        return None

    scansion, names = [], []
    for i, line_result in enumerate(result.result.line, start=1):
        cr = line_result.result
        scansion.append({"quarter": i, "text": cr.line, "matra": cr.matra})
        for name, _padas in (cr.chanda or []):
            if name not in names:
                names.append(name)
    if not names and not scansion:
        return None
    return {
        "description": "१०. छन्दस्/अलङ्कारः -- Meter auto-identified by the "
                        "'chanda' (Chandojnanam) package; NOT manually "
                        "verified, and alankara (figures of speech) still "
                        "needs manual authoring.",
        "chandas_name": " / ".join(names) if names else "(not identified)",
        "scansion": scansion,
        "alankara": [],
        "_auto_identified": True,
    }


# =========================================================================== #
# Source loading: every format below is normalized into the SAME shape
# ss.parse_gretil_verses() already returns --
#     {(kanda, sarga, verse_number): [pada_line_1, pada_line_2, ...], ...}
# -- so the rest of the pipeline (analyze_verse_corpus, build_verse_json,
# MANUAL_DATA merge) does not need to know or care which source format
# was actually used.
# =========================================================================== #

DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')


def _to_iast_if_devanagari(text):
    """Transliterate Devanagari input to IAST; leaves already-IAST text
    (or anything else) untouched. The engine's dictionaries/rules are
    IAST/WX-based, so Devanagari verse text must be converted before
    any sandhi/samasa/karaka analysis can run on it."""
    if DEVANAGARI_RE.search(text):
        return tl(text, sanscript.DEVANAGARI, sanscript.IAST)
    return text


def detect_source_type(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".txt", ".iast", ""):
        # Peek at the file: GRETIL files carry a "# Text" marker.
        try:
            with open(path, encoding="utf-8") as f:
                head = f.read(20000)
            if "# Text" in head:
                return "gretil"
        except Exception:
            pass
        return "iast"
    return "iast"


def load_gretil(path, kanda, sarga, verse_start, verse_end):
    if kanda is None or sarga is None:
        print("[kanda/sarga not specified for a GRETIL multi-kanda source -- "
              "defaulting to kanda=1, sarga=1 (Bala Kanda, Sarga 1)]", file=sys.stderr)
        kanda = kanda if kanda is not None else 1
        sarga = sarga if sarga is not None else 1
    return ss.parse_gretil_verses(path, kanda=kanda, sarga=sarga,
                                   verse_start=verse_start, verse_end=verse_end)


# A trailing verse-number marker at the end of a line, in any of the
# conventional forms: "|| 12 ||", "॥ १२ ॥", "(12)", or a bare "12".
_VERSE_MARKER_RE = re.compile(
    r'(?:\|\||\u0965)\s*([0-9\u0966-\u096F]+)\s*(?:\|\||\u0965)\s*$'
    r'|\(([0-9\u0966-\u096F]+)\)\s*$'
    r'|(?<!\S)([0-9]+)\s*$'
)
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _marker_to_int(m):
    for g in m.groups():
        if g:
            return int(g.translate(_DEVANAGARI_DIGITS))
    return None


def load_iast_plain(path, kanda, sarga, verse_start, verse_end):
    """
    Parse a plain-text (non-GRETIL) source: one verse per block. A block
    ends either at a blank line, or at a line carrying an explicit
    verse-number marker (see _VERSE_MARKER_RE) -- whichever comes first.
    If no markers are present at all, verses are simply numbered in
    order starting at 1.
    """
    with open(path, encoding="utf-8") as f:
        raw_text = f.read()

    verses = {}
    buffer = []
    auto_num = 0
    seen_any_marker = False

    def flush(explicit_num=None):
        nonlocal auto_num
        if not buffer:
            return
        auto_num += 1
        num = explicit_num if explicit_num is not None else auto_num
        pada_lines = [_to_iast_if_devanagari(l) for l in buffer]
        verses[(kanda or 0, sarga or 0, num)] = pada_lines
        buffer.clear()

    for raw in raw_text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        m = _VERSE_MARKER_RE.search(line)
        if m and _marker_to_int(m) is not None:
            seen_any_marker = True
            num = _marker_to_int(m)
            text_part = line[: m.start()].strip()
            if text_part:
                buffer.append(text_part)
            flush(explicit_num=num)
        else:
            buffer.append(line)
    flush()

    if not seen_any_marker:
        print("[no explicit verse-number markers found in the plain-text "
              "source -- verses numbered sequentially in file order]",
              file=sys.stderr)

    return {k: v for k, v in verses.items()
            if verse_start <= k[2] <= verse_end}


def _extract_text_field(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("text", "iast", "devanagari", "shloka", "verse_text"):
            if item.get(key):
                return item[key]
    return None


def load_json_source(path, kanda, sarga, verse_start, verse_end):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "verses" in data:
        data = data["verses"]
    if not isinstance(data, list):
        sys.exit("JSON source must be a list of verses, or {'verses': [...]}.")

    verses = {}
    for idx, item in enumerate(data, start=1):
        text = _extract_text_field(item)
        if not text:
            continue
        if isinstance(item, dict):
            k = item.get("kanda", kanda or 0)
            s = item.get("sarga", sarga or 0)
            v = item.get("verse", item.get("number", idx))
        else:
            k, s, v = (kanda or 0), (sarga or 0), idx
        if not (verse_start <= v <= verse_end):
            continue
        pada_lines = [_to_iast_if_devanagari(l.strip())
                      for l in re.split(r'[|\u0964\u0965]|\n', text) if l.strip()]
        if not pada_lines:
            continue
        verses[(k, s, v)] = pada_lines
    return verses


def load_pdf_source(path, kanda, sarga, verse_start, verse_end):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            import subprocess
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pypdf", "--quiet"])
            from pypdf import PdfReader
        except Exception:
            sys.exit(
                "PDF support needs the 'pypdf' package and automatic "
                f"install failed. Install manually:\n"
                f"    {sys.executable} -m pip install pypdf"
            )
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    tmp_path = Path(path).with_suffix(".extracted.txt")
    tmp_path.write_text(text, encoding="utf-8")
    print(f"[extracted PDF text cached at {tmp_path} for inspection]", file=sys.stderr)
    return load_iast_plain(tmp_path, kanda, sarga, verse_start, verse_end)


def load_verses(source, source_type, kanda, sarga, verse_start, verse_end):
    if source_type == "auto":
        source_type = detect_source_type(source)
        print(f"[auto-detected source type: {source_type}]", file=sys.stderr)

    if source_type == "gretil":
        return load_gretil(source, kanda, sarga, verse_start, verse_end)
    if source_type == "iast":
        return load_iast_plain(source, kanda, sarga, verse_start, verse_end)
    if source_type == "json":
        return load_json_source(source, kanda, sarga, verse_start, verse_end)
    if source_type == "pdf":
        return load_pdf_source(source, kanda, sarga, verse_start, verse_end)
    sys.exit(f"Unknown --source-type: {source_type}")


# =========================================================================== #
# Verified-exemplar overrides: comprehensive-10-component-template.json
# holds one (or more, in future) fully hand-checked worked example(s).
# When the verse being generated matches one, its Component 1/8/9 content
# is authoritative and replaces the raw automatic guess for that
# component. Tamil fields are dropped (this pipeline's output is
# Sanskrit + English only, per spec); everything else is carried through.
# =========================================================================== #

def _strip_ta_keys(obj):
    if isinstance(obj, dict):
        return {k: _strip_ta_keys(v) for k, v in obj.items()
                if not (k.endswith("_ta") or k == "meaning_ta")}
    if isinstance(obj, list):
        return [_strip_ta_keys(v) for v in obj]
    return obj


def load_template_overrides(template_path):
    """Returns {verse_id: {"padaccheda":[...], "sandhi":[...], "samasa":[...],
    "translation_en": "..."}} for every exemplar verse found in the
    template file. Silently returns {} if the file is missing or doesn't
    parse -- this is a quality bonus, not a hard requirement."""
    if not template_path or not Path(template_path).exists():
        return {}
    try:
        with open(template_path, encoding="utf-8") as f:
            tmpl = json.load(f)
    except Exception as e:
        print(f"[warning: could not read template file {template_path}: {e}]",
              file=sys.stderr)
        return {}

    verse_id = tmpl.get("shloka_metadata", {}).get("id")
    if not verse_id:
        return {}

    overrides = {}
    c1 = tmpl.get("COMPONENT_1_padaccheda", {}).get("padaccheda")
    c8 = tmpl.get("COMPONENT_8_sandhi", {}).get("sandhi")
    c9 = tmpl.get("COMPONENT_9_samasa", {}).get("samasa")
    c2 = tmpl.get("COMPONENT_2_anvaya", {}).get("translation_en")
    entry = {}
    if c1:
        entry["padaccheda"] = _strip_ta_keys(c1)
    if c8:
        entry["sandhi"] = _strip_ta_keys(c8)
    if c9:
        entry["samasa"] = _strip_ta_keys(c9)
    if c2:
        entry["translation_en"] = c2
    if entry:
        overrides[verse_id] = entry
    return overrides


def apply_template_override(doc, verse_id, overrides):
    ov = overrides.get(verse_id)
    if not ov:
        return doc
    if "padaccheda" in ov:
        doc["COMPONENT_1_padaccheda"]["padaccheda"] = ov["padaccheda"]
        doc["COMPONENT_1_padaccheda"]["description"] += (
            " [Component 1 replaced with verified exemplar data from the "
            "comprehensive-10-component-template.]")
    if "sandhi" in ov:
        doc["COMPONENT_8_sandhi"]["sandhi"] = ov["sandhi"]
        doc["COMPONENT_8_sandhi"]["description"] += (
            " [replaced with verified exemplar data]")
    if "samasa" in ov:
        doc["COMPONENT_9_samasa"]["samasa"] = ov["samasa"]
        doc["COMPONENT_9_samasa"]["description"] += (
            " [replaced with verified exemplar data]")
    if "translation_en" in ov and "COMPONENT_2_anvaya" in doc:
        doc["COMPONENT_2_anvaya"]["translation_en"] = ov["translation_en"]
    doc["shloka_metadata"]["verified_exemplar"] = True
    return doc


# =========================================================================== #
# Merge (same logic as combine_grammar_json.py's merged_verse_json, kept
# here rather than imported so verified-exemplar overrides can be
# layered on top in the right order: auto -> manual -> verified exemplar).
# =========================================================================== #

def _karaka_role_bucket(role):
    """Classify a MANUAL_DATA pada_vigraha 'role' free-text string into a
    karaka bucket, but ONLY when the role text is actually ABOUT this
    word's own karaka status (starts with the karaka name) -- not when
    it merely mentions one in passing, e.g. 'qualifies vālmīkiḥ (karta)'
    describes a word that qualifies the karta, and is not itself the
    karta."""
    r = role.strip()
    if r.startswith("karta"):
        return "karta"
    if r.startswith("karma"):
        return "karma"
    if r.startswith("kriy"):
        return "kriya"
    if r.startswith("karaṇa") or r.startswith("karana"):
        return "karana"
    if r.startswith("adhikaraṇa") or r.startswith("adhikarana"):
        return "adhikarana"
    if r.startswith("sambandha"):
        return "sambandha"
    return None


def build_karaka_from_manual(pada_vigraha):
    """A verified alternative to build_grammar_json.build_karaka(), using
    the hand-authored 'role' field in MANUAL_DATA's pada_vigraha list
    (which reflects real grammatical judgement) instead of the
    automatic engine's linear-order case-tag heuristic. Used only for
    verses that have MANUAL_DATA -- see merged_verse_json."""
    karta = karma = None
    karana, adhikarana, sambandha = [], [], []
    for w in pada_vigraha:
        bucket = _karaka_role_bucket(w.get("role", ""))
        if bucket == "karta" and karta is None:
            karta = w["word"]
        elif bucket == "karma" and karma is None:
            karma = w["word"]
        elif bucket == "karana":
            karana.append(w["word"])
        elif bucket == "adhikarana":
            adhikarana.append(w["word"])
        elif bucket == "sambandha":
            sambandha.append(w["word"])
    return {
        "karta": karta or "",
        "karma": karma or "",
        "karana": ", ".join(karana) if karana else "इदं श्लोके प्रत्यक्षं करणपदं नास्ति",
        "adhikarana": ", ".join(adhikarana) if adhikarana else "इदं श्लोके प्रत्यक्षम् अधिकरणपदं नास्ति",
        "sambandha": ", ".join(sambandha) if sambandha else "",
        "_note": "Derived from the hand-authored pada-vigraha role "
                 "assignments in manual_grammar_data.py (verified), not "
                 "the automatic case-tag heuristic.",
    }


def merged_verse_json(sp, verse_key, verse_lines, meta, template_overrides):
    doc = bg.build_verse_json(sp, verse_key, verse_lines, meta)
    verse_id = doc["shloka_metadata"]["id"]
    manual = MANUAL_DATA.get(verse_id)

    if manual:
        doc["COMPONENT_2_anvaya"] = {
            "description": "२. अन्वयः -- Syntactic prose order.",
            "anvaya_sa": manual["anvaya"]["sa"],
            "translation_en": manual["anvaya"]["en"],
        }
        doc["COMPONENT_3_padavigraha"] = {
            "description": "३. पद-विग्रहः -- Word-by-word analysis "
                            "(pos/gender/number/case/meaning/etymology/role).",
            "word_count": len(manual["pada_vigraha"]),
            "pada_vigraha": manual["pada_vigraha"],
        }
        doc["COMPONENT_5_shabdarupani"] = {
            "description": "५. शब्दरूपाणि -- Declension paradigms (IAST) for "
                            "every distinct declinable stem in the verse.",
            "shabdarupani": manual["shabdarupani"],
        }
        doc["COMPONENT_6_dhaturupani"] = {
            "description": "६. धातुरूपाणि -- Verb conjugation.",
            "dhaturupani": manual["dhaturupani"],
        }
        doc["COMPONENT_10_chandas"] = {
            "description": "१०. छन्दस्/अलङ्कारः -- Meter and literary devices.",
            "chandas_name": manual["chandas"]["name"],
            "scansion": manual["chandas"]["scansion"],
            "alankara": manual["chandas"]["alankara"],
        }
        doc["COMPONENT_4_karaka"]["karaka"] = build_karaka_from_manual(manual["pada_vigraha"])
        doc["COMPONENT_4_karaka"]["description"] = (
            "४. कारकः -- karta/karma/karana/adhikarana/sambandha derived from "
            "the verified pada-vigraha role assignments (manual_grammar_data.py).")
        doc["shloka_metadata"]["manual_content_status"] = "fully authored"
        doc["grammar_components"] = (
            "१. पदच्छेदः | २. अन्वयः | ३. पद-विग्रहः | ४. कारकः | ५. शब्दरूपाणि | "
            "६. धातुरूपाणि | ७. प्रत्ययाः | ८. सन्धिः | ९. समासः | १०. छन्दस्/अलङ्कारः "
            "(all 10 components complete)")
    else:
        doc["shloka_metadata"]["manual_content_status"] = (
            "NOT YET AUTHORED for this verse -- components 2/3/5/6/10 "
            "remain the SKELETON_NEEDS_MANUAL_AUTHORING placeholder. Add "
            "an entry to MANUAL_DATA in manual_grammar_data.py to complete it.")
        auto_chandas = auto_identify_chandas(verse_lines)
        if auto_chandas:
            doc["COMPONENT_10_chandas"] = auto_chandas

    doc = apply_template_override(doc, verse_id, template_overrides)

    # Ensure there is always a top-level, easy-to-find English translation
    # of the whole verse, regardless of which path produced it.
    translation_en = None
    if "COMPONENT_2_anvaya" in doc:
        translation_en = doc["COMPONENT_2_anvaya"].get("translation_en")
    doc["shloka_metadata"]["translation_en"] = (
        translation_en or "(not yet authored for this verse)")

    return doc


# =========================================================================== #
def main():
    parser = argparse.ArgumentParser(
        description="Generate the mandatory 10-component Sanskrit grammar "
                    "treatise (Sanskrit + English) for a range of verses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)

    parser.add_argument("--source", required=True,
                         help="Path to the source text: .txt (GRETIL-tagged "
                              "or plain IAST/Devanagari), .json, or .pdf")
    parser.add_argument("--source-type", default="auto",
                         choices=["auto", "gretil", "iast", "json", "pdf"],
                         help="Force a source format instead of auto-detecting "
                              "from the file extension/content. Default: auto")
    parser.add_argument("--kanda", type=int, default=None,
                         help="Optional: restrict to this kanda number")
    parser.add_argument("--sarga", type=int, default=None,
                         help="Optional: restrict to this sarga number")
    parser.add_argument("--verse-start", type=int, required=True,
                         help="Mandatory: first verse number to include")
    parser.add_argument("--verse-end", type=int, required=True,
                         help="Mandatory: last verse number to include")
    parser.add_argument("--output", required=True,
                         help="Path to write the combined treatise JSON")
    parser.add_argument("--cdsl", nargs="+", default=None,
                         help="One or more CDSL dictionary files (mw.txt, "
                              "ap90.txt). Default: ap90.txt and mw.txt in "
                              "this script's own directory, whichever exist.")
    parser.add_argument("--kanda-name", default=None,
                         help="Optional display name for the kanda, e.g. "
                              "'बाल-काण्डः' (defaults to the kanda number)")
    parser.add_argument("--template", default=None,
                         help="Path to comprehensive-10-component-template.json "
                              "(default: same file in this script's directory, "
                              "if present) -- used only to upgrade components "
                              "1/8/9 to verified content for exemplar verses.")

    args = parser.parse_args()

    if args.verse_start > args.verse_end:
        sys.exit("--verse-start must be <= --verse-end")

    # --- resolve dictionary files -------------------------------------
    cdsl_paths = args.cdsl
    if not cdsl_paths:
        cdsl_paths = [str(p) for p in
                      (SCRIPT_DIR / "ap90.txt", SCRIPT_DIR / "mw.txt")
                      if p.exists()]
        if not cdsl_paths:
            sys.exit("No dictionary files found. Pass --cdsl ap90.txt mw.txt "
                      "(or wherever you keep them).")
    print(f"[dictionaries: {', '.join(cdsl_paths)}]", file=sys.stderr)

    # --- resolve template (verified-exemplar) file --------------------
    template_path = args.template
    if template_path is None:
        default_tmpl = SCRIPT_DIR / "comprehensive-10-component-template.json"
        template_path = str(default_tmpl) if default_tmpl.exists() else None
    template_overrides = load_template_overrides(template_path)
    if template_overrides:
        print(f"[verified exemplar data available for: "
              f"{', '.join(template_overrides.keys())}]", file=sys.stderr)

    # --- load the requested verses -------------------------------------
    verses = load_verses(args.source, args.source_type, args.kanda, args.sarga,
                          args.verse_start, args.verse_end)
    if not verses:
        sys.exit("No verses matched the given source/kanda/sarga/verse-range.")
    print(f"[loaded {len(verses)} verse(s): "
          f"{', '.join('.'.join(map(str, k)) for k in sorted(verses.keys()))}]",
          file=sys.stderr)

    # --- build the engine and load dictionaries -------------------------
    sp = ss.SamasaSplitter()
    n = sp.load_cdsl_dictionaries(cdsl_paths)
    print(f"[loaded {n} unique stems]", file=sys.stderr)
    nr = sp.load_verb_roots(cdsl_paths)
    print(f"[loaded {nr} verified verb roots]", file=sys.stderr)
    nn = sp.load_proper_nouns(cdsl_paths)
    print(f"[loaded {nn} proper-noun entries]", file=sys.stderr)
    nc = sp.load_compound_headwords(cdsl_paths)
    print(f"[loaded {nc} documented-compound headwords]", file=sys.stderr)
    ng = sp.load_glosses(cdsl_paths)
    print(f"[loaded {ng} glosses]", file=sys.stderr)

    # --- run the sandhi/samasa/karaka/pratyaya engine --------------------
    report, _stats = ss.analyze_verse_corpus(sp, verses, mode="both")

    # --- assemble the final combined document --------------------------
    combined = {
        "note": "Generated by generate_treatise.py. Components 1/4/7/8/9 are "
                "mechanically derived (samasa_splitter.py's engine, "
                "dictionary-checked); components 2/3/5/6/10 are hand-authored "
                "(manual_grammar_data.py) where available, else a labeled "
                "skeleton (Component 10 falls back to automatic meter ID via "
                "'chanda' if installed); components 1/8/9 are upgraded to "
                "verified exemplar content where the template file covers "
                "this exact verse. All grammatical content is rendered in "
                "Sanskrit; only word/verse meanings and the 'confidence' "
                "field remain in English.",
        "source": str(args.source),
        "source_type": (args.source_type if args.source_type != "auto"
                         else detect_source_type(args.source)),
        "kanda": args.kanda,
        "sarga": args.sarga,
        "verse_range": [args.verse_start, args.verse_end],
        "shlokas": [],
    }
    for v in report:
        k, s, sh = map(int, v["verse"].split("."))
        print(f"[processing verse {v['verse']}]", file=sys.stderr)
        doc = merged_verse_json(
            sp, (k, s, sh), v["lines"],
            {"number": sh, "kanda_name": args.kanda_name or (str(k) if k else "")},
            template_overrides)
        doc = sanskritize_doc(doc)
        combined["shlokas"].append(doc)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"[wrote {out_path} -- {len(combined['shlokas'])} shloka(s)]", file=sys.stderr)

    # --- friendly console summary ---------------------------------------
    print("\n=== Summary ===")
    for doc in combined["shlokas"]:
        meta = doc["shloka_metadata"]
        print(f"  {meta['id']}: {meta.get('manual_content_status', '?')}"
              + ("  [verified exemplar]" if meta.get("verified_exemplar") else ""))
        print(f"      translation: {meta.get('translation_en', '')}")


if __name__ == "__main__":
    main()
