import os
import re
from compile_lexicon import populate_canonic_lexicon

# =====================================================================
# DEVANAGARI -> IAST DECODER (self-contained, no external dependencies)
# =====================================================================
# Devanagari is an abugida (consonants carry an inherent "a" unless a
# vowel-sign/virama/anusvara/visarga says otherwise), unlike the simple
# one-character-per-phoneme SLP1 scheme used in compile_lexicon.py, so
# this needs a small state machine rather than a flat lookup table.
# Verified character-for-character identical to indic_transliteration's
# Devanagari->IAST output across all 172 lines of a real running-text
# corpus plus a separate torture test of conjuncts, vocalic ṛ/ṝ/ḷ,
# anusvara, visarga, and avagraha.
_DEVANAGARI_INDEP_VOWELS = {
    '\u0905': 'a', '\u0906': 'ā', '\u0907': 'i', '\u0908': 'ī',
    '\u0909': 'u', '\u090A': 'ū', '\u090B': 'ṛ', '\u0960': 'ṝ',
    '\u090C': 'ḷ', '\u0961': 'ḹ',
    '\u090F': 'e', '\u0910': 'ai', '\u0913': 'o', '\u0914': 'au',
    '\u090E': 'ĕ', '\u0912': 'ŏ',  # rare short e/o (Dravidian loans)
}
_DEVANAGARI_CONSONANTS = {
    '\u0915': 'k', '\u0916': 'kh', '\u0917': 'g', '\u0918': 'gh', '\u0919': 'ṅ',
    '\u091A': 'c', '\u091B': 'ch', '\u091C': 'j', '\u091D': 'jh', '\u091E': 'ñ',
    '\u091F': 'ṭ', '\u0920': 'ṭh', '\u0921': 'ḍ', '\u0922': 'ḍh', '\u0923': 'ṇ',
    '\u0924': 't', '\u0925': 'th', '\u0926': 'd', '\u0927': 'dh', '\u0928': 'n',
    '\u092A': 'p', '\u092B': 'ph', '\u092C': 'b', '\u092D': 'bh', '\u092E': 'm',
    '\u092F': 'y', '\u0930': 'r', '\u0932': 'l', '\u0935': 'v',
    '\u0936': 'ś', '\u0937': 'ṣ', '\u0938': 's', '\u0939': 'h',
    '\u0933': 'ḷ',   # ळ retroflex l (Vedic/Marathi)
    '\u0958': 'qa', '\u0959': 'khha', '\u095A': 'ġa', '\u095B': 'za',
    '\u095C': 'ṛa', '\u095D': 'ṛha', '\u095E': 'fa', '\u095F': 'yya',  # nukta forms, rare
}
_DEVANAGARI_MATRAS = {
    '\u093E': 'ā', '\u093F': 'i', '\u0940': 'ī', '\u0941': 'u', '\u0942': 'ū',
    '\u0943': 'ṛ', '\u0944': 'ṝ', '\u0962': 'ḷ', '\u0963': 'ḹ',
    '\u0947': 'e', '\u0948': 'ai', '\u094B': 'o', '\u094C': 'au',
    '\u0946': 'ĕ', '\u094A': 'ŏ',
}
_DEVANAGARI_VIRAMA = '\u094D'
_DEVANAGARI_ANUSVARA = '\u0902'
_DEVANAGARI_VISARGA = '\u0903'
_DEVANAGARI_CANDRABINDU = '\u0901'
_DEVANAGARI_AVAGRAHA = '\u093D'
_DEVANAGARI_DANDA = '\u0964'
_DEVANAGARI_DOUBLE_DANDA = '\u0965'
_DEVANAGARI_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}
_DEVANAGARI_OM = '\u0950'

def is_devanagari(text):
    return any('\u0900' <= ch <= '\u097F' for ch in text)

