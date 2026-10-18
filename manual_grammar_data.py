"""
manual_grammar_data.py
======================
Hand-authored content for the components build_grammar_json.py cannot
mechanically derive: COMPONENT_2 (anvaya), COMPONENT_3 (full pada-vigraha
prose), COMPONENT_5 (declension paradigms), COMPONENT_6 (verb conjugation),
and COMPONENT_10 (chandas/alankara). Declension/conjugation paradigms are
given in IAST (matching this project's working convention throughout);
Tamil fields are left blank rather than machine-translated, since
translation quality here needs a human reviewer, not a rushed guess.

Organized as one dict per verse, keyed by verse id ("1.1.1" etc.), merged
into the auto-generated JSON by combine_grammar_json.py.
"""

# --------------------------------------------------------------------------- #
# Reusable declension paradigms (IAST). Each function takes the STEM (the
# citation form minus its class-marking final vowel/consonant, as noted)
# and returns a standard 7-case x 3-number table. These are fixed,
# regular paradigms -- correct for any noun of that class, not derived
# per-word.
# --------------------------------------------------------------------------- #
HEADERS = ["vibhakti", "singular", "dual", "plural"]
CASE_NAMES = ["prathamā (nom.)", "dvitīyā (acc.)", "tṛtīyā (instr.)",
              "caturthī (dat.)", "pañcamī (abl.)", "ṣaṣṭhī (gen.)",
              "saptamī (loc.)"]


def a_stem_masc(stem):
    """stem = citation form minus final -a, e.g. "vara" -> "var"."""
    end = [
        ("aḥ", "au", "āḥ"), ("am", "au", "ān"), ("ena", "ābhyām", "aiḥ"),
        ("āya", "ābhyām", "ebhyaḥ"), ("āt", "ābhyām", "ebhyaḥ"),
        ("asya", "ayoḥ", "ānām"), ("e", "ayoḥ", "eṣu"),
    ]
    return {"headers": HEADERS,
            "rows": [[c] + [stem + e for e in row] for c, row in zip(CASE_NAMES, end)]}


def a_stem_neut(stem):
    end = [
        ("am", "e", "āni"), ("am", "e", "āni"), ("ena", "ābhyām", "aiḥ"),
        ("āya", "ābhyām", "ebhyaḥ"), ("āt", "ābhyām", "ebhyaḥ"),
        ("asya", "ayoḥ", "ānām"), ("e", "ayoḥ", "eṣu"),
    ]
    return {"headers": HEADERS,
            "rows": [[c] + [stem + e for e in row] for c, row in zip(CASE_NAMES, end)]}


def i_stem_masc(stem):
    """stem minus final -i, e.g. "vālmīki" -> "vālmīk"."""
    end = [
        ("iḥ", "ī", "ayaḥ"), ("im", "ī", "īn"), ("inā", "ibhyām", "ibhiḥ"),
        ("aye", "ibhyām", "ibhyaḥ"), ("eḥ", "ibhyām", "ibhyaḥ"),
        ("eḥ", "yoḥ", "īnām"), ("au", "yoḥ", "iṣu"),
    ]
    return {"headers": HEADERS,
            "rows": [[c] + [stem + e for e in row] for c, row in zip(CASE_NAMES, end)]}


def in_stem_masc(stem):
    """stem = citation form minus final -in, e.g. "tapasvin" -> "tapasv"."""
    end = [
        ("ī", "inau", "inaḥ"), ("inam", "inau", "inaḥ"),
        ("inā", "ibhyām", "ibhiḥ"), ("ine", "ibhyām", "ibhyaḥ"),
        ("inaḥ", "ibhyām", "ibhyaḥ"), ("inaḥ", "inoḥ", "inām"),
        ("ini", "inoḥ", "iṣu"),
    ]
    return {"headers": HEADERS,
            "rows": [[c] + [stem + e for e in row] for c, row in zip(CASE_NAMES, end)]}


def vat_mat_stem_masc(stem, allomorph):
    """stem = citation form minus final -vat/-mat, e.g. "guṇavat" -> "guṇa".
    allomorph is "vat" or "mat". These stems alternate between a STRONG
    grade (-vant-/-mant-, used in nom./acc.) and a WEAK grade (-vat-/-mat-,
    used elsewhere), with t->d voicing before the voiced -bhyām/-bhiḥ
    endings but not before voiceless -su (hence "-vatsu", not "-vadsu")."""
    v = allomorph                 # "vat" or "mat"
    first = v[0]                  # "v" or "m"
    vant = first + "ant"          # "vant" or "mant" (strong grade)
    voiced = v[:-1] + "d"          # "vad" or "mad" (weak grade, voiced before bh)
    end = [
        (f"{first}ān", f"{vant}au", f"{vant}aḥ"),
        (f"{vant}am", f"{vant}au", f"{v}aḥ"),
        (f"{v}ā", f"{voiced}bhyām", f"{voiced}bhiḥ"),
        (f"{v}e", f"{voiced}bhyām", f"{voiced}bhyaḥ"),
        (f"{v}aḥ", f"{voiced}bhyām", f"{voiced}bhyaḥ"),
        (f"{v}aḥ", f"{v}oḥ", f"{v}ām"),
        (f"{v}i", f"{v}oḥ", f"{v}su"),
    ]
    return {"headers": HEADERS,
            "rows": [[c] + [stem + e for e in row] for c, row in zip(CASE_NAMES, end)]}


