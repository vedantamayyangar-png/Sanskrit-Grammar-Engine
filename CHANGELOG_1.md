# Changelog — Dhaturupa Manjari & Sabdamanjari Extraction

## Sabdamanjari — section 4 (अजन्त पुंलिङ्ग विशेषशब्दाः) complete, 20 words — भाग-2 (विशेष शब्दाः) begun

- **Section 4 (अजन्त पुंलिङ्ग विशेषशब्दाः — special/irregular masculine words), COMPLETE**: 20 words (ऐक्ष्वाक, निर्जर, दन्त, पाद, यूष, मास, विश्वपा, हाहा, औडुलोमि, पति, सखि, प्रधी, वातप्रमी, सुधी, सेनानी, क्रोष्टु, वर्षाभू, स्वभू, नृ, रै), PDF pp.22-33 (book pp.22-33). This is भाग-2's first subsection — the book's own two-part division (भाग-1 = साधारण/ordinary, भाग-2 = विशेष/special) confirmed by direct read.
- **Two genuine patronymic vṛddhi/guṇa alternations** confirmed: ऐक्ष्वाक (word 30) and औडुलोमि (word 38) both take वृद्धि (ऐ/औ) in एकवचन/द्विवचन but गुण (इ/उ) in बहुवचन — not an error, a real Paninian rule for descent-names.
- **Several words carry two parallel declension tracks** (a contracted consonant-stem alongside a fuller vowel-stem), all transcribed verbatim hyphen-joined as printed: निर्जर (निर्जर-/निर्जरस्-), दन्त (दन्त-/दत्-), पाद (पाद-/पद्-), यूष (यूष-/यूष्ण्-), मास (मास-/मा-), क्रोष्टु (agent-noun ऋ-stem/plain उ-stem).
- **दन्त (word 32) shows an unusual पञ्चमी=षष्ठी syncretism** (both द्विवचन and बहुवचन identical in both its tracks) confirmed by repeated zoom — flagged as a likely genuine feature of this word's origin as an old root-noun (मूलतः दत्) rather than a print error, since the structurally parallel पाद (word 33), checked immediately after specifically to test this, does NOT show the same merge.
- **वातप्रमी/सुधी/सेनानी (words 42-44) share an alternate षष्ठी-बहुवचन ending in -याम्** (वातप्रम्याम्, सुधियाम्, सेनान्याम्) instead of the more common -नाम् (used by प्रधी, word 41) — cross-checked across all four ईकारान्त-विशेष words before concluding this is a genuine recurring sub-pattern, not an isolated misread.
- **One cell corrected rather than transcribed as scanned**: औडुलोमि's (word 38) षष्ठी/सप्तमी एकवचन printed with wrong medial consonants (औषुलोमेः, औहुलोमौ — ष्/ह् where ड् is required by every other cell in the same word's table); corrected to औडुलोमेः/औडुलोमौ with a note, judged a probable compositor error in the source rather than a misreading here (glyphs were unambiguous at zoom).
- **One cell flagged as reconstructed rather than confidently read**: नृ's (word 48) तृतीया/चतुर्थी एकवचन and षष्ठी/सप्तमी द्विवचन glyphs stayed ambiguous between 'न्र' and 'त्र' even after repeated high-zoom re-renders; reconstructed as नरा/नरे/नरोः from the invariant गुण rule for this bare ऋ root-noun.
- **One grouped word name flagged illegible**: in वर्षाभू's (word 46) grouping note, one name between खलपू and पुनर्भू could not be confidently read even at zoom; left unresolved rather than guessed, and the note also captured a footnoted exception for हूहू (which does NOT follow वर्षाभू's own contraction pattern in द्वितीया).
- Validated `sabdamanjari.json` with PowerShell's `ConvertFrom-Json` (11 + 10 + 8 + 20 = 49 words across four sections).
- **Next task: Section 5 (अथ अजन्त स्त्रीलिङ्ग विशेष शब्दाः, special feminine words), starting word #50 अम्बा, PDF p.34.**

## Sabdamanjari — section 3 (अजन्त नपुंसकलिङ्ग साधारण शब्दाः) complete, 8 words — MILESTONE: भाग-1 (साधारण शब्दाः) fully closed