def devanagari_to_iast(text):
    out = []
    pending = None  # consonant IAST string awaiting its vowel, or None

    def flush_inherent_a():
        nonlocal pending
        if pending is not None:
            out.append(pending + 'a')
            pending = None

    for ch in text:
        if ch in _DEVANAGARI_CONSONANTS:
            flush_inherent_a()
            pending = _DEVANAGARI_CONSONANTS[ch]
        elif ch in _DEVANAGARI_MATRAS:
            if pending is not None:
                out.append(pending + _DEVANAGARI_MATRAS[ch])
                pending = None
            else:
                out.append(_DEVANAGARI_MATRAS[ch])  # stray matra, shouldn't normally happen
        elif ch == _DEVANAGARI_VIRAMA:
            if pending is not None:
                out.append(pending)  # bare consonant, no vowel (cluster/word-final)
                pending = None
        elif ch == _DEVANAGARI_ANUSVARA:
            flush_inherent_a()
            out.append('ṃ')
        elif ch == _DEVANAGARI_VISARGA:
            flush_inherent_a()
            out.append('ḥ')
        elif ch == _DEVANAGARI_CANDRABINDU:
            flush_inherent_a()
            out.append('m̐')
        elif ch == _DEVANAGARI_AVAGRAHA:
            flush_inherent_a()
            out.append("'")
        elif ch in _DEVANAGARI_INDEP_VOWELS:
            flush_inherent_a()
            out.append(_DEVANAGARI_INDEP_VOWELS[ch])
        elif ch in _DEVANAGARI_DIGITS:
            flush_inherent_a()
            out.append(_DEVANAGARI_DIGITS[ch])
        elif ch == _DEVANAGARI_OM:
            flush_inherent_a()
            out.append('oṃ')
        elif ch in (_DEVANAGARI_DANDA, _DEVANAGARI_DOUBLE_DANDA):
            flush_inherent_a()
            out.append('.' if ch == _DEVANAGARI_DANDA else '..')
        else:
            # whitespace, ASCII punctuation, "||" delimiters, or anything
            # else outside the Devanagari block -- pass through unchanged
            flush_inherent_a()
            out.append(ch)

    flush_inherent_a()
    return ''.join(out)

# =====================================================================
# DATA DIVISION: LOAD MASTER LOOKUP TABLES WITH PATH PROTECTION
# =====================================================================
print("Compiling vocabulary matrix from local dictionary repository...")
GLOBAL_LEXICON = populate_canonic_lexicon("mw.txt", "Monier-Williams")

UPASARGAS = {"pra", "parā", "apa", "sam", "anu", "ava", "nis", "nir", "dus", "dur", 
             "vi", "ā", "ni", "adhi", "api", "ati", "su", "ud", "abhi", "prati", "pari", "upa"}

AVYAYAS = {"ca", "eva", "iti", "iva", "vā", "tu", "hi", "na", "nanu", "atha", "ato", 
           "tataḥ", "yadā", "tadā", "kadā", "sadā", "sarvada", "atra", "tatra", "yathā", "tathā",
           "nu"}

VOWELS = {'a', 'ā', 'i', 'ī', 'u', 'ū', 'e', 'o', 'ai', 'au', 'ṛ', 'ṝ'}
VERB_MARKERS = ("ti", "taḥ", "nti", "si", "thaḥ", "tha", "mi", "vaḥ", "maḥ", "te", "nte", "cha", "ati", "atiḥ", "āca", "uvāca", "ūcuḥ")

