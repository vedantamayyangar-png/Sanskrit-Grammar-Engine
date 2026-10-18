"""
compare_with_gold.py — score the local sandhi/samāsa/morphology tools against the hand-written
Sarga 1 analysis (working_files/d01.py … d08.py, 913 rows).

Inputs
  --system   JSON written by run_combined_splitter.py (per verse → per pāda-line → per GRETIL token)
  --gold     folder holding d01.py … d08.py, lib.py, translit.py, sarga1_iast.txt
  --morph    optional JSON written by run_morphology.py (guess_case / stem / verb / upasarga per token)
Outputs
  --out-md   human-readable scorecard + every disagreement, grouped by error class
  --out-json machine-readable per-token comparison (for tracking progress between runs)

The gold rows are one per *word*; GRETIL prints one token per *pada-as-printed*. The two are aligned
per verse by a small dynamic programme (1 token ↔ 1–3 gold words, or 2 tokens ↔ 1 word for
periphrastic «°याम् आस» and similar), scored on Devanagari similarity.
"""
import argparse, collections, difflib, importlib, json, os, re, sys

# ------------------------------------------------------------------ helpers
STRIP = re.compile(r"[ंःँ्ऽ\s]")


NASAL_BEFORE_CONS = re.compile(r"[ङञणनम]्(?=[क-ह])")


def skel(s):
    """Spelling-insensitive skeleton: anusvāra and a class nasal before a stop compare equal
    (पुंगव = पुङ्गव), and marks that sandhi changes (visarga, virama, avagraha) are ignored."""
    return STRIP.sub("", NASAL_BEFORE_CONS.sub("ं", s))


def sim(a, b):
    return difflib.SequenceMatcher(None, skel(a), skel(b)).ratio()


# gold junction rule → class   (order matters: most specific first)
GOLD_RULES = [
    ("अचि परे पदान्त-मकारः यथावत्", "none"),
    ("अवसाने", "none"),
    ("पदान्ते सन्धिः नास्ति", "none"),
    ("खरि च (चर्त्वम्)", "none"),
    ("नश्च / पदान्त-नकारः", "none"),
    ("दीर्घात् परस्य नकारस्य", "none"),
    ("दीर्घपूर्वकत्वात् ङमुडागमः न", "none"),
    ("अतो रोरप्लुतादप्लुते", "visarga→o+avagraha"),
    ("हशि च", "visarga→o"),
    ("विसर्जनीयस्य सः → स्तोः", "visarga→ś"),
    ("विसर्जनीयस्य सः", "visarga→s"),
    ("हलि सर्वेषाम्", "visarga-lopa (āḥ)"),
    ("भोभगोअघोअपूर्वस्य योऽशि → लोपः शाकल्यस्य (आः", "visarga-lopa (āḥ)"),
    ("लोपः शाकल्यस्य", "visarga-lopa (aḥ+vowel)"),
    ("एतत्तदोः सुलोपो", "sa-lopa"),
    ("खर्परे शरि वा विसर्गलोपो", "visarga-lopa (khar-para śar)"),
    ("ससजुषो रुः (", "visarga→r"),
    ("पुनर्-शब्दस्य रेफः", "visarga→r"),
    ("झयो होऽन्यतरस्याम्", "t+h→ddh"),
    ("यरोऽनुनासिके", "t→n (anunāsika)"),
    ("स्तोः श्चुना श्चुः", "ścutva"),
    ("झलां जशोऽन्ते", "jaśtva"),
    ("मोऽनुस्वारः", "anusvāra"),
    ("अकः सवर्णे दीर्घः", "savarṇa-dīrgha"),
    ("आद्गुणः", "guṇa"),
    ("वृद्धिरेचि", "vṛddhi"),
    ("इको यणचि", "yaṇ"),
    ("एङः पदान्तादति", "pūrvarūpa"),
    ("एचोऽयवायावः", "ayādi"),
    ("वा शरि", "visarga kept"),
    ("खरवसानयोर्विसर्जनीयः (क/प", "visarga kept"),
]
SYS_RULES = {
    "rutva-> utva-> guṇa-sandhiḥ": "visarga→o",
    "rutva -> utva-> guṇa-> pūrvarupa": "visarga→o+avagraha",
    "satva-> ścutva-sandhiḥ": "visarga→ś",
    "satva-sandhiḥ": "visarga→s",
    "repha-sandhiḥ": "visarga→r",
    "yaṇ": "yaṇ",
    "anusvāra-sandhiḥ": "anusvāra",
    "sulopa-sandhiḥ": "sa-lopa",
    "jaśtva-sandhiḥ": "jaśtva",
    "jaśtva-> pūrvasavarṇa-sandhiḥ": "t+h→ddh",
    "jaśtva-> ścutva-sandhiḥ": "ścutva",
    "ścutva-sandhiḥ": "ścutva",
    "anunāsika-sandhiḥ": "t→n (anunāsika)",
    "satva-> ṣṭutva-sandhiḥ": "visarga→s",
    "pūrvarūpa-sandhiḥ": "pūrvarūpa",
    "ayādi-sandhiḥ": "ayādi",
    "visarga-lopa (āḥ)": "visarga-lopa (āḥ)",
    "visarga-lopa (aḥ)": "visarga-lopa (aḥ+vowel)",
    "visarga-lopa (khar-para śar)": "visarga-lopa (khar-para śar)",
    # the oracle's own names for vowel sandhi (niyama.py table)
    "dīrgha-sandhiḥ": "savarṇa-dīrgha", "guṇa-sandhiḥ": "guṇa", "vṛddhi-sandhiḥ": "vṛddhi",
    "pūrvarūpa": "pūrvarūpa",
}
# classes whose absence at a junction is "no sandhi to report"
NULL_CLASSES = {"none", "visarga kept"}

