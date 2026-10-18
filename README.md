# Bāla Kāṇḍa, Sarga 1: working files

These files produced `sanskrit_analysis.xlsx`, `sanskrit_analysis_tables.md` and `build_sanskrit_analysis.py` in the folder above.

## What each file is

| File | Role |
|---|---|
| `sarga1_iast.txt` | The input: verses R_1,001.001–079 copied from `source_texts\sa_rAmAyaNa.txt` (GRETIL, IAST). |
| `translit.py` | Converts IAST to Devanagari and splits the text into verses and tokens. Fully mechanical. |
| `lib.py` | Formatting helpers. `n(case, number, gender)` expands to the sup-pratyaya and its labels (e.g. «अम्» — द्वितीया, एकवचनम्…). `v(lakāra, puruṣa, vacana, pada)` does the same for tiṅ endings. `av()` covers avyayas and `kr()` covers क्त्वा/ल्यप्/तुमुन्. The file also holds the sandhi-rule strings used again and again (O_SOFT, SH_C, YAN, GUNA …). |
| `d01.py` … `d08.py` | **The analysis itself**, 10 verses per file. `V[n] = (translation, [rows])`, and each row is `(मूलपदम्, सन्धि, उपसर्गः, प्रातिपदिकम्, विभक्तिः…, समासः)`. These rows were written by hand (by Claude), not computed. |
| `check_rows.py` | Checks that no verse has fewer rows than words. |
| `gen.py` | Puts it all together: writes `out/build_sanskrit_analysis.py`, runs it to make the xlsx, and writes the markdown tables. |

## To fix an error and rebuild

1. Find the verse in `dNN.py` (verse 34 is in `d04.py`) and edit that row.
2. `python check_rows.py`
3. `python gen.py`. The new files appear in `out\`.

Needs Python 3 and `pip install openpyxl`.

## Using these as a learning / test set

Each row names the Pāṇinian sūtra, so the d-files work as a labelled answer key. You can check your sandhi splitter, samāsa splitter and grammar engine against them word by word. Rows marked «आर्षप्रयोगः» or «GRETIL-पाठे …» flag epic irregularities and places where the source text probably has a typo.
