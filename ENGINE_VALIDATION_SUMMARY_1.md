# Engine validation against the hand-written Sarga 1 treatise

**Scope.** Bāla Kāṇḍa, Sarga 1 (79 verses, 826 words), from `source_texts\sa_rAmAyaNa.txt`.
**Date.** 23 September 2026.
**Reference ("gold").** The hand-written word-by-word analysis in `working_files\d01.py … d08.py`.
**Tools validated.** The project's own sandhi, samāsa and grammar files, plus the dictionaries and LSK data they read.
**Rule used throughout.** Every change is built only from files already in the project. Nothing was looked up online, and no fact was typed in from memory without a project source for it.

---

## 1. Headline result

The same scorer (`engine_validation\compare_with_gold.py`) was run on the tools as they were before this pass and as they are after it, both times against the hand analysis.

| Measure (Sarga 1, 826 words) | BEFORE | AFTER |
|---|---|---|
| Sandhi between printed words — real junctions correctly named | 88 / 301 (29.2 %) | **291 / 301 (96.7 %)** |
| Sandhi reported where there is none | 0 | 0 |
| Two words fused inside one printed token (च+एव, सीता+अपि …) split correctly | 0 / 43 | **37 / 43 (86.0 %)** |
| Samāsa found (recall) | 54.1 % | **79.5 %** |
| Samāsa flagged that really are compounds (precision) | 58.8 % | **88.0 %** |
| Samāsa type exactly right (of compounds found) | 3 / 100 (90 left "uncertain") | **121 / 147 (82.3 %)**, none left uncertain |
| Finite verbs recognised | 16 / 57 | **59 / 66 (89.4 %)** |
| Vibhakti + vacana correct (declined words) | 62.1 % | **89.3 %** |
| Prātipadika / dhātu correct (all words) | 9.5 % | **86.4 %** |

Full scorecards, with every disagreement listed by class:

- `engine_validation\scorecard_before.md`
- `engine_validation\scorecard_AFTER.md`

The verb denominator differs (57 → 66) because the BEFORE tools merged or dropped some verb rows before they reached the scorer.

### Honest caveat — overfitting

Many rules were written while looking at Sarga 1, so the Sarga 1 scores above are optimistic. To measure how the tools do on text they were not tuned on, I checked **Sarga 2, verses 11–20** (122 words) by hand. The rate was about **82 % words fully right**, compared with 86–89 % on Sarga 1. That 5-point gap is the realistic size of the overfitting.

Six general fixes came out of that held-out check. They were then applied to all text and re-verified on Sarga 1:

- the periphrastic perfect (कथयाम्+आस)
- three-word fusions
- ṭvā gerunds
- ṃs+t (8.3.7)
- ṅamuṭ (8.3.32)
- śatṛ genitive vs. the tasil avyaya

### The engine also found an error in my hand analysis

In verse 35 I had tagged **अभ्यागमन्** as लङ्. It is **लुङ्**: the aṅ-aorist of गम्, by पुषादिद्युताद्लृदितः परस्मैपदेषु 3.1.55. I corrected it in `working_files\d04.py`, and the treatise was regenerated:

- `sanskrit_analysis_tables.md`
- `build_sanskrit_analysis.py`
- `sanskrit_analysis_v2_verse35_corrected.xlsx`. It carries a new name because the original .xlsx was open in Excel and locked.

A known inconsistency remains in my gold: सुग्रीव is marked बहुव्रीहि in one place and N/A elsewhere. It is noted here and not silently changed.

---

## 2. Backups

Every file that was modified was copied first, unchanged, into these folders:

