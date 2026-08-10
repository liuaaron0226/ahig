# ELECTRONICA 2026 — VISUAL REBUILD BRIEF
### Decision-ready. Every choice below is made, not offered.

---

## 1. THE DIAGNOSIS

The visuals read as cheap because nothing in them is lit. Every object is a flat `fill` — `rgba(48,209,88,0.10)` with a `#30d158` stroke — so a cell is a rectangle, a nail is a triangle, a battery pack is a grid of circles; there is no key light, no specular, no terminator, no contact shadow, so nothing occupies space and nothing reads as aluminium, steel, copper or polymer. The colour compounds it: `#30d158` is Apple's systemGreen at a chroma no photographed object reaches, so the eye codes it as emissive plastic, and green + amber + ice + blue in one frame gives four competing hues with no luminance hierarchy at all. Third, the drawings are diagrams of events rather than depictions of things — a chart of a short circuit instead of the busbar glowing, a polyline instead of the cell — and annotation is exactly what turns a render into a diagram. Finally the motion fades and loops instead of operating: `repeat: Infinity` sits on the data layer, `ease: "easeInOut"` is on every trace, and nothing has a cause that precedes its effect, so the pages read as screensavers rather than machines.

Two supporting facts, both verified: a 1px hairline inside a 1200-wide viewBox renders at 0.28px on a 340px phone, so half the structure is invisible on the device the QR code actually lands on; and the pages ship 1.31–1.94 MB of photography, which is the entire performance budget, spent already.

---

## 2. THE VERDICT ON TOOLING

**Adopt nothing. Zero new dependencies for the entire programme.**

**Use what is already installed and already shipping:**

| Tool | What it is FOR |
|---|---|
| `motion/react` v13 | Every animation on the site. `useScroll`/`useTransform`/`useSpring`/`pathLength` cover every capability the shortlist asked GSAP for. |
| Inline SVG + `<defs>` | Materials, lighting filters, section hatching, dimension lines, traces. This is the layer that kills "rectangles and polylines". |
| CSS: `clip-path`, `@property`, conic/radial gradients, `mask-image`, blend modes | Silhouette morphing, turned-metal discs, light rakes across as-shot photos. GPU-composited, zero bytes. |
| Tailwind v4 `@theme` tokens | The `--viz-*` palette and the material gradient table. |
| `@playwright/test` (already configured, `tests/` exists) | The verification loop. Screenshot at 375/768/1280 after every change. |
| The four existing sodium test-chart photos (`chart-short-circuit.webp`, `chart-13ah-temp.webp`, `chart-charge-rate.webp`, `chart-discharge-rate.webp`) | Already in `public/photos/sodium/`, already paid for, already shipping, and unfakeable. Audit these before drawing a single new trace. |

**Explicitly do NOT adopt:**

- **Blender.** Killed. The product geometry does not exist, there is no 3D artist, and an agent cannot iterate on an offline render through Playwright. Everything downstream of it — exploded PBR cutaways, turntables, tab-weld renders — dies with it.
- **Image-sequence scroll scrubbing.** Killed twice over. 24–30 AVIF frames at 750px is 250–450 KB on pages already at 1.9 MB, and the field research found that *nobody in the reference set scrubs anything* — Apple plays short clips inside a scroll window and unloads them. Building a scrubbed sequence imitates a technique the reference already abandoned.
- **three.js / @react-three/fiber.** Killed. 400 KB–1 MB gz before any geometry, plus WebGL context loss on iOS Safari under memory pressure — a blank hero on the one device you cannot debug on the show floor. Takes `pixel-liquid-bg`, `aurora-blur` and `blob-card` with it.
- **GSAP + ScrollTrigger/MorphSVG/DrawSVG.** Killed, and the "already paid for" premise is factually false: `grep` over `out/_next` returns zero hits for gsap. Its only importer (`page-transition.tsx`) has zero importers itself, so it is tree-shaken out entirely today. The real cost is ~36 KB gz of **new** weight to add a second animation engine beside one that already ships every capability requested.
- **Hand-written GLSL shaders.** Not in v1. The harness is real (`smoothui/shader-reveal-transition`, 454 lines, raw WebGL1), but authoring anisotropic-metal GLSL and verifying it by screenshot is the slowest, highest-variance loop available, and a full-viewport fragment shader is the single biggest battery and thermal risk on a phone standing in a hall. CSS gradients plus bounded SVG lighting filters get 90% of it at zero device risk. Revisit exactly one bounded shader only after a human has judged the CSS version insufficient on a real phone.
- **Rive, Lottie, Spline, Remotion, p5, Pixi, Paper, Theatre, OGL, Motion Canvas.** All fail on licence, weight, or redundancy. Spline watermarks free-tier commercial exports. Remotion's licence triggers on company headcount and an electronica exhibitor is over the line. Lottie's runtime is free but authoring is After Effects. p5 is 250 KB and LGPL. Motion Canvas is genuinely MIT and genuinely good and still loses: a 2D schematic that renders live in SVG at vector crispness for 3 KB beats an encoded video of the same schematic.
- **Any charting library.** Recharts/D3/visx is 50–100 KB gz. Every chart pattern in section 5 is HTML divs, inline SVG paths and Tailwind.

**And delete what is already there.** 24 vendored components have zero importers (5 MagicUI, 15 SmoothUI, 5 Unlumen). The recommendation to "wire them up" is sunk-cost reasoning: content decides the component, the component never decides the content. Wiring `shader-reveal-transition` into a page because the file exists is precisely how you get the templated look you rejected. The correct action is `git rm`. The same applies to the decoration layer currently *live* — meteors, ripple, particles, sparkles-text, warp-background, animated-grid-pattern, dot-pattern, border-beam, shimmer-button, orbiting-circles, hyper-text, morphing-text. That set is the visual signature of a 2024 AI-generated SaaS landing page and is a larger source of the cheap read than the four schematics you named. Deleting it raises perceived quality more than any new mechanism, at a negative diff.

**Realistic page weight.** Everything in this brief adds **≈10–14 KB gzipped across all 8 pages**, plus one 1.2 KB noise tile, plus zero new image assets. For comparison: the industrial packs page ships 1.94 MB of photography today. Re-encoding the existing photos is worth more page-weight than every technique in this document combined, and nobody has proposed touching it. See Tier 2.