PRONOUN_KIM = {
    "headers": HEADERS,
    "rows": [
        ["prathamā (nom.)", "kaḥ", "kau", "ke"],
        ["dvitīyā (acc.)", "kam", "kau", "kān"],
        ["tṛtīyā (instr.)", "kena", "kābhyām", "kaiḥ"],
        ["caturthī (dat.)", "kasmai", "kābhyām", "kebhyaḥ"],
        ["pañcamī (abl.)", "kasmāt", "kābhyām", "kebhyaḥ"],
        ["ṣaṣṭhī (gen.)", "kasya", "kayoḥ", "keṣām"],
        ["saptamī (loc.)", "kasmin", "kayoḥ", "keṣu"],
    ],
    "note": "masculine forms shown (the verse uses kaḥ throughout, "
            "interrogative pronoun agreeing with an unstated masc. referent)",
}

PRONOUN_IDAM_MASC = {
    "headers": HEADERS,
    "rows": [
        ["prathamā (nom.)", "ayam", "imau", "ime"],
        ["dvitīyā (acc.)", "imam", "imau", "imān"],
        ["tṛtīyā (instr.)", "anena", "ābhyām", "ebhiḥ"],
        ["caturthī (dat.)", "asmai", "ābhyām", "ebhyaḥ"],
        ["pañcamī (abl.)", "asmāt", "ābhyām", "ebhyaḥ"],
        ["ṣaṣṭhī (gen.)", "asya", "anayoḥ", "eṣām"],
        ["saptamī (loc.)", "asmin", "anayoḥ", "eṣu"],
    ],
}

PRONOUN_AHAM = {
    "headers": HEADERS,
    "rows": [
        ["prathamā (nom.)", "aham", "āvām", "vayam"],
        ["dvitīyā (acc.)", "mām / mā", "āvām / nau", "asmān / naḥ"],
        ["tṛtīyā (instr.)", "mayā", "āvābhyām", "asmābhiḥ"],
        ["caturthī (dat.)", "mahyam / me", "āvābhyām / nau", "asmabhyam / naḥ"],
        ["pañcamī (abl.)", "mat", "āvābhyām", "asmat"],
        ["ṣaṣṭhī (gen.)", "mama / me", "āvayoḥ / nau", "asmākam / naḥ"],
        ["saptamī (loc.)", "mayi", "āvayoḥ", "asmāsu"],
    ],
}

PRONOUN_TVAD = {
    "headers": HEADERS,
    "rows": [
        ["prathamā (nom.)", "tvam", "yuvām", "yūyam"],
        ["dvitīyā (acc.)", "tvām / tvā", "yuvām / vām", "yuṣmān / vaḥ"],
        ["tṛtīyā (instr.)", "tvayā", "yuvābhyām", "yuṣmābhiḥ"],
        ["caturthī (dat.)", "tubhyam / te", "yuvābhyām / vām", "yuṣmabhyam / vaḥ"],
        ["pañcamī (abl.)", "tvat", "yuvābhyām", "yuṣmat"],
        ["ṣaṣṭhī (gen.)", "tava / te", "yuvayoḥ / vām", "yuṣmākam / vaḥ"],
        ["saptamī (loc.)", "tvayi", "yuvayoḥ", "yuṣmāsu"],
    ],
}


def dhatu_table(rows_dict):
    return {"headers": ["puruṣa", "singular", "dual", "plural"],
            "rows": [[p] + list(v) for p, v in rows_dict.items()]}


PRACH_PERFECT = dhatu_table({
    "prathama (3rd)": ("papraccha", "papracchatuḥ", "papracchuḥ"),
    "madhyama (2nd)": ("papracchitha / papraṣṭha", "papracchathuḥ", "papraccha"),
    "uttama (1st)": ("papraccha", "papracchiva", "papracchima"),
})

AS_PRESENT = dhatu_table({
    "prathama (3rd)": ("asti", "staḥ", "santi"),
    "madhyama (2nd)": ("asi", "sthaḥ", "stha"),
    "uttama (1st)": ("asmi", "svaḥ", "smaḥ"),
})