- `02_Sanskrit_Grammar_Engine\_backup_before_sarga1_validation_2026-09-23\` (17 files)
- `03_Sandhi_and_Samasa_Tools\_backup_before_sarga1_validation_2026-09-23\` (18 files)

The exact line-level diff of the three pre-existing files that were edited is in `engine_validation\changes_to_existing_files.patch` (346 lines added, 7 changed).

---

## 3. Changes made, file by file

### 3a. Existing files corrected

#### `03_Sandhi_and_Samasa_Tools\samasa\combined_splitter.py`

The main integration file, extended. Its public API is unchanged, and `--test` (corpus smoke test + `_self_check()`) still passes on both your machine and the cloud copy.

| Change | Why (what the Sarga 1 comparison showed) |
|---|---|
| **`deterministic_junction(t1, t2)`**: a rule table applied to the *printed* word endings whenever `samasa_splitter.restore_word_boundary()` returns nothing or "as printed". It covers 17 junction types, each with its sūtra:<br>• anusvāra 8.3.23<br>• jaśtva 8.2.39<br>• ścutva 8.4.40<br>• anunāsika 8.4.45<br>• jhayo ho 8.4.62<br>• repha/rutva 8.2.66<br>• o-kāra + avagraha 6.1.113–114/6.1.109<br>• satva<br>• visarga-lopa 8.3.17/19<br>• sa-lopa 6.1.132<br>• ayādi 6.1.78<br>• yaṇ 6.1.77<br>• pūrvarūpa 6.1.109<br>• ṃs+t 8.3.7<br>• ṅamuṭ 8.3.32<br>• khar-para śar | The old path named only 88 of 301 real junctions. The third-party `sandhi` package often returns the token unchanged even for regular sandhi. Reading the printed endings is deterministic and needs no dictionary. |
| Avagraha citation fix: `'pi` → `api` | Citation forms carried the ऽ into later lookups. |
| **`split_fused_token()`**: splits a single printed token only under strict conditions:<br>• the whole token is not already a validated word or compound<br>• the left piece is a closed-class word or carries an overt inflection<br>• the right piece is a real word | Closes PROJECT_STATE **open item 8** (`caitat`-class orphans) without reintroducing the proven "split every token" 99 %-error regression. It went from 0/43 to 37/43. Of the 6 still wrong, 2 are split at the right place but with the wrong vowel restored (च+ऐक° for च+एक°). |
| Samāsa now comes from the new `samasa_classifier` (the old decision is kept as `samasa_legacy`) | The old path left 90 of 100 compounds "uncertain" and gave the right type for 3. |
| Deterministic ordering of all candidates | Python randomises set order per process. Your machine and the cloud copy produced different outputs until every tie-break was made explicit. They are now byte-identical (checked again today on Sarga 2 v. 11–20). |

#### `03_Sandhi_and_Samasa_Tools\samasa\samasa_splitter.py`

| Change | Why |
|---|---|
| `CASE_ENDING_TABLE_WX`: typo `"Anam"` → `"AnAm"` (genitive plural -ānām) | The typo meant no genitive plural was ever stripped. |
| Added the missing endings `ANAm`, `eNa`, `EH`, `eByaH`, `ayoH` | Common a-stem forms (रामेण, देवैः, देवेभ्यः) were not being recognised. |

#### `02_Sanskrit_Grammar_Engine\scripts\citation_lookup.py`

| Change | Why |
|---|---|
| Dvigu citation: garbled `"2.1.51 (दvigu-1…)"` → **2.1.52** संख्यापूर्वो द्विगुः | Wrong sūtra number and mixed-script text. |
| Nañ-tatpuruṣa citation: 2.2.61 → **2.2.6** नञ् | Wrong sūtra number. |
| Added `satva-sandhiḥ` and every new junction type to `SANDHI_TYPE_CITATIONS`. Each rule id was checked against `sandhi_rulebook.json`; where the rulebook has no entry (6.1.132, 8.3.7) it is marked `sandhi_rulebook.json-बहिः` instead of inventing an id. | Rows for these types previously had no citation. |
| `DEVANAGARI_SAMASA_CITATIONS` for the classifier's Devanagari type names | Needed so the 10-component report and the new CLI can cite samāsa types. |

**Checked on your machine today.** `generate_10component_quality_report.py` still runs with these changes. For verses 1.1.6–10 its Sandhi column now fills 19 of 54 words (was 14) and its Samāsa column 14 of 54 (was 12).

