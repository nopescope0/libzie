---
name: libzie
description: A dark, calm personal course archive made of flat color blocks; like books on a shelf, everything stays where it is.
colors:
  shelf-night: "#0e1a2b"
  shelf-side: "#0a1422"
  shelf-surface: "#172a42"
  shelf-hover: "#213a5a"
  hairline: "#1d3350"
  hairline-strong: "#36527a"
  paper-white: "#eaf1fb"
  muted-ink: "#a3b6cf"
  faint-ink: "#8aa0bd"
  lamp-orange: "#ff8a3d"
  lamp-orange-hover: "#ffa466"
  warning-clay: "#c98080"
  type-pdf: "#d39a9a"
  type-slide: "#d6b38a"
  type-doc: "#93afd3"
  type-sheet: "#95c2a2"
  type-image: "#b8a3cf"
  press-scrim: "rgba(0, 0, 0, 0.18)"
  backdrop-scrim: "rgba(10, 12, 16, 0.6)"
  course-red: "#f87171"
  course-orange: "#fb923c"
  course-yellow: "#facc15"
  course-green: "#4ade80"
  course-teal: "#2dd4bf"
  course-sky: "#38bdf8"
  course-violet: "#a78bfa"
  course-pink: "#f472b6"
typography:
  display:
    fontFamily: "Linux Libertine, Linux Libertine O, Georgia, Times New Roman, serif"
    fontSize: "72px"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-1px"
  headline:
    fontFamily: "Linux Libertine, Linux Libertine O, Georgia, Times New Roman, serif"
    fontSize: "28px"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.5px"
  title:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.4px"
  body:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.35
  widget-numeral:
    fontFamily: "Linux Libertine, Linux Libertine O, Georgia, Times New Roman, serif"
    fontSize: "36px"
    fontWeight: 400
    lineHeight: 1
  widget-temperature:
    fontFamily: "Linux Libertine, Linux Libertine O, Georgia, Times New Roman, serif"
    fontSize: "24px"
    fontWeight: 400
    lineHeight: 1
  sidebar-title:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
  tile-title-narrow:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.1
  tile-title-small:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "21px"
    fontWeight: 400
    lineHeight: 1.1
  tile-summary:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.28
  tile-summary-narrow:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.28
  course-chip:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "11.5px"
    fontWeight: 500
    lineHeight: 1.5
  type-badge:
    fontFamily: "Linux Biolinum, Linux Biolinum O, Segoe UI, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "0.4px"
rounded:
  sharp: "2px"
  chip: "3px"
  soft: "4px"
spacing:
  tile-gap: "5px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  section: "38px"
components:
  button-primary:
    backgroundColor: "{colors.lamp-orange}"
    textColor: "{colors.shelf-night}"
    rounded: "{rounded.sharp}"
    padding: "6px 12px"
  button-primary-hover:
    backgroundColor: "{colors.lamp-orange-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.muted-ink}"
    rounded: "{rounded.sharp}"
    padding: "6px 12px"
  button-secondary-hover:
    backgroundColor: "{colors.shelf-hover}"
    textColor: "{colors.paper-white}"
  search-field:
    backgroundColor: "{colors.shelf-surface}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.sharp}"
    padding: "7px 10px 7px 32px"
  file-card:
    backgroundColor: "{colors.shelf-surface}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.sharp}"
  widget:
    backgroundColor: "{colors.shelf-surface}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.soft}"
    padding: "10px 12px"
---

# Design System: libzie

## Overview

**Creative North Star: "The Study Shelf"**

libzie is a quiet shelf in a dim room. Everything sits where it belongs, flat and at arm's reach: courses are solid colored blocks standing side by side like book spines, files are cards laid out beneath them, and the interface itself recedes to a calm charcoal so the documents are the only bright things. The brand logo — three books leaning on a shelf spelling "lib" — is the whole system in miniature: upright, tidy, slightly relaxed.

The system is built for long sessions, not first impressions. Surfaces are flat and tonal, borders are hairlines, corners are almost square, and motion explains what changed rather than decorating it. Color is concentrated in exactly one place — the per-course tiles — so a course is recognizable at a glance, and the chrome around it stays neutral. Type pairs a regular-weight serif for headings with its sans companion for everything that has to be read quickly.

It borrows its landing grid from jackywinter.com (flat saturated blocks, thin outline shapes, dark gaps) but turns it down: darker ground, one warm accent, and no hard-offset or glossy effects.

**Key Characteristics:**
- Flat, tonal surfaces; depth comes from one step lighter, never from shadows on cards.
- Near-square corners (2px); a single slightly softer 4px reserved for the home widgets.
- Per-course color is the only saturated color in the UI; tile text color is chosen for 4.5:1 contrast.
- Thin outline shapes (one per course) are the system's ornament.
- Large regular-weight serif headings; a quiet sans for names, labels and body.
- Motion is short, ease-out, and gated by `prefers-reduced-motion`.