ISH_PRESENT = dhatu_table({
    "prathama (3rd)": ("icchati", "icchataḥ", "icchanti"),
    "madhyama (2nd)": ("icchasi", "icchathaḥ", "icchatha"),
    "uttama (1st)": ("icchāmi", "icchāvaḥ", "icchāmaḥ"),
})

BHI_PRESENT = dhatu_table({
    "prathama (3rd)": ("bibheti", "bibhītaḥ", "bibhyati"),
    "madhyama (2nd)": ("bibheṣi", "bibhīthaḥ", "bibhītha"),
    "uttama (1st)": ("bibhemi", "bibhīvaḥ", "bibhīmaḥ"),
})


MANUAL_DATA = {}

# ============================================================ 1.1.1 ===== #
MANUAL_DATA["1.1.1"] = {
    "anvaya": {
        "sa": "vālmīkiḥ tapasvī tapaḥsvādhyāyanirataṃ vāgvidāṃ varaṃ "
              "munipuṅgavaṃ nāradaṃ paripapraccha.",
        "en": "The ascetic Vālmīki asked Nārada -- who was absorbed in "
              "austerity and Vedic study, the best among the eloquent, "
              "and foremost among sages -- [the question that follows].",
    },
    "pada_vigraha": [
        {"word": "tapaḥsvādhyāyanirataṃ", "pos": "adjective (compound)",
         "gender": "masc", "number": "sg", "case": "accusative",
         "meaning": "absorbed in penance and Vedic self-study",
         "etymology": "tapas + svādhyāya (dvandva) + nirata (ni+ram, kta) "
                       "-- saptamī-tatpuruṣa", "role": "qualifies nāradam"},
        {"word": "tapasvī", "pos": "noun/adjective", "gender": "masc",
         "number": "sg", "case": "nominative",
         "meaning": "the ascetic, one devoted to penance",
         "etymology": "tapas + in (possessive taddhita)",
         "role": "qualifies vālmīkiḥ (karta)"},
        {"word": "vāgvidāṃ", "pos": "noun (compound)", "gender": "masc",
         "number": "pl", "case": "genitive",
         "meaning": "of those who know/master speech",
         "etymology": "vāc + vid (kvip) -- upapada-tatpuruṣa; c->g jaṣtva",
         "role": "sambandha, qualifies varam"},
        {"word": "varam", "pos": "adjective", "gender": "masc",
         "number": "sg", "case": "accusative", "meaning": "the best, foremost",
         "etymology": "√vṛ + ap", "role": "qualifies nāradam"},
        {"word": "nāradaṃ", "pos": "proper noun", "gender": "masc",
         "number": "sg", "case": "accusative", "meaning": "Nārada",
         "etymology": "nārada (rūḍha) + am", "role": "karma"},
        {"word": "paripapraccha", "pos": "verb", "gender": "-", "number": "sg",
         "case": "-", "meaning": "asked",
         "etymology": "pari + √prach, liṭ (perfect) 3sg parasmaipada",
         "role": "kriyā"},
        {"word": "vālmīkiḥ", "pos": "proper noun", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "Vālmīki",
         "etymology": "vālmīki + su", "role": "karta"},
        {"word": "munipuṅgavam", "pos": "noun (compound)", "gender": "masc",
         "number": "sg", "case": "accusative",
         "meaning": "foremost among sages (lit. 'bull among sages')",
         "etymology": "muni + puṅgava -- ṣaṣṭhī-tatpuruṣa w/ embedded upamā",
         "role": "qualifies nāradam"},
    ],
    "shabdarupani": {
        "tapahsvadhyayanirata": {"lemma": "tapaḥsvādhyāyanirata",
                                  "gender": "masc/neut adj.",
                                  "declension_table": a_stem_masc("tapaḥsvādhyāyanirat")},
        "tapasvin": {"lemma": "tapasvin", "gender": "masc",
                     "declension_table": in_stem_masc("tapasv")},
        "vara": {"lemma": "vara", "gender": "masc",
                 "declension_table": a_stem_masc("var")},
        "narada": {"lemma": "nārada", "gender": "masc",
                   "declension_table": a_stem_masc("nārad")},
        "valmiki": {"lemma": "vālmīki", "gender": "masc",
                    "declension_table": i_stem_masc("vālmīk")},
        "munipungava": {"lemma": "munipuṅgava", "gender": "masc",
                         "declension_table": a_stem_masc("munipuṅgav")},
        "note": "vāgvid (consonant/d-stem) omitted from this generator set -- "
                "irregular root-noun declension (nom.sg. vāgvit via cartva, "
                "governed by the root vid- 'know', not a fixed-vowel-stem "
                "pattern) -- needs its own hand-checked table, not one of "
                "the generic paradigms above.",
    },
    "dhaturupani": {
        "root": "prach", "gana": "6 (tudādi)", "lakara": "liṭ (perfect)",
        "form": "paripapraccha = pari + papraccha, 3rd sg. parasmaipada",
        "conjugation": PRACH_PERFECT,
    },
    "chandas": {
        "name": "anuṣṭubh", "scansion": [
            {"quarter": 1, "text": "tapaḥ svādhyāyanirataṃ", "matra": 8},
            {"quarter": 2, "text": "tapasvī vāgvidāṃ varam", "matra": 8},
            {"quarter": 3, "text": "nāradaṃ paripapraccha", "matra": 8},
            {"quarter": 4, "text": "vālmīkir munipuṅgavam", "matra": 8},
        ],
        "alankara": [
            {"name": "svabhāvokti", "definition": "plain, unadorned narration -- the verse's overall style"},
            {"name": "rūpaka (minor, embedded)", "definition": "munipuṅgavam figures the sage as a bull among sages"},
        ],
    },
}