---

## 3. THE PROPOSED VISUAL SYSTEM

One language, eight pages. These are rules, not suggestions; a reviewer should be able to reject a PR by citing a number.

### 3.1 Light — one lamp, no exceptions
```ts
export const LIGHT = { azimuth: 225, elevation: 58, shear: -32 } as const;
```
Upper-left key, 225° azimuth, 58° elevation, on **every object on every page**. The proposal to give the charger page an overhead "bench light" for identity is rejected: consistency of light direction across a page is roughly 80% of what people read as expensive, and one deliberate exception costs more than the identity it buys.

Every object that represents a physical thing gets **four** things derived from that vector, or it does not ship:
1. a specular hairline on the lit edge,
2. a body gradient running along the vector,
3. a rim/bounce light on the opposite edge (1px, `#ffffff` at 0.22 — nothing may dissolve into `#050507`),
4. a **contact shadow** — a tight dark ellipse at the touch point, plus a larger soft one sheared to `-32°`.

A shape whose stroke is the same colour all the way round can never look lit. That is the rule that invalidates most of what ships today.

### 3.2 Material — five recipes, no flat fills
Banned: `fill="rgba(...)"` or a two-stop gradient on anything meant to be an object. Minimum five stops, with a **core shadow at 46%** and a **bounce at 100% that is brighter than the core shadow**. That upward bounce is what the eye reads as "sitting in a real room".

```css
--m-alu:    linear-gradient(168deg,#cfd8e3 0%,#8d97a5 18%,#5b6472 46%,#6f7b8b 74%,#9fb0c4 100%);
--m-steel:  /* double bright band — the mirrored mid is what says "polished" */
--m-copper: /* specular is pale gold, never white; shadow goes maroon */
--m-resin:  /* never #000 — very dark desaturated blue with one tight white streak */
--m-laminate: /* 105° four-stop + 22% specular band + static grain */
```
Rule of thumb: if a material's darkest stop is `#000` or its brightest is `#fff`, it will look like plastic. Keep both SVG `<linearGradient>` and CSS forms generated from **one shared stop array** so they cannot drift.

Surface grain is directional and that direction *is* the material: `feTurbulence baseFrequency="0.9 0.012"` = horizontal brushing (a can lid, a busbar); `"0.012 0.9"` = vertical brushing (an extruded case); `"0.7 0.7"` = ceramic/separator/matte polymer. Rasterise turbulence **once** into a tiled pattern. Never animate `baseFrequency` or `stdDeviation`.

### 3.3 Line weights — √2 ladder, device pixels
```ts
export const LINE = {
  object:    { strokeWidth: 3.2, strokeLinejoin: "miter", strokeLinecap: "butt" },
  trace:     { strokeWidth: 4.5, strokeLinejoin: "round", strokeLinecap: "round" },
  hidden:    { strokeWidth: 1.6, strokeDasharray: "12 6", vectorEffect: "non-scaling-stroke" },
  dimension: { strokeWidth: 1,    vectorEffect: "non-scaling-stroke" },
  hair:      { strokeWidth: 0.75, vectorEffect: "non-scaling-stroke", shapeRendering: "crispEdges" },
} as const;
```
`vector-effect="non-scaling-stroke"` on every hairline, grid and dimension line is mandatory — it fixes a real currently-shipping legibility bug, not just an aesthetic one.

Caps and joins carry meaning and must not be mixed: **data traces** get round caps and round joins (organic, a measured quantity); **geometry** — object outlines, axes, ticks, dimension lines — gets butt caps and miter joins. Sharp corners are what say "machined". Today the nail, the axis and the traces all use round caps, which flattens the distinction.

Dashes derive from one base unit of 6: hidden `"12 6"`, ISO centre line `"24 6 6 6"`, threshold/limit `"2 8"` round-cap. No per-element invented values.

### 3.4 Palette — two hues, luminance leads
```css
--viz-bg:        #050507;                /* blue-tinted black, keep */
--viz-shadow:    #0b0d16;                /* object shadows go blue-violet, never #000 */
--viz-structure: #7b8798;                /* outlines, dimensions, leaders */
--viz-hair:      rgba(160,178,204,.22);
--viz-ink:       #f5f5f7;
--viz-cold: oklch(.80 .10 232);          /* cold / electrical / charge */
--viz-heat: oklch(.79 .13 68);           /* heat / hazard — thermal only, site-wide */
--viz-hold: #ffffff;                     /* "it holds" = the brightest thing on screen */
```

- **`#30d158` is retired site-wide.** Green stops meaning "pass". **Brightness** means pass — the held value becomes the whitest, hottest thing in the frame.
- **Amber is globally reserved for thermal quantities and limits.** It reads as heat wherever it appears, which means the CR-coin page's identity accent moves off amber onto neutral steel. That is the cost of a shared language and it is worth paying.
- Each page keeps **one** identity accent, used **fewer than 15 times per page**, only on eyebrows, the one hero figure, and the single active element in a visual.
- **Accent quota by area:** full chroma is permitted only on strokes ≤5px, dots and type. Fills get the same hue at 12–18% alpha over the dark background, which the eye reads as coloured *light* rather than coloured plastic. A `#30d158` stroke at 3.5px around a 500×240 rect breaks this; a 10%-alpha fill obeys it.
- **Never a third series colour.** More than two series means you have a table.
- **Greyscale gate:** `html{filter:grayscale(1)}` must leave the hierarchy intact — which line matters, object vs background, where the eye lands. Lock it as a Playwright screenshot assertion in the existing suite.
- Target luminance ladder: bg L≈8, grid L≈18, object body L≈28–45, highlight L≈70, the trace that matters L≈92.

