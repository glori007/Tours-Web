# Walk Prague — Work Log (First Working Session)

This document summarises everything implemented in this session: the bugs fixed,
the features added, the database model, the validation rules enforced, the UI/UX
redesigns, the seeded sample data, and the manual steps that remain (photos).

The app is a Flask + SQLite + Flask-Login web app for managing free walking tours
in Prague, with three account types (guides, participants, administrator).

---

## 1. Initial requirements audit

The codebase was reviewed against `CLAUDE.md`. The app looked complete but several
mandatory requirements were only mocked up. The gaps found and then fixed:

- Homepage **filtering didn't work** (decorative checkboxes).
- The **tour detail page was static** (hardcoded stops/schedule/overview for every tour).
- **Reservations were assigned to the wrong user** and reservation/cancel/report
  routes had no authentication.
- **Tour editing / the post-reservation lock** existed only in the UI, not the backend.
- Spec violations: an invalid 6th language ("French") in seed data, no 5-photo
  enforcement, multiple start times per day allowed, **Flask-Login missing from
  `requirements.txt`**, inline CSS/JS in templates, no sample credentials in the README.

---

## 2. Database model

### 2.1 Three separate account tables
The original single `users` table (with a `role` column) and `guide_profiles` table
were **split into three independent tables**:

- **`guides`** — `id` (PK), `email` (unique), `password_hash`, `first_name`,
  `last_name`, `profile_photo`, `bio`, `active_since`, `rating_average`,
  `total_reviews`, `guests_guided`.
- **`participants`** — `id`, `email` (unique), `password_hash`, `first_name`, `last_name`.
- **`admins`** — `id`, `email` (unique), `password_hash`, `first_name`, `last_name`.

The guide profile fields were merged into `guides` (no more `guide_profiles`).

### 2.2 Relationships (one-to-many, all `ON DELETE CASCADE`)
`guides` is the parent of:
- `guide_languages (guide_id → guides.id, language)`
- `guide_specialties (guide_id → guides.id, specialty)`  ← specialty is its own entity
- `tours (guide_id → guides.id, …)`
- `guide_reports (guide_id → guides.id, …)`