# ============================================================ 1.1.2 ===== #
MANUAL_DATA["1.1.2"] = {
    "anvaya": {
        "sa": "asmin loke sāmprataṃ kaḥ nu guṇavān, kaḥ ca vīryavān, "
              "dharmajñaḥ ca kṛtajñaḥ ca, satyavākyaḥ dṛḍhavrataḥ ca (asti)?",
        "en": "Who indeed is there now, in this world, who is virtuous and "
              "mighty, who knows dharma and is grateful, whose word is "
              "true and whose vow is firm?",
    },
    "pada_vigraha": [
        {"word": "kaḥ", "pos": "interrogative pronoun", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "who",
         "etymology": "kim + su (masc.)", "role": "karta (implied 'asti')"},
        {"word": "nu", "pos": "indeclinable particle", "gender": "-",
         "number": "-", "case": "-", "meaning": "indeed, pray",
         "etymology": "unanalyzable particle", "role": "emphasis"},
        {"word": "asmin", "pos": "pronoun (idam)", "gender": "masc/neut",
         "number": "sg", "case": "locative", "meaning": "in this",
         "etymology": "idam, loc.sg.", "role": "adhikaraṇa, qualifies loke"},
        {"word": "sāmprataṃ", "pos": "indeclinable (adverb)", "gender": "-",
         "number": "-", "case": "-", "meaning": "now, at present",
         "etymology": "sam+pra+√ap, taddhita -tana, used adverbially",
         "role": "kālavācaka (time adverb) -- NOT an accusative object, "
                 "despite the -am ending coincidentally matching one"},
        {"word": "loke", "pos": "noun", "gender": "masc", "number": "sg",
         "case": "locative", "meaning": "in the world",
         "etymology": "loka + i (loc.sg.)", "role": "adhikaraṇa"},
        {"word": "guṇavān", "pos": "adjective (matup)", "gender": "masc",
         "number": "sg", "case": "nominative",
         "meaning": "possessing good qualities, virtuous",
         "etymology": "guṇa + vat (matup)", "role": "viśeṣaṇam of kaḥ"},
        {"word": "vīryavān", "pos": "adjective (matup)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "mighty, powerful",
         "etymology": "vīrya + vat (matup)", "role": "viśeṣaṇam of kaḥ"},
        {"word": "dharmajñaḥ", "pos": "noun (compound)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "knowing dharma",
         "etymology": "dharma + jña (upapada, dvitīyā-tatpuruṣa)",
         "role": "viśeṣaṇam of kaḥ"},
        {"word": "kṛtajñaḥ", "pos": "noun (compound)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "grateful",
         "etymology": "kṛta + jña (upapada, dvitīyā-tatpuruṣa)",
         "role": "viśeṣaṇam of kaḥ"},
        {"word": "satyavākyaḥ", "pos": "adjective (compound)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "true-speeched",
         "etymology": "satya + vākya (karmadhāraya, bahuvrīhi as a whole)",
         "role": "viśeṣaṇam of kaḥ"},
        {"word": "dṛḍhavrataḥ", "pos": "adjective (compound)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "firm-vowed",
         "etymology": "dṛḍha + vrata (karmadhāraya, bahuvrīhi as a whole)",
         "role": "viśeṣaṇam of kaḥ"},
    ],
    "shabdarupani": {
        "kim": {"lemma": "kim", "gender": "masc (interrogative pronoun)",
                "declension_table": PRONOUN_KIM},
        "idam": {"lemma": "idam", "gender": "masc",
                 "declension_table": PRONOUN_IDAM_MASC},
        "loka": {"lemma": "loka", "gender": "masc",
                 "declension_table": a_stem_masc("lok")},
        "guna_vat": {"lemma": "guṇavat", "gender": "masc",
                     "declension_table": vat_mat_stem_masc("guṇa", "vat")},
        "virya_vat": {"lemma": "vīryavat", "gender": "masc",
                      "declension_table": vat_mat_stem_masc("vīrya", "vat")},
        "dharmajna": {"lemma": "dharmajña", "gender": "masc",
                      "declension_table": a_stem_masc("dharmajñ")},
        "kritajna": {"lemma": "kṛtajña", "gender": "masc",
                     "declension_table": a_stem_masc("kṛtajñ")},
        "satyavakya": {"lemma": "satyavākya", "gender": "masc",
                       "declension_table": a_stem_masc("satyavāky")},
        "dridhavrata": {"lemma": "dṛḍhavrata", "gender": "masc",
                        "declension_table": a_stem_masc("dṛḍhavrat")},
    },
    "dhaturupani": {
        "note": "No overt finite verb in this verse -- an elliptical "
                "existential 'asti' (is there) is understood, governing "
                "the string of nominative predicate-adjectives. See "
                "COMPONENT_6 of 1.1.5 for the paradigm of √as."
    },
    "chandas": {
        "name": "anuṣṭubh", "scansion": [
            {"quarter": 1, "text": "ko nv asmin sāmprataṃ loke", "matra": 8},
            {"quarter": 2, "text": "guṇavān kaś ca vīryavān", "matra": 8},
            {"quarter": 3, "text": "dharmajñaś ca kṛtajñaś ca", "matra": 8},
            {"quarter": 4, "text": "satyavākyo dṛḍhavrataḥ", "matra": 8},
        ],
        "alankara": [
            {"name": "praśna (rhetorical question, not a formal alaṅkāra "
                      "but the verse's organizing device)",
             "definition": "the first of a chain of questions Vālmīki puts "
                            "to Nārada, continuing through 1.1.4"},
        ],
    },
}

