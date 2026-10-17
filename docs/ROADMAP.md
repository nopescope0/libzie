# libzie roadmap

Last updated: 2026-10-17. The prioritization is not final; it changes with user feedback.
Size estimate: **S** (a few hours), **M** (a day or two), **L** (more than a week).

## Principles (the roadmap adds nothing that breaks these)

1. **Reaching the file beats everything:** no feature is added that does not shorten the path course → the right page.
2. **One archive, no double bookkeeping:** no feature that forces the user to keep data outside the folders. The folder structure is the real source.
3. **Local and private:** works offline; everything that goes online is optional and clearly visible. No accounts, no cloud, no tracking.
4. **Suited to long sessions:** a calm interface; motion explains state, it does not decorate.
5. **Easy to keep running:** when running from source there are no dependencies or build steps (packaging is only for the Windows app).

## 1. Release preparation (now)

- [ ] Verify the setup wizard build in GitHub Actions; try `libzie-setup.exe` and the portable version on a clean account **(S)**
- [ ] `v0.2.0` release: release notes, installation instructions **(S)**
- [ ] Turn on email privacy and command-line push protection on the GitHub account **(S)**
- [ ] Hand it to a few people for first feedback **(S)**
- [ ] A short screen recording (GIF) in the README: adding a course, tabbed PDFs, picking an icon **(S)**
- [ ] Actions version warnings (Node 20 → current action versions) **(S)**
- [ ] The `SmartScreen` warning note is already in the README; research code-signing options (free/cheap ways) in a later release **(M)**
- [ ] Remove the legacy release file names (`libzie-kurulum.exe`, `libzie-tasinabilir.exe`) from the workflow once nobody updates from 0.1.6 or older any more **(S)**

## 2. Near term (v0.2 – v0.4): making daily use easier

Source: the first critique round (`.impeccable/critique/`) and my own usage notes.

- [ ] **Layout for courses with many files:** grouping by type (slides, notes, exams), sorting and a filter for courses with 30–40 files; "see everything at a glance" in exam week **(M)**
- [ ] **A view of the trash:** `.trash` can currently only be reached through the "Undo" toast and Explorer; listing, restoring and permanent deletion inside the app **(M)**
- [ ] **Keyboard between tabs:** `Ctrl+Tab`, `Ctrl+W`, `Ctrl+1..9` **(S)**
- [ ] **Keyboard focus:** when a course opens, focus should move into the content, not return to the top of the page **(S)**
- [ ] **First-run welcome:** a 3-step guide in an empty archive (add a course, drag files, pick an icon/color) and a sample course **(S)**
- [ ] **Customize a course:** merge the color and icon choice into one window **(S)**
- [x] **Update (optional):** version information and one-click/automatic update in Settings → About
- [ ] **Start with Windows (optional):** start in the background without opening a window, together with the tray icon; an option in Settings → General **(S)**
- [ ] **Backup export:** export a course as a `.zip` **(S)**
- [ ] **Settings window:** a folder picker (instead of typing the path by hand) **(S)**

## 3. Medium term (v0.5 – v1.0): widening the user base

- [x] **English interface:** id-keyed language files (`static/lang/tr.json`, `en.json`), the language is chosen in Settings; adding a language means adding a file
- [x] **Light theme:** theme files (`static/themes/navy.json`, `light.json`), dark/light/system choice in Settings → Theme; `tools/theme_check.py` verifies the contrast
- [ ] **Custom themes:** the user drops their own theme file into the `%APPDATA%\libzie\themes\` folder and picks it in the Theme tab. The server already validates (only allowed color variables and color values); to do: a second theme folder, a warning for file-name clashes/invalid themes, a multilingual `name` field in the theme file for the display name, an "open themes in Explorer" button, a sample theme template and a theme-writing guide in the README **(M)**
- [ ] **More built-in themes:** high contrast, warm (sepia) and color-blind-friendly accent options **(S)**
- [ ] **macOS and Linux:** the server is already platform independent (`open`/`reveal`); pywebview packages and a three-platform build in GitHub Actions **(L)**
- [ ] **Searching inside PDFs:** search the content instead of the file name (the index is local, in a hidden folder like `.trash`); must not slow down on big archives **(L)**
- [ ] **Remember the page you stopped at in a PDF:** the browser's embedded viewer does not expose page information; we would need our own pdf.js viewer, which would also fix the problem that keyboard shortcuts (Esc, F, Ctrl+K) do not work while the PDF has focus **(L)**
- [ ] **Tags / term layout:** grouping such as "2026 Fall"; only a view layer, without breaking the folder structure **(M)**
- [ ] **Exam mode:** gather all midterm/final/homework files of a course on one page **(M)**

## 4. Technical debt and quality

- [ ] **Automated tests:** for the `server.py` API (upload, move, delete, restore, icon, security: escaping the root) with the standard library `unittest`; run on every push in CI **(M)**
- [ ] **Line ending and encoding consistency:** `.gitattributes` exists; a CRLF/LF check in CI **(S)**
- [ ] **The size of `index.html` (~3500 lines):** consider splitting it with ES modules without adding a build step (`static/js/*.js`); measure first: does splitting really make maintenance easier **(L)**
- [ ] **Error log:** a "copy the log" button when something goes wrong in the app (makes opening a GitHub issue easier) **(S)**
- [ ] **Python version compatibility:** a CI matrix for 3.10–3.14 **(S)**
- [ ] **Accessibility review:** a real trial with a screen reader, high contrast, `prefers-reduced-motion` tests **(M)**
- [ ] **Performance:** `/api/tree` and thumbnails with an archive of 5000+ files; incremental loading and a smarter thumbnail cache **(M)**

## 5. Ideas (undecided)

- A short note / bookmark per file (because of the principle of not keeping data outside the folders it would need a `.libzie` sidecar file next to it; to be discussed)
- A weekly schedule / exam-date countdown per course
- A browser extension or a "save here" shortcut (put a downloaded PDF into the right course)
- Ready-made settings templates for Notability / GoodNotes backup folders
- Another optional small tool instead of the weather (a Pomodoro timer)
- A mobile/tablet layout (not a goal now; principle: one desktop computer)

## Done (summary)

- **0.0.1:** first Windows version (local server, course tiles, tabbed PDFs, thumbnails, search, Undo, keyboard access)
- **0.1.0:** desktop app (pywebview + PyInstaller), Documents/APPDATA data location, single instance, GitHub Actions build, MIT license
- **0.1.1:** general course icons and the icon picker
- **0.1.2 – 0.1.6:** setup wizard and portable version, in-app update, security hardening, English interface, tabbed Settings, dark/light theme, system tray, weather box
- **Next:** the project's code, file names and documents were translated into English (the README stays Turkish); data names on disk were renamed (`materials`, `settings.json`, …) with automatic migration