- **Section 3 (अजन्त नपुंसकलिङ्ग साधारण शब्दाः — vowel-ending neuter words), COMPLETE**: 8 model words (वन, नगर, दधि, वारि, शुचि, मधु, मृदु, कर्तृ), PDF pp.17-21 (book pp.16-21).
- **Captured a general structural rule** (printed once, before word #24, governing the whole neuter list): (1) नपुंसकलिङ्ग words always have प्रथमा = द्वितीया, meaning/case inferred from context; (2) तृतीया onward is identical to the masculine declension of the same stem class. Recorded as the section's own `general_rule_note`.
- **णत्व rule seen operating word-internally**: नगर (word 23) contrasts with वन (word 22) — नगर's own र् triggers न्→ण् in its bahuvacana (नगराणि/नगराणाम् vs वनानि/वनानाम्), same rule already noted cross-word for देव (section 1, word 2) and again for श्मश्रु (this section, attached to मधु/word 27's grouping note).
- **Two distinct इकारान्त-नपुंसक sub-patterns identified**: दधि (word 24) takes a strong न्-stem contraction (दध्ना, दध्ने, दध्नः...) resembling न्-stem nouns, while वारि (word 25) stays a plain इ-stem throughout (वारिणा, वारिणे...) — flagged as a structural distinction the book itself doesn't spell out explicitly, inferred from the two tables.
- **शुचि (word 26, "pure") and मृदु (word 28, "soft") are this book's first adjectives** among the अजन्त-साधारण words (all prior words were nouns) — each shows two full alternate declension tracks (न्-stem vs. plain/गुण-stem), both transcribed verbatim, hyphen-joined exactly as printed.
- **One cell required reconstruction rather than a confident direct read**: कर्तृ's (word 29) षष्ठी/सप्तमी द्विवचन alternate contraction — repeated high-zoom re-renders kept showing what looked like an invalid 'कत्रोः' (missing repha); reconstructed as 'कर्त्रोः' by direct analogy to पितृ/भ्रातृ's own confirmed -त्रोः contraction pattern (section 1, words 8-9), flagged with `provenance: direct_read_with_one_reconstructed_cell` rather than asserted as a plain read.
- **MILESTONE: भाग-1 'साधारण शब्दाः' (ordinary words) is now fully closed** — all 29 words across sections 1-3 (11 पुंलिङ्ग + 10 स्त्रीलिङ्ग + 8 नपुंसकलिङ्ग). PDF p.22 opens भाग-2 'विशेष शब्दाः' (special/irregular words), section 4, '४. अजन्त पुंलिङ्ग विशेषशब्दाः', starting word #30 ऐक्ष्वाक — confirmed by direct read but not yet transcribed.
- Validated `sabdamanjari.json` with PowerShell's `ConvertFrom-Json` (11 + 10 + 8 = 29 words across three sections).
- **Next task: Section 4 (अजन्त पुंलिङ्ग विशेषशब्दाः, special/irregular masculine words), starting word #30 ऐक्ष्वाक, PDF p.22.**

## Sabdamanjari — section 2 (अजन्त स्त्रीलिङ्ग साधारण शब्दाः) complete, 10 words

- **Section 2 (अजन्त स्त्रीलिङ्ग साधारण शब्दाः — vowel-ending feminine words), COMPLETE**: 10 model words (रमा, मति, गौरी, नदी, धेनु, वधू, मातृ, स्वसृ, द्यो, नौ), each with full 8-row table, Tamil+English gloss, grouping note where printed. PDF pp.12-17 (book pp.11-16).
- मति (word 13) and धेनु (word 16) each show two alternative case-forms (stem-vowel vs. गुण/vṛddhi-stem) in चतुर्थी/पञ्चमी/षष्ठी/सप्तमी, joined by hyphen in the book — transcribed both options verbatim rather than picking one.
- गौरी (word 14) and नदी (word 15) are both ईकारान्त but printed as two separate models; the book gives no explicit rule text distinguishing them beyond the two tables themselves — flagged as a structural observation rather than asserted as a firm rule.
- वधू's (word 17) grouping note carries a parenthetical remark '(श्वश्रूः-श्वश्रूणाम्)' flagging श्वश्रू's own प्रथमा/षष्ठी-बहुवचन forms — transcribed verbatim.
- द्यो (word 20) mirrors गो's (section 1, word 10) irregular ओकारान्त shape as its feminine counterpart. स्वसृ (word 19) and द्यो/नौ (words 20-21) have no grouping notes — each a one-off paradigm in this book's list, same pattern as गो/ग्लौ in section 1.
- One transcription correction caught mid-pass: द्वितीया-एकवचन cells for रमा/नदी/वधू/द्यो/नौ are printed with an anusvāra diacritic (रमां, नदीं, वधूं, द्यां, नावं) rather than the spelled-out final न्+म् — matched to the scan exactly rather than normalized, after a first-pass zoom check on नदीं caught a stray-mark misread ("नर्दीं") that a closer re-zoom resolved.
- Validated `sabdamanjari.json` with PowerShell's `ConvertFrom-Json` (11 + 10 = 21 words across both sections).
- **Next task: Section 3 (अजन्त नपुंसकलिङ्ग साधारण शब्दाः, neuter vowel-ending words), starting PDF p.17** — confirmed to begin immediately after word 21 with no gap.

## Sabdamanjari — track started, section 1 (अजन्त पुंलिङ्ग साधारण शब्दाः) complete, 11 words