# ============================================================ 1.1.3 ===== #
MANUAL_DATA["1.1.3"] = {
    "anvaya": {
        "sa": "cāritreṇa ca kaḥ yuktaḥ, sarvabhūteṣu kaḥ hitaḥ, kaḥ vidvān, "
              "kaḥ samarthaḥ ca, kaḥ ca eka-priyadarśanaḥ (asti)?",
        "en": "Who is disciplined in conduct? Who is beneficial to all "
              "beings? Who is learned? Who is capable? And who alone is "
              "pleasant to behold?",
    },
    "pada_vigraha": [
        {"word": "cāritreṇa", "pos": "noun", "gender": "neut", "number": "sg",
         "case": "instrumental", "meaning": "by/in conduct",
         "etymology": "caritra + ā (taddhita) + inā", "role": "karaṇa"},
        {"word": "ca", "pos": "indeclinable", "gender": "-", "number": "-",
         "case": "-", "meaning": "and", "etymology": "particle", "role": "conjunction"},
        {"word": "kaḥ", "pos": "interrogative pronoun", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "who",
         "etymology": "kim + su", "role": "karta (implied 'asti'), repeated 5x"},
        {"word": "yuktaḥ", "pos": "adjective", "gender": "masc", "number": "sg",
         "case": "nominative", "meaning": "disciplined, endowed",
         "etymology": "√yuj + kta", "role": "viśeṣaṇam of kaḥ"},
        {"word": "sarvabhūteṣu", "pos": "noun (compound)", "gender": "neut",
         "number": "pl", "case": "locative", "meaning": "among all beings",
         "etymology": "sarva + bhūta (karmadhāraya)", "role": "adhikaraṇa"},
        {"word": "hitaḥ", "pos": "adjective", "gender": "masc", "number": "sg",
         "case": "nominative", "meaning": "beneficial",
         "etymology": "√dhā (dhi) + kta", "role": "viśeṣaṇam of kaḥ"},
        {"word": "vidvān", "pos": "participle (kvasu)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "learned, knowing",
         "etymology": "√vid + vas (kvasu-pratyaya, perfect active "
                       "participle) -- NOT the matup vat/mat suffix, "
                       "despite the surface resemblance to 'X-vān' words "
                       "elsewhere in this verse-set",
         "role": "viśeṣaṇam of kaḥ"},
        {"word": "samarthaḥ", "pos": "adjective", "gender": "masc", "number": "sg",
         "case": "nominative", "meaning": "capable",
         "etymology": "sam + √arth + a", "role": "viśeṣaṇam of kaḥ"},
        {"word": "ekapriyadarśanaḥ", "pos": "adjective (compound)", "gender": "masc",
         "number": "sg", "case": "nominative",
         "meaning": "alone pleasant to behold",
         "etymology": "eka + priya + darśana (karmadhāraya chain)",
         "role": "viśeṣaṇam of kaḥ"},
    ],
    "shabdarupani": {
        "caritra": {"lemma": "cāritra", "gender": "neut",
                    "declension_table": a_stem_neut("cāritr")},
        "yukta": {"lemma": "yukta", "gender": "masc",
                  "declension_table": a_stem_masc("yukt")},
        "sarvabhuta": {"lemma": "sarvabhūta", "gender": "neut",
                       "declension_table": a_stem_neut("sarvabhūt")},
        "hita": {"lemma": "hita", "gender": "masc",
                 "declension_table": a_stem_masc("hit")},
        "samartha": {"lemma": "samartha", "gender": "masc",
                     "declension_table": a_stem_masc("samarth")},
        "ekapriyadarshana": {"lemma": "ekapriyadarśana", "gender": "masc",
                              "declension_table": a_stem_masc("ekapriyadarśan")},
        "note": "vidvān (vidvas-stem participle, kvasu) omitted from this "
                "generator set -- an irregular -vas/-vat consonant-stem "
                "participle paradigm distinct from both the a-stem and "
                "matup patterns above; needs its own hand-checked table.",
    },
    "dhaturupani": {
        "note": "No overt finite verb -- same elliptical 'asti' as 1.1.2. "
                "vidvān is a participle (see pada_vigraha), not a finite form."
    },
    "chandas": {
        "name": "anuṣṭubh", "scansion": [
            {"quarter": 1, "text": "cāritreṇa ca ko yuktaḥ", "matra": 8},
            {"quarter": 2, "text": "sarvabhūteṣu ko hitaḥ", "matra": 8},
            {"quarter": 3, "text": "vidvān kaḥ kaḥ samarthaś ca", "matra": 8},
            {"quarter": 4, "text": "kaś caikapriyadarśanaḥ", "matra": 8},
        ],
        "alankara": [
            {"name": "praśna (continued)",
             "definition": "second verse of the question-chain begun in 1.1.2"},
        ],
    },
}