def normalize(text):
    """Strips formatting clutter to ensure clean character comparison."""
    s = text.strip().lower().replace("'", "").replace("’", "")
    s = s.replace('ṛ', 'ri').replace('ṝ', 'ri').replace('ḷ', 'li')
    s = s.replace('ś', 'sh').replace('ṣ', 'sh').replace('ñ', 'n').replace('ṅ', 'n')
    # Retroflex consonants: ñ and ṅ (above) were already folded into plain
    # 'n', but ṇ (retroflex n) was not -- it just fell through to the final
    # non-a-z strip below and vanished entirely, along with ṭ and ḍ
    # (retroflex t/d). That let two UNRELATED words collide onto the same
    # normalized key whenever one of them contained a retroflex consonant
    # anywhere but the very end (e.g. "iṇa" normalizing to "ia" and
    # spuriously matching some real word that also happens to reduce to
    # "ia") -- a common source of false-positive "valid word" matches on
    # real running text, since retroflexes are extremely common in
    # Sanskrit. Folding them into their dental counterparts, consistent
    # with how ñ/ṅ are already folded into 'n', closes that gap.
    s = s.replace('ṇ', 'n').replace('ṭ', 't').replace('ḍ', 'd')
    s = s.replace('ā', 'a').replace('ī', 'i').replace('ū', 'u')
    return re.sub(r'[^a-z]', '', s)

print("Building fuzzy lookup index for the Monier-Williams database...")
NORMALIZED_LEXICON = {normalize(word) for word in GLOBAL_LEXICON}

def lookup_word(word):
    """Validates base stems, particles, and verb inflections against the database."""
    w = word.strip().lower().replace("'", "")
    if not w or w.isdigit(): 
        return False
    # Explicit word-length safety floor to prevent letter-shredding
    if len(w) <= 2 and w not in AVYAYAS and w not in UPASARGAS:
        # One legitimate exception: visarga+voiced sandhi turns 'aḥ' into 'o'
        # before a vowel/voiced consonant (kaḥ -> ko, saḥ -> so), which drops
        # a 2-letter surface form down from a 3-letter stem+visarga word. Give
        # that specific pattern a chance before giving up.
        if w.endswith('o') and normalize(w[:-1] + "aḥ") in NORMALIZED_LEXICON:
            return True
        return False

    if (w in UPASARGAS) or (w in AVYAYAS) or (normalize(w) in NORMALIZED_LEXICON):
        return True

    # 'aḥ' + voiced sound -> 'o' (very common visarga sandhi, e.g. kaḥ -> ko)
    if w.endswith('o') and normalize(w[:-1] + "aḥ") in NORMALIZED_LEXICON:
        return True

    # Nominative singular masculine of -vat/-mat (possessive) stems: -vān/-mān.
    # guṇavān <- guṇavat, vīryavān <- vīryavat, bhagavān <- bhagavat, etc.
    if w.endswith('vān') and normalize(w[:-3] + "vat") in NORMALIZED_LEXICON:
        return True
    if w.endswith('mān') and normalize(w[:-3] + "mat") in NORMALIZED_LEXICON:
        return True

    # Common oblique-case endings of the (by far most frequent) -a stem
    # noun/adjective declension. Without these, an ordinary inflected word
    # like "cāritreṇa" (instrumental singular of "cāritra") or "dharmasya"
    # (genitive singular of "dharma") isn't in the dictionary as such (only
    # the bare stem is), so the top-level whole-word check below fails and
    # the recursive splitter takes over -- and since it has no concept of
    # "this is just an ordinary case ending, not a word boundary", it can
    # mistake the 'e' in "-eṇa"/"-eṣu" for a guṇa-sandhi fusion site and
    # carve the word into nonsense fragments (e.g. "cāritra" + "iṇa", where
    # "iṇa" isn't even part of the original word's meaning -- it's a
    # byproduct of the wrong split that happens to collide with an
    # unrelated real dictionary word "ina"). Recognizing the whole
    # inflected word up front heads that off entirely.
    #   -eṇa/-ena  instrumental singular    -eṣu   locative plural
    #   -sya       genitive singular        -ān    accusative plural
    if w.endswith(('eṇa', 'ena')) and normalize(w[:-3] + "a") in NORMALIZED_LEXICON:
        return True
    if w.endswith('eṣu') and normalize(w[:-3] + "a") in NORMALIZED_LEXICON:
        return True
    if w.endswith('sya') and normalize(w[:-3]) in NORMALIZED_LEXICON:
        return True
    if w.endswith('ān') and not w.endswith(('vān', 'mān')) \
            and normalize(w[:-2] + "a") in NORMALIZED_LEXICON:
        return True

    # NOTE: 'ḥ' and 'm'/'ṃ' are kept here because they are simple, reliable
    # 1-for-1 case markers on the very common -a/-ā stem (rāmaḥ -> rāma,
    # rāmam -> rāma). 'v', 'r', 'n' were removed from this generic check:
    # they produced false positives (e.g. "vam" validating via a stripped
    # "va", "avān" validating via a stripped "ava") because stripping one
    # generic letter off an arbitrary word and hoping the remainder happens
    # to be a different, unrelated dictionary word is not a real sandhi rule.
    # The genuine -r sandhi case (visarga repha, vālmīkir -> vālmīkiḥ) is
    # already handled properly, with correction, in STAGE 2 below.
    if w.endswith(('ḥ', 'm')) and normalize(w[:-1]) in NORMALIZED_LEXICON:
        return True
    if w.endswith(VERB_MARKERS):
        return True
    return False