- **User explicitly asked to switch to Sabdamanjari** (the noun-declension companion book), overriding PROJECT_STATE.md's prior "do not begin until Dhaturupa Manjari is complete" note — per that note's own escape clause. Dhaturupa Manjari's आर्धधातुकप्रकरण work (लिट् partial, लुङ् not started) is left exactly where it stood; resume it separately when asked.
- **New file: `sabdamanjari.json`** (sibling of `dhaturupa_manjari.json` in this same folder). Source: `E:\Downloads\Sabdamanjari.pdf` (116 pages, no text layer, same scanned-image situation as the verb book — confirmed by direct rendering, not assumed). Publisher: Samskrit Education Society, Chennai (same publisher as Dhaturupa Manjari); scan interleaves a 4th-edition (2005) cover with a 3rd-edition (2003) inner title page, flagged in the JSON's `source_book` block rather than silently picking one.
- **Also present in this project: a pre-existing, independently-authored `vibhakti_table.json`** (used by `generate_10component_quality_report.py`). This is NOT the same file as the user's `E:\Downloads\vibhakti_table.json` reference copy, and is NOT derived from this new extraction — both cover overlapping stem classes (राम, मुनि, गुरु, रमा) and can be cross-checked against each other, but are deliberately kept as separate, independently-sourced files. Documented the relationship in `sabdamanjari.json`'s own `related_files` block so this isn't lost.
- **Section 1 (अजन्त पुंलिङ्ग साधारण शब्दाः — vowel-ending masculine words), COMPLETE**: all 11 model words (राम, देव, हरि, मुनि, शम्भु, गुरु, धातृ, पितृ, भ्रातृ, गो, ग्लौ), each with a full 8-row declension table (7 विभक्तिs + संबोधनम्, all 3 numbers), Tamil+English meaning gloss, and the book's own "एवं...प्रभृतयः" grouping note listing further words on the same pattern. PDF pp.6-12 (book pp.5-11).
- Also captured the book's **णत्व sandhi rule note** (attached to देव, PDF p.7): तृतीया एकवचन / षष्ठी बहुवचन न→ण after र्/ष्/ऋ, with रामेण vs. देवेन as the book's own contrast pair.
- **One read required a confidence correction caught before finalizing**: गो's सप्तमी बहुवचन initially misread as "गोपु" at low zoom; re-rendered at scale=10 and confirmed "गोषु" (matching the expected Paninian ऋ/उ-diphthong sandhi outcome) — corrected before writing to JSON, per the project's standing never-fabricate/never-silently-smooth-over rule. Documented in the word's own `note` field for future auditability.
- पितृ (word 8) has no grouping note printed directly under it in the book; the following word भ्रातृ's "एवं जामातृ प्रभृतयः" note likely covers both (same contracted-vowel kinship paradigm, distinct from धातृ's agent-noun paradigm) — flagged as a structural inference in a `note` field rather than asserted outright.
- Validated `sabdamanjari.json` with PowerShell's `ConvertFrom-Json`.
- **Next task: Section 2 (अजन्त स्त्रीलिङ्ग साधारण शब्दाः, feminine vowel-ending words), starting word #12 रमा, PDF p.12** — confirmed to begin immediately after word 11 with no gap.

## आर्धधातुकप्रकरण — delivery 1: लुट्/लृट्/लृङ्/आशीर्लिङ् complete, लिट् partial (नया top-level JSON key)