## Colors

A deep navy ground with one warm orange accent; the saturated palette exists only to tell courses apart.

### Primary
- **Lamp Orange** (#ff8a3d): the single interface accent — primary buttons, the sidebar fill for courses without a color, progress lines, drop outlines, scrollbars, the logo's "i" dot. Its hover state is **Lamp Orange Hover** (#ffa466).

### Secondary — course colors
- **Course palette** (#f87171, #fb923c, #facc15, #4ade80, #2dd4bf, #38bdf8, #a78bfa, #f472b6): eight vivid hues assigned to courses, least-used first. A tile's background starts as the course color darkened 15%; its text and outline shape are **Paper White** or **Shelf Night**, whichever reaches 4.5:1 with the smaller nudge of the background (see The Legible Ink Rule). The same color fills the active sidebar row, the active tab and the thumbnail badge swatch. Existing pastel selections from an earlier palette are remapped in order at read time.

### Neutral
- **Shelf Night** (#0e1a2b): page ground and the dark text on light tiles.
- **Shelf Side** (#0a1422): the sidebar, one step lighter than the ground.
- **Shelf Surface** (#172a42): cards, search field, widgets, menus, dialogs.
- **Shelf Hover** (#213a5a): hover and pressed neutral fill.
- **Hairline** (#1d3350) and **Hairline Strong** (#36527a): 1px dividers and borders; the strong one frames menus, dialogs and focused inputs.
- **Paper White** (#eaf1fb): primary text and icon strokes.
- **Muted Ink** (#a3b6cf) and **Faint Ink** (#8aa0bd): secondary and tertiary text; both meet 4.5:1 on the ground and on card surfaces.
- **Warning Clay** (#c98080): destructive actions and errors only.
- **File-type tints** (pdf #d39a9a, slide #d6b38a, doc #93afd3, sheet #95c2a2, image #b8a3cf, each at about 10% over Shelf Hover): the small type badge only; deliberately outside the interface palette.

### Named Rules
**The One Saturated Place Rule.** Saturated color belongs to course identity (tiles, the active row/tab, badge swatches). Interface chrome stays neutral plus Lamp Orange; never add a second accent.
**The Tonal Step Rule.** To separate two surfaces, step one tone (ground → side → surface → hover) or draw a hairline. Do not reach for a shadow or a gradient.
**The Legible Ink Rule.** Text on a course color is chosen by WCAG contrast, never by a brightness cutoff: Shelf Night or Paper White, whichever reaches 4.5:1 with the smaller nudge of the course color (darker for light ink, lighter for dark ink). The same pair fills the active sidebar row and the active tab.

## Typography

**Display / Headline Font:** Linux Libertine (with Georgia, Times New Roman, serif) — headings only.
**Body / Title / Label Font:** Linux Biolinum (with Segoe UI, system-ui, sans-serif) — everything else, including course names.

**Character:** A bookish serif that talks, and its sans sibling that works. Both are regular weight; hierarchy comes from size, never from bold or caps. Both are bundled (SIL OFL), so the system looks the same offline on any machine.

### Hierarchy
- **Display** (400, 72px, 1.05, -1px): the home greeting only; the one place type performs (letters wave on load and hover).
- **Headline** (400, 28px, 1.1, -0.5px): section headings, always sentence case with a line icon, a faint count and a hairline rule.
- **Title** (400, 26px, 1.1, -0.4px): course names on tiles (22px on narrow widths; 21px on small subfolder tiles).
- **Body** (400, 15px, 1.5): navigation, buttons, file names. Prose lines are short; there are no long paragraphs.
- **Label** (400, 12.5px, 1.35): file size and date, hints. Never uppercase, never tracked out. The one exception is the file-type badge (600, 11px, uppercase, .4px tracking), a three-letter extension rather than a word.
- **Widget numerals** (serif, 400): 36px clock, 24px temperature. **Sidebar title** (sans, 17px): the "Courses" label. **Tile summary** (sans, 19px; 15.5px on small tiles): the two-line hover text. **Course chip** (sans, 11.5px, 500).

### Named Rules
**The Serif-For-Headings Rule.** The serif is for headings, the logotype, the clock and the temperature. Names, labels and body copy use the sans; a serif at small size looked harsh and was removed from them.
**The No-Eyebrow Rule.** No small uppercase kicker above a heading. The heading carries its own weight.

## Layout

A fixed 260px sidebar (collapsible with Ctrl+B to 0) beside a fluid main area; the top bar holds the breadcrumb, search and two actions. Content is a column of sections, each introduced by a headline row. Grids are auto-filling with a deliberate **5px dark gap** between tiles and cards (the gap is the grout of the flat-block look). Large course tiles are 5:6 portrait at a 220px minimum; small subfolder tiles are 4:3 at 190px; file thumbnails are 4:3 at 180px. Subfolders inside a course use the compact 4:3 tiles. Sections are separated by 38px above and 14px below their heading.

While a document is open the top bar is hidden and the tab bar is the only chrome, so the PDF takes the whole main area. Narrow widths (≤760px) shrink the sidebar to 200px and hide secondary columns; the product is desktop-only, so there is no dedicated mobile layout.

## Elevation & Depth

Flat by default. Depth is conveyed tonally (ground → sidebar → surface → hover) and with 1px hairlines. The only shadow in the system belongs to floating layers that leave the page: context menus, dialogs and the toast.

### Shadow Vocabulary
- **Floating layer** (`box-shadow: 0 10px 30px rgba(10, 12, 16, 0.5)`): context menus and dialogs, together with a Hairline Strong border.
- **Glass chip** (`backdrop-filter: blur(8px)` over a 48% Shelf Night fill): the course badge and the "more" button laid over thumbnail images, so they stay legible over any page.

### Named Rules
**The Flat-Until-Floating Rule.** Cards, tiles, rows and tabs never carry a shadow. A shadow appears only when a layer detaches from the page.

## Shapes

Almost square. Interface corners are **2px**; the clock and weather widgets use **4px** and the frosted course chip over thumbnails uses **3px**, as deliberate, barely softer exceptions. Tiles and file cards are cut square. Circles appear only as small dots (the course dot, the logo's "i" dot) and the weather sun. Ornament is a single thin (1.2px) outline shape per course — diamond, plus, four-lobe, square, triangle, banner, circle, octagon, hexagon — assigned by the course's alphabetical position, drawn in the tile's text color at 72% opacity. Icons are drawn with a 1.3–1.6px stroke, square caps and mitered joins.

## Components

### Buttons
- **Shape:** 2px corners, 6px 12px padding, 1px border.
- **Primary:** Lamp Orange fill with Shelf Night text ("Upload"). Hover lightens to #ffa466.
- **Secondary (default):** transparent with a Hairline border and Muted Ink text; hover fills Shelf Hover and brightens the text. Icon buttons are 26px squares with the same hover.
- **Signature motion:** icons animate on hover to say what the button does — the upload arrow flies up and re-enters, the new-folder document slides out of the folder.

### Course tiles
- **Style:** solid course-color fill, 14px 16px padding, name top-left, outline shape centered in the lower area.
- **Hover:** the shape dissolves while a two-line summary and an arrow rise in; brightness lifts 6%.
- **Active context:** the same color paints the active sidebar row (a triangle slides in on hover, then fills on selection), the active tab and the breadcrumb icon. Navigating a tile morphs its shape into the breadcrumb icon.

### File cards and rows
- **Card:** Shelf Surface, square, 4:3 thumbnail (first PDF page rendered with pdf.js, cached) over name + size · date. The course badge is a frosted chip in the top-left (swatch + name); on hover it turns into the course's outline shape and the image zooms 7% — there is no highlight color change. The chip is omitted on a course page (every file there shares the course) and shown in search results and "Recently opened", where files come from several courses.
- **Row:** the list-view equivalent with a type badge, name, course chip, size and date.

### Inputs / Fields
- **Search:** Shelf Surface fill, Hairline border, leading magnifier; focus shifts the border to Hairline Strong. Placeholder is Faint Ink and shows the `/` shortcut.
- **Dialog input:** same treatment on the ground color.

### Navigation
- **Sidebar:** brand (logo + serif wordmark), clock and weather widgets, Home, then the course list with colored squares. Rows have no hover fill — only the sliding course-color triangle.
- **Tabs:** Home plus one tab per open file; the active tab takes the course color and text color of its course. Tabs can be dragged to reorder and closed with × or middle-click.
- **Breadcrumb:** Home icon, the course's shape icon in its color, folder icons for subfolders; a search appends its own segment instead of replacing the path.
- **Keyboard:** every tile, card, row, sidebar row and tab is a focus stop (Tab); Enter or Space opens it, arrow keys move between neighbours, F2 renames, Delete deletes. The focus ring is 2px Lamp Orange with a 2px offset (inside the block and in the tile's ink color on tiles), and the ⋯ button appears on focus as well as hover.

### Home widgets
- **Clock and weather:** 4px corners, Shelf Surface fill, serif numerals. The clock separator is static; the weather icon is a line drawing that animates only on hover or keyboard focus (rays rotate, rain falls), and infinite loops pause while the tab is hidden. With no city set the weather widget shows a quiet "Add weather" action instead of a placeholder. Both are small; they must never outweigh the course tiles.

### Menus, dialogs and toasts
- Floating layers use Shelf Surface, a Hairline Strong border and the floating shadow; menus open from the cursor in 250ms with a 0.97 scale, dialogs scale from 0.96. The toast sits bottom-center and carries an optional 2px Lamp Orange progress line; delete and move add an underlined "Undo" action that stays for 7 seconds.

## The Shelf (Motif)

The one idea that runs through the system: a course is a **book on a shelf**. On the home page the courses stand on a 14px shelf board (`--shelf`): each book is a 168px-wide block with a spine (the course's vivid color, vertical serif title, 52px) and a cover (the darkened tile color, file count, the course's outline shape). Height follows the file count (190-300px). Pointing at a book pulls it 8px up off the shelf. "Continue" cards are folder tabs: a trapezoid tab in the course color (the file tag, e.g. "Lecture 3") on a surface block. On a course page the header is a 22px spine block in the course color beside a 64px serif title, and each file is a page with the same trapezoid tab above its thumbnail. Hover reveals and focus rings follow the earlier rules; the shelf and tabs are flat, with no shadows or gradients.

**Engineering ornament.** The per-course outline shapes are engineering symbols, assigned by alphabetical position: gear, IC chip, resistor, capacitor, inductor, transistor, diode, op-amp, sine wave. Two inline-SVG decorations carry the theme in the page itself: a meshing gear pair (12 and 8 teeth, the small one turning 1.5x as fast in the opposite direction so the teeth stay meshed) beside the home greeting and the course title; pointing at that block accelerates them at constant acceleration to 140°/s in 1.5s, and leaving it coasts them down to a stop over 2.3s (the same curves as the "Motion — Shelf and Gears" frame in Figma; never a standing loop, still under reduced motion); and a faint PCB (traces with 45° bends, a chip, a resistor, solder pads, a ground symbol) in the bottom-right of the main area, 55% opacity, behind the content, hidden while a file is open and below 900px. Section rules end in a small solder-pad ring. All of it is stroke-only in `--line-strong` with the accent on a few pads; none of it may sit under text that needs contrast.

## Do's and Don'ts

### Do:
- **Do** keep every radius at 2px (4px for the home widgets, 3px for the thumbnail course chip only).
- **Do** put saturated color only on course identity (tiles, active row/tab, badge swatch).
- **Do** separate surfaces with one tonal step or a 1px hairline.
- **Do** keep a 5px gap between tiles and cards so the dark ground reads as grout.
- **Do** pick text on a course color by contrast (4.5:1), not by a brightness cutoff.
- **Do** make every clickable block keyboard-focusable with a visible focus ring.
- **Do** use the motion tokens in `:root`: open slower than close, hover-in ≤250ms, stagger 40ms, emphasis 500ms; honor `prefers-reduced-motion`.
- **Do** keep headings in the serif and everything else in the sans.

### Don't:
- **Don't** add a second accent or a gradient; no gradient text.
- **Don't** put shadows on cards, tiles, rows or tabs; shadows are only for menus, dialogs and the toast.
- **Don't** round corners beyond 4px or use pill shapes.
- **Don't** use bold or uppercase for hierarchy, and don't add eyebrow labels above headings.
- **Don't** highlight a hovered card by changing its fill; reveal or zoom instead.
- **Don't** let a decorative loop run on screen without a reduced-motion fallback, and don't start an infinite animation unless the user is hovering or focusing it.
- **Don't** put an action behind hover alone; it must also appear on keyboard focus.
- **Don't** introduce emoji or unicode glyphs as icons; icons are drawn SVG in the existing stroke style.

**Sidebar double helix.** Two large traces (48px wide, 120px per turn) wind around each other down the right edge of the sidebar for its full height behind the navigation: one in `--line-strong`, one in the accent, each fading and thinning where it passes behind the other, with a solder pad at every other crossing and at the four ends. Stroke-only, 50% opacity, static.

**Space shuttle.** Between the heading text and the gear pair a space shuttle stack lies on its side, drawn in outline only (nose left): the orbiter on top (cockpit window, payload-bay seam, tail fin, engine bell), the external tank with its intertank band, and a solid rocket booster below with segment joints and a nozzle. The strip starts 56px after the right edge of the greeting (or the course title) and ends at the first tooth of the left gear, so it stretches with the window (its viewBox ratio, 540:112, stays fixed; it is hidden when under 240px wide or below 900px). Two flames, one from the orbiter's engines and one from the booster, reach toward the gears: the gears are the engine, and the flames' length and brightness follow the gears' speed (70% length and 45% opacity at rest, full at 140°/s). Stroke-only in `--line-strong`, flames in the accent. Nothing else sits in that strip.
