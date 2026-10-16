# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

University students (Turkish-speaking), each running their own copy on their own Windows computer, opened in a desktop browser or as a desktop app. Every installation is a personal tool for one person: no shared data between users, no sharing features, no accounts.

The jobs, in priority order:

- **Studying:** long sessions moving between lecture slides, handwritten notes and solved/past problems for one course.
- **Exam period:** seeing everything for a course at once and working back through it.
- **Archiving:** keeping Notability notes and downloaded course material tidy, by course.

Live in-lecture lookup was not named as a primary job.

## Product Purpose

libzie (formerly "Ders Arşivi") keeps a student's course materials — PDFs, slides, scanned/handwritten notes — organized by course and quick to reach, and lets them read PDFs side by side in tabs without leaving the page. Success means: during a study session or exam week the user finds and opens the right document in seconds and never has to maintain two separate archives (for example a note-taking app's backup folder and this one) by hand.

## Positioning

The filesystem is the database. A course is just a folder (locally, or a cloud-synced folder such as Google Drive that a note-taking app like Notability backs PDFs up into), so files added in Explorer or synced from the tablet simply appear; there is no import step, no account, no cloud service of its own. It runs entirely on the user's machine and works offline.

## Operating Context

- Launched locally (Python server on `127.0.0.1:8765`, opened in a desktop browser) or, for end users, as the packaged Windows desktop app (installer or portable exe).
- Optional: students who take notes on a tablet (e.g. Notability with auto-backup to Google Drive) can point libzie's content folder at the synced Drive folder (Ayarlar). Nothing depends on this setup.
- Typical session: open a course, scan thumbnails, open several PDFs as tabs, read with the sidebar collapsed; occasionally upload, rename, move or delete files.

## Capabilities and Constraints

- Courses and nested folders; per-course color and shape; drag-and-drop upload (including whole folders) and moving; rename; soft delete into `.silinenler`.
- In-page PDF/image viewer with persistent tabs; other types (pptx, docx…) open in the default Windows program.
- PDF first-page thumbnails (pdf.js, cached in the browser); Turkish-aware search; "recently opened".
- Small home widgets: clock and weather (Open-Meteo, city typed by the user).
- Technical: Python standard library server + one vanilla HTML/CSS/JS file; no dependencies, no build step; vendored assets (pdf.js, Linux Libertine/Biolinum fonts) so it works offline. The only outbound network call is the optional weather widget; browser geolocation is intentionally not used.
- UI language is Turkish.
- Not needed: multi-user features, sharing, sync of its own, mobile/tablet layouts (one desktop computer per installation).

## Brand Commitments

- Name: **libzie**, lowercase.
- Logo: three leaning books on a shelf spelling "lib", the "i" book's dot in the accent color.
- Voice: short, plain Turkish; friendly but not chatty (e.g. "İyi akşamlar", "Şehir seç", "Silindi").

## Evidence on Hand

- Each user's course archive lives in their own content folder; it is private personal material and must never be published, committed to the repository or used as marketing content. Use invented sample text in screenshots and examples.
- No testimonials, users, metrics or press exist; do not fabricate any.

## Product Principles

1. **Reaching the document beats everything.** Every screen should shorten the path from "which course" to "the page I need open".
2. **One archive, no double bookkeeping.** Never add a feature that makes the user maintain data outside the folders themselves.
3. **Local and private by default.** Works offline, keeps files on the machine; anything that talks to the internet is optional and explicit.
4. **Built for long sessions.** Calm, low-strain reading and navigation over attention-grabbing effects; motion explains state rather than decorating.
5. **Simple to keep running.** No dependencies or build steps the user would have to maintain.
