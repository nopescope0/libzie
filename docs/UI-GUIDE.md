# libzie UI guide

Read this file **before** adding a new window, menu, setting, card or animation. [DESIGN.md](DESIGN.md) is the full description of the system (colors, typography, components); this file is its **practical guide**: it summarizes the character, gives ready-made recipes and lists the rules that came out of past mistakes. If they conflict, DESIGN.md wins. If you learn a new rule, update this file.

## 1. Character (one paragraph)

libzie is a calm, dark or light "study shelf": everything stays where it is, flat and close at hand. **Flat color blocks, almost square corners, thin lines, large regular-weight serif headings.** Motion *explains* something (where it came from, where it went); it does not decorate. Color is concentrated in one place: the identity of the course. The interface is neutral plus a single orange accent.

When designing something new, ask yourself: *Can I build this from an existing component?* Most of the time the answer is yes: do not invent a new style, use what exists.

## 2. Hard rules

**Do**
- Corner radius **2px** (`var(--r)`); only the home-page widget boxes use 4px and the thumbnail badge 3px.
- Gap between blocks **5px** (`var(--gap)`); spacing from the 4 / 8 / 12 / 16 scale, 38 between sections.
- Separate surfaces by **one tone step** (background → sidebar → surface → hover) or by a **1px line**.
- For color use only CSS variables: `var(--bg)`, `--text`, `--muted`, `--accent`… If you need a translucent tone use `color-mix(in srgb, var(--accent) N%, transparent)`. Never write a fixed color (it breaks the themes).
- Headings are serif (`var(--font-head)`), everything else is sans. Hierarchy comes from **size**.
- Every clickable block must be keyboard focusable (`tabindex`, role, a visible focus ring); a function must not be hidden on hover only.
- Every user-visible text goes through `t('id')` or `data-i*` (see "Languages" in CLAUDE.md); every new color variable goes into the theme files.
- Under `prefers-reduced-motion` motion is turned off; always have a fallback path that opens directly.

**Don't**
- A second accent color, gradients, bold/uppercase emphasis, an "eyebrow" label, emoji or unicode icons.
- A **shadow** on a card/tile/row/tab (shadows are only for layers that separate from the page: menus, windows, toasts).
- Highlighting a card on hover by **changing its fill color**; instead make something appear/zoom (the preview grows 3-7%) or change a line. (Exception: `.node` rows and buttons take the `--hover` fill, that is how the system works.)
- Pill/round forms, a corner radius larger than 4px.
- An infinite loop that runs while the screen is at rest (decorative loops run only on hover/focus).

## 3. Component recipes (all existing classes)

| Need | Use | Notes |
|---|---|---|
| Section heading | `.sec-head` = icon (`svg.sec-ic`, 22px, 1.3 miter stroke) + `h2` (28px serif) + `.sec-rule` | the solder ring at the end of the line is automatic; the first heading in a panel has `margin-top: 0` |
| Side navigation / tab list | `.node` (+ selected: `background: var(--hover); color: var(--text)`) | 16px icon, `padding: 7px 8px; gap: 8px`; do not invent a new "active bar" |
| Button | `.btn`, primary `.btn.primary`, danger `.btn.danger`, icon `.icon-btn` (26px) | a text button is 6px 12px |
| Form field | `.field` (12px muted label) + `input`/`select` + `.hint` (12.5px muted description) | fields inherit the page's font (`font: inherit`) |
| Checkbox | `input[type=checkbox]` + `span` inside `label.chk`/`.gen-chk` | `accent-color: var(--accent)` |
| Window | `<dialog>`; border `1px var(--line-strong)`, surface `var(--surface)`, shadow `var(--shadow)`, 2px corners | the `pop` opening (0.96, 250ms) is already on `dialog[open]`; do **not** turn it off or restart it |
| Selection blocks (e.g. theme) | flat block `var(--bg)` + preview; selected = preview frame in the accent color + a check mark | `role="radio"`/`radiogroup`, navigated with ←/→ |
| Notification | `toast(...)` (+ an "Undo" action) | a 2px accent progress line |
| Context menu | `menu(anchor, items, pos)` | 250ms from the pointer, scale 0.97 |

Icons: 24 viewBox line icons; in the interface 16px/1.6 round caps, in headings and ornaments 1.3 miter (`stroke-linejoin: miter; stroke-linecap: square`).

## 4. Motion

Durations only from the `:root` tokens: `--duration-quick` 150 (closing, text change), `--duration-fast` 250 (window/menu opening, icon swap, tab), `--duration-medium` 350, `--duration-slow` 400 (panel opening), `--duration-very-slow` 500 (an emphasis moment). Curve: `--ease-smooth-out` for opening/closing/sliding; distance `--distance-*`, scale `--scale-*` (window 0.96), blur `--blur-*`.