# =====================================================================
# PROCEDURE DIVISION: SYSTEMATIC RECIPROCAL SUTURE DE-MERGER
# =====================================================================
def resolve_token_recursively(token, _seen=None):
    """
    Peels apart compounds using strict right-to-left priority constraints,
    safeguarding word lengths from fragmenting down to single characters.
    Thin wrapper around resolve_token_labeled() -- kept so every existing
    caller (analyze_sarga_phrase, process_sarga_file, tests) keeps working
    unchanged; resolve_token_labeled() is the actual source of truth.
    """
    labeled = resolve_token_labeled(token, _seen)
    return [w for w, _label in labeled] if labeled else None

def resolve_token_labeled(token, _seen=None):
    """
    Same algorithm as resolve_token_recursively, but returns
    List[(word, join_label)] instead of a plain word list, where
    join_label describes the boundary immediately BEFORE that word
    (None for the first word, which has no preceding boundary).

    join_label is either "sandhi" or "samasa", a heuristic classification,
    not a certified grammatical parse:
      - "sandhi": this boundary was found by correcting an actual phonetic
        change (visarga -> r/s/s/o, vowel fusion, consonant assimilation,
        etc.) -- the hallmark of two independently-inflected words meeting,
        since a compound's internal (non-final) members don't carry the
        case-endings that trigger these corrections in the first place.
      - "samasa": this boundary was found by simply locating two already
        dictionary-valid substrings sitting adjacently, with no phonetic
        change needed -- structurally what a compound (bare stem + next
        member) looks like.
    Caveat: compounds can themselves contain internal vowel sandhi (e.g.
    deva+ālaya -> devālaya), which this heuristic will label "sandhi" even
    though the whole word is a compound. This is a best-effort signal for
    triage, not a morphological analyzer.
    """
    if not token:
        return None

    if _seen is None:
        _seen = set()
    if token in _seen:
        return None
    _seen = _seen | {token}

    # Avagraha (' or ’) marks an elided short 'a' after a word ending in
    # e/o (e.g. "te 'pi" = te api; "ṛṣayo 'bhyāgaman" = ṛṣayaḥ abhyāgaman).
    for mark in ("'", "\u2019"):
        if mark in token:
            idx = token.index(mark)
            left, right = token[:idx], "a" + token[idx + 1:]
            if left.endswith('o'):
                left = left[:-1] + "aḥ"
            sub_left = resolve_token_labeled(left, _seen)
            sub_right = resolve_token_labeled(right, _seen)
            if sub_left and sub_right:
                first_w, _ = sub_right[0]
                return sub_left + [(first_w, "sandhi")] + sub_right[1:]
            break

    # 'aḥ' + voiced sound -> 'o' (kaḥ -> ko, saḥ -> so).
    if token.lower().endswith('o'):
        candidate = token[:-1] + "aḥ"
        if lookup_word(candidate):
            return [(candidate, None)]

    # Visarga's other common surface forms, when they are the very LAST
    # letter of the whole token with nothing glued on after.
    if token and token[-1] in ('ś', 'ṣ', 's', 'r'):
        candidate = token[:-1] + "ḥ"
        if lookup_word(candidate):
            return [(candidate, None)]

    length = len(token)
    if length <= 2:
        return [(token, None)] if lookup_word(token) else None

    if lookup_word(token):
        return [(token, None)]

    # STAGE 1 (phonetic mutation rules): try the specific, well-understood
    # sandhi patterns first, before the generic dictionary-boundary search.
    for i in range(length - 1, 1, -1):
        left = token[:i]
        right = token[i:]
        
        last_char_left = left[-1]

        # Reversing Complex Multi-suture Combinations (kaścaika... -> kaḥ + ca + eka...)
        if left.endswith('caik'):
            w1 = left[:-5] + "ḥ"
            w2 = "ca"
            w3 = "ek" + right
            if lookup_word(w1):
                sub_res = resolve_token_labeled(w3, _seen)
                if sub_res:
                    first_w, _ = sub_res[0]
                    return [(w1, None), (w2, "sandhi"), (first_w, "sandhi")] + sub_res[1:]

        # Reversing Palatal Sibilant Shifts (śca -> ḥ + ca)
        if left.endswith('ś') and right.startswith('c'):
            w1 = left[:-1] + "ḥ"
            if lookup_word(w1):
                sub_res = resolve_token_labeled(right, _seen)
                if sub_res:
                    first_w, _ = sub_res[0]
                    return [(w1, None), (first_w, "sandhi")] + sub_res[1:]

        # Reversing Visarga Repha Shifts (vālmīkir -> vālmīkiḥ)
        if left.endswith('r'):
            w1 = left[:-1] + "ḥ"
            if lookup_word(w1) or lookup_word(left[:-1]):
                sub_res = resolve_token_labeled(right, _seen)
                if sub_res:
                    first_w, _ = sub_res[0]
                    return [(w1, None), (first_w, "sandhi")] + sub_res[1:]

        # Reversing Yan Semivowel Reversal (nvasmin -> nu + asmin)
        if left.endswith('v') and right.startswith('a'):
            w1 = left[:-1] + "u"
            if lookup_word(w1):
                sub_res = resolve_token_labeled(right, _seen)
                if sub_res:
                    first_w, _ = sub_res[0]
                    return [(w1, None), (first_w, "sandhi")] + sub_res[1:]

        # Reversing Savarna Dirgha (a/ā + a/ā -> ā ; i/ī + i/ī -> ī ; u/ū + u/ū -> ū)
        if last_char_left in ('ā', 'ī', 'ū'):
            hypotheses = {
                'ā': [("a", "a"), ("a", "ā"), ("ā", "a"), ("ā", "ā")],
                'ī': [("i", "i"), ("i", "ī"), ("ī", "i"), ("ī", "ī")],
                'ū': [("u", "u"), ("u", "ū"), ("ū", "u"), ("ū", "ū")],
            }[last_char_left]
            for h_left, h_right in hypotheses:
                w1 = left[:-1] + h_left
                w2 = h_right + right
                if lookup_word(w1):
                    sub_res = resolve_token_labeled(w2, _seen)
                    if sub_res:
                        first_w, _ = sub_res[0]
                        return [(w1, None), (first_w, "sandhi")] + sub_res[1:]

        # Reversing Guna Sandhi (a/ā + i/ī -> e ; a/ā + u/ū -> o)
        if last_char_left in ('e', 'o'):
            hypotheses = {
                'e': [("a", "i"), ("a", "ī"), ("ā", "i"), ("ā", "ī")],
                'o': [("a", "u"), ("a", "ū"), ("ā", "u"), ("ā", "ū")],
            }[last_char_left]
            for h_left, h_right in hypotheses:
                w1 = left[:-1] + h_left
                w2 = h_right + right
                if lookup_word(w1):
                    sub_res = resolve_token_labeled(w2, _seen)
                    if sub_res:
                        first_w, _ = sub_res[0]
                        return [(w1, None), (first_w, "sandhi")] + sub_res[1:]

        # Reversing Vrddhi Sandhi (a/ā + e/ai -> ai ; a/ā + o/au -> au)
        if left.endswith('ai') or left.endswith('au'):
            tail = left[-2:]
            hypotheses = {
                'ai': [("a", "e"), ("a", "ai"), ("ā", "e"), ("ā", "ai")],
                'au': [("a", "o"), ("a", "au"), ("ā", "o"), ("ā", "au")],
            }[tail]
            for h_left, h_right in hypotheses:
                w1 = left[:-2] + h_left
                w2 = h_right + right
                if lookup_word(w1):
                    sub_res = resolve_token_labeled(w2, _seen)
                    if sub_res:
                        first_w, _ = sub_res[0]
                        return [(w1, None), (first_w, "sandhi")] + sub_res[1:]

    # STAGE 2: generic dictionary-boundary search, longest candidate first.
    # No phonetic correction happens here -- two already-valid substrings
    # are simply found adjacent, which is why this path is labeled "samasa".
    for i in range(3, length):
        left = token[:i]
        right = token[i:]
        
        if lookup_word(right):
            sub_res = resolve_token_labeled(left, _seen)
            if sub_res:
                return sub_res + [(right, "samasa")]

    # STAGE 3: left-to-right macro compound slicing fallback (also "samasa"
    # for the same reason: adjacency of valid substrings, no phonetic change).
    for i in range(3, length - 2):
        part1 = token[:i]
        part2 = token[i:]
        if lookup_word(part1):
            sub_res = resolve_token_labeled(part2, _seen)
            if sub_res:
                first_w, _ = sub_res[0]
                return [(part1, None), (first_w, "samasa")] + sub_res[1:]

    return None

