# CREDIBILITY WITHOUT A CAMERA
### Evidence plan for the BixLink electronica 2026 site — no photo shoot available

*The eight needs referenced throughout: **N1** proof the tests happened · **N2** proof of a real production line · **N3** measurement discipline · **N4** macro grain (lot codes, welds, print) · **N5** true-scale anchoring · **N6** the invisible component (product installed in something) · **N7** material reference under real light · **N8** removal of fabrication risk.*

---

## 1. THE ANSWER IN FOUR SENTENCES

**Yes — about 80% of it, and the missing 20% should be cut rather than faked.** The single best finding is that the two 95×95 cm QC posters nobody had opened are a laboratory evidence sheet carrying five genuine instrument outputs at 848–1556 px, and BixLink's own sodium catalogue p.1 carries a photograph of a nail-penetrated cell with the test engineer's blue ballpoint still on it — evidence a staged shoot would probably have lost, not gained. The replacement mechanism is not "find better pictures"; it is a document system: reproduce the company's own artefacts at first generation, annotate outside the frame, and print the provenance including the native pixel dimensions, so smallness reads as documentary candour instead of as a failure. Two needs (N3 measurement discipline, N6 invisible component) cannot be met from any existing material and are the only real losses — for those, cut the sections rather than prop them, because the one thing worse than no evidence is vendor photography wearing BixLink's name at a show where the vendor has a stand forty metres away.

---

## 2. WHAT WE FOUND THAT NOBODY WAS USING

Ranked by how a sceptical engineer at the booth would weight it. The test is not "is it a photograph" — it is **does the artefact contain information the company did not get to choose.** Grime, thermal lag, dimensional scatter, an unflattering maximum, an instrument's own warning.

### TIER A — unfakeable, because they carry information against interest

| # | Asset | Where | Native | Why it cannot be faked |
|---|---|---|---|---|
| 1 | Nail-test **rig** | `evidence/EVID_na-p1_nail-test-rig_PRESS-AND-CLAMP_358x527.png` — Sodium-Ion Battery (EN) p.1, xref 1673 | 358×527 | A scarred, oil-stained chamber floor with a blast port. Copper plates on threaded posts, thermocouples to both tabs. It is a bad photograph of a real place. |
| 2 | Nail-test **specimen** | `evidence/EVID_na-p1_tested-cell_2-punctures_handwritten_266x352.png` — same page, xref 1677 | 266×352 | `305.28 / 408.19` in blue ballpoint with `1→ 2→` at two punctures. Nobody art-directs handwriting. |
| 3 | FLIR thermogram | `evidence/INSTR-flir-thermogram-pack-max37.3C__1123x836.jpeg` — 95×95 poster p.1, xref 155 | 1123×836 | **Max 37.3 °C is an unimpressive number.** A company drawing its own thermogram picks a flattering one. Busbars read hotter than the cells — physics a drawing gets backwards. |
| 4 | IM-7030T ten dimensions | `evidence/INSTR-keyence-im7030t-10-dimensions__893x469.jpeg` — 95×95 p.1, xref 153 | 893×469 | Same features measured on **two** nominally identical parts: 18.455/35.382/39.844/39.935 vs 18.405/35.369/39.805/39.792. Part-to-part variation of 0.013–0.143 mm, disclosed. Nobody publishes their own scatter on purpose. |
| 5 | VHX-970FN weld profile | `evidence/CROP-vhx-profile-5-measured-heights__1556x555.jpg` + `CROP-vhx-micrograph-5-weld-nuggets__744x566.jpg` — 95×95 p.1, xref 154 | 1556×1125 parent | Five nugget heights that are **not equal**: 0.13 / 0.13 / 0.15 / 0.11 / 0.12 mm. |
| 6 | Four named addresses + instrument roster | Company File EN p.1 and p.2 | text | HQ Taode Rd Taoyuan · Japan Design Center Kodaira · pack factory Tamsui · coin-cell factory Jintan. Tektronix TCP0150 / DMM6500 / MDO-3054, Keyence IM-7030T / XM-5000 / VHX-970FN, EM TEST NX30.1. **Checkable text outranks most of the imagery**, and both prior planners buried it. |

### TIER B — real measurement, self-selected, unverifiable

The five sodium charts (`CHART_na-p1_short-circuit_3series_449.7A_697x433.png`, the two 1C-vs-temperature families at 730×408, the two 11-point C-rate families at 704×400) and the MDO-3054 capture (`INSTR-tek-mdo3054-capture-77.0A-2022-03-15__928x557.jpeg`).

Both prior documents treat "you can see the per-sample jitter, therefore it's logged" as settling the question. **It settles exactly one question — a designer did not draw this in Illustrator — and leaves every other one open.** Which cell, which run of how many, who chose the axis window, no third party anywhere in the bundle. The correct internal label is **not fabricated**, never **verified**, and no copy may let the second meaning leak in.

### TIER C — re-plated assertion, worth ~zero to a sceptic

The five-gate QMS chevron. "100% cell screening." "100% PCBA inspection." ISO 9001 / UL / TÜV as word-lists with **no certificate numbers, no test house, no report numbers, no dates anywhere in four files.** The application icon row. The blank world map. Printing these does not add evidence; it adds surface area for questions we cannot answer.

### TIER D — actively negative: vendor stock

**This is the most valuable single finding of the exercise, and the excavation got it exactly backwards.** `BENCH-dmm6500-026.2785V-probing-pack__3456x2303.jpeg` and both its crops are **Keithley application photography** — knocked-out studio ground, anonymous probe barrels, a generic sealed lead-acid block with a blank label, Keithley's own printed cable flags. The excavation calls it *"the strongest single credibility frame available anywhere in the bundle."* It is a meter vendor's press kit. Same verdict: `BENCH-xm5000-cmm-in-use__2052x2053.jpeg`, `BENCH-vhx-microscope-station-pcba__3456x2303.jpeg` (+ its refdes crop), `BENCH-im7030t-machine`, `BENCH-terchy-chamber-minus40-plus150C`, `VENDOR-mdo3054-body`, `VENDOR-tcp0150-current-probe`.