### 3.5 Motion grammar
```ts
export const M = {
  seat:    { type: "spring", visualDuration: 0.42, bounce: 0.22 },  // hardware seating
  settle:  { type: "spring", visualDuration: 0.55, bounce: 0.34 },  // light object
  heavy:   { type: "spring", visualDuration: 0.70, bounce: 0.10 },  // real mass
  trace:   { duration: 1.6, ease: [0.28, 0.11, 0.32, 1] },          // reveals, data
  release: { duration: 0.9, ease: [0.16, 1, 0.30, 1] },             // released / falling
  driven:  { duration: 0.7, ease: [0.70, 0, 0.84, 0] },             // pulled / forced
} as const;
```
Six rules:
1. **Nothing fades in.** Objects either *energise* (light travels through them) or *engage* (they move with mass and settle). Opacity fades are for scene transitions only.
2. **Cause → effect → aftermath.** Nothing may start at the same instant as its cause. Effect lags 40–200 ms; aftermath decays over 1.5–4 s and outlives the effect. Nail seats → cell recoils and its contact shadow compresses (+0/+40 ms) → heat blooms and fades over 3.2 s (+180 ms).
3. **Springs for objects, cubic-bezier for data.** A measurement that overshoots is a different measurement. `ease: "easeInOut"` is banned outright — nothing physical accelerates and decelerates identically.
4. **No `repeat: Infinity` on a data layer, ever.** Each stage plays once on enter and holds a composed final state, or it is scrubbed by scroll so the user is the clock. At most **one** living element per screen, and it must be something genuinely still moving in the real world.
5. **Stagger geometrically**, `delay: 0.12 * Math.pow(i, 0.82)` — a constant 100 ms reads mechanical.
6. **Every stage has a designed poster frame.** `prefers-reduced-motion` does not mean "no animation", it means jump to the best-composed still of that mechanism. A visitor scrolling fast on hall 5G mostly sees final frames, so those must be composed, not accidental. Every play-once stage carries a 15px `replay ↻` affordance, because people land mid-page.

### 3.6 One idea per screen
Dark act (`#050507`) = **one figure or one shape per screen**, no tables. Light act (`#f5f5f7`) = every figure, all tables. This is already accidentally true on the sodium page; make it a written rule. Corollary: **one chart per section.** If a section needs two, one of them is a table.

### 3.7 Two rules that cost nothing and do disproportionate work
- **Static film grain**, one 64×64 `feTurbulence` data-URI, tiled, `mix-blend-mode: overlay`, at **3.5% on the dark act and 2% on the light act**. It dithers gradient banding, unifies photos with SVG, and is the cheapest anti-cheap measure that exists. No animated grain shift — that is a full-viewport repaint gated only by a touch heuristic. No chromatic aberration, no unexplained dust speck, no ±1.5% jitter on tick lengths: engineering ticks are stamped, and jitter reads as a rendering bug.
- **Occlusion ordering is free 3D and it is currently missing.** Let things go *behind* other things. Draw the nail in three passes — the part inside the cell clipped and dimmed, then the cell wall, then the part outside at full brightness — and add a 2-line entry wound. That does more for realism than any filter.

### 3.8 Typography
Ten named semantic roles (`.t-headline-super`, `.t-eyebrow`, `.t-spec-value`, `.t-spec-unit`, `.t-footnote`…), never ad-hoc `text-{size}` in a section component. Every number that will ever sit above another number is **mono + `tabular-nums`**. **15px is the floor**: on narrow screens things get *dropped*, never shrunk. No SVG `<text>` anywhere — HTML labels over viewBox coordinates via the existing `viz-labels.tsx`.

---

## 4. PER-PRODUCT DIRECTION

One signature moment per page. Everything else holds still or is a photograph. Where both critics condemned an idea it is gone; where they disagreed the adjudication is stated.

### 1. Industrial Li-Ion Packs (BXL7630H / BXLE330H)
**Hero — COLD START.** The pack physically waking up, played on the macro photograph you already ship. Frame graded cold (hue +8° blue, sat −18%), LEDs dead glass, `AMBIENT −40 °C`. A 3px strike ignites where the red 10 AWG meets the Anderson barrel; current propagates left along a hand-traced path following the cable's real curve, brightening *the cable's own specular*. It enters the enclosure — then **200 ms of dead air while the BMS boots**. LEDs strike at 180 ms intervals with a real LED curve (40 ms rise overshooting to 130%, 120 ms settle). The grade warms to neutral over 1.4 s. Plays once.
*Technique:* existing WebP + one inline SVG overlay (~1.5 KB of path data) + CSS filter animation on the `<img>` + mask-composited streaks. ~1 day, +6 KB, zero new assets. The `−40 °C` claim is enacted rather than stated, and it needs no photograph anyone has to shoot.

**Mechanisms:** (a) **The 7S6P matrix, built by weld** — one 21700 `<symbol>` instanced ×42, nickel strip lays per parallel group, **two** weld dimples per cell because a spot welder splits current between two electrodes, temper rings cooling straw→blue→brown, running total climbing to 25.2 V. (b) **Balancing as heat**, on the shared `<PCB>` primitive: the fast group's bleed FET switches in one frame (silicon does not ease), its resistor glows with a 300 ms rise and 1.4 s asymmetric decay, the BMS hunts, all seven converge.

**Excluded as cliché:** the invented isotherm through the aluminium wall (a fabricated thermogram shown to an audience that owns FLIRs — worse than a lazy diagram, it is a false instrument reading); the Anderson connector cutaway (invented internal geometry of a commodity part an engineer may know better than you); PCB pulse-trace glow; orbiting certification badges.

### 2. 2S–4S Standard 18650 Packs
**Hero — THE SCALLOP.** A sheet of PVC descends over the four-cell bundle, straight-edged and slack. Heat: the silhouette morphs from straight to scalloped as the film pulls into the valleys between cylinders, and the **one continuous specular band breaks into four per-cell bands**. 700 ms with a slight overshoot as the film grips. That single move explains what a soft pack is better than any paragraph, matches your own photograph, and costs half a day.
*Technique:* two node-matched SVG paths (the scalloped one is literally arcs struck between cell centres, so the geometry *is* the engineering) morphed with motion/react, plus a gradient splitting one band into four via animated stop offsets.

**Mechanisms:** (a) **Weld topology and fold** — paired dimples, series tabs folding group to group, voltage stepping 3.6 → 14.4 V; this doubles as the eight-model selector, so the bundle physically rearranges instead of a spec table, deleting a whole component. (b) **Inside the cell** — Archimedean jelly-roll spiral, gasket, PTC, and the **CID disc inverting with a snap** (bistable dome, one frame, high-stiffness spring), breaking the current path.