# ============================================================ 1.1.4 ===== #
MANUAL_DATA["1.1.4"] = {
    "anvaya": {
        "sa": "kaḥ ātmavān, kaḥ jitakrodhaḥ, kaḥ matimān, kaḥ anasūyakaḥ, "
              "kasya jātaroṣasya saṃyuge devāḥ ca bibhyati (asti)?",
        "en": "Who is self-controlled? Who has conquered anger? Who is "
              "wise? Who is free of envy? Of whose aroused wrath do even "
              "the gods stand in fear in battle?",
    },
    "pada_vigraha": [
        {"word": "ātmavān", "pos": "adjective (matup)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "self-controlled",
         "etymology": "ātma(n) + vat (matup)", "role": "viśeṣaṇam of kaḥ"},
        {"word": "kaḥ", "pos": "interrogative pronoun", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "who",
         "etymology": "kim + su", "role": "karta (implied 'asti'), repeated 3x"},
        {"word": "jitakrodhaḥ", "pos": "adjective (compound, bahuvrīhi)",
         "gender": "masc", "number": "sg", "case": "nominative",
         "meaning": "one who has conquered anger",
         "etymology": "jita + krodha", "role": "viśeṣaṇam of kaḥ"},
        {"word": "matimān", "pos": "adjective (matup)", "gender": "masc",
         "number": "sg", "case": "nominative", "meaning": "wise, intelligent",
         "etymology": "mati + mat (matup)", "role": "viśeṣaṇam of kaḥ"},
        {"word": "anasūyakaḥ", "pos": "adjective (compound, nañ-tatpuruṣa)",
         "gender": "masc", "number": "sg", "case": "nominative",
         "meaning": "not envious, free of fault-finding",
         "etymology": "an (nañ) + asūyaka", "role": "viśeṣaṇam of kaḥ"},
        {"word": "kasya", "pos": "interrogative pronoun", "gender": "masc",
         "number": "sg", "case": "genitive", "meaning": "of whom",
         "etymology": "kim, gen.sg.", "role": "sambandha, qualifies jātaroṣasya"},
        {"word": "bibhyati", "pos": "verb", "gender": "-", "number": "pl",
         "case": "-", "meaning": "fear, are afraid",
         "etymology": "√bhī, laṭ (present) 3rd pl. parasmaipada", "role": "kriyā"},
        {"word": "devāḥ", "pos": "noun", "gender": "masc", "number": "pl",
         "case": "nominative", "meaning": "the gods",
         "etymology": "deva + jas (nom.pl.)", "role": "karta"},
        {"word": "jātaroṣasya", "pos": "adjective (compound)", "gender": "masc",
         "number": "sg", "case": "genitive",
         "meaning": "of one whose wrath is aroused",
         "etymology": "jāta + roṣa (bahuvrīhi)", "role": "qualifies kasya"},
        {"word": "saṃyuge", "pos": "noun", "gender": "neut/masc", "number": "sg",
         "case": "locative", "meaning": "in battle",
         "etymology": "sam + √yuj + a, loc.sg.", "role": "adhikaraṇa"},
    ],
    "shabdarupani": {
        "atma_vat": {"lemma": "ātmavat", "gender": "masc",
                     "declension_table": vat_mat_stem_masc("ātma", "vat")},
        "jitakrodha": {"lemma": "jitakrodha", "gender": "masc",
                       "declension_table": a_stem_masc("jitakrodh")},
        "mati_mat": {"lemma": "matimat", "gender": "masc",
                     "declension_table": vat_mat_stem_masc("mati", "mat")},
        "anasuyaka": {"lemma": "anasūyaka", "gender": "masc",
                      "declension_table": a_stem_masc("anasūyak")},
        "kim": {"lemma": "kim", "gender": "masc", "declension_table": PRONOUN_KIM},
        "deva": {"lemma": "deva", "gender": "masc",
                 "declension_table": a_stem_masc("dev")},
        "jataarosha": {"lemma": "jātaroṣa", "gender": "masc",
                       "declension_table": a_stem_masc("jātaroṣ")},
        "samyuga": {"lemma": "saṃyuga", "gender": "neut",
                    "declension_table": a_stem_neut("saṃyug")},
    },
    "dhaturupani": {
        "root": "bhī", "gana": "3 (juhotyādi/reduplicating class)",
        "lakara": "laṭ (present)",
        "form": "bibhyati = √bhī, 3rd pl. parasmaipada",
        "conjugation": BHI_PRESENT,
    },
    "chandas": {
        "name": "anuṣṭubh", "scansion": [
            {"quarter": 1, "text": "ātmavān ko jitakrodho", "matra": 8},
            {"quarter": 2, "text": "matimān ko 'nasūyakaḥ", "matra": 8},
            {"quarter": 3, "text": "kasya bibhyati devāś ca", "matra": 8},
            {"quarter": 4, "text": "jātaroṣasya saṃyuge", "matra": 8},
        ],
        "alankara": [
            {"name": "praśna (concludes the question-chain)",
             "definition": "final verse of questions begun in 1.1.2, "
                            "culminating in the vivid image of even gods "
                            "fearing this person's wrath in battle "
                            "(ativāda/atiśayokti -- hyperbolic praise)"},
            {"name": "atiśayoktiḥ", "definition": "hyperbole -- that even "
                      "the devas themselves fear this person's anger"},
        ],
    },
}