CASE_EN = {"nominative": 1, "accusative": 2, "instrumental": 3, "dative": 4, "ablative": 5,
           "genitive": 6, "locative": 7, "vocative": 8}
NUM_EN = {"singular": "e", "dual": "d", "plural": "b"}
CASE_DV = {"प्रथमा": 1, "द्वितीया": 2, "तृतीया": 3, "चतुर्थी": 4, "पञ्चमी": 5, "षष्ठी": 6,
           "सप्तमी": 7, "सम्बोधनम्": 8}
NUM_DV = {"एकवचनम्": "e", "द्विवचनम्": "d", "बहुवचनम्": "b"}
SAMASA_TYPES = ["अव्ययीभावः", "द्विगुः", "नञ्तत्पुरुषः", "नञ्बहुव्रीहिः", "उपपदतत्पुरुषः", "प्रादितत्पुरुषः",
                "प्रादिबहुव्रीहिः", "बहुव्रीहिः", "द्वन्द्वः", "कर्मधारयः", "तत्पुरुषः"]


def gold_junction_class(sandhi_cell):
    ext = sandhi_cell.split("; समासे")[0]
    for key, cls in GOLD_RULES:
        if key in ext:
            return cls
    return "none"


def gold_case(stripped):
    m = re.search(r"«[^»]+» — (\S+) (?:विभक्तिः)?,? ?(\S+वचनम्)", stripped)
    if not m:
        m = re.search(r"— (\S+)(?: विभक्तिः)?, (\S+वचनम्)", stripped)
    if not m:
        return None
    c = CASE_DV.get(m.group(1).rstrip(","))
    n = NUM_DV.get(m.group(2).rstrip(","))
    return (c, n) if c else None


def gold_samasa_type(cell):
    if cell == "N/A":
        return None
    # the LAST analysed layer that names a type is the compound's own type
    parts = [p for p in cell.split(";") if any(t in p for t in SAMASA_TYPES)]
    last = parts[-1] if parts else cell
    for t in SAMASA_TYPES:
        if t in last:
            return {"नञ्तत्पुरुषः": "तत्पुरुषः", "उपपदतत्पुरुषः": "तत्पुरुषः", "प्रादितत्पुरुषः": "तत्पुरुषः",
                    "नञ्बहुव्रीहिः": "बहुव्रीहिः", "प्रादिबहुव्रीहिः": "बहुव्रीहिः", "द्विगुः": "द्विगुः",
                    "कर्मधारयः": "कर्मधारयः"}.get(t, t)
    if "तत्पुरुषः" in last or "षष्ठी" in last or "सप्तमी" in last:
        return "तत्पुरुषः"
    return "other"