**Adjudication — match cut killed.** The proposed cross-dissolve from drawing into `pack-4s2p.webp` requires the drawing to register in scale, angle and lighting with an as-shot photo at every breakpoint. That is a narrow-window art-direction task with no cutout to help and a very expensive failure mode. **End on the drawing and place the photograph adjacent in its own frame.** Drawing beside photograph of the identical object is the premium editorial move anyway, and it deletes the registration problem entirely.

### 3. Sodium-Ion NFPP Cells
**Hero — THE FLAT LINE.** The 12-hour dead short, where the *axis* does the work. The current trace slams to 449.7 A and decays; the temperature trace climbs to 98.69 °C and goes flat. Then the time ruler rescales beneath it — 1 min → 10 min → 1 h → 4 h → 12 h — and the current spike compresses to a hairline at the origin while **nothing about the flat line changes**. Twelve hours pass in four seconds and the only thing that moved was time. A thin dashed line at 100 °C labelled *water boils* sits 1.31 °C above the plateau and is never touched.

This is the strongest visual available anywhere in the programme, because its subject is a non-event and it is therefore unstealable: it only works for a company whose good news is a flat line.

**Adjudication — the five-stage "DESCENT" hero is killed outright.** One critic wanted it cut to two layers; the other wanted it cut to the final lattice. The union of their objections leaves nothing standing: the 8× push asks a 65 KB WebP to survive an 8× crop (it will be mush), and the NFPP framework has no source geometry — corner-sharing phosphate tetrahedra are not something to eyeball, so the payoff frame would be fabricated. Spend the budget on the tests, which are the page's real assets.

**Mechanisms:** (a) **Nail penetration, instrument view** — the cell drawn at its true 110 × 140 mm face at 12° tilt so thickness reads; the laminate **dimples and the specular band bends across the dimple** before contact; one over-bright frame at the tip, no sparks; the thermal plume blooms and **stalls at three cell-thicknesses**, then cools; and the voltage readout **does not move**, held dead still while everything else animates. Do not animate the wound self-sealing — what the test proves is *locality*, which is both true and more impressive. (b) **6,000 cycles as a ribbon** — 32 real discharge curves arriving on a stagger, plus one filled envelope between cycle 1 and cycle 6,000; the eye reads thousands, the counter rolls, and the ribbon's lower edge stops with visible air above the dashed 70% floor. Never render 6,000 paths. (c) **−40 °C** — audit `chart-charge-rate.webp` / `chart-discharge-rate.webp` first; if the printed charts carry it, annotate the photograph and draw nothing.

**Excluded as cliché:** the descent through orders of magnitude into molecular structure (pharma/semiconductor documentary convention); **frost, dendrites and condensation** (weather effects, not battery effects — they ship on energy drinks and ski resorts, and they compete with the one thing that carries the claim, which is the discharge line not changing); particles flowing along a trace to suggest current; the `Grid()` component's four evenly-spaced lines that encode nothing.

### 4. Li-Polymer Custom Pouch (15–10,000 mAh)
**Hero — ANY SILHOUETTE.** One pouch cell flowing continuously through six real form factors — an L-shape beside a motor, a wearable disc, a stylus strip, a **wristband arc**, a tablet slab, a stepped camera-module shape. Not stretching: the silhouette genuinely changes, the internal stack lines re-lay themselves parallel to the long axis, the tabs walk to the position the customer's PCB needs, the specular re-forms, and the capacity readout counts. Six answers, one object, never a cut. The arc is the frame people remember, and it is a true capability.
*Technique:* `clip-path: polygon()` on a **div**, not SVG. Author all six as 24-point polygons and they interpolate natively — no morph library, no path-matching code. Material and internal stack lines ride as stacked CSS backgrounds on the same div and get clipped for free. GPU-composited, so it stays smooth where an arbitrary SVG path morph would judder. All labels HTML, so the 15px rule is satisfied by construction. ~5 KB. **Author the six silhouettes in a scratch HTML file with a slider before writing any React.**

**Mechanisms:** (a) **The stack, exploded** — 24 layers rising on a 45 ms stagger, and the whole image is carried by one adjacency: **matte black graphite directly against mirror copper and aluminium**, repeated 24 times, with a genuinely translucent separator you can see through. Far layers get a *static* 1.5px blur. (b) **The ultrasonic weld** — thirty 8 µm copper tails fan out, the horn descends, and it **vibrates instead of sparking**: a 3px lateral jitter so fast it renders as blur. Ultrasonic welding is a cold process; everyone else draws sparks. The horn lifts to reveal one consolidated band with the diamond knurl pressed into it. Fire the vibration on the exact frame the `20 kHz` caption lands, so the motion reads as caused. (c) **The pouch wall** — five layers named, moisture dots stalling against the aluminium barrier and spreading sideways, then the heat seal.

**Adjudication — the melt is downgraded.** Animating `feDisplacementMap` scale over an area is the one filter that reliably drops frames on a mid-range Android, and both the recipe and its own warning appear in the same proposal. Ship the seal as a **three-frame opacity crossfade between pre-authored boundary states**. Verify the CPP melt on a real device before merge or take the crossfade permanently.

### 5. Solid-State Packs (FLCB / PLCB)
Zero photographs exist for this line, so the material language must be invented once and held.

**Hero — TWO WAYS TO CROSS A ROOM.** A cross-section band of five real material layers, with the single best craft tell in the programme: in the liquid lane, ions drift on smooth beziers with lateral jitter through a blurred solvent haze; in the ceramic lane, they advance in **discrete quantised hops on a visible lattice**, vertex to vertex, arriving as a wavefront. Liquid = smooth, ceramic = stepped. Then a temperature ramp crosses both: the haze boils off and that lane goes amber; the lattice does not change. The point is not that ceramic is faster — **the haze is the thing that burns**.
*Technique:* CSS `offset-path` with `animation-timing-function: steps(6)`. The stepping is free and it is the entire idea.

**Mechanisms:** (a) **170 °C as material, not a ticker** — two swatches on a blackbody ramp; the pouch swatch bloats and yellows from ~85 °C, the ceramic swatch's grain brightens marginally. (b) **0.5 mm, measured against something, then bent** — a proper CAD elevation beside a credit card (0.76 mm) and paper (0.1 mm), with extension lines and arrowhead dimension lines, then the band bends to a 12 mm radius. Cheap trick: draw **one** spine path and stroke it five times at different widths and colours, so all five layers bend together automatically.