**Rules** (the same as the `transitions-polish` skill)
1. **Opening is slower than closing:** window open 250, close 150; panel 400 / 350.
2. **Hover-in ≤250ms, no delay on exit;** use a delay not to hold something back but only for ordering (stagger 40ms, total ≤300ms) or to filter out an accidental trigger.
3. **Motion explains something:** before inventing a new motion look at the existing vocabulary: a course tile's shape flies to the icon in the breadcrumb; the Settings icon turns one tooth (60°) on hover; a closing tab narrows. A new motion should be a continuation of one of these.
4. **A shared-element transition** (View Transitions) is the cleanest way: the icon on the triggering element flies to the **same icon** on the surface that opens. Recipe: `transition(update, nameOld, nameNew, after)` + `vtName(el, 'name')`; add a class to `:root` during the transition (`vt-set-open`) and tune the durations with it. Example: the Settings gear (sidebar icon → the icon in the window title, open 400ms / close 250ms, 180° turn; the root cross-fade is off on opening, 150ms on closing).
5. **The transition must not rewrite the surface's own opening.** The window already opens with `pop`; the transition should only carry the shared element.

**Rules that came from mistakes** (experienced with the Settings window transition)
- ❌ **A circle mask** (`clip-path: circle`) looks like a "ring" behind an icon; do not use a mask.
- ❌ **Blur / large scaling on a thin-line icon:** enlarging a 16px icon to 150px or adding `blur` turns the line into a bright halo. Fly the icon at its own size, do not add blur (blur only in wide-surface transitions, `--blur-small`).
- ❌ **Turning the surface's built-in animation back on by removing a class when the transition ends:** the `pop` of `dialog[open]` restarted and opened the window a second time. Never turn the built-in animation off; do not turn it off and on with a temporary class.
- ❌ **If two layers fade at the same time** (the root cross-fade + the window fading) the page content gets "washed out" behind the window. Turn one off.
- In fast motions such as spinning the scene darkens with the frame rate (the gear's teeth flicker); limit the rotation to multiples of the tooth spacing (60°) and do not accelerate much.
- Tab/navigation icons: the parts are separate elements (`.k`, `.d`, `.doc`, `.dot`), a one-shot keyframe; it plays on hover, `:focus-visible` and when the tab is selected (`.play`), with the individual `translate`/`scale` properties (`transform-box: fill-box`), no blur; the bounce curve (`--ease-bounce`) only for appearances.
- ❌ **If the target of a shared element is inside a scaling surface:** the transition captures the target position at the start (when the window is at 96% scale) and when the animation ends the real element jumps left/up. That is why the Settings window opens with only a `fade` instead of `pop`.
- Small dialogs (`ask()`): if given `icon` (24 viewBox inner markup) and `from` (the triggering element) they open like the Settings window (the 24px icon on the trigger flies to the title icon, the window only fades); otherwise the old `pop`. With an iconless trigger (a book, a tile) there is no flight, only a fade.
- Start the animation **without waiting for data** (e.g. open the window before the `fetch` finishes, fill the fields afterwards); a delay feels "slow".

## 5. Skeleton for tabbed/settings windows

```
<dialog id="x" aria-labelledby="x-title">
  <form method="dialog" class="set">
    <nav class="set-nav" role="tablist" aria-orientation="vertical">
      <p class="set-title" id="x-title"><svg/> <span data-i="…">Title</span></p>
      <button class="node set-tab" role="tab" aria-controls="pane-…">… <svg/> <span data-i>Name</span></button>
    </nav>
    <div class="set-main">
      <button class="icon-btn set-x" …>×</button>
      <section class="set-pane" role="tabpanel" aria-labelledby="tab-…">
        <div class="sec-head"><svg class="sec-ic"/><h2>Name</h2><span class="sec-rule"></span></div>
        …fields (.field / .hint / .btn)…
```
Behavior: roving tabindex, ↑/↓ (←/→ in a narrow window), Home/End; Esc, × and **a click outside the window** (the press must also start outside) close it with the animation; the selected tab is remembered for the session; operations that go online run only when the relevant tab is opened. In a narrow window (<700px) the tabs turn into a horizontal strip on top.

## 6. Checklist for new UI

- [ ] Built from existing classes (section 3); if a new style is needed it follows the rules in DESIGN.md (2px, 5px, flat block, no shadow).
- [ ] Colors from variables; looked at by eye in **both the dark and light theme** (`python tools/theme_check.py` contrast).
- [ ] Texts via `t()`/`data-i*`; added to `en.json` + `tr.json`; `python tools/i18n_check.py` is clean.
- [ ] Keyboard: focus order, Enter/Space, Esc, focus ring; roles and `aria-*`.
- [ ] Motion with tokens; opening > closing; a reduced-motion fallback; **no blur/mask/shadow**.
- [ ] Watched frame by frame in real Chrome (CDP): no double triggering, no class/name leaks, Esc/outside click/double click are safe.
- [ ] Every error that comes from the server is an `AppError("id")`; the UI shows it with `errText()`.
- [ ] The newly learned rule was added to this guide.
