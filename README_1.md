# Sanskrit Grammar Engine

A single evolving Python engine for generating an auditable Sanskrit grammatical treatise from Sanskrit source material, beginning with a deliberately closed benchmark: Vālmīki Rāmāyaṇa, Bālakāṇḍa, Sarga 1, ślokas 1.1.1–1.1.5.

## Deliverable model

The only evolving implementation deliverable is:

`sanskrit_grammar_engine.py`

Historical Stage artifacts are development history. They are not separate engines and should not be required for normal operation of the current engine.

Project-state files are durable control documents:

- `PROJECT_STATE.md` — current authoritative project state.
- `README.md` — operating contract.
- `CHANGELOG.md` — concise evolution history.

Do not create a separate `memory.md` or `summary.md`; those would duplicate state and create synchronization risk.

## Source policy

All grammatical treatise content must be grounded in material available in the Library. The engine must not use external web grammar content as evidence. If Library evidence is absent, the engine must return GAP or NOT_ASSERTED.

The Library Rāmāyaṇa file is authoritative for the five benchmark source verses. The Library comprehensive template is authoritative for the requested treatise component structure.

## Treatise contract

The engine works toward these components:

1. पदच्छेदः + gloss
2. अन्वयः
3. पद-विग्रहः
4. कारकः
5. शब्दरूपाणि
6. धातुरूपाणि
7. प्रत्ययाः
8. सन्धिः
9. समासः
10. छन्दस् / अलङ्कारः
11. runtime प्रश्नोत्तरी

Component 1 is authoritative for the word inventory. All other components must reconcile with it.

## Evidence classes

`SOURCE_ASSERTION` means the source/template explicitly asserts the analysis.

`COMPUTED_EVIDENCE` means a deterministic exact join or lookup produced the result from Library-derived records.

`MATCH`, `AMBIGUOUS`, `GAP`, and `NOT_ASSERTED` are outcome states. An exact lexical match must not be promoted to a stronger scholarly assertion than its source supports.

## Development method

This is a closed-loop benchmark project. The five verses remain fixed through the Stage-30 review and all subsequent benchmark-improvement cycles.

Each user-authorized cycle is:

`generate → audit → identify highest-value gap → retrieve Library evidence → update engine → regression test → measure → stop`

Do not expand the corpus simply to increase the apparent amount of progress.

## Determinism rules

- exact matching only
- no fuzzy matching
- no silent inference
- preserve ambiguity
- preserve source provenance
- do not reinterpret identifier namespaces
- do not convert rule references into productive rules without sufficient operational evidence
- keep source text immutable

## Running the engine

From a terminal:

```text
python sanskrit_grammar_engine.py
python sanskrit_grammar_engine.py --gap-report
python sanskrit_grammar_engine.py --benchmark
python sanskrit_grammar_engine.py --benchmark-out benchmark.json
python sanskrit_grammar_engine.py --verse 1.1.1
```

The benchmark command generates the current engine-generated five-śloka treatise scaffold and its evidence audit. The engine deliberately reports gaps instead of inventing unsupported grammar.

## 99% target

The target is approximately 99% **evidence-backed grammatical coverage**, not merely 99% populated fields. A successful engine must also preserve ambiguity and expose unsupported claims. Stage 30 established the measurement framework; v0.3 currently reports 30.91% supported/source-asserted component-slot coverage after integrating the seven complete 1.1.1 Subanta paradigms explicitly supplied by the Library template.

Before claiming 99%, the benchmark must undergo a formal correctness/evidence review.

## New-conversation handoff

When starting a new conversation, instruct the assistant to read:

1. `PROJECT_STATE.md`
2. `README.md`
3. `CHANGELOG.md`
4. the current `sanskrit_grammar_engine.py`

Then request exactly one improvement cycle. Do not rely on the previous chat as project memory.

## Parallel track: Sandhi/Samāsa Combined Engine + 10-Component Quality Report

A second deliverable line, separate from `sanskrit_grammar_engine.py` and not part of its Stage-N sequence, lives across `03_Sandhi_and_Samasa_Tools\{sandhi,samasa}`, `02_Sanskrit_Grammar_Engine\scripts`, and `04_Laghu_Siddhanta_Kaumudi`. It produces the Excel 10-component quality report (`01_Ramayana_Project\quality_reports\`) for verses 1.1.1–1.1.5. See the **"PARALLEL TRACK"** section at the end of `PROJECT_STATE.md` for its full state, architecture, the critical `analyze_pada_line`-vs-`split_word_recursive` methodology finding, and open items. Read that section (not just this one) before resuming that track.