**Adjudication — two kills.** (i) **"The Cut" fracture beat is removed** until BixLink produces a cut-cell or crush report. It stages a specific abuse-test outcome as if observed, on a page with no photography and no visible evidence behind it. Rendering an unbacked demonstration in a cinematic register is the one failure mode that costs more credibility than a boring page. Restore it the day a report exists, with the protocol named in-frame. (ii) **The logarithmic pressure gauge is removed** — gauges and speedometers are on the banned chart list, and a brushed-metal bezel is chrome carrying mood, not fact. Render the 10⁻¹¹ → 680 ATM envelope as a labelled log span with the decade ticks and the `≈ 6.8 km ocean depth` anchor, which is the part that actually lands.

### 6. CR Coin Cells (38 models)
**Hero — THE SPECIMEN SHEET.** All 38 cells at **true relative scale**, computed from the catalogue dimensions the page already parses. CR2032 opens centred and large as polished turned stainless; it shrinks to true scale and 37 siblings fly in around it on a 22 ms stagger — CR927 at ⌀9.5 mm a speck, CR3032 at ⌀30 mm 3.2× its width. The detail that sells it: **all 38 speculars point the same way**, so the grid reads as a photographed specimen tray under one lamp rather than clip art.

This is the second-strongest image in the programme, because the art direction *is* the company's own data. Nobody else has 38 sizes, so nobody else can make it, and a visitor can hold a CR2032 against the screen and check it. That checkability is the aesthetic.
*Technique:* 38 divs, each a pure-CSS disc — conic gradient of ~24 alternating stops at *irregular* angular widths (irregularity is what reads as machine-turned rather than a pie chart), plus a radial specular, an inset rim light and a contact shadow. Zero image assets. Animate transform and opacity only, never repaint the gradients; `content-visibility: auto` offscreen. Spend the entire art budget on that one disc gradient — it decides between specimen tray and pie chart. The 12° isometric tilt with a cylindrical side wall is a **stretch, not a requirement**; that is where the cost quietly doubles.

**Mechanisms:** (a) **The crimp** — a half-section at ISO drafting convention: positive can hatched at 45°, negative cap at −45° because it is a different part, gasket visibly compressed where the rim folds. That single convention buys more engineering credibility than any effect currently on the site. (b) **Termination family drawn beside its photograph** — the eight AH/AV footprints as true top-view CAD drawings with dimension lines, each next to the existing `pin-tabs` / `pin-top` macro at the same rotation. Both assets already exist. (c) **Raking-light reveal** on the five as-shot macros — a soft-edged gradient mask travelling across each photo on scroll. Zero new assets, zero bytes, and it makes as-shot photography feel directed without touching a pixel.

**Excluded as cliché:** every piece of oscilloscope costume — 10×8 graticule, phosphor bloom, persistence trail, CRT curvature, annunciator pills, machined bezel, fake calibration stamps. Your own data guidance names this exact list as "a sci-fi prop… nobody who has used a scope is impressed." The audience is battery engineers; costume costs credibility with the only people whose opinion converts.

### 7. Rechargeable Coin Cells (LIR / LDA / GRP)
**Hero — THE WIND AND THE SEAL.** A four-layer electrode ribbon winds into a true Archimedean spiral from the outside in, layers staying parallel with constant inter-turn gap; it drops into the can, the wall closes, and **the laser seal fires** — one fine bright point traverses the rim exactly once, leaving a bead that cools white → amber → steel-grey over 600 ms. Scroll-scrubbed and fully reversible, which is what makes a booth visitor scrub it four times.
*Technique:* the spiral is one path generated from `r = a + bθ` sampled to ~200 points; four copies with offset `a` give the four layers. Winding is `pathLength`. The seal is one `stroke-dashoffset` plus a colour tween, and it is the only place on the site where a small bloom earns its GPU cost, because it is genuinely a light source.

**Adjudication — the "unroll / restack" morph is cut.** Spiral and fan-folded stack are topologically different shapes with fiddly matched point counts, and it is the single most expensive visual proposed (2 days before it goes over). Show the stacked construction as a separate adjacent build with no morph. You lose the "one object, two fates" line and keep 80% of the value at half the cost — and the laser seal is the frame people actually remember.

**Mechanisms:** (a) **556 Wh/L as volume** — a true isometric litre cube with three differently shaded faces (top lightest, right mid, front darkest — that shading is the entire trick that makes a cube a solid rather than a hexagon outline), filling to 556 against a lower reference, then dissolving into the count of real LIR2450s it takes to fill it. (b) **LFP vs LCO plateau** — the honest chemistry difference on one properly built chart, with only voltages the catalogue prints; if no measured discharge data exists, label the curve *shape* illustrative in the conditions block.

**Excluded:** frost accumulating on the photo (same weather cliché as sodium); all scope chrome.

### 8. Battery Chargers (14 BL-HP models)
Zero photographs, and the page's own copy says so. Turn that into the brief: **the product is the curve.**

**Hero — THE CHARGE CURVE, PLOTTED FROM REAL RATINGS.** Current flat at the rated CC value, then the knee, then the decaying tail; voltage rising through CC and pinning flat at the CV setpoint; the NTC channel drifting up and flattening. What makes it an instrument rather than a diagram is that the traces are **computed from each model's actual rated V and A out of `specs`**, so all fourteen chargers plot visibly different curves. A cursor travels once on scroll and the traces only exist behind it, with a bright pen tip. Corner readouts update in tabular mono. A plain text label flips CC → CV at the knee.

**Adjudication — plotted data kept, chrome removed.** The bezel, graticule, phosphor and annunciator pills go. What earns the instrument read is **disclosure**: units on both axis ends, the range set by the instrument's limits not by what flatters the data, real time units, and the conditions in the frame. And one mandatory honesty label: the catalogue prints no time constant, so **the CV decay tail is invented and the conditions block must say `SCHEMATIC — CV tail illustrative`**. One unbackable number contaminates every real number beside it.