# ============================================================ 1.1.5 ===== #
MANUAL_DATA["1.1.5"] = {
    "anvaya": {
        "sa": "he maharṣe, etat śrotum ahaṃ paraṃ kautūhalaṃ (icchāmi), me "
              "hi (kautūhalam asti); tvaṃ evaṃvidhaṃ naraṃ jñātuṃ samarthaḥ asi.",
        "en": "O great sage, I wish to hear this -- for I have great "
              "curiosity; you indeed are capable of knowing of such a man.",
    },
    "pada_vigraha": [
        {"word": "etat", "pos": "pronoun (etad)", "gender": "neut",
         "number": "sg", "case": "accusative", "meaning": "this",
         "etymology": "etad, acc.sg.neut.", "role": "karma of icchāmi/śrotum"},
        {"word": "icchāmi", "pos": "verb", "gender": "-", "number": "sg",
         "case": "-", "meaning": "I wish/desire",
         "etymology": "√iṣ, laṭ (present) 1st sg. parasmaipada", "role": "kriyā"},
        {"word": "ahaṃ", "pos": "pronoun (aham)", "gender": "-", "number": "sg",
         "case": "nominative", "meaning": "I", "etymology": "aham, nom.sg.",
         "role": "karta"},
        {"word": "śrotuṃ", "pos": "infinitive", "gender": "-", "number": "-",
         "case": "-", "meaning": "to hear",
         "etymology": "√śru + tumun", "role": "purpose, complements icchāmi"},
        {"word": "paraṃ", "pos": "adjective", "gender": "neut", "number": "sg",
         "case": "accusative", "meaning": "great, supreme",
         "etymology": "para + am", "role": "qualifies kautūhalam"},
        {"word": "kautūhalaṃ", "pos": "noun", "gender": "neut", "number": "sg",
         "case": "accusative", "meaning": "curiosity",
         "etymology": "kutūhala + taddhita vṛddhi + am", "role": "karma"},
        {"word": "hi", "pos": "indeclinable", "gender": "-", "number": "-",
         "case": "-", "meaning": "indeed, for", "etymology": "particle",
         "role": "emphasis/causal connective"},
        {"word": "me", "pos": "pronoun (aham, enclitic)", "gender": "-",
         "number": "sg", "case": "genitive", "meaning": "my, of me",
         "etymology": "aham, gen.sg. enclitic", "role": "sambandha"},
        {"word": "maharṣe", "pos": "noun (compound)", "gender": "masc",
         "number": "sg", "case": "vocative", "meaning": "O great sage",
         "etymology": "mahā + ṛṣi (karmadhāraya)", "role": "sambodhana (address)"},
        {"word": "tvaṃ", "pos": "pronoun (tvad)", "gender": "-", "number": "sg",
         "case": "nominative", "meaning": "you", "etymology": "tvad, nom.sg.",
         "role": "karta"},
        {"word": "samarthaḥ", "pos": "adjective", "gender": "masc", "number": "sg",
         "case": "nominative", "meaning": "capable",
         "etymology": "sam + √arth + a", "role": "predicate, qualifies tvam"},
        {"word": "asi", "pos": "verb", "gender": "-", "number": "sg",
         "case": "-", "meaning": "you are",
         "etymology": "√as, laṭ (present) 2nd sg. parasmaipada", "role": "kriyā"},
        {"word": "jñātuṃ", "pos": "infinitive", "gender": "-", "number": "-",
         "case": "-", "meaning": "to know",
         "etymology": "√jñā + tumun", "role": "complements samarthaḥ asi"},
        {"word": "evaṃvidhaṃ", "pos": "adjective (compound)", "gender": "masc",
         "number": "sg", "case": "accusative", "meaning": "of such a kind",
         "etymology": "evam + vidha", "role": "qualifies naram"},
        {"word": "naram", "pos": "noun", "gender": "masc", "number": "sg",
         "case": "accusative", "meaning": "man",
         "etymology": "nara + am", "role": "karma of jñātum"},
    ],
    "shabdarupani": {
        "etad": {"lemma": "etad", "gender": "neut",
                 "declension_table": {
                     "headers": HEADERS,
                     "rows": [["prathamā (nom.)", "etat", "ete", "etāni"],
                              ["dvitīyā (acc.)", "etat", "ete", "etāni"],
                              ["tṛtīyā (instr.)", "etena", "etābhyām", "etaiḥ"],
                              ["caturthī (dat.)", "etasmai", "etābhyām", "etebhyaḥ"],
                              ["pañcamī (abl.)", "etasmāt", "etābhyām", "etebhyaḥ"],
                              ["ṣaṣṭhī (gen.)", "etasya", "etayoḥ", "eteṣām"],
                              ["saptamī (loc.)", "etasmin", "etayoḥ", "eteṣu"]],
                     "note": "neuter forms shown (etat qualifies an unstated "
                             "neuter referent, 'this [matter]')"}},
        "aham": {"lemma": "aham", "gender": "-", "declension_table": PRONOUN_AHAM},
        "tvad": {"lemma": "tvad", "gender": "-", "declension_table": PRONOUN_TVAD},
        "para": {"lemma": "para", "gender": "neut",
                 "declension_table": a_stem_neut("par")},
        "kautuhala": {"lemma": "kautūhala", "gender": "neut",
                      "declension_table": a_stem_neut("kautūhal")},
        "maharshi": {"lemma": "maharṣi", "gender": "masc",
                     "declension_table": i_stem_masc("maharṣ")},
        "samartha": {"lemma": "samartha", "gender": "masc",
                     "declension_table": a_stem_masc("samarth")},
        "evamvidha": {"lemma": "evaṃvidha", "gender": "masc",
                      "declension_table": a_stem_masc("evaṃvidh")},
        "nara": {"lemma": "nara", "gender": "masc",
                 "declension_table": a_stem_masc("nar")},
    },
    "dhaturupani": {
        "roots": [
            {"root": "iṣ", "gana": "6 (tudādi)", "lakara": "laṭ (present)",
             "form": "icchāmi = √iṣ, 1st sg. parasmaipada",
             "conjugation": ISH_PRESENT},
            {"root": "as", "gana": "2 (adādi)", "lakara": "laṭ (present)",
             "form": "asi = √as, 2nd sg. parasmaipada",
             "conjugation": AS_PRESENT},
        ],
        "note": "śrotum (√śru + tumun) and jñātum (√jñā + tumun) are "
                "infinitives, not finite forms -- no conjugation table "
                "applies; see COMPONENT_7 pratyaya for their derivation.",
    },
    "chandas": {
        "name": "anuṣṭubh", "scansion": [
            {"quarter": 1, "text": "etad icchāmy ahaṃ śrotuṃ", "matra": 8},
            {"quarter": 2, "text": "paraṃ kautūhalaṃ hi me", "matra": 8},
            {"quarter": 3, "text": "maharṣe tvaṃ samartho 'si", "matra": 8},
            {"quarter": 4, "text": "jñātum evaṃvidhaṃ naram", "matra": 8},
        ],
        "alankara": [
            {"name": "svabhāvokti", "definition": "plain first-person "
                      "statement of intent -- closes the frame Vālmīki "
                      "opened in 1.1.1, transitioning from the list of "
                      "questions (1.1.2-4) back to direct address of Nārada"},
        ],
    },
}