- **Started आर्धधातुकप्रकरण**, the book's second major division (PDF p.121, right after गण 7 closed the सार्वधातुकप्रकरण). Added a NEW top-level JSON key `ardhadhatuka_prakarana` (sibling of `ganas`, not nested in it) since this section is organized लकार-by-लकार across all गणs together, a genuinely different structure -- confirmed by direct reading, not assumed.
- **सेट्/अनिट्/वेट् इट्-आगम rules** (the section's own opening explanation) captured in full.
- **लुट् (First Future), लृट् (Second Future), लृङ् (Conditional): all COMPLETE** -- प्रत्यय tables for both पदs plus सेट्/अनिट् contrast examples (भू, जि, भाष्, लभ्). Also captured the book's own excellent **32-root comparison table** ("the most difficult forms of the 3rd person singular of लुट्, लृट् and लृङ्"), giving all three future/conditional 3rd-sg. forms side by side for 32 tricky roots across परस्मै/आत्मने/उभय -- a very efficient, high-value systematic reference (PDF pp.121-123).
- **आशीर्लिङ् (Benedictive): COMPLETE** -- प्रत्यय table, 3 examples (भू, एध्, लभ्), and 5 special root-transformation rules (e.g. दा→देयात्, roots dropping their penultimate nasal).
- **लिट् (Perfect): PARTIAL.** Captured the book's own 7 rules distinguishing द्वित्वलिट् (reduplicative) from अनुप्रयोगलिट् (periphrastic), द्वित्वलिट्'s प्रत्यय table, its भू/भाष् examples, and **16 numbered special-root-groups** -- each a full irregular-reduplication 3×3 table (e.g. गम्→जगाम, दृश्→ददर्श, चि→चिचाय) plus an "एवं...रूपाणि" note grouping further roots onto that same pattern. This is dense, valuable data: group #4 (चर्) alone groups 22 further roots.
- **NOT yet captured**: द्वित्वलिट्'s special-root-groups beyond #16 (the book's own sequence continues -- root #16 चि is marked "प्रथमं रूपम्", implying more follows), all of अनुप्रयोगलिट्, and लुङ् (Aorist, 7 traditional प्रकरणs) in its entirety.
- A few cells (लृट् comparison table's कृप् row, लिट् group #13's कृप् entry, group #2's grouped-root list) were read at moderate confidence from dense/small-print scan regions and are flagged in their own `note` fields.
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json`.
- **Next task: continue द्वित्वलिट्'s remaining special-root-groups, then अनुप्रयोगलिट्, then लुङ्** -- see PROJECT_STATE.md's next-cycle protocol.

## गणs 8 (तनादि), 9 (क्र्यादि), 7 (रुधादि) — delivery 1, all complete: MILESTONE — all 10 गणs done, सार्वधातुकप्रकरण closed

- **गण 8 (तनादिः)**: the smallest traditional गण (10 roots total, all 10 listed — the book's header confirms "अत्र केवलं परस्मैपदिनो धातवः न सन्ति"). TWO full 3×3 models given (unusual for a small गण): तन् (covers roots #1-9 per the book's own footnote "Roots 1 to 9 are to be conjugated like तन्") and कृ ("to do" — given its own table specifically because it diverges from तन्'s shape, करोति/कुर्वन्ति vs तनोति/तन्वन्ति). PDF pp.99-103.
- **गण 9 (क्र्यादिः)**: ना-vikaraṇa (क्री+ना+ति=क्रीणाति). One full model, क्री ("to buy"), both पदs. 27 of 61 traditional roots listed, including a footnoted mnemonic verse for root धू showing it spans FIVE different गणs (5th/9th/6th/10th/1st) with the same meaning. PDF pp.104-107.
- **गण 7 (रुधादिः)**: न-infix vikaraṇa (रुध्+न+ति=रुणद्धि). **Uses the dense गण-2/3-style format** (many individually-conjugated roots with full tables and एवं-grouping notes), NOT the compact style of गण 1/4/5/6/8/9/10 — confirmed by direct reading, an important format-varies-by-गण finding recorded in PROJECT_STATE.md. 16 of 25 traditional roots listed; root list has a genuine numbering gap (#15 never printed anywhere, #14→#16 jump, verified by a targeted re-zoom). One root (#16 छुद्) is a pure list-only entry with no individual conjugation or grouping note at all. **This गण's closing marker ALSO closes the entire सार्वधातुकप्रकरण section of the book** ("॥ इति रुधादिः ॥" immediately followed by "॥ इति सार्वधातुकप्रकरणम् ॥", PDF p.120). PDF pp.108-120.
- A few cells in गण 7's अञ्ज् and तृह् entries (विधिलिङ् forms, retroflex ण्ढ clusters) were read at moderate confidence from dense/small-print scan regions and are flagged in their own `note` fields rather than asserted with full certainty.
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json` (all 10 गण keys now present: 1_bhvadi, 2_adadi, 3_juhotyadi, 4_divadi, 5_svadi, 6_tudadi, 7_rudhadi, 8_tanadi, 9_kryadi, 10_curadi).
- **MILESTONE: all 10 traditional गणs are now structurally complete.** The book's सार्वधातुकप्रकरण (PDF pp.9-120) is fully covered. Next task: आर्धधातुकप्रकरण (लृट्/लुट्/लृङ्/आशीर्लिङ्/लिट्, book pp.116-139) and लुङ्/Aorist (book pp.140-159, 7 varieties) — a structurally different section (covers all गणs' roots together, not गण-by-गण), needing a fresh JSON schema design rather than forcing it into the existing `ganas` shape.

## गणs 6 (तुदादि), 4 (दिवादि), 10 (चुरादि) — delivery 1, all complete: 7 of 10 गणs now done

- **Located and transcribed all three गणs the TOC-check identified as sitting between गण 1 and गण 2**: गण 6 (तुदादिः, PDF pp.25-28), गण 4 (दिवादिः, PDF pp.28-31), गण 10 (चुरादिः, PDF pp.32-38) — confirmed by direct reading, each opening immediately where the previous one's own closing marker appears (इति तुदादिः → चतुर्थगणः दिवादिः → इति दिवादिगणः → दशमगणः चुरादिः → इति चुरादिगणः), with no gaps.
- **Discovered and documented this book's "compact format" convention**, shared by गण 1, 4, 5, 6, and 10 (as opposed to गण 2/3's dense per-root full-table format): one or two model roots are given, but even the models are compact — only the प्रथमपुरुष (3rd person) row per लकार, with remaining persons explicitly deferred to गण 1's own भू/लभ् paradigms via a closing instruction ("इत्यादि भू/लभ् धातुवत् रूपाणि"). Captured in the JSON under new `..._pra_pu_only` keys rather than fabricating full 3×3 grids the book itself never gives.
- **गण 4 (दिवादिः)**: य-vikaraṇa, no गुण of the root vowel (contrast गण 1). Two compact models (दिव् परस्मैपदी, दीप् आत्मनेपदी). 54 of 140 traditional roots listed. One root-list entry (#17, फुल्ल्) had a genuinely degraded scan region (not just low-res); reconstructed from partial legibility + standard Paninian convention, explicitly flagged rather than asserted as a confident read.
- **गण 6 (तुदादिः)**: अ-vikaraṇa like गण 1, but the penultimate vowel stays unchanged (no गुण) — the book's own footnote rule, distinguishing it from गण 1's भवति-type गुण-taking अ. One compact model, तुद् itself (उभयपदी). 35 of 157 traditional roots listed.
- **गण 10 (चुरादिः)**: अय-vikaraṇa with गुण/वृद्धि conditioning rules (4 numbered rules transcribed in full from the book's own introduction) and a structural peculiarity confirmed from the book's own rule 4: only आत्मनेपदी and उभयपदी root-sets exist in this गण, no परस्मैपदी-only roots at all. One compact model, चुर् itself (उभयपदी). **110 of 410 traditional roots listed — the largest root-list transcription of any गण in this project so far**, all individually captured with footnotes (many चुरादि roots optionally belong to गण 1 or 4 as well) preserved per-root.
- **Added `reference.gana_presentation_order` to the JSON's top-level `reference` object**, recording the book's actual non-numeric गण order (1,6,4,10,2,3,5,8,9,7) with book-page numbers for each — so this structural fact is now load-bearing project state, not something to re-derive or re-confuse in a future session.
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json` (gana keys: 1_bhvadi, 2_adadi, 3_juhotyadi, 5_svadi, 4_divadi, 6_tudadi, 10_curadi — 7 of 10 गणs now present).
- **7 of 10 गणs now structurally complete.** Remaining: गण 7 (रुधादि, book p.103), गण 8 (तनादि, book p.94 — already partially glimpsed in an earlier session), गण 9 (क्र्यादि, book p.99), all confirmed present via the TOC and next in line.

## RESOLUTION: the "गण 4/6/7 missing" finding was a wrong ordering assumption, not missing content

- Checked the PDF's own front matter/table of contents (PDF pp.1-5) as requested, after the two prior delivery entries below flagged गण 4/6/7 as apparently absent.
- **The book's TOC (PDF p.4) proves it does NOT present the 10 गणs in numeric order.** Actual order: 1st (भ्वादि, p.9) → 6th (तुदादि, p.19) → 4th (दिवादि, p.22) → 10th (चुरादि, p.25) → 2nd (अदादि, p.33) → 3rd (जुहोत्यादि, p.74) → 5th (स्वादि, p.91) → 8th (तनादि, p.94) → 9th (क्र्यादि, p.99) → 7th (रुधादि, p.103) [all book-page numbers, not PDF indices].
- **गणs 4 (दिवादि), 6 (तुदादि) and 10 (चुरादि) are real, present content, located BEFORE गण 2 (अदादि)** — in the PDF page range this project never rendered, because earlier sessions assumed गण 2 would follow गण 1 immediately. They are NOT missing from the scan.
- The one genuinely-confirmed gap remains real and unaffected by this correction: **PDF page 83 (within गण 3) is still confirmed missing** — that finding used direct page-number-delta evidence specific to that location and doesn't depend on the ordering assumption that caused the गण-4/6/7 confusion.
- **PROJECT_STATE.md has been substantially rewritten** to reflect this correction and is now the authoritative source on this topic — the "गणs 4/6/7 missing" language in the two delivery entries below (गण 3 and गण 5 deliveries) is superseded by this entry; kept in place for the historical record of how the investigation unfolded, not as current guidance.
- **New top priority**: locate and transcribe गण 6, 4, and 10 (in that book order, or any convenient order), using the TOC's book-page numbers (19, 22, 25) plus the previously-established +6 book-page-to-PDF-index delta as a starting estimate for where to render.

## गण 5 (स्वादिः) — delivery 1, complete: root list + one full model, plus escalated finding on गणs 4/6/7

- **Transcribed गण 5 (स्वादि, नु-insertion conjugation) in full**: the gaṇa's own defining rule (PDF p.96: नु inserted before तिङ्-प्रत्यय, e.g. सु+नु+ति=सुनोति), its one full model root सु अभिषवे ("to press out juice", उभयपदी, both पद tables, PDF pp.96-97), and its root list (15 of 24 traditional roots, PDF p.98, unusually placed AFTER the model rather than before as in गण 1-3). Closing marker confirmed: "॥ इति स्वादिगणः ॥" (PDF p.98).
- **Escalated the गण-4 finding from delivery 1 (गण 3) into a confirmed 3-गण gap**: checked the pages immediately following गण 5's close and found गण 6 (तुदादि) and गण 7 (रुधादि) ALSO absent -- PDF p.98 closes गण 5 and PDF p.99 opens directly into गण 8 (तनादिः), with zero गण 6/7 content, headers, or page numbers in between. Combined with गण 3→5's earlier-confirmed gap (गण 4 missing), this means **three consecutive गणs (4, 6, 7) are absent from this PDF's page sequence**, while गण 1, 2, 3, 5, 8 are all present.
- **New working hypothesis**: गणs 1, 4, 6, 10 are traditionally the "thematic" (regular, mechanically-predictable) गणs, while 2, 3, 5, 7, 8, 9 are "athematic" (irregular, genuinely need memorized tables) -- this book may deliberately limit itself to the athematic गणs. Complicated by गण 1 (thematic) being fully present, so not yet certain; recorded as an open question rather than a conclusion, with a concrete next step (check the PDF's own front matter/TOC first).
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json` (गण keys now: 1_bhvadi, 2_adadi, 3_juhotyadi, 5_svadi -- deliberately no "4_divadi" key, since nothing exists to put in it; the gap itself is documented in गण 3's and गण 5's own notes[] fields rather than as an empty placeholder object).
- **Next task: गण 8 (तनादिः)**, whose intro rule (उ-insertion, PDF p.99) and first root तन् विस्तारे ("to spread", उभयपदी) were already glimpsed this session but not fully transcribed. The गण-4/6/7 question remains the top-priority item to resolve, ideally before or alongside गण 8/9/10.

## गण 3 (जुहोत्यादि) — delivery 1, complete: all 11 roots, plus two confirmed PDF page/content gaps found

- **Transcribed गण 3 (जुहोत्यादि, reduplicating conjugation) in full**: the gaṇa's own 4 introductory rules on reduplication (PDF p.80), the root list (11 of 24 traditional roots — the book's own "प्रधानभूताः"/principal selection), and all 11 individual root conjugations across all three पद-sections:
  - परस्मैपदिनः (5 roots): हु (1, "to sacrifice/eat" — the gaṇa's own worked example, जुहोति), ह्री (2, "to be ashamed", जिह्रेति), पृ (3, "to protect/fill", पिपर्ति), भी (4, "to fear", dual बिभि-/बिभी- grade throughout plus a second विधिलिङ् paradigm), हा-त्यागे (5, "to abandon", closes the section).
  - आत्मनेपदिनः (2 roots): मा (6, "to measure", मिमीते), हा-गतौ (7, "to go", जिहीते — a genuinely different root from #5 despite the identical spelling).
  - उभयपदिनः (4 roots): दा (8, "to give" — परस्मैपद table incomplete, see below), धा (9, "to place/hold", both पद tables), भृ (10, "to hold/maintain", both पद tables — book's own header oddly marks it अकर्मकः despite being ordinarily transitive, recorded as printed), निज् (11, "to wash/cleanse", both पद tables, closes उभयपदिनः AND गण 3 in one marker "इति जुहोत्यादिः॥").
- **Found and corrected a same-session misreading**: root #2's name was initially misread as bare "ही" from a low-zoom root-list glyph; a high-resolution re-zoom of both the root-list page and the model-conjugation page's own header confirmed it is genuinely "ह्री" (लज्जायाम्, "to be ashamed" — the standard Paninian जुहोत्यादि root), with reduplicated लट् जिह्रेति, not जिहेति.
- **Found a confirmed missing PDF page**: PDF page 83 (the book's own printed-page numbering) does not exist anywhere in the scanned sequence — the delta between the PDF's page index and the book's own page number is a consistent -6 through PDF-index 88 (book page 82) and shifts to -5 starting at PDF-index 89 (book page 84), with no page in between. This page almost certainly held root #8 दा's परस्मैपद conjugation table (its आत्मनेपद table survives, on the "book page 84" page). दा's entry records `sarvadhatuka_parasmai: null` rather than fabricating the missing table; its already-known लट् प्र.पु.ए. ("ददाति", from the root-list page) is preserved in `roots[]`.
- **Found a much larger, unconfirmed gap: गण 4 (दिवादि) is missing from the expected page position.** PDF p.95 closes गण 3 ("इति जुहोत्यादिः॥") and PDF p.96 opens directly into गण 5 (स्वादिः) — confirmed by rendering and reading both pages in full; no running header, no page number, and no गण 4 content anywhere between them. **Not yet confirmed whether गण 4 exists elsewhere in this PDF file out of sequence** — flagged as the top-priority item for the next session (a coarse page-range search across PDF pp.96-167 before concluding it's genuinely unrecoverable from this file).
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json` (11 model_conjugations entries, 11 roots in गण 3 — structure intact).
- **गण 3 is structurally complete** (modulo the one missing-page gap on दा). Next task: locate or confirm-missing गण 4, then continue to गण 5 (स्वादिः), whose intro (PDF p.96) and first root (सु अभिषवे, "to press juice", उभयपदी) were already glimpsed this session but not transcribed.

## गण 2 (अदादि) — delivery 4 (2026-09-19, same session): उभयपदिनः section completed — गण 2 STRUCTURALLY CLOSED

- **All 6 remaining उभयपदी roots transcribed in full** (both पद-tables each): दिह् (45), दुह् (46), द्विष् (47), ब्रू (48), लिह् (49), स्तु (50). Combined with delivery 3's ऊर्णु (44), the उभयपदिनः section (PDF pp.66-80) is now complete.
- **गण 2 confirmed fully closed**: PDF p.80 ends with "॥ इति अदादिगणः ॥", immediately followed on the same page by the गण 3 (जुहोत्यादि) header and its first 4 numbered rules about reduplication (द्वित्व) as this गण's defining feature.
- **#48 ब्रू** is defective/suppletive in परस्मैपद लट् — the book's own footnote: "The root ब्रू takes आह as आदेश in the First 5 Forms of लट् (परस्मैपद)." Captured both the ordinary ब्रू-stem paradigm and the आह-suppletion paradigm (`lat_rupam_2`), matching this file's existing convention for #27 विद्'s dual paradigm.
- **#50 स्तु** carries a triple-stem alternation (स्तु-/स्तव-/स्तुवी-) through nearly every सार्वधातुक cell in both पदs — captured as inline "/"-separated alternates. Its own page header oddly reads "सकर्मकः—परस्मैपदी" despite being उभयपदी per the root list and despite the very next page giving a full आत्मनेपद table — flagged as a likely book misprint rather than resolved silently. Its closing note groups root #22 रु (परस्मैपदी) onto this same pattern.
- **Caught and reverted a same-session transcription error**: an initial pass on #45 दिह् read धेक्षि/धिक्षे (मध्यमपुरुष लट्, both पद) as scan-glyph errors and "corrected" them to देक्षि/दिक्षे (द-initial). Transcribing #46 दुह् immediately after, on a much cleaner scan, showed the identical cells unambiguously as धोक्षि/धुक्षे — revealing this is a real Sanskrit phonological process (aspiration-throwback from the root-final ह् onto the initial consonant) and the "correction" had itself been the error. Reverted दिह्'s cells to the ध-initial spellings, with a note explaining the cross-check.
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json` (29 model_conjugations entries, 50 roots in गण 2 — structure intact; all root_num values from 29 distinct roots present).
- **गण 2 is now structurally complete.** Next task: गण 3 (जुहोत्यादि), starting PDF p.80 — see PROJECT_STATE.md's next-cycle protocol.

## गण 2 (अदादि) — delivery 3 (2026-09-19): आत्मनेपदिनः section completed & closed, उभयपदिनः started, 11 more परस्मैपदी roots, 6 root-list corrections

- **Resolved the prior session's environment blocker**: `D:\python\python.exe` with `pypdfium2` rendered pages without issue this session; the browser/desktop-control workarounds documented previously were not needed.
- **आत्मनेपदिनः section (roots #34-43): now COMPLETE and confirmed CLOSED.** Transcribed full सार्वधातुक (लट्/लङ्/लोट्/विधिलिङ्) tables for all 8 individually-conjugated roots: आस् (34, the primary model — confirmed as predicted in PROJECT_STATE), इ/अधि (35), ईड् (36), ईश् (37), चक्ष् (38), शी (41), सू (42), हु-with-नि (43). PDF p.65 ends with "इति अदादौ आत्मनेपदिनः॥", confirming closure. **Roots #39 वस् and #40 आ+शास् were directly confirmed (by page-by-page reading of PDF pp.58-65) to have no individual conjugation and no grouping-note anywhere in this section** — this is a genuine gap in the source book's own coverage, recorded as such rather than filled in with a guess.
- **उभयपदिनः section (roots #44-50): STARTED.** Root #44 ऊर्णु captured in full — both पद-tables (परस्मैपदे and आत्मनेपदे), confirming उभयपदी roots receive complete conjugations for each पद. Roots #45-50 remain for the next increment.
- **11 additional परस्मैपदी roots transcribed** (opportunistic, since paging forward through them was required to reach आत्मनेपदिनः anyway): रुद् (23), नु (12), चकास् (7), जागृ (8), दरिद्रा (9), मृज् (18), वच् (25, notably defective in 3rd pl. लट् per the book's own footnote), विद् (27, carries two full लट्/लोट् paradigms — an ordinary one plus a लिट्-based one, per Panini 3.4.83), शास् (28), हन् (33, closes the परस्मैपदिनः section — PDF p.57 "इति अदादौ परस्मैपदिनः॥"). Combined with the previous delivery's अद्/अस्/या, गण 2's परस्मैपदी section now has 14 of 33 roots individually transcribed.
- **Found and fixed 6 real errors in the root list** (`roots[]` array) by directly re-reading the root-list page (PDF p.41), the same page an earlier delivery had transcribed from — a second instance of this project's recurring "re-verify against the master root list" lesson (see delivery 2's या/अद् grouping-note fix below):
  - #36: "ईङ् गतौ, to go" → **"ईड् स्तुतौ, to praise"** (wrong root entirely; confirmed independently from both the root-list page and the root's own model-conjugation page).
  - #39 वस्: "निवासे, to dwell" → **"आच्छादने, to dress/cover"** (conflated with the भ्वादि root वस्).
  - #40 आ+शास्: "आशीःकर्मणि, to bless" → **"इच्छायाम्, to desire"**.
  - #42 सू: wording tightened to the book's own exact phrase "प्राणिप्रसवे" (was "प्राणिगर्भविमोचने", same sense).
  - #43 हु: "दानादनयोः, to sacrifice" (actually the गण-3 जुहोति root's meaning) → **"अपनयने, to conceal"**; also identified as always नि-prefixed in this गण's usage.
  - उभयपदिनः list: added missing alternate forms for #44 ऊर्णु, #48 ब्रू, #50 स्तु.
- A handful of individual cells across the new entries were faded/ambiguous in the scan; each is flagged with an explicit `note` on its entry (e.g. चकास्'s स्/म् ligature confusion, नु's लोट् उत्तमपुरुष cells, मृज्'s लोट् मध्यमपुरुष cell) rather than silently guessed.
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json` (23 model_conjugations entries, 50 roots in गण 2 — structure intact).

## गण 2 (अदादि) — delivery 2, partial (root list + 3 परस्मैपदी models), plus one transcription-error fix

- Delivered: complete 50-root list for गण 2 (परस्मैपदिनः #1–33, आत्मनेपदिनः
  #34–43, उभयपदिनः #44–50), and full सार्वधातुक conjugations (लट्/लङ्/
  लोट्/विधिलिङ्) for अद् (#1), अस् (#3, "to be" — including the एधि
  imperative form), and या (#19).
- Discovered and documented a real structural fact about this गण's layout:
  the book conjugates a larger number of individual roots than गण 1 did,
  in an order grouped by shared paradigm shape rather than list order —
  see PROJECT_STATE.md for the confirmed page-by-page evidence.
- **Found and fixed a real transcription error from the prior delivery**:
  the "एवं ६ ऋच्छ्, १० द्रा..." grouping note had been recorded against
  अद्'s entry (page 42); re-reading the actual page image confirmed page
  42 carries no such note, and the note in fact belongs to या's entry
  (page 44). Corrected by moving the note and fixing one misread root name
  in it (#6 was guessed "ऋच्छ्" from a faded glyph; the root list's own
  entry for #6 is ख्या, which fits the आकारान्त grouping the note actually
  describes far better than the guessed name did).
- Validated the resulting JSON with PowerShell's `ConvertFrom-Json`
  (Python was not reachable in this session — see PROJECT_STATE.md's
  environment-blocker note):
  ```powershell
  $obj = Get-Content -Raw -Encoding UTF8 "dhaturupa_manjari.json" | ConvertFrom-Json
  ```
- **Not completed this delivery**: आत्मनेपदी and उभयपदी model conjugations
  for गण 2 — blocked mid-task by a PDF-page-rendering environment issue
  (Python unreachable on PATH in this session; browser pane refuses local
  PDF file interaction; desktop-control path via Adobe Acrobat surfaced an
  unrelated pre-existing user browser window and got stuck). Full detail
  and recommended next steps in PROJECT_STATE.md's blocker section.

## गण 1 (भ्वादि) — delivery 1, complete

- Delivered: full root list (174 entries, including duplicate root #117
  keyed `117.1`), model सार्वधातुक conjugations for भू (परस्मैपदी) and लभ्
  (आत्मनेपदी), each with full लट्/लङ्/लोट्/विधिलिङ् tables across all three
  persons and numbers.
- Established the extraction method for this whole track: render PDF
  pages via `pypdfium2` at high resolution, read/transcribe by hand (no
  OCR — Devanagari OCR is unreliable and Tesseract isn't installed), flag
  any faded/illegible scan cell explicitly with a `note` rather than
  silently guessing.
- User confirmed the incremental, गण-by-गण delivery approach via an
  explicit choice ("Incremental, section by section (Recommended)") over
  a single continuous full-book pass.