SYS_TYPE = [("dvandva", "द्वन्द्वः"), ("xvanxva", "द्वन्द्वः"), ("bahuvrIhi", "बहुव्रीहिः"),
            ("karmaXAraya", "कर्मधारयः"), ("dvigu", "द्विगुः"), ("avyayIBAva", "अव्ययीभावः"),
            ("tatpuruSa", "तत्पुरुषः")]


def sys_samasa_type(tg):
    for t in SAMASA_TYPES:                       # Devanagari labels from samasa_classifier.py
        if tg.startswith(t):
            return {"नञ्तत्पुरुषः": "तत्पुरुषः", "उपपदतत्पुरुषः": "तत्पुरुषः", "प्रादितत्पुरुषः": "तत्पुरुषः",
                    "नञ्बहुव्रीहिः": "बहुव्रीहिः", "प्रादिबहुव्रीहिः": "बहुव्रीहिः"}.get(t, t)
    if "uncertain" in tg:
        return "uncertain"
    for k, v in SYS_TYPE:
        if tg.startswith(k) or k in tg.split("(")[0]:
            return v
    return "other"


def is_compound_row(row):
    """gold: a *nominal compound* word (not upasarga+dhātu, not taddhita)."""
    return row[5] != "N/A"


# ------------------------------------------------------------------ alignment
def align(tokens_dev, rows):
    """DP alignment: returns list of (token_idx_list, row_idx_list)."""
    T, R = len(tokens_dev), len(rows)
    INF = -1e9
    best = [[INF] * (R + 1) for _ in range(T + 1)]
    back = [[None] * (R + 1) for _ in range(T + 1)]
    best[0][0] = 0
    moves = [(1, 1), (1, 2), (1, 3), (2, 1)]
    for i in range(T + 1):
        for j in range(R + 1):
            if best[i][j] == INF:
                continue
            for di, dj in moves:
                ni, nj = i + di, j + dj
                if ni > T or nj > R:
                    continue
                a = "".join(tokens_dev[i:ni])
                b = "".join(r[0] for r in rows[j:nj])
                s = sim(a, b) - 0.02 * (di + dj - 2)
                if best[i][j] + s > best[ni][nj]:
                    best[ni][nj] = best[i][j] + s
                    back[ni][nj] = (i, j)
    out, i, j = [], T, R
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        out.append((list(range(pi, i)), list(range(pj, j))))
        i, j = pi, pj
    return out[::-1]


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--morph", default=None)
    ap.add_argument("--out-md", default="scorecard.md")
    ap.add_argument("--out-json", default="comparison.json")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    sys.path.insert(0, a.gold)
    from translit import to_dev
    GOLD = {}
    for f in sorted(os.listdir(a.gold)):
        if re.fullmatch(r"d0\d\.py", f):
            GOLD.update(importlib.import_module(f[:-3]).V)
    SYS = {int(k): v for k, v in json.load(open(a.system, encoding="utf-8")).items()}
    MORPH = {}
    if a.morph:
        MORPH = {int(k): v for k, v in json.load(open(a.morph, encoding="utf-8")).items()}

    S = collections.Counter()
    ERR = collections.defaultdict(list)
    CONF = collections.Counter()          # (gold_class, sys_class) for junctions
    per_token = []

    for v in sorted(GOLD):
        if v not in SYS:
            continue                 # scoring a partial run (e.g. --verses 1-10)
        rows = GOLD[v][1]
        toks, srows, mrows = [], [], []
        for li, line in enumerate(SYS[v]):
            for ti, (t, r) in enumerate(zip(line["tokens"], line["rows"])):
                last_in_line = ti == len(line["tokens"]) - 1
                toks.append(t)
                srows.append((r, last_in_line))
        if v in MORPH:
            mrows = [m for line in MORPH[v] for m in line]
        tdev = [to_dev(t) for t in toks]
        for tix, rix in align(tdev, rows):
            grow = [rows[j] for j in rix]
            ref = f"{v}"
            tok_str = " ".join(tdev[i] for i in tix)
            # ---- segmentation: a single token holding 2+ separate words
            if len(tix) == 1 and len(rix) > 1:
                n_words = sum(1 for g in grow)
                S["seg_gold_multi"] += 1
                sys_split = False  # analyze_pada_line never splits a printed token into words
                srow = srows[tix[0]][0]
                if srow.get("token_split"):
                    sys_split = [p for p in srow["token_split"]]
                if sys_split and [skel(to_dev(p)) for p in sys_split] == [skel(g[0]) for g in grow]:
                    S["seg_ok"] += 1
                else:
                    ERR["segmentation (word fused inside one printed token)"].append(
                        f"{ref}: {tok_str} → gold {' + '.join(g[0] for g in grow)}; system "
                        f"{' + '.join(sys_split) if sys_split else 'not split'}")
            # ---- junction sandhi at the END of this token group
            ti_last = tix[-1]
            srow, last_in_line = srows[ti_last]
            gcls = gold_junction_class(grow[-1][1])
            if not last_in_line:
                scls = SYS_RULES.get(srow["sandhi_rule"], srow["sandhi_rule"] or "none")
                gnull, snull = gcls in NULL_CLASSES, scls in NULL_CLASSES
                CONF[(gcls, scls)] += 1
                S["junctions"] += 1
                if gnull and snull:
                    S["junction_ok"] += 1; S["junction_tn"] += 1
                elif gcls == scls:
                    S["junction_ok"] += 1; S["junction_tp"] += 1
                elif snull:
                    S["junction_fn"] += 1
                    ERR[f"junction sandhi missed — {gcls}"].append(f"{ref}: {tok_str} ⟶ {grow[-1][1][:90]}")
                elif gnull:
                    S["junction_fp"] += 1
                    ERR[f"junction sandhi wrongly reported — system said {scls}"].append(f"{ref}: {tok_str}")
                else:
                    S["junction_wrongclass"] += 1
                    ERR[f"junction sandhi wrong class — gold {gcls} / system {scls}"].append(f"{ref}: {tok_str}")
            # ---- samāsa (per token that is one gold word)
            if len(tix) == 1 and len(rix) == 1:
                g = grow[0]
                gcomp = is_compound_row(g)
                sam = srow["samasa"]
                S["words_1to1"] += 1
                if gcomp and sam:
                    S["samasa_tp"] += 1
                    gt, st = gold_samasa_type(g[5]), sys_samasa_type(sam["type_guess"])
                    S["samasa_type_total"] += 1
                    if st == gt:
                        S["samasa_type_ok"] += 1
                    elif st == "uncertain":
                        S["samasa_type_uncertain"] += 1
                    else:
                        ERR[f"samāsa type wrong — gold {gt} / system {st}"].append(f"{ref}: {g[0]} {' + '.join(sam['members'])}")
                elif gcomp:
                    S["samasa_fn"] += 1
                    ERR["samāsa missed"].append(f"{ref}: {g[0]} — {g[5][:80]}")
                elif sam:
                    S["samasa_fp"] += 1
                    ERR["samāsa invented (word is not a compound)"].append(f"{ref}: {g[0]} → {' + '.join(sam['members'])}")
                else:
                    S["samasa_tn"] += 1
                # ---- morphology
                if mrows:
                    m = mrows[tix[0]]
                    gverb = g[4].startswith("तिङ्")
                    gavy = "अव्ययम्" in g[4][:30]
                    gcase = gold_case(g[4])
                    S["morph_words"] += 1
                    if gverb:
                        S["verb_gold"] += 1
                        if m.get("is_verb"):
                            S["verb_tp"] += 1
                        else:
                            ERR["finite verb not recognised"].append(f"{ref}: {g[0]} ({g[3]})")
                    elif m.get("is_verb") and not gavy:
                        S["verb_fp"] += 1
                        ERR["noun wrongly tagged as verb"].append(f"{ref}: {g[0]}")
                    if gcase:
                        S["case_gold"] += 1
                        sc = m.get("case")
                        if sc:
                            S["case_answered"] += 1
                            if (CASE_EN.get(sc[0]), NUM_EN.get(sc[1])) == gcase:
                                S["case_ok"] += 1
                            else:
                                ERR["vibhakti/vacana wrong"].append(
                                    f"{ref}: {g[0]} gold {gcase} system {sc[0]}/{sc[1]}")
                        else:
                            ERR["vibhakti not identified"].append(f"{ref}: {g[0]} (gold {gcase})")
                    gstem = g[3].split(" (")[0].strip()
                    if m.get("stem"):
                        S["stem_answered"] += 1
                        if skel(to_dev(m["stem"]) if re.search("[a-z]", m["stem"]) else m["stem"]) == skel(gstem):
                            S["stem_ok"] += 1
                        else:
                            ERR["prātipadika/dhātu wrong"].append(f"{ref}: {g[0]} gold {gstem} system {m['stem']}")
                    S["stem_gold"] += 1
            per_token.append({"verse": v, "tokens": [toks[i] for i in tix], "gold": [r[0] for r in grow],
                              "gold_junction": gcls,
                              "system_junction": SYS_RULES.get(srow["sandhi_rule"], srow["sandhi_rule"] or "none"),
                              "system_samasa": srow["samasa"]})

    def pct(a, b):
        return f"{a}/{b} = {100*a/b:.1f}%" if b else "n/a"

    L = [f"# Scorecard — local tools vs hand analysis, Bāla Kāṇḍa Sarga 1 {a.label}", ""]
    L += ["| Measure | Result |", "|---|---|",
          f"| Junction sandhi between printed tokens, all junctions | {pct(S['junction_ok'], S['junctions'])} |",
          f"| — real sandhi correctly named (recall) | {pct(S['junction_tp'], S['junction_tp']+S['junction_fn']+S['junction_wrongclass'])} |",
          f"| — sandhi reported where there is none | {S['junction_fp']} |",
          f"| — right junction, wrong sandhi class | {S['junction_wrongclass']} |",
          f"| Words fused inside one printed token (च+एव, सीता+अपि…) split correctly | {pct(S['seg_ok'], S['seg_gold_multi'])} |",
          f"| Samāsa detection — recall (gold compounds found) | {pct(S['samasa_tp'], S['samasa_tp']+S['samasa_fn'])} |",
          f"| Samāsa detection — precision (flagged words that really are compounds) | {pct(S['samasa_tp'], S['samasa_tp']+S['samasa_fp'])} |",
          f"| Samāsa type exactly right (of compounds found) | {pct(S['samasa_type_ok'], S['samasa_type_total'])} ({S['samasa_type_uncertain']} left 'uncertain') |"]
    if S["morph_words"]:
        L += [f"| Finite verbs recognised | {pct(S['verb_tp'], S['verb_gold'])} (+{S['verb_fp']} false) |",
              f"| Vibhakti+vacana: answered | {pct(S['case_answered'], S['case_gold'])} |",
              f"| Vibhakti+vacana: correct (of all declined words) | {pct(S['case_ok'], S['case_gold'])} |",
              f"| Prātipadika/dhātu correct (of all words) | {pct(S['stem_ok'], S['stem_gold'])} (answered {S['stem_answered']}) |"]
    L += ["", "## Junction confusion (gold class → system class, count)", ""]
    for (g, s), c in sorted(CONF.items(), key=lambda x: -x[1]):
        if g != s and not (g in NULL_CLASSES and s in NULL_CLASSES):
            L.append(f"- {g} → {s}: {c}")
    L += ["", "## Disagreements by class", ""]
    for k in sorted(ERR, key=lambda k: -len(ERR[k])):
        L += [f"### {k} ({len(ERR[k])})", ""] + [f"- {e}" for e in ERR[k]] + [""]
    open(a.out_md, "w", encoding="utf-8").write("\n".join(L))
    json.dump({"scores": S, "per_token": per_token}, open(a.out_json, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