**Mechanisms:** (a) **The 14 models as a V×A power map** — ring markers (rings read as plotted data, filled dots read as decoration), model codes at 15px mono, with faint **isopower hyperbolas** at 50/100/200 W behind them. Real physics, and the single detail that makes the plot look like it came out of an engineering department. Tapping a point loads that model into the hero — which is what turns two visuals into one system. (b) **Worldwide input as a mains envelope** — a rectangle in V×Hz space with the actual named standards plotted (100/50–60 JP, 120/60 US, 230/50 EU, 220/50 CN, 240/50 UK-AU) and the accepted band drawn around them. Makes the claim with evidence instead of a globe with dots. (c) **Fault injection on the same plot** — OCP clamps the spike within two divisions, reverse polarity clamps at zero, OVP pins the voltage, over-temp steps the current down in a visible shelf. Same component, four datasets, one step index.

---

## 5. THE DATA-PRESENTATION SYSTEM

### 5.1 Which form
Choose by how many numbers the buyer must hold, and whether the conclusion is a **magnitude**, a **shape**, or a **lookup**.

| Situation | Form |
|---|---|
| 1 number and the number is the argument | **Big number / stat tile.** `−40 °C`, `6,000 cycles`, `38 sizes`. |
| 2–5 numbers where the *relationship* is the argument | Not a chart. One comparison pair, direct-labelled, baseline named in words. |
| 6+ numbers on one ordered dimension where the *shape* is the argument | **Chart.** The 11-point C-rate series qualifies: barely sagging across a 45× current range *is* the claim. |
| The buyer needs to look up their own case | **Table.** Never chart a value someone has to read precisely. Charts persuade; tables let people select. |
| The quantity has no intuitive scale for a non-specialist | **Physical anchor.** 98.69 °C is *below boiling*. 55 °C is *a hot tap*. Never anchor a spec to another spec. |

### 5.2 Chart craft
- **No frame, no plot fill, no tick marks.** The only structural line permitted is one baseline or reference at the value that matters — not at zero by default.
- **At most 3 gridlines, each a claim.** Evenly spaced lines every N units is the Excel tell; unevenly spaced lines at *meaningful thresholds* (the 70% floor, ambient, the rated limit) is the premium tell. Each is labelled with its value and its meaning. **Delete `Grid()`.**
- **No legend, ever.** Direct-label the end of each series in its own colour. No colour without a direct label; if the label does not fit, you do not get that series.
- **Annotation-led, not minimal.** 2–4 annotations per chart, each naming a real point with its value and unit. The headline states the **conclusion** ("Push it to 9C — it barely notices"), never the variable ("Rate capability").
- **Declare truncation on the chart face**, as a required prop, not a hand-typed caption. A non-zero baseline is fine; hiding it is not.
- **Round on the page, exact in the annotation.** Headline `~450 A`, annotation `449.7 A`.
- **Whitelist:** stat tile; paired horizontal bars (≤12 rows, ≤2 series, HTML divs); range/window strip; single annotated trace; threshold-and-hold (a trace plus a filled band it never enters); one two-item comparison bar per page; table with exactly one in-cell bar column. **Banned:** pie, donut, stacked anything, dual y-axis, radar, scatter, 3D, gauge, small multiples >2, any legend, any SVG `<text>`.
- **Bars grow by mask reveal, not by width** — an `<hr>` inside an `overflow:hidden` rounded mask, so the cap stays crisp with no sub-pixel mush. The bar is `aria-hidden`; the printed number carries the meaning. **The baseline row prints no number** — name the reference in words and give only the comparison rows a multiplier. Three bars maximum; swap workloads with tabs.

### 5.3 Dense data
Group into families and lead with the group (38 sizes = **5 diameters**). Rank by what the buyer shops on, never by part number. **One** in-row micro-visual, on the single column with the widest spread. Sticky first column (`position:sticky; left:0`) so row identity survives horizontal scroll — three lines, and the biggest phone-table improvement available. Progressive disclosure **by rows only**: 8 visible plus a native `<details>` "Show all 38 sizes". **Hiding a row reads as courtesy; hiding a column reads as evasion** to exactly the buyer you are trying to convince. Units once, in the header. No search box on a 38-row table. The 14-model charger matrix is pivoted to cards below 768px from the same array — one `hidden md:block` / `md:hidden` pair, zero JS. Tables live in the light act, never the dark one.

### 5.4 Instrument aesthetic — disclosures, not photons
An element earns its place if it carries a fact (unit, range, condition, tolerance, sample interval). If it carries a mood it is costume, and at a battery trade show costume costs credibility.

**Earns it:** units on every axis end; an axis range set by the instrument's limits, not by what flatters the data; **visible sampling artefacts** — steppy on the plateau, dense at the event; **asymmetric time**, because the interesting thing happens in the first 2% of the window; conditions in the frame; a tolerance band the curve never enters; one spot marker at the maximum with its measurement point named; real time units.

**Affectation:** phosphor, scanlines, CRT curvature, graticules, fake noise sprinkled on a smooth curve, invented calibration stamps, HUD brackets, particles flowing along a curve to suggest current. **Smooth beziers presented as measurements are the current page's biggest exposure.**

**The escape hatch that protects everything else:** where you must draw and do not have the log, write `SCHEMATIC` in the conditions block and keep it *visibly* schematic — straight segments, no invented noise, no pretend sampling. That one word protects every other number on the page.

### 5.5 Animating data
Legitimate: draw-on **at measurement pace** (map draw rate to the time axis, or do not animate the draw — animating a 449.7 A spike and an 11-hour plateau at a constant rate animates a lie); count-up once on entry, 700–900 ms, landing on the printed value with the same significant figures; bars growing from the declared baseline; scrub-linked state change; staged reveal in reading order.

Gimmick: infinite loops on a data layer; **spring physics on a measured quantity** (overshoot implies a different measurement); particles suggesting current; animating between charts of different data; any animation that must finish before the number is readable.

Hard rule: **every figure is present in the DOM and legible at t=0.** A visitor scrolls fast and hall wifi may not have delivered the JS.

### 5.6 Worked example — staging the sodium safety result

The 12-hour short circuit is the page's strongest number and it is currently two hand-authored cubic beziers with no stated conditions. Seven moves, in order:

1. **Name the protocol before the result.** "External short circuit, 3 mΩ, held 12 h" is a protocol. "Safe under short circuit" is a claim. Protocols are believed; claims are discounted.
2. **Conditions in the frame**, six mono lines at 15px in `--viz-dim`:
   `CELL 70155250 · 13.0 Ah · SoC 100% · EXTERNAL R = 3 mΩ · AMBIENT 25 ±3 °C · TC AT CASE CENTRE · DURATION 12 h`
   The cell identity is currently absent and it matters. Highest-leverage change on the page; it costs nothing.
3. **Give the reader arithmetic they can check.** Two are free in the existing data and this is the single most persuasive content in the entire programme, because a visitor can redo it on their own phone at the booth:
   - 449.7 A on a 13.0 Ah cell = **34.6C — inside the cell's own printed 40C pulse rating.** The abuse test lands within the rated envelope.
   - 449.7 A × 3 mΩ ≈ **1.35 V across the shunt**, from a 3.0 V nominal cell — most of the pack voltage dropped internally, which is precisely why it did not run away.
4. **Show the non-event at the honest time scale.** Broken time axis: 0–60 s occupying the left 40% of the width, 1 h–12 h the right 60%, with an explicit break glyph and both ranges labelled. Annotate `peak 449.7 A at t < 1 s` and `98.69 °C max, then flat for 11 h 59 min`. The boredom is the product, and the truthful shape is also the more persuasive one.
5. **Anchor to human scale, once.** 98.69 °C is below boiling — a dashed `water boils` line 1.31 °C above the plateau. Then the one contrast that makes the act land: lithium-ion thermal runaway is 400–800 °C, against 55 °C on nail penetration. **This is the only comparison chart permitted on the page.** Do not draw an invented competitor curve — an engineer at the booth will ask for the source.
6. **Grade every claim.** Three mono tags: `MEASURED` (this cell, this report) / `RATED` (design spec) / `SERIES` (product-line claim). The page already does this in prose for cycle life — 6,000 @3C to ≥70% measured, versus the 8,000–10,000 @1C to ≥80% series claim. Make it a visible tag system. Admitting which numbers are weaker is what makes the strong ones believable.
7. **Offer the report.** One line — "Full test report available on request" — pointed at the existing mailto. Converts scepticism into a lead.

**Sampling:** render the plateau as a stepped polyline at a stated interval (`logged 1/min`). If the real log is unavailable, `SCHEMATIC — PLOTTED FROM REPORTED PEAK VALUES` goes in the conditions block and the trace stays visibly schematic. **Never a smooth bezier presented as a measurement.** Delete the infinite dash-flow and the pulsing peak circle; draw on once over 1.9 s, then hold.

**Before drawing any of it:** open `chart-short-circuit.webp` and `chart-13ah-temp.webp`. If the printed test charts carry the trace, an annotated photograph of the real report beats any SVG you can author, respects the as-shot photo policy exactly, and sidesteps the bezier-honesty problem entirely.

**Never:** explosion imagery, burning-competitor-cell video, flames, or the word "safe" as a headline. Premium safety staging is deadpan. The tone of a test report *is* the persuasion.

---

## 6. HONEST COST

### Tier 1 — this week. Zero new dependencies, zero new assets. **≈4 working days.**
1. **The craft substrate** (~3 h to write): `components/site/viz-defs.tsx` (shared `<defs>`: five material gradients, contact-shadow radial, bounded specular/diffuse `lit` filter), `components/site/viz-tokens.ts` (`LIGHT`, `LINE`, `M` exported from one stop array so CSS and SVG cannot drift), `--viz-*` palette and static `.bx-grain` in `globals.css`.
2. **Prove it on sodium alone** (~4 h): gradients replace flat fills, rim strokes and contact shadows added, `LINE` applied with `non-scaling-stroke` everywhere, two-hue palette swap, `Grid()` deleted, every `repeat: Infinity` stripped from data layers, poster frames composed.
3. **Rebuild the 12-hour short-circuit visual** per §5.6, including the checkable arithmetic (~4 h).
4. **Delete** the 24 zero-importer components and the live MagicUI decoration layer (~2 h, negative diff).
5. **Data-system pass across all 8 pages** (~1 day): conditions blocks, MEASURED/RATED/SERIES tags, legends removed, truncation declared as a prop, mono `tabular-nums`, sticky first column, `<details>` row disclosure, charger matrix pivoted to cards.
6. **Verification gate** (~1 h): greyscale screenshot assertion, every-label-≥15px assertion, no-horizontal-overflow assertion, added to the existing Playwright suite.
7. **Roll out steps 1–2 to the remaining 7 pages** (~2 h each with screenshot verification).

**What it buys:** every page stops reading as vector clip art, because the objects become lit; a real mobile legibility bug is fixed; the recognisable OS-default green is gone; the screensaver read disappears; and the numbers become defensible. This is roughly 8% of the scope in the input bundles and it carries most of the perceived-quality gain. Every flashier idea still looks cheap sitting on top of `rgba` fills and 0.28px hairlines.

### Tier 2 — one build-step dependency or an offline asset step. **≈6–8 dev-days plus one photo day.**
1. **Re-encode the existing photography** (~0.5 day, one offline CLI step — sharp/squoosh/ffmpeg, dev-time only). The packs page ships 1.94 MB today. This is worth more page-weight than every technique in this brief combined, and nobody proposed it. Do it before adding a single byte anywhere else.
2. **The two signature heroes:** the li-polymer clip-path silhouette morph (~2 days) and the CR-coin specimen sheet (~1.5 days). Zero dependencies, both unstealable.
3. **The shrink-wrap scallop** (~0.5 day) and the **ultrasonic cold weld** (~1.5 days) — the two manufacturing-step visuals that come off the factory floor rather than a component library.
4. **One shared `<PCB>` primitive** (~1.5 days) reskinned across the packs, protection and charger pages. Three sub-bundles each proposed building this separately at 1.5 days apiece; building it once saves 3 days.
5. **A one-day photo shoot** — the highest-return asset spend available, because it removes the fabrication risk from all 8 pages at once. Shot list: the welder mid-cycle; a caliper closed on a real cell; the OCV tester; a mass balance reading to 0.01 g; a tray of pulled rejects; the printed test report on the bench; the real lot code and date stamp on a wrapper, blown up as the site's typographic motif; and the *invisible component* frames — a smoke alarm on a ceiling, a smart meter, a hearing aid, an AGV — with the cell marked at true scale inside. Every one of these is unfakeable and needs no motion.