### 3b. New files, and why they were needed

| New file | What it does | Built only from |
|---|---|---|
| `03_Sandhi_and_Samasa_Tools\morphology\pada_analyser.py` (918 lines) | Morphology for one word. Nouns: prātipadika, vibhakti, vacana, liṅga and model word, found by inverting the Śabdamañjarī declension tables into ending rules and checking each candidate stem against the lexicon. Verbs: dhātu, gaṇa, lakāra, puruṣa, vacana and pada, learned from the Dhatu-Lakara paradigms over all 2,259 Dhatu-Manjari roots. Indeclinables: closed list, kṛt (क्त्वा/ल्यप्/तुमुन्) and taddhita (तसिल्, वति …). Participles (क्त, शतृ, शानच् …). Every reading carries its evidence and a confidence level. | `sabdamanjari_vibhakti_tables.json`, `Dhatu-Lakara.json`, `Dhatu-Manjari.json`, `lexicon_index.json` |
| `03_Sandhi_and_Samasa_Tools\samasa\samasa_classifier.py` | Finds compound members on the stem after the ending is stripped, with guards (an upasarga is not a member; no suffix scraps; participles are not split). Assigns the type with an explicit, sūtra-cited reason: नञ्, सह, उपपद, द्विगु/सङ्ख्या, तृतीया-तत्पुरुष, कर्मधारय vs बहुव्रीहि by adjective-first + gender test, default तत्पुरुष. | pada_analyser + lexicon |
| `03_Sandhi_and_Samasa_Tools\sarga_analyser.py` | **The terminal tool you asked for.** It writes your six-column analysis for any kāṇḍa/sarga/verse range as xlsx, md or json. A seventh column shows how each row was obtained (validated / rule / guess), and guesses are highlighted amber. Optional `--gold` scores the run against a hand analysis. | everything above |
| `03_Sandhi_and_Samasa_Tools\morphology\run_morphology.py` | Helper used by `--gold` scoring. | — |
| `05_Sanskrit_Dictionaries\build_lexicon_index.py` → `lexicon_index.json` | A single index of 241,163 headwords from MW + Apte + SKD, with gender, adjective, root and indeclinable tags. `apte_dictionary.sqlite` alone was missing common words (वीर्य), so correct stems were being rejected. | `mw.txt`, `sanskrit_dictionary_skd_apte.sqlite` |
| `engine_validation\*.py` | The scorer (`compare_with_gold.py`), runners for the BEFORE baseline, and `eval_samasa.py`. | — |

**No .json data file was edited.** The JSON sources (Śabdamañjarī tables, Dhatu-Lakara, Dhatu-Manjari, `sandhi_rulebook.json`) were found correct wherever they were used. The problems were in how the Python read them. Two examples: numeral tables use gender columns, not vacana columns; and table forms are written with anusvāra (रमां) where lookup needs the class nasal. Both are handled in code, and the data is untouched. The one new JSON (`lexicon_index.json`) is generated and can be rebuilt at any time with `build_lexicon_index.py`.

---

## 4. What could NOT be fixed, and why

The remaining errors on Sarga 1 are listed in `scorecard_AFTER.md`. They fall into these groups:

| Remaining error class (Sarga 1 count) | Why it is not fixed | What would fix it |
|---|---|---|
| **Samāsa semantics:** बहुव्रीहि vs कर्मधारय vs तत्पुरुष (26 type errors), द्वन्द्व missed | The type depends on meaning and context. पीनवक्षाः is बहुव्रीहि only because it describes Rāma, and nothing in the word itself says so. | An agreement pass: if the compound's gender/case follows a noun elsewhere in the verse, it is a बहुव्रीहि. Plus a small द्वन्द्व lexicon (pairs such as रामलक्ष्मणौ, and dual/plural endings on a stem of two nouns). |
| **Samāsa missed (38) / invented (20):** proper names (भरद्वाज, सुग्रीव), lexicalised words | A name looks exactly like a compound, and the gold treats most names as N/A. | A proper-noun list, generated once from the sarga indexes or MW's "N. of" entries, used to stop splitting. |
| **Vibhakti/vacana wrong (59)**, mostly -am (acc. masc. vs nom./acc. neut.) and -āḥ | Needs the gender of the stem *and* sentence agreement. MW gender tags are noisy. | A gender-clean lexicon (only the first grammatical label, already started) and a verse-level agreement pass. |
| **-āḥ before a voiced sound (4 junctions)** | रामा गच्छन्ति could be -āḥ (visarga-lopa) or plain -ā. Both are grammatical, so no rule can decide. | Decide using the morphology score of both readings (partly done) plus agreement. |
| **7 finite verbs:** कथयामास (periphrastic split across tokens), महीयते, प्रमुच्यते, मज्जन्ति, आयात्, शंसत् | These roots and stems are not among the 30 fully conjugated roots in `Dhatu-Lakara.json`, so the analyser has to guess their present stems. | **The single highest-value data addition:** fuller paradigms (or at least present stems) for the common roots, e.g. a Dhātupāṭha stem list with present stem, passive and perfect for each root. |
| **Prātipadika wrong (112):** lexicon noise (पश्यत, वीक्ष entered as nouns), wrong root for a correct form | 241k headwords includes rare words that match accidentally. | A frequency or "common word" flag in `lexicon_index.json`, used as a tie-breaker. |
| **Translation column** | There is no translation engine in the project. | `--translations` accepts a file of your own translations. The hand treatise remains the source. |
| **`sanskrit_grammar_engine.py`** itself | Not touched. It is Library-only for verses 1–5 by design (Stages 30–49), and the Stage protocol governs it. | Out of scope for this pass. |

**One small trade-off to know about.** The final śatṛ/tasil fix corrected ब्रुवतः, वीक्षतः (now षष्ठी of the participle) and सर्वतः (tasil). On Sarga 1 the samāsa count moved by one word (148 → 147 found; precision 88.6 % → 88.0 %). Every other measure stayed the same or improved.

---

## 5. Roadmap: bringing the tools up to the hand treatise

In order of payoff per effort:

1. **Present stems / paradigms for common roots** (data). This fixes most remaining verb misses and many wrong prātipadikas.
2. **Verse-level agreement pass** (code, in `sarga_analyser.py`). It resolves -am/-āḥ gender and case, and बहुव्रीहि vs कर्मधारय. I estimate +4–6 points on vibhakti and samāsa type.
3. **Proper-noun list** (data). It stops false compound splits of names.
4. **द्वन्द्व detection** (code + small list).
5. **Frequency flag in `lexicon_index.json`** (data), to cut lexicon noise.
6. **Grow the gold set.** Every sarga you hand-check becomes a new held-out test. Run `sarga_analyser.py … --gold <folder>` after any change, alongside `combined_splitter.py --test`.

---

## 6. How to run it

From `03_Sandhi_and_Samasa_Tools`:

```
python sarga_analyser.py --kanda 1 --sarga 2
python sarga_analyser.py --kanda 1 --sarga 2 --verses 1-10 --out ..\01_Ramayana_Project\analysis\bala_kanda_sarga_002
python sarga_analyser.py --kanda 1 --sarga 1 --out ..\01_Ramayana_Project\analysis\bala_kanda_sarga_001\auto_analysis --gold ..\01_Ramayana_Project\analysis\bala_kanda_sarga_001\working_files
python samasa\combined_splitter.py --test
```

Requirements: Python 3.10+, `pip install indic_transliteration sandhi openpyxl`.

Run times on your machine: about 30 s for 10 verses, about 3 min for a full sarga.

The full-sarga automatic output is in `auto_analysis\` (`sanskrit_analysis_auto.xlsx/.md/.json` + scorecard). Read it side by side with the hand treatise: the amber rows are the ones to check.