**Rule to write on the wall: in this bundle, instrument *screen output* is evidence; "instrument in use" photographs are vendor press kit.** The tell is press-kit dimensions (3456×2303 / 2052×2053 / 2074×3112) + knocked-out background + no BixLink product in frame. One vendor frame discredits every genuine number beside it, retroactively.

`BENCH-emtest-nx30.1-esd-gun-firing__1788x1125.jpeg` is **amber** — it does show what looks like a BixLink connector face (CHARGE / OUTPUT / DB9) but sits on a white sweep with the same sleeved arm as the confirmed vendor frames. Do not ship without client confirmation.

### The macro library (N4/N7) — real, and smaller than advertised

`D:\UserData\Downloads\德國參展\補充照片\PNG` (mirrored at `F:\德國參展\產品照片\PNG`): 236 frames, 190 at 12 MP, two at 48 MP. ~130 are near-duplicate turntable angles that yield "a blurry corner of a black box."

The 16 confirmed crops are, as *subjects*, **eight pictures**: dot-matrix laminate print (`c33_pouch_lotcode_fixed.png`), tab weld nuggets (`c01`/`c03`), BMS board face (`c11_bms_pcb_face.png`), heat-seal edge (`c22`), laser-etched can top (`c04_LIR2450_cantop.png`), barcode label stock (`c29`), the 3M 300LSE liner (`c30`), sodium print and polarity (`c23`). c05/c06/c27/c28/c33 are one lot code five times. **Budget eight, one hero macro per page, never two in a section** — two tight crops of the same white sweep read as one photograph reused.

### Shipped and never rendered