**What it buys:** page weight roughly halved; two images no competitor can copy; and a credibility layer built from photographs of the actual line rather than drawings of an imagined one.

### Tier 3 — genuinely out of scope before the show.
Blender geometry of any kind; image-sequence scrubbing; three.js or GLSL of any kind; the NFPP crystal lattice; the Anderson connector cutaway; false-colour thermal fields; the solid-state fracture demonstration (until a test report exists); the "unroll/restack" morph; the drawing-to-photograph match cut; and the roughly twenty bespoke four-beat mechanisms across seven pages that the input bundles self-cost at 45+ dev-days.

**Say this plainly to the user:** the risk is not that these are too hard. The risk is volume. Premium is one set piece and the nerve to leave the rest still. Apple's own `/mac/` page is 9,730px tall with zero video, zero canvas and zero sticky elements and still reads expensive; NVIDIA's flagship consumer page ships 121 stills, no motion, and hand-drawn outlined SVG charts. A page where every section is a virtuoso mechanism does not read as an engineering company — it reads as a studio's demo reel, and try-hard is the same cheap signal as low-craft, one floor up. Worse: twenty mechanisms cannot all be backed by real data, so volume itself forces fabrication — invented isotherms, invented layer counts, curves plotted from a formula and dressed as measurements. In front of an electronica audience, one unbackable number contaminates every real number beside it, and the expensive look becomes the thing that made the lie plausible.

---

## 7. THE FIRST MOVE

**Rebuild the sodium page's 12-hour short-circuit visual, on the craft substrate, and stop.**

One page, one visual. Why this one:

- It is the page you like least, so the delta is largest and most legible.
- It is the visual with the strongest underlying claim in the entire catalogue, and today that claim is carried by two hand-authored beziers with no stated test conditions — the biggest gap between what is true and what is shown.
- It forces the substrate into existence. You cannot build it without `viz-defs`, `viz-tokens`, the two-hue palette, the line hierarchy and the poster-frame discipline, so proving the visual proves the system.
- It is the only visual whose subject is a non-event, which makes it unstealable, and the fix is deletion plus two sentences of arithmetic rather than new art.
- It costs about seven hours and needs no asset, no dependency and no skill nobody has.

**Then hard stop and show it to a human before touching page two.** An agent can verify "no horizontal overflow, every label ≥15px, hierarchy survives greyscale". It cannot verify "that reads as anodised aluminium". That judgement has to happen once, on one page, before the same decision is replicated seven more times.

**"It worked" looks like this:**
1. With `html{filter:grayscale(1)}` applied, the temperature plateau is still obviously the most important thing in the frame and the object still reads as an object. (Playwright screenshot assertion.)
2. At 375px, every label is ≥15px, nothing overflows horizontally, and the axis hairlines are visible — the 0.28px ghost is gone.
3. With `prefers-reduced-motion` on, the page shows a composed poster frame: the plateau flat, the conditions block readable, both readouts locked. Not a blank stage.
4. The frame states the cell, the SoC, the ambient, the shunt resistance and the duration, and it says either `logged 1/min` or `SCHEMATIC`.
5. Both pieces of arithmetic — 34.6C inside the 40C rating, and 1.35 V dropped across the shunt — are on the page and a stranger with a phone can redo them.
6. Nothing on the data layer is still animating after 2 seconds.
7. Page weight is unchanged or lower than before the edit.

If a human looks at that and says "that looks like an engineering company", the remaining seven pages are mechanical. If they say it still looks flat, the problem is the material gradients and you have spent one day, not nineteen, finding out.

---

## 8. OPEN QUESTIONS

Ordered by what unblocks the most. Ask one at a time.

**1. Photography: do we shoot, or do we commit to drawing-only?**
One day with a camera on the production line — the welder mid-cycle, a caliper on a cell, the mass balance, a tray of rejects, the printed test report, the lot code on a wrapper, and the cell installed inside the ordinary objects it disappears into. Either we book that day, or we accept that every mechanism visual is a drawing and we label the unbacked ones `SCHEMATIC` throughout. **My recommendation: shoot.** It has the longest lead time, it gates all of Tier 2, and it is the single largest credibility purchase available — a photograph of the measurement being taken is unfakeable and removes the fabrication risk from all eight pages at once.

**2. Can we get the raw test data or the full report behind the sodium numbers?**
Specifically: the logged sampling interval for the 12-hour short, the actual discharge-curve shape, and whether `chart-short-circuit.webp` and `chart-13ah-temp.webp` are photographs of the real printed charts. **Recommendation: chase this before drawing.** If the printed charts are usable, we annotate the photograph and draw nothing — better, cheaper, and it makes the bezier-honesty problem vanish. Without the interval we must print `SCHEMATIC`, which is survivable but weaker.

**3. Do we delete the decoration layer — meteors, ripple, particles, sparkles, warp-background, grid patterns, border-beams, orbiting circles, glitch text — outright?**
This is a taste call only you can make, and it is a negative diff. **Recommendation: delete all of it.** That set is the visual signature of an AI-generated SaaS landing page and it is a bigger source of the cheap read than the four schematics you named. Removing it raises perceived quality more than any new mechanism in this brief.

**4. Time budget: four days, or ten?**
Tier 1 alone (~4 days) lifts all eight pages onto the craft substrate and fixes the honesty problem. Tier 1 + the two signature heroes + the two manufacturing visuals + the photo re-encode is ~10 days. **Recommendation: commit to Tier 1 now, decide on Tier 2 after you have seen the sodium page.** Do not commit to both up front — the whole point of the first move is that it is a decision point.

**5. May we add one build-time-only tool to re-encode the existing photography?**
No runtime dependency, no bundle impact — a CLI step that re-encodes the 1.3–1.9 MB of photos per page to modern formats at the exact sizes we ship. **Recommendation: yes.** It buys more real-world performance for a trade-show visitor on congested hall 5G than every "zero new bytes" technique in this brief put together, and it is half a day of work.