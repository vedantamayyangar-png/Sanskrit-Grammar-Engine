# Dhaturupa Manjari & Sabdamanjari Extraction

A page-by-page manual transcription of two scanned, image-only Sanskrit
reference books into structured JSON, so the wider project's grammar
engines can consult them locally instead of hitting external sources.

## Sources

- `E:\Downloads\Dhaturupa Manjari - RS Vadhyar 2001.pdf` — 167 pages, verb
  conjugation (धातुरूप) reference covering all 10 गणs plus a separate
  आर्धधातुक section. **In progress.**
- `E:\Downloads\Sabdamanjari.pdf` — noun declension (शब्दरूप) reference.
  **Not yet started.**

Both PDFs are scanned page images with **no embedded text layer**
(confirmed: `pypdf`/`pdfplumber` text extraction returns empty strings on
every page; Producer metadata confirms an image-conversion scan). OCR is
not used — Tesseract is not installed in this environment and Devanagari
OCR is unreliable even where available. Every entry in the output JSON is
read directly from a rendered page image and transcribed by hand.

## Deliverables

- `E:\Sanskrit & Tamil Scholarship\04_Laghu_Siddhanta_Kaumudi\dhaturupa_manjari.json` — in progress, built incrementally गण by गण.
- A future `sabdamanjari.json` in the same folder — not yet started.

Project-state files are durable control documents, matching this project's
established convention (see `01_Ramayana_Project\project_docs`):

- `PROJECT_STATE.md` — current authoritative extraction state (which गणs/
  sections are done, what's pending, known scan-quality issues).
- `README.md` — this file, the operating contract.
- `CHANGELOG.md` — dated, concrete history of each incremental delivery.

Do not create a separate `memory.md` or `summary.md` — see PROJECT_STATE.md
for why (duplication/synchronization risk).

## Method

1. **Incremental, section by section** — the user explicitly chose this
   over a single continuous pass, given the source is 167 pages of scanned
   images requiring manual transcription. Each increment delivers one
   coherent unit (one गण, or one clearly-bounded sub-section) as a
   self-contained addition to the JSON, sent to the user for review before
   the next increment begins.
2. **Never fabricate.** If a scanned cell is faded/illegible, either
   re-render it at higher resolution and re-read it, or reconstruct it
   from the invariant grammatical rule for that cell's own paradigm slot
   — and if reconstructed, say so explicitly in a `note` field on that
   entry. Never silently guess and present a guess as a direct reading.
3. **Verify structural claims against the book's own text**, not assumed
   pedagogical convention — e.g. this book does NOT conjugate roots in a
   fixed 1→72 list order within a गण; it groups them by shared paradigm
   pattern instead, with "एवं (roots)...रूपाणि द्रष्टव्यानि" closing notes
   cross-referencing the numbered list. Confirmed by direct page-by-page
   reading, not assumed from गण 1's simpler two-model layout.
4. **Cross-check every closing "एवं" grouping note's root numbers against
   the JSON's own already-transcribed root list** before trusting a
   guessed/faded root name in that note — a real misattribution was found
   and fixed this way (see CHANGELOG).

## Rendering pages without external network OCR

- Preferred: `pypdfium2` (Python), rendering each page to a PNG at a given
  scale, then reading the PNG directly. Requires a working Python — on
  this machine that is `D:\python\python.exe` (bare `python`/`py` are NOT
  on PATH in a fresh PowerShell session; see `sandhi-splitter-maintenance`
  skill for the same finding in a different context).
- Fallback if Python is unreachable in a session: open the PDF in a local
  desktop PDF viewer (e.g. Adobe Acrobat) via computer-use / desktop
  control and read pages directly off the rendered viewer — see
  CHANGELOG for a worked example of when this was needed and what to
  watch out for (granting a browser at "read" tier can surface an
  unrelated pre-existing browser window; avoid interacting with it).

## New-conversation handoff

When starting a new conversation for this track, instruct the assistant to
read, in order:

1. `PROJECT_STATE.md` (this folder)
2. `README.md` (this file)
3. `CHANGELOG.md` (this folder)
4. the current `dhaturupa_manjari.json`

Then continue with the next undelivered गण/section only — do not restart
from गण 1, and do not expand scope to Sabdamanjari until Dhaturupa Manjari
is complete, unless the user explicitly redirects.