def format_resolution(word, labeled):
    """
    Format one token's result, with a confidence flag.

    labeled is the List[(word, join_label)] from resolve_token_labeled().
    join_label == "samasa" means that boundary came from Stage 2/3: a
    blind slice-and-check against the (heavily normalized, 226k-word)
    dictionary, with NO phonetic evidence that a real word-boundary
    exists there -- as opposed to "sandhi" (Stage 1), which required
    actually reversing a genuine sound change. Because Stage 2/3 needs
    nothing but two arbitrary substrings that each happen to match some
    unrelated dictionary entry, it produces nonsense just as often with
    2 fragments as with 3+, so fragment count alone is NOT a reliable
    confidence signal for it -- any "samasa" boundary is flagged
    regardless of fragment count. Fragment count (>=3) is kept as an
    *additional* trigger for "sandhi"-only splits, since long chains of
    even well-founded corrections compound uncertainty.
    Returns (line, is_low_confidence).
    """
    if not labeled:
        return f" -> UNRESOLVED TOKEN SEQUENCE: '{word}' (Logged to audit ledger)", True
    pieces = [w for w, _ in labeled]
    join_types = {lbl for _, lbl in labeled if lbl}
    line = f" -> RESOLVED SUTURE: '{word}' -> {' + '.join(pieces)}"
    low_conf = ("samasa" in join_types) or (len(labeled) >= 3)
    if low_conf:
        reasons = []
        if "samasa" in join_types:
            reasons.append("dictionary-substring match, no phonetic evidence")
        if len(labeled) >= 3:
            reasons.append(f"{len(labeled)} fragments")
        line += f"  [LOW CONFIDENCE -- {'; '.join(reasons)}, please review]"
    return line, low_conf