Tour-related tables:
- `tours` — includes `rating` and `review_count` columns (per-tour rating, distinct
  from the guide's own rating), plus accessibility flags
  (`wheelchair_accessible`, `suitable_for_children`, `pet_friendly`).
- `tour_photos (tour_id, image_path, is_cover)`
- `tour_stops (tour_id, stop_order, title)` — **no description column** (removed by request).
- `tour_themes (tour_id, theme)`
- `tour_schedules (tour_id, weekday, start_time, language, duration_minutes, max_participants, active)`
  — the recurring weekly rule (a tour may run several times on the same weekday).
- `tour_occurrences (schedule_id, starts_at, ends_at, max_participants, status, finished)`
  — concrete dated instances generated from the schedule. Has a **`finished`** flag.
- `reservations (participant_id → participants.id, occurrence_id, status, cancelled_at)`
- `reservation_guests (reservation_id, first_name, last_name)`
- `reviews`, `guide_reports` (the latter has a **`finished`** flag).

`tour_occurrences` and `tour_schedules` are intentionally separate: a *schedule* is
the recurring weekly rule; an *occurrence* is a specific dated run that reservations,
reports and the "finished" state attach to.

### 2.3 Authentication
- Flask-Login id encodes the role (e.g. `"guide:3"`) so the user loader knows which
  table to read.
- `authenticate_user(email, password, role)` checks the matching table; a participant
  cannot log in as a guide and vice-versa.
- Emails are unique across all account types.

---

## 3. Features implemented / fixed

### 3.1 Homepage filtering (date, duration, language + more)
- Each tour card carries real `data-*` attributes (languages, duration, dates,
  start-times, places-left, themes, accessibility).
- Live JS filtering by **date / date range, duration, language**, plus theme,
  accessibility, start-time window, and availability.
- A tour appears only if it has an actual scheduled occurrence on the selected
  date / within the selected period.
- **Bug fixed:** two conflicting date pickers (one inline in the page, one in
  `main.js`) meant the chosen date never reached the filter. Consolidated to a
  single picker that publishes the range.

### 3.2 Pagination
- Homepage shows **6 tours initially**; "Load more tours" reveals **4 more** per
  click and hides when none remain. Resets to 6 when filters change.

### 3.3 Reservations
- `create_reservation` uses the **logged-in participant** (`current_user`).
- Routes `/reservations`, `/reservations/<id>/cancel`, `/guide/reports`,
  `/guide/tours`, `/guide/tours/<slug>`, `/guide/occurrences/<id>/done` are all
  `@login_required` with role + ownership checks.
- A reservation is **1–4 people** (participant + up to 3 named guests); the system
  prevents exceeding the occurrence capacity.
- Cancellation only allowed ≥ 24h before start.

### 3.4 Tour creation & editing (guide form)
- Create requires: title, ≥4 stops, ≥1 theme, **exactly 5 photos**, **one start time
  per day**, and the tour language must be one the guide speaks.
- **Edit lock:** once any reservation exists for a tour, the Edit button is disabled
  (grey) and shows "Booking exists - Cannot be edited" with a grey padlock icon.
  The backend also enforces that essential fields can't change after a booking.
- New-tour photos are uploaded by the form and stored in `app/static/uploads/tours/`
  with unique names; the seeded tours use `app/static/img/tours/tourN_M.jpg`.

### 3.5 Availability calendar (tour detail page)
- Replaced the fixed list with a **weekly calendar paged by arrows** (one click =
  one week; can browse well into the future).
- Days with scheduled departures are marked (orange underline); full days are greyed;
  the selected day is highlighted.
- Selecting a day groups departures **by language** and shows **time slots** with the
  **free/total places in green** (or "No availability" when full).

### 3.6 Guide dashboard
- Real statistics (all derived from the data, no fabricated values):
  - **Active Tours**, **Total Bookings** (= total scheduled departures),
    **Participants** (= total actual attendees from reports), **Tours Reported**,
    **Avg. Rating**, **Upcoming Schedules** (= future, not-yet-done departures that
    have ≥1 booking), **Pending Reports**, **Avg. Group Size**
    (= attendees ÷ reported tours).
- **Mark as done → Tours History → Reports flow:**
  - Each booked, started, not-yet-done departure shows a **"Mark as done"** button
    (blue, green on hover).
  - Marking done sets `tour_occurrences.finished = 1`, moves the departure into a
    **Tours History** section (same card layout as the timetable, with "View
    Participants" showing who was present, no Mark-as-done button), and opens a
    **Pending Report**.
  - Filing a report: if **≥1 attendee a photo is mandatory**; **0 attendees** needs no
    photo and is cleared (no-show, not kept in history). Submitted reports
    (`finished = 1`, ≥1 attendee) appear under **Past Reports**.

### 3.7 Tour detail page (display)
- Duration, languages, meeting point, overview (description), stops, and tour
  conditions all come from the tour's own data.
- Removed the "This activity includes" and "Weekly Schedule" sections.
- Guide info box: shows the guide's real rating/reviews, specialties as the "main
  specialty", and **guests guided = real total attendees from that guide's reports**.
  Removed the static "Local guide since … specialty" line.
- **"More Tours by [guide]"** lists that guide's real other tours (with flags,
  "Duration: …", and links).
- Reviews section is intentionally kept static for now.
- Rating shows as **n/10** with the review count shown separately.

---

## 4. Validation rules enforced

- Languages limited to **Italian, English, Spanish, Portuguese, German**.
- Specialties limited to a fixed set (History, Architecture, Castle District,
  Communism & Cold War, Gastronomy, Jewish Heritage, Local Legends,
  Alternative & Street Art, Art & Culture); **up to 4** per guide.
- A tour's languages must be among the guide's spoken languages.
- Tours need **≥ 4 stops**, **≥ 1 theme**, **exactly 5 photos**.
- Reservations: 1–4 people, no double-booking, capacity respected, 24h cancel rule.

---

## 5. UI / design changes

- **No emojis:** replaced all decorative emojis with custom inline line-style SVG
  icons (clock, hourglass/duration, map-pin, people, camera, clipboard, star, flag,
  route, ticket, check, wheelchair, child, paw) via an `icon()` Jinja macro.
  Dropdown carets `⌄` replaced with a chevron icon.
- **Circular flag images** (`app/static/img/flags/{en,de,es,it,pt,fr,xx}.svg`) instead
  of emoji flags, via a `flag()` macro. Used on tour cards, tour detail, the calendar,
  and "More tours". Card/"More tours" flags are 30×30; flag sits beside the language word.
- **Guide hero card** redesigned: name + email link + language pills (Czech-flag red,
  white text) + a prominent specialties row; removed the rating/active-tours tags and
  the static bio line.
- **"How It Works"** section restyled to use the page font (Inter) with circular
  gradient numbered badges.
- **Tour cards:** "Duration: …" label; description clamped to 3 lines with an ellipsis.
- **Filter buttons:** "Apply filters" matches "Clear all" colour.
- **Registration:** styled profile-photo picker with live preview and default-avatar
  fallback; specialty multi-select with chips.
- Removed inline CSS/JS from templates (spec compliance); removed dead code
  (old static `TOURS` dict, unused helpers).
- Footer "Explore" column reduced to just "All Tours".

### Photo handling (graceful fallback)
- `get_profile_photo_url` and `resolve_tour_image` check whether the file exists and
  fall back to a default avatar / placeholder until the real image is added, and they
  accept any of `.jpg/.jpeg/.png/.webp`.
- **Guide photos:** `app/static/img/guides/{tomas-novak,klara-vesela,petru-svobodova}.jpg`.
- **Seeded tour photos:** `app/static/img/tours/tourN_M.jpg` (N = tour 1–10, M = 1–5;
  M=1 is the cover).
- **Form-created tour photos:** auto-saved to `app/static/uploads/tours/`.

---

## 6. Seeded sample data

The database (`instance/walk_prague.sqlite3`) is created and seeded automatically on
first run. Delete the file to reset.

### 6.1 Administrator
- Platform Administrator — `admin@walkprague.cz` / `password123`

### 6.2 Guides (3)
| Name | Email | Password | Rating | Languages | Specialties |
|---|---|---|---|---|---|
| Tomas Novak | tomas.novak@gmail.com | tomas1234 | 9.0 / 125 | English, Spanish, Portuguese | Architecture, Castle District, History |
| Klara Vesela | veselaklara344@yahoo.com | chicken1234 | 8.7 / 225 | English, Italian, German, Spanish | Local Legends, Communism & Cold War, Gastronomy |
| Petru Svobodova | petrusvb@icloud.com | petruelectronics1234 | 8.9 / 335 | English, Portuguese, German, Spanish | Architecture, Gastronomy, Local Legends |

### 6.3 Tours (10) — connected to their guide
Each has its own rating/review count, weekly schedule (with multiple times/day where
specified), 4–7 stops, themes, accessibility, description, and 5 photo slots.

| # | Tour | Guide | Duration | Rating/Reviews |
|---|---|---|---|---|
| 1 | Complete Prague Tour | Tomas | 120m | 8.5 / 125 |
| 2 | Original Free Tour of Prague | Tomas | 180m | 8.7 / 225 |
| 3 | Royal Road to Prague | Tomas | 90m | 7.7 / 400 |
| 4 | Free Tour New Town, WWII & Communism | Klara | 60m | 8.7 / 505 |
| 5 | Free Tour Around the Prague Castle | Klara | 150m | 8.3 / 123 |
| 6 | Walking Tour: Old Town & Jewish Quarter | Klara | 90m | 8.1 / 185 |
| 7 | Prague Free Tour: Old Town & Jewish Quarter | Klara | 120m | 8.9 / 120 |
| 8 | Welcome to Prague Freetour | Petru | 60m | 8.8 / 184 |
| 9 | Classic Prague Castle Free Tour | Petru | 120m | 8.7 / 198 |
| 10 | Panoramic Vltava River Cruise | Petru | 90m | 8.4 / 233 |

### 6.4 Participants (4) and their upcoming bookings
Booking dates use the week starting **Tuesday 30 June 2026** (Tue = 06-30,
Wed = 07-01, Thu = 07-02, Fri = 07-03, Mon = 07-06). Each booking is matched to the
real tour occurrence by tour + date + start time + language. **14 reservations total.**

| Name | Email | Password | # bookings |
|---|---|---|---|
| Anna Walker | annawalker@gmail.com | annaaa1111 | 5 |
| Martin Cerny | martincerny@gmail.com | ghostmarty007 | 4 |
| Teresa Dvorazoka | dvorazoka.teresa@gmail.com | teresaflyinginsky | 3 |
| Adela Vesela | adela.vesela@gmail.com | ADELAsinging1234 | 2 |

**Guests added** to selected reservations (party sizes 2–4, within the 4-person max):
- Anna → Complete Prague Tour (Mon 7/6): +3 (Liam Walker, Sophie Walker, Noah Brooks);
  New Town (Tue 6/30): +1 (Emma Walker).
- Martin → Original Free Tour (Tue 6/30): +2 (Petra Cerny, Jakub Cerny);
  Welcome to Prague (Fri 7/3): +3 (Lucie Novak, Tomas Marek, Eva Cerny).
- Teresa → Vltava Cruise (Tue 6/30): +2 (Marco Rossi, Giulia Bianchi);
  Around the Castle (Mon 7/6): +1 (Elena Dvorazoka).
- Adela → Complete Prague Tour (Fri 7/3): +3 (Karel Vesely, Marie Vesela, Jan Horak).

All bookings are **upcoming** (future dates); no past tours/reports were seeded yet
(to be added later).

---

## 7. Infrastructure / misc

- Added `Flask-Login` to `requirements.txt`.
- `run.py` honours a `PORT` env var (for the preview/dev server).
- `.claude/launch.json` added for the local preview server.
- `README.md` updated with the current sample accounts (guides, participants, admin).

---

## 8. Manual steps / notes

- **Guide photos** and **tour photos** are real files on disk (not stored in the DB).
  Drop guide photos in `app/static/img/guides/` and tour photos in
  `app/static/img/tours/` as `tourN_M.jpg`. Until present, placeholders show.
- Deleting `instance/walk_prague.sqlite3` re-seeds the guides, tours, participants,
  bookings and guests described above.
- The edit-lock UI fully disables editing a booked tour, which is slightly stricter
  than the spec's "essential fields only" lock (kept per request).