Four sodium chart WebPs sit in `site/public/photos/sodium/` and in `content/photo-manifest.json`, referenced by **no page in the repo** (the brief's claim they are "already shipping" is wrong). The fifth chart — 1C-vs-temperature for the 5.3 Ah cell — was never extracted at all. Plus 3.11 MB of unused 2000 px studio pack photography under `public/products/li-ion-pack/assets/` and 819 KB of byte-identical `-cut` duplicates.

---

## 3. THE FIVE REPLACEMENT STRATEGIES

### STRATEGY 1 — Reproduce the company's own test documents and rig photographs. Never redraw.
**What it is:** extract the embedded raster from the PDF at native resolution with PyMuPDF (base pixmap composited with its SMask — every sodium chart is white-on-*transparent* line art; the catalogue's blue is the page, not the image), ship it unmodified, annotate around it. Never screenshot a rendered page. Never re-typeset an axis label: the moment you set the chart's type in the site's font it stops being evidence and becomes an illustration.
**Serves:** N1, N3 (partly), N8.
**Worked example:** the short-circuit chart. I colour-traced it to test whether redrawing was defensible — three well-separated stroke colours, detectable gridlines, linear axes; tracing the green current stroke returns 452.2 A against the printed 449.7 A, 0.6% error. So a redraw would be *honest*. It still loses: the continuous per-sample jitter along both temperature decays is the one property that cannot be counterfeited, and a redraw discards it to gain styling. It also costs bytes instead of saving them. **Re-extracted with alpha and quantised to 128 colours, all five charts = 82.3 KB against 139.5 KB currently shipping for four.** The document programme is cheaper than what already ships.

### STRATEGY 2 — Manufacture new macro imagery by cropping 12 MP frames.
**What it is:** a quarter-width crop of a 12 MP frame still yields ~1000 px, so a crop **is** a new photograph — for the product library only. It does **not** transfer to the film stills (see Strategy 5).
**Serves:** N4 (over-delivered), N7 (~90%), N5 (partly).
**Worked example:** `crops/c33_pouch_lotcode_fixed.png` — 830×500 out of `IMG_9226.png`, showing production dot-matrix inkjet printed directly onto aluminium laminate, *"BixLink TRM01 / − FT402023P / 165mAh 0.6105Wh / + NG10L 3.7V"*, with every individual print dot resolved. This is the cancelled shoot's own top shot-list item — "the real lot code blown up as the site's typographic motif" — delivered at higher resolution than a rushed shoot day would have produced. It runs full-bleed edge-to-edge at the head of the light act on every page, cropped so the print runs off **both** side edges: the only image permitted to bleed on two edges, and therefore the site's rule line.

### STRATEGY 3 — Technical-illustration conventions that make a drawing read as engineer-authored.
**What it is:** where a drawing must exist, obey the conventions only a draughtsman knows. ISO 128-50 hatching (45° / 135° on adjacent parts *and* a change of pitch; the same part keeps its angle in **every** view; fasteners, pins, ribs and webs unhatched when the plane passes lengthwise). ISO 128-2 line precedence. ISO width series at a strict 1:2 narrow-to-wide. Butt caps and mitre joins on geometry, round caps on measured traces. First-angle projection symbol (correct for a Munich audience) and an ISO 2768-m general tolerance note in the title block. And the mechanical enforcement of N8: **every drawing carries `DRAWN FROM: <named source, page>` in its title block, and anything without that line does not ship.**
**Serves:** N8 above all, plus N3 and N6-adjacent geometry.
**Worked example:** the CR-coin page. The brief proposed *authoring* eight CR2032 termination footprints as new CAD. They already exist — `evidence/TECH_cr-p1_pin-drawings_AH01-AH04_1179x224.png` and `_AV01-AV04_1163x217.png`, eight true dimensioned drawings with extension lines, arrowhead dimension lines, dash-dot centre lines, 45° section hatching on the AV end views, ⊕/⊖ glyphs and European comma decimals (5±0,5 · 10±0,5 · 0,75 · 3,41 · 3,2 · 0,15 · 20 · 2,6 · 3,8). Redrawing them as SVG is **tracing, not fabricating** — and the catalogue's own caveat travels with them verbatim: *"CR2032 pin drawings are for reference only."* Same mechanism retires the packs page's invented internal layout via `TECH_company-p2_exploded-pack-assembly_789x441.png`, and the rechargeable-coin cutaway via `TECH_rcoin-p1_stacked-electrode-cutaway_300x240.png`.

### STRATEGY 4 — Data disclosure and checkable arithmetic as a substitute for pictures.
**What it is:** a number a stranger can re-derive on their phone from two other numbers on the same page is the only claim that cannot be faked. Transcribe printed values verbatim into native HTML tables (15 px, tabular-nums, animatable, a few hundred bytes) rather than redrawing the plot; keep the reproduced chart small beside the table purely as provenance that the numbers were *measured*, not typed. Grade every figure **MEASURED / RATED / SERIES / REFERENCE**.
**Serves:** N1, N3, N5, N8 — and it is the only strategy that works on pages with no usable imagery at all.
**Worked example:** the two C-rate families. Both legends print their results as *text*, so they transcribe exactly: discharge 0.2C=100.00% down to 9C=86.21%, strictly monotonic; charge 0.2C=100.00% … **6C=93.96%** … 9C=86.50%, which breaks the trend. Put the two tables side by side so the anomaly is disclosed **by comparison** rather than buried in a footnote — a defect converted into a demonstration of candour at zero cost. Tag the 0.2C row REFERENCE in both: 100.00% is a normalisation, and two decimals on a definition is false precision, which is the first thing an engineer notices.

### STRATEGY 5 — Frames cut from the company's own film.
**What it is:** `site/public/media/still-*.jpg` — eight ffmpeg-extracted frames (all carry the `Lavc62.28.102` comment). **Hard constraint: they are upscaled.** Measured by downscale-round-trip, real detail dies at 800–1100 px. Ship full-frame or near-full-frame; **no crop deeper than 1.4×, ever.** The crop lever from Strategy 2 does not exist here.
**Serves:** N2 (conditionally — see §9 Q3), N3 (weakly).
**Worked example:** `still-welding.jpg` — a servo welding head on a linear axis with a drag chain, against an orange phenolic masking plate drilled in 2×3 and 3×3 groups, carrying the operators' own black-marker group numbers (67 66 55 54 43 42 17 46 45 44 31 40 19 13 12 18 7, and a large R), with bilingual machine labels for the head and the X-axis servo. **Handwritten marker on a production fixture is the least counterfeitable thing in the media folder.** Caption it only for what is visible — "welding head on a servo X-axis; group numbers written on the masking fixture by the operator" — never "spot-welding 21700 cells," because the cell type is not in frame.

---

## 4. THE DOCUMENT TREATMENT SYSTEM

One React component, `<Plate>`, wraps **every** reproduced artefact site-wide — chart, rig photo, instrument screen, certificate crop, drawing. Nothing reproduced is ever styled ad hoc. This is the part of the plan that is a *rule* rather than an *asset*: it keeps working on material nobody has found yet, and it enforces N8 mechanically instead of by taste.

**Frame.** Border-radius `0`, everywhere. Radius is a UI signal; documents have corners. No card, no panel. The mat is a single 1 px hairline drawn **on the artefact's own edge**: `rgba(160,178,204,.22)` on dark, `rgba(20,24,34,.20)` on light. Exactly one edge of every artefact is cut — on phone the left edge bleeds to `x=0`, on desktop the plate overhangs the content column by one grid column. A document that fits neatly inside its container reads as an asset; one that continues off-canvas reads as a page that exists.

**Shadow.** None. Not on charts, not on document scans, not on rectangular photographs. A drop shadow under a reproduced page is the tell of a stock paper mockup. Contact shadows are reserved for cut-out objects; none of these are cut out.

**Grading.** Two rules, no exceptions.
- *Charts and instrument screens:* **no grading at all.** The trace colours **are** the legend key. False-colour scales (FLIR palette, VHX height map) are never regraded — the colour is the calibration.
- *Photographs:* one shared build-time LUT applied identically to all — black point lifted to `#0b0d16` (never `#000`, so nothing dissolves into the `#050507` ground), saturation 92%, white point clamped to 247. Dust cleanup only. That is the entire retouch budget.
- Over everything, the existing `.bx-grain` tile at 3.5% (dark) / 2% (light), running unbroken from the page across the plate. Never a per-image grain. That single overlay is what welds a 266 px catalogue JPEG, a 1556 px instrument screen and an SVG drawing into one world.

**Dark act vs light act.** On `#050507`, every artefact sits directly on the page ground with the hairline and nothing else, one artefact per screen. On `#f5f5f7` the artefacts split: photographs sit directly on the light ground with the light hairline; **charts and instrument screens cannot** — their gridlines, axes, ticks and labels are white and vanish (verified by compositing). So on the light act every dark-ground artefact sits inside a `#0b0d16` **light-table inset** (the existing `--viz-shadow` token) with the light hairline: a document presented as a lit transparency on a light box. One rule, not per-chart colour surgery. **Never an invert filter** — inversion recolours the traces and destroys the legend.

**Annotation.** All annotation is HTML positioned over viewBox coordinates via the existing `viz-labels.tsx`. **Zero SVG `<text>`, ever.** Two roles only: `.t-callout` (mono, 15 px, `--viz-ink`, tabular-nums) carries a value; `.t-annot` (mono, 15 px, `--viz-structure`) carries a name. Leaders are 1 px `--viz-structure`, `vector-effect: non-scaling-stroke`, butt cap and mitre join, terminating in a 3 px dot on a face or an arrow on an edge. Leaders never cross each other. **Labels live outside the artefact's bounding box; only the leader crosses the boundary. Nothing is ever painted over the evidence** — no highlight fills, no boxes on the image. Five leaders maximum per plate.

**The 15 px floor, solved by rule not by scaling.** Measured: the printed charts' own tick digits are 13–14 px tall in a 697–730 px master, so rendering them at 15 CSS px needs ≥810 CSS px of display width — fine on desktop, impossible on a 375 px phone (they land at 6.4 px). Therefore: **the reproduced artefact's own type never counts toward the 15 px floor. It is document texture, and a document is allowed to be a document.** Every figure the reader must read is re-stated in the annotation layer at 15 px outside the bitmap, and every plate carries a 15 px `↗ open at full size` anchor — a plain `<a target="_blank">` to the native file. No lightbox, no JS.

**Magnification.** Progressive, and always declared. A detail is a **rectangle with a stated ratio** — `DETAIL · SCALE 1.9:1` — never a magnifier circle with a cone, which is decoration. A declared magnification is *allowed* to be soft, and must never be sharpened or model-upscaled; a crisp 1.9× enlargement of a 266 px source would itself be an invention. An **undeclared** enlargement is forbidden.

**Banned from the system.** Paper texture, torn edges, coffee rings, corkboard pins, perspective "document on a desk" mockups, page curl, sepia, duotoned evidence, decorative frames. Re-typesetting an artefact's own labels. And the catalogue's own decorative layer — blue data-centre backdrops, neon card outlines, glow frames, the circular magnifier-and-cone — is stripped at extraction. **Corollary: no `CTX_*` page composites ship anywhere.** A 600 dpi render of catalogue *layout* is literally the screenshot-of-a-PDF failure this system exists to prevent, and it arrives complete with the banned furniture.

### Provenance caption format

Three mono lines at 15 px in `--viz-structure` (dark) / `#3a4250` (light), left-aligned under every plate, separated by a 1 px hairline. Fixed grammar, never improvised:

```
SOURCE   Sodium-Ion Battery (EN), BixLink catalogue, p.1 — reproduced as printed
FIGURE   Continuous Short-Circuit Test · 3 traces · 697 × 433 px as extracted · no retouch
TERMS    "Tested at -20℃、25℃、and 60℃, based on IEC 60079-11 standards."
         · Full test report available on request →
```

- **Line 1** — document, page, and either `reproduced as printed` or `as shot, dust only`.
- **Line 2** — what the figure is, **its native pixel size**, and its technical state. Stating `697 × 433 px as extracted` is the single highest-value line in the system: it converts the plan's central weakness (everything is small) into its signature, and pre-empts the "why is this tiny" question before it forms.
- **Line 3** — the standard the source itself cites, **verbatim, never paraphrased upward**, plus the report offer against a real mailbox.
- **Dates are never invented.** Where the artefact carries its own date, quote it and attribute it to the instrument: `instrument's own stamp, 15 Mar 2022 13:42:19`. Where none exists: `DATE NOT STATED IN SOURCE`. That admission is worth more than a guessed year.

---

## 5. PER-PAGE ASSIGNMENT

| Page | Evidence asset it carries | What it replaces | Honesty label |
|---|---|---|---|
| **Home** | `BOOTH-counter-product-array-japan-show__1477x1108.jpg`, cropped to the counter band (~1400×430), full-width strip, light act. Deliberately the least-designed image on the site. | The N5 true-scale anchor. ~40 real samples from a CR1620 to a 24 V pack, one frame, one light, human-height counter. Its own ordinariness is what a render cannot do. | `AS SHOT · BixLink stand, Japanese battery show` |
| **Industrial Li-Ion Packs** *(still served by the static `public/products/li-ion-pack/index.html`)* | `INSTR-flir-thermogram-pack-max37.3C__1123x836.jpeg` full-bleed at native. Plus `TECH_company-p2_exploded-pack-assembly_789x441.png` as the **reference the traced SVG derives from**, not as a shipped image. Page-weight: the unused 1500–2000 px `pack-silver-*.jpg` / `pack-black-*.jpg` replace the 1.94 MB currently shipping. | The invented isotherm through the aluminium wall — the exact mechanism the brief banned as *"a fabricated thermogram shown to an audience that owns FLIRs."* And an invented 7S6P internal layout. | `MEASURED · THERMOGRAM, REPRODUCED AS CAPTURED · subject: Li-ion pack under load` |
| **2S–4S 18650 Packs** | `still-factory.jpg` near-full-frame (≤1100 px of source). Then `CROP-vhx-micrograph-5-weld-nuggets__744x566.jpg` above `CROP-vhx-profile-5-measured-heights__1556x555.jpg`. Process → artefact of process → artefact measured. Macro: `c29_barcode_BLJ243900006.png`. | The drawn "nickel strip lays per parallel group," and the brief's *reasoned* claim of two weld dimples per cell — now five real nuggets at 0.13 / 0.13 / 0.15 / 0.11 / 0.12 mm. | Factory frame: **`SUBJECT NOT CONFIRMED`** until §9 Q3 is answered. VHX: `MEASURED · INSTRUMENT OUTPUT` (0.04 mm range flagged as *derived from the five printed heights*) |
| **Li-Polymer Pouch** | `crops/c33_pouch_lotcode_fixed.png` full-bleed, both edges. Then `c11_bms_pcb_face.png` (silkscreen TUA01-1-R1, R025 sense shunt, tabs soldered to ENIG gold), `c22_48mp_heatseal_edge.png`. **Explicitly not** `PROD_poly-p1_lipo-pack-family` — I opened it: blue glitter bokeh in an oval vignette, banned vocabulary, and uncroppable because the packs sit *on* the glitter. | The shoot's own #1 shot-list item, one for one. And the invented surface of the shared `<PCB>` primitive. | `AS SHOT, DUST ONLY` |
| **Sodium-Ion NFPP** | Plate 1 rig (358×527, **shown small and sharp**), Plate 2 specimen (266×352, native), Plate 3 declared detail `DETAIL · SCALE 1.9:1` on the handwriting. Plus all five re-extracted charts + two transcribed C-rate tables. | The drawn nail mechanism and its payoff frame; the two hand-authored beziers; and the brief's flat-line hero, which the chart proves cannot be built. | Charts `MEASURED · REPRODUCED AS PRINTED`; tables `TRANSCRIBED VERBATIM`; handwriting caption: *"BixLink has not published what these figures denote, and we have not guessed."* |
| **Solid-State (FLCB / PLCB)** | `PROD_ssb-p1_ceramic-cell_prologium_300ppi_1622x1293.png` — real lithium-ceramic cell, white ceramic panel on gold laminate, copper-brown tabs, plus its bent-cell and grey-pouch insets. Everything else on the page is drawn. | The page's founding premise — "zero photographs exist, so the material language must be invented" — which is false. | Page demoted to an **explicitly attributed ProLogium partnership page**. Every claim (10⁻¹¹–680 ATM, −40 to 115 °C, 80% in 12 min, 170 °C, no fire under puncture) carries `PROLOGIUM — PARTNER SPECIFICATION`. Drawings: `SCHEMATIC` |
| **CR Coin Cells** | `TECH_cr-p1_pin-drawings_AH01-AH04_1179x224.png` + `_AV01-AV04_1163x217.png` as trace sources. `crops/c01_pintype_tabweld_CR.png`. Specimen sheet stays CSS-computed from the catalogue diameter/height table — **zero image assets, 37 models (specs.json says 37; the brief's 38 is wrong — count before printing).** | Mechanism (b), which proposed *authoring* the eight footprints. Tracing beats inventing. | Drawings: `DRAWN FROM: CR Coin Battery (EN) p.1` + the catalogue's caveat verbatim: *"for reference only."* |
| **Rechargeable Coin** | `TECH_rcoin-p1_stacked-electrode-cutaway_300x240.png` with its three printed callouts, redrawn at true proportion. `crops/c04_LIR2450_cantop.png` supplies the disc's conic-gradient stops by eyedropper. | The brief's winding-spiral-only hero, which **misdescribes half the range**: the catalogue documents and *assigns* two processes — STACKING for GRP (p.1), WINDING for LIR/LDA (p.2). | `DRAWN FROM: Rechargeable Coin Battery (EN) p.1 stacked-electrode cutaway` |
| **Chargers** | **The 14-model table and the per-model certification column — the best content on that page — and nothing else.** No photography beat. | Nothing; the section is cut rather than propped. 220–364 px is a thumbnail, not a photograph, and the page composite is banned by §4. | CV decay tail: `SCHEMATIC — CV tail illustrative`. Cert marks quoted verbatim per model (`cTUVus・TUV-GS・SAA・PSE・KC・CE・FCC・UKCA・CEC・CE-IEC60601`) |

**Adjudication note on chargers.** The excavation's correction — "eight charger photographs exist, the brief is wrong" — is true about the fact and wrong about the consequence. The premise was right; only the wording was. Contrast solid-state, where 1622×1293 is genuinely usable and the correction holds. Both were presented as equal wins. They are not.

---

## 6. WHAT WE STILL CANNOT DO

### N3 — measurement discipline. **CUT the quality/QC section.**
Realistically **~35%**, not the 50% the substitution plan claims and emphatically not the "FULLY MET, better than the shoot would have been" of the excavation — that verdict rested on three vendor frames. What survives proves BixLink **owns** metrology and once used it. **Nothing proves a spec is applied to a part.** No caliper, no micrometer, no mass balance, no limit printed beside any reading, no pass/fail, no reject tray, no gauge R&R, no second reading to compare against a first — anywhere in 236 product frames, 8 catalogues, 9 posters, a company file and 8 film stills. A caliper closed on a cell with the tolerance printed next to it is a five-minute photograph, and there is no substitute for it.

**Do not build a QC section out of the five-gate chevron and the 100% claims.** Replace it with three things: (1) the instrument roster as text, with the source's own caveat verbatim — *"Note: The equipment shown is a partial list of our capabilities"*; (2) **one** exhibit, the IM-7030T frame, captioned strictly as ten dimensions measured across two nominally identical parts; (3) `Full test report available on request` against a real mailbox. One honest exhibit outperforms a propped section, and a claim you will back on request beats a photograph you do not have.

**Explicitly deleted from the plan, not deferred:** pairing "100% cell screening / 100% PCBA inspection" with `still-lab.jpg`, and pairing the "−40 to +150 °C chamber" stat with `still-testing.jpg` (whose HMI reads **25.0**, i.e. ambient). The substitution plan calls this *"the single highest-leverage move available from existing material… costs zero new assets."* It costs one credibility. **Two individually true statements composed into a third that is false**, in the exact section where we have nothing, aimed at the audience most able to notice. It is the textbook version of the risk the entire plan exists to avoid.

### N6 — the invisible component. **CUT.**
Zero application photography exists anywhere: all 236 product frames are the battery alone on a sweep or a bench mat; the Company File, both poster sets and the PPTX contain no product-in-situ frame; the film contains no host product.

**Reject the substitution plan's option A** (a schematic host outline with a real cut-out pack inside at true scale). The moment you outline an AGV you are illustrating a design-in you may not have, and a drawn use-case with a real object pasted in is precisely "assertion in a different font." **Replace with type:** the four named addressable sites, the named partners (Molicel, ProLogium), and the catalogue's own line *"Proven in medical, industrial, AGV/AMR & robotics."* A named partner is stronger evidence of being designed-in than any silhouette. **Do not buy licensed stock** — it forfeits the exact unfakeability the whole plan rests on, and reverse image search takes eight seconds.

The loss is smaller at electronica than on a general launch: this audience already knows where a pouch cell goes. Book it as a real loss and move on.

### N2 — production line. **CONDITIONAL. Substitute, pending one answer.**
`still-factory.jpg` shows a star-wheel escapement feeding ~30 **bare cylindrical cells** nose-up with copper weld nubs already on the caps. That is cell-manufacturing or cell-sorting furniture. **BixLink is a pack assembler** whose cells come from Molicel, Japan, Korea and Taiwan, with a coin-cell plant in Jiangsu and a charger OEM in Kunshan. Nobody has established that this is BixLink's own line. **Until confirmed, N2 is provisionally zero, not 70%** — and the "re-cut the film" recommendation must not be executed first, because re-cutting someone else's factory at higher resolution just buys a bigger problem. See §9 Q3.

### Other cuts
- **The two 1C-vs-temperature charts on mobile.** 730×408, ten overplotting traces, tick digits at ~6.4 CSS px. The §4 rule makes that *legal*, not *legible* — a licence, not a solution. Ship the reading key and one cropped detail (the −30 °C terminus against the 45 °C terminus, no legend); full plot on desktop and behind the full-size anchor.
- **Every certification badge row** other than the one photographed label — and that only with consent and a copy fix (§7).
- **All `CTX_*` page composites**, everywhere.
- **`--m-copper`.** No copper busbar surface exists in any source; the only busbar view is the false-colour thermogram. Derive it from the ~90 px weld nubs in `still-factory.jpg` or **drop the two mechanisms that use it.**

### Labelled SCHEMATIC (drawn, straight segments, no simulated sampling noise)
Charger CV decay tail · jelly-roll / CID / PTC / gasket internal geometry · the NFPP lattice · Anderson connector internals · any solid-state internal structure.

---

## 7. HONESTY LEDGER

| # | Discrepancy | Handling |
|---|---|---|
| 1 | **`449.7 A (88C)` is not reproducible from the catalogue's own capacity.** 449.7 / 5.3 Ah = 84.9C; 449.7 / 13.0 Ah = 34.6C; 449.7 / 88 implies 5.11 Ah. The brief's **34.6C is wrong** (the catalogue prints 88C) and the catalogue's 88C is also not derivable from the catalogue. | **Drop the `(88C)` parenthesis. Print `449.7 A` alone.** Reproducing verbatim is the right rule for reproducing a *document*; choosing which figures to promote into your own headline is authorship. A number that fails division on a page whose entire argument is "check our arithmetic" is worse than no number. Get the basis from BixLink or leave it out. Strike 34.6C from every draft. |
| 2 | **12 h vs 848 s.** The conditions line says "3 mΩ short for 12 hrs"; the plotted record ends at ~848 s (x-axis calibrated off tick centres: 0 at x=121.5, 800 at x=568.5, 55.9 px/100 s). | Kill the brief's signature hero — *"the time ruler rescales to 12 h while the flat line does not change"* would plot eleven and a half hours nobody logged, on a plateau that does not exist. Conditions block carries both, unmerged: `EXTERNAL R 3 mΩ · HELD 12 h (as stated) · CHART SHOWS 0–848 s (as plotted)`. |
| 3 | **"It was over in two minutes / the cell self-limits."** The substitution plan's replacement hero. | **Cut both halves.** "The cell self-limits" is a mechanism claim present in no source — fabrication committed in the sentence that kills someone else's. And an engineer's first read of a current collapse under a still-applied short is *the cell was empty*: 5.3 Ah ÷ 450 A ≈ 42 s of coulombs at peak. **Replacement hero, free and fully honest and noticed by nobody so far: the surface-temperature peak *lags* the current peak by ~70 s — the current is already collapsing when 98.69 °C arrives.** That is thermal mass, it is physically correct, and it is the shape nobody draws because nobody thinks to. |
| 4 | **−30 °C plotted vs −40 °C rated.** Both 1C families stop at −30 °C; the spec table claims −40 to 60 °C discharge. | −30 °C carries **MEASURED**, −40 °C carries **RATED**, and the two never appear in the same sentence without their tags. No "−40 °C" headline above this chart. |
| 5 | **9C plotted vs 20C / 40C rated.** Both C-rate families stop at 9C; the table claims 20C continuous / 40C peak, 12C/15C charge. | Same MEASURED / RATED split. Additionally the 40C pulse rating must **not** be used as the comparator for the short, because the C-basis itself does not reconcile (row 1). |
| 6 | **Charge C-rate is non-monotonic:** 6C = 93.96% between 5C = 91.16% and 7C = 88.39%. | Reproduce verbatim, never smoothed, never omitted, footnote: *"printed as 93.96%; breaks the monotonic trend. Reproduced as printed, not corrected."* Place the charge and discharge tables side by side. Ask BixLink; if a typo, print both values and the correction. |
| 7 | **Nominal voltage: 3.0 ± 0.1 V (spec table) vs 2.85 V (cell label).** Both label arithmetics check: 13 × 2.85 = 37.05 ✓, 5.3 × 2.85 = 15.105 ✓. | Any arithmetic states its basis inline. Show `2.85 V (cell label) / 3.0 V nominal (spec table)` **once**, then use one consistently. |
| 8 | **Part number: 70155250 (spec table, `c23` crop, and the nail-cell barcode reading `…155250…`) vs 701455320 (poster p.9 macro).** | Resolve from the 12 MP original before anything prints. Until then use 70155250 and print no serial. **Never print a part number read off a 266 px raster.** |
| 9 | **The shunt-drop sum is loose physics.** 449.7 A × 3 mΩ = 1.35 V is the *external* path; at peak the terminal voltage is not the OCV, so "most of a 3.0 V cell dropped internally" does not follow. | State it without the subtraction — *"at the 449.7 A peak the 3 mΩ external path accounts for 1.35 V; the balance is internal"* — or drop it. Do not present it as a clean checkable sum to engineers. |
| 10 | **IEC 60079-11 is the intrinsic-safety standard for explosive atmospheres, not a battery abuse standard**, and the footnote names three ambients under a chart plotting one run. | Reproduce verbatim; never explain, paraphrase or upgrade. Conditions block adds `AMBIENT OF THE PLOTTED RUN NOT STATED IN SOURCE`. Never caption the chart "25 °C". **And get BixLink an answer before the doors open — this is the line a German engineer will query at the booth.** |
| 11 | **My own colour-trace returns a Negative Tab Temp peak of ~74 °C.** That figure is nowhere in the catalogue. | Do not print it, and print **no** figure obtained by digitising a bitmap. A number we traced is our number, not BixLink's. Only 98.69 °C (surface) and 55 °C (nail) are theirs. |
| 12 | **Cycle life: 6,000 @3C to ≥70% (p.2 table) vs 8,000–10,000 @1C to ≥80% (p.1 series copy).** | MEASURED and SERIES tags, shown adjacent so the reader sees the distinction rather than discovering it. Both defensible; only merging them is not. |
| 13 | Two of five 18650 pack cycle-life figures are printed **"(estimate)"**. | Carry the word into the table cell. **Transcription never drops a qualifier.** |
| 14 | **`0.2C = 100.00%`** is a normalisation printed to two decimals. | Tag the row **REFERENCE** in both tables. |
| 15 | **Three unrelated "−40 °C" figures:** chamber range (−40/+150), sodium discharge rating (−40/60), industrial Li-ion DSG temp (−40/60). | Never one number, never one badge. Each carries its subject in the same line, always. |
| 16 | **The FLIR thermogram is a Li-ion pack, not a sodium cell.** | Banned from the sodium act and from any position adjacent to 98.69 °C. Subject named in the provenance line. |
| 17 | **The MDO capture names no DUT** — 77.0 A *of what, on what?* "CH1 High Std Dev 0.00" over a flat measurement means the quantity was trivially constant, not that the instrument was precise. **"Clipping negative" means part of that acquisition exceeded range and is invalid.** | Ship it with what it actually means in the annotation, or do not ship it. Do not present Std Dev 0.00 as precision. |
| 18 | **Everything is 3–5 years old.** MDO stamp 2022-03-15; film scope 2021-04-23; lot codes BLJ2439 / BJP2313 / BLJ2345. | Enforce the date convention on **all** assets including the film stills, not just the one the plan flags. Nothing is ever captioned "current" or "recent". |
| 19 | **The handwriting `305.28 / 408.19` is legible on the clamped cell in the *rig* photo — before the nail goes in.** So it cannot be a post-test measurement. | **Strike the excavation's "N3 (hand-recorded measurements)" attribution — it is false.** The caption *"BixLink has not published what these figures denote, and we have not guessed"* survives intact and is the right posture. The continuity beat is also slightly weaker than sold: same hand, same cell, two frames proves the frames belong to one event; it does not prove the writing records a result. |
| 20 | **The two sodium tests were probably run on different cells** — 88C implies ~5.1–5.3 Ah, the nail cell's barcode reads `…155250…` (13 Ah). | Name the cell in each test's own conditions block. **Never imply one cell survived both tests**, and never write a sentence whose subject spans both blocks. |
| 21 | **"No fire, no explosion, no thermal runaway"** is printed twice on p.1, under two different tests. | Attribute each instance to its own block, as the catalogue does. Never promote to a site-wide claim; **never use "safe" as a headline.** |
| 22 | **"Voltage remained at 3.1V"** sits above a 2.85 V label and near 3.0 V nominal, while a fully charged sodium cell rests nearer 3.5 V. | Print verbatim as a post-test measurement. Never paraphrase as "voltage unchanged" or "no voltage loss". |
| 23 | **Three equipment tiles are vendor catalogue stock**, plus the four confirmed vendor "in use" frames (§2 Tier D). | Banned from every evidence plate. Only frames containing hands, BixLink product, **or instrument output** ship as evidence. The roster is text. |
| 24 | **The charger rating label prints the OEM's name, full Kunshan address and "MADE IN CHINA"** — while the company page says *"Manufactured in ISO 9001, UL and TÜV certified Taiwan facilities."* | This is a **copy** problem, not just a consent problem: client consent does not fix a contradiction sitting on one domain. Since the charger photography beat is cut (§5), the cleanest handling is **do not publish the label at all** unless the company copy is first amended to distinguish pack manufacture from charger sourcing. |
| 25 | **Two library frames carry third-party brands:** CHAOCHUANG (`IMG_9367`) and lvzhoudianqi.com.cn (`IMG_9371`). | Excluded at build time, by filename. |
| 26 | **Unattributed partner claims.** Solid-state: 10⁻¹¹–680 ATM, −40 to 115 °C, 80% in 12 min, 170 °C, no fire under puncture — **not one measurement exists in the bundle**; these are ProLogium's. Packs: Molicel's 265 / 284 / 325 Wh/kg and 100 A. | **Attribute by name or drop, every one.** In BixLink's voice they are borrowed authority; attributed they become credentials and cost nothing. |
| 27 | **The four shipped chart WebPs are flattened to opaque black and lossy** (alpha discarded at extraction), and the excavation's claim that 1123–2358 px chart originals exist is **false** (those xrefs are decorative/product rasters). | Re-extract all five with SMask, quantise to 128 colours, lossless WebP: **82.3 KB total vs 139.5 KB currently shipping for four.** Record in the brief that **697×433 / 730×408 / 704×400 IS the ceiling**, so nobody spends a day chasing a bigger file. |
| 28 | **The brief says the four charts are "already shipping."** They are on disk and in `photo-manifest.json`, referenced by no page. The fifth (5.3 Ah temperature family) was never extracted. | Correct the brief. Extract and ship the fifth — it is the cell the short-circuit test most likely used, so it is the only temperature evidence attached to the safety story. |
| 29 | **CR model count: specs.json holds 37; the brief repeatedly says 38.** | Count before printing. **Never print a figure you have not personally counted, on a page whose entire argument is checkability.** |
| 30 | **Every good exhibit is a question generator** the booth cannot currently answer: the QMS chevron invites *"screened to what limit, what's your reject rate?"*; the IM-7030T frame invites *"what's the drawing tolerance on that 39.8 mm feature?"*; the VHX frame invites *"what's your nugget-height spec and Cpk?"* | Not a reason to cut — good evidence *should* invite questions. Add the deliverable neither prior document lists: **a one-page booth crib sheet, one line per exhibit.** An hour's work protecting everything else. |

---

## 8. COST AND FIRST MOVE

**What changed from the earlier brief.** The shoot line item is gone and nothing replaces it. The document programme is **cheaper than what already ships** (82.3 KB of five lossless charts against 139.5 KB of four lossy ones), and there is **4.31 MB of recoverable dead weight** in the tree — 3.11 MB of unused 2000 px pack studio photography, 1.20 MB of never-rendered photos including 819 KB of byte-identical `-cut` duplicates. Net asset cost of the whole evidence programme is **negative**. The real cost is judgement time, and the real risk is one vendor photograph shipping by accident.

**First move: build `<Plate>` and push exactly one artefact sequence through it — the sodium nail-test, three plates, on the sodium page. Then stop.**

**Why that one.** It is the hardest case in the entire plan: a 266 px source and a 358 px source, on a page whose credibility carries the whole site. If the treatment holds there — if a 266 px JPEG with a hairline, a provenance strip stating `266 × 352 px as extracted`, and a declared `DETAIL · SCALE 1.9:1` reads as a **document** rather than as a **bad upload** — then it holds on every richer asset in the plan, and the system is proved before any of the other seven pages are touched. It also exercises every rule at once: annotation outside the bounding box, the 15 px floor rule, the full-size anchor, declared magnification, the no-shadow / no-radius frame, and the provenance grammar. And it deletes the green rectangle, the blue arrow, any SVG nail and any nail-seating animation — so the fabrication-risk reduction is banked in the same commit.

**Sizing, and this reverses the substitution plan.** It shows the 358 px rig at 1.45× as a page hero and the 266 px specimen small "because the size difference is the truth about the source." Right instinct, wrong application: the truth to honour is **native resolution**, not native aspect. At ~360 px the rig is sharp and reads as a document; at 520 px it reads as a bad upload — and it is the page's first impression. **Invert it: rig small and sharp (≤1.05×), specimen native, and the *declared magnification* is the only thing allowed to go big.** A declared magnification is permitted to be soft; an undeclared enlargement is not.

**One craft note:** at 266 px the two punctures are four to six pixels each. The handwriting survives 1.9×; the holes do not. **Annotate the writing, not the punctures.** And Plate 3's crop `(60,70) → (240,210)` excludes the barcode strip, so the default is safe on the one consent gate in this section.

**Byte cost of the first move:** ~59 KB (36.4 + 13.5 + ~9 KB, WebP q90 at native) for the whole section — against an SVG nail animation that would have cost more in JS alone.

**What "it worked" looks like.** Five checks, in order:
1. On a 375 px phone, every figure a reader must read is at 15 px **outside** the bitmap, and no reproduced pixel is covered.
2. The `DETAIL · SCALE 1.9:1` plate is legibly soft and does not read as an upscale.
3. `#30d158` no longer appears anywhere on the page.
4. Read cold by someone who has not seen the sources, the provenance strip answers "where did this come from" and "why is it small" without anyone asking.
5. `449.7 A` appears without a C-multiple; `−30 °C` and `−40 °C` never share a sentence untagged.

If any of those fail, the fault is in the system, not in the asset — fix `<Plate>`, do not add a second page. **Then stop for human judgement before touching page two.**

---

## 9. QUESTIONS FOR THE USER

**Q1 — Is reproducing BixLink's own catalogue documents on the website acceptable to management, or must the site present only newly authored visuals?**
This gates roughly everything: the five charts, both nail-test photographs, the eight CR drawings, the exploded pack view. If reproduction is off the table, the plan collapses to §6's cut list plus drawn schematics, and the honest answer becomes "postpone the site."
**Recommendation: yes, reproduce.** It is the marketing department's own printed material, the treatment is stated as reproduction on every plate, and a first-generation reproduction of your own test document is stronger than any drawing of it.

**Q2 — Can the raw test logs or full test reports be requested internally before the show, or do we build only from what is already in the marketing PDFs?**
A CSV from whoever ran the 3 mΩ short would resolve the 88C basis, the ambient of the plotted run, the −40 °C gap and the 12 h vs 848 s question in one afternoon. **A spreadsheet is not a photo shoot, and it may well be sitting on an engineer's desktop.** This is the single highest-upside unknown in the plan.
**Recommendation: ask.** Even a "no" is worth having, because it converts `Full test report available on request` from a hopeful line into a checked promise.

**Q3 — Is the factory in the company film BixLink's own line, or a supplier's? And if it is a supplier's, do we cut N2 entirely or caption it honestly as a partner facility?**
The escapement is feeding bare cylindrical cells with weld nubs already on the caps — cell-manufacturing furniture, not pack assembly, and BixLink buys its cells. **Until this is answered, N2 is provisionally zero and the film must not be re-cut**, because re-cutting someone else's plant at higher resolution just buys a bigger problem.
**Recommendation: ask first, then re-cut.** If it is BixLink's, re-cutting the existing film at the highest available rendition for the four missing beats — welding head in contact, escapement mid-index, HIOKI at a second reading, chamber HMI at a non-ambient setpoint — is the cheapest recovery left anywhere in this plan and costs an afternoon. If it is a supplier's, cut N2 and say nothing about production.

**Q4 — Do we cut the four evidence-free sections outright (quality/QC, invisible-component/applications, charger photography, solid-state as a claims page), or does management require them present?**
Every one of them can only be built from Tier C assertion, and each dilutes the Tier A evidence sitting beside it.
**Recommendation: cut all four**, replacing them with type — instrument roster with its own "partial list" caveat, four addressable sites, named partners (Molicel, ProLogium), and one report offer against a real mailbox. Solid-state becomes an explicitly attributed ProLogium partnership page rather than a claims page. **A shorter site with nothing unbacked on it beats a complete one with four soft sections, in front of this audience.**