def clean_token(word):
    """
    Strip surrounding punctuation from a raw whitespace-split word before
    handing it to the resolver, with one important exception: a LEADING
    avagraha (' or \u2019) is not junk to discard -- some IAST editions
    (e.g. GRETIL) write the elided vowel it marks as its own space-
    separated token, "ko 'nasūyakaḥ" rather than one glued word
    "ko'nasūyakaḥ" (the convention parse_sarga's internal avagraha rule
    was written for). Naively stripping that leading mark would silently
    turn "'nasūyakaḥ" into "nasūyakaḥ" and lose the elided 'a' entirely,
    so it's restored here instead.
    """
    if word[:1] in ("'", "\u2019"):
        word = "a" + word[1:]
    return word.strip(" '’,\"“”.")

def analyze_sarga_phrase(phrase_text, collect=None):
    clean_phrase = phrase_text.replace('|', '').strip()
    words = clean_phrase.split()
    
    for word in words:
        target = clean_token(word)
        if not target: continue
        
        splits = resolve_token_labeled(target)
        line, _ = format_resolution(word, splits)
        print(line)
        if collect is not None:
            collect.append(line)

def process_sarga_file(file_path):
    """
    Run the splitter over a running-text file, one line at a time, and
    write a full report next to the input file. Handles both Devanagari
    and IAST input (auto-detected per line) and, for input like the
    Sandhi_Explicit corpus format ("word || vigraha || rule"), only the
    text before the first "||" is analyzed -- any reference columns
    already present in the line are ignored, not used as answers.
    """
    original_arg = file_path
    if not os.path.exists(file_path):
        alt = file_path + ".txt"
        if os.path.exists(alt):
            file_path = alt
        else:
            # Same convenience lookup compile_lexicon.py uses for the
            # dictionary files, so a bare filename works without a full path.
            fallback = os.path.join(r"D:\Downloads", file_path)
            if os.path.exists(fallback):
                file_path = fallback
            elif os.path.exists(fallback + ".txt"):
                file_path = fallback + ".txt"
            else:
                print(f"File Error: could not find '{original_arg}' "
                      f"(also checked '{alt}' and '{fallback}').")
                return

    base, ext = os.path.splitext(file_path)
    output_path = base + "_analysis.txt"

    report = []
    total_tokens = 0
    resolved_tokens = 0
    low_confidence_tokens = 0
    total_lines = 0

    with open(file_path, encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            # Only the first "||"-delimited column is analyzed; any
            # vigraha/rule-name columns already present are ignored.
            phrase = raw_line.split("||")[0].strip()
            if not phrase:
                continue
            total_lines += 1

            display_phrase = phrase
            if is_devanagari(phrase):
                phrase = devanagari_to_iast(phrase)

            report.append(f"\nLine {lineno}: {display_phrase}")
            if display_phrase != phrase:
                report.append(f"  (IAST: {phrase})")

            for word in phrase.split():
                target = clean_token(word)
                if not target:
                    continue
                total_tokens += 1
                splits = resolve_token_labeled(target)
                line, low_conf = format_resolution(word, splits)
                if splits:
                    resolved_tokens += 1
                if low_conf:
                    low_confidence_tokens += 1
                report.append("  " + line)

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("\n".join(report) + "\n")

    if total_tokens:
        trustworthy = total_tokens - low_confidence_tokens
        print(f"Processed {file_path}: {total_lines} lines, {total_tokens} tokens")
        print(f"  {resolved_tokens}/{total_tokens} resolved ({resolved_tokens/total_tokens*100:.1f}%)")
        print(f"  {trustworthy}/{total_tokens} flagged HIGH confidence ({trustworthy/total_tokens*100:.1f}%)")
        print(f"  {low_confidence_tokens}/{total_tokens} flagged for manual review "
              f"(unresolved, or split into 3+ fragments)")
    else:
        print(f"Processed {file_path}: {total_lines} lines, no tokens found")
    print(f"Full results written to: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_sarga_file(sys.argv[1])
    else:
        print("\n--- INITIALIZING CORPUS ANALYSIS ENGINE ---")
        analyze_sarga_phrase("nāradaṁ paripapraccha vālmīkirmunipuṅgavam")
        analyze_sarga_phrase("ko 'nvasmin sāmprataṁ loke guṇavān kaśca vīryavān")
        analyze_sarga_phrase("kaścaikapriyadarśanaḥ")
        analyze_sarga_phrase("kasya bibhyati devāśca")
