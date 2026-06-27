# Walk Prague — Requirements Check

A running log of requirements / professor clarifications and how the application
satisfies them. For each item: the **question / requirement**, the **professor's
answer** (where applicable), the **status**, and **how it is implemented** (with
file references and how it was verified).

> New items are appended at the bottom as they come up. If an item is already
> implemented, it is explained here; if not, it is implemented first and then
> documented.

---

## 1. The same email may be used for both a guide and a participant account

**Question (to professor):** Can an email be used both as a guide and as a
participant, as long as it is unique among guides when registering as a guide,
and among participants when registering as a participant?

**Professor's answer:** Yes — using two separate tables (one for participants,
one for guides), the same person can register with the same email address either
as a participant or as a guide. When logged in as a participant they are a
participant; when logged in as a guide they are a guide.

**Status:** ✅ Implemented (this required a change — email was previously global).

**How it is done:**
- There are **two separate tables**, `participants` and `guides` (plus `admins`),
  each with `email TEXT NOT NULL UNIQUE` and an integer `id` primary key
  (`app/backend.py`, schema in `init_backend`).
- `register_user()` enforces uniqueness **only within the role being registered**
  (`SELECT 1 FROM <role_table> WHERE email = ?`), so the same email can exist once
  in `participants` and once in `guides` as two independent accounts. A duplicate
  **within the same role** is still rejected (`app/backend.py`, `register_user`).
- `authenticate_user(email, password, expected_role)` looks the email up in the
  **table for the role chosen at sign-in**, so the role selector disambiguates
  which account logs in. The session id is stored as `"role:id"`, so the two
  accounts never collide (`app/backend.py`).

**Verified:** Registered `dual.role@example.com` as a participant (OK), then the
same email as a guide (now allowed → separate account), then as a participant
again (blocked — duplicate within role). Signing in as participant → participant
dashboard; signing in as guide → guide dashboard. Two distinct rows result
(participant id 7, guide id 4).

---

## 2. Routes must be protected so a participant cannot open guide-only pages (and vice versa), even via a forced URL

**Question (to professor):** Do we need to prevent a user from reaching a guide's
page (and vice versa) if they force the URL in the address bar, beyond the normal
redirection to their own pages?

**Professor's answer:** Yes — protect the routes with Flask-Login decorators, as
seen in class.

**Status:** ✅ Already implemented.

**How it is done:**
- Every protected route uses the Flask-Login `@login_required` decorator **and**
  an explicit role guard (`if current_user.role != "<role>": abort(403)` or a
  redirect to the user's own dashboard) — `app/__init__.py`.
- Coverage:
  - `/admin-dashboard` → admin only (else `403`).
  - `/guide-dashboard`, `/guide/tours`, `/guide/tours/<slug>`, `/guide/reports`,
    `/guide/occurrences/<id>/done` → guide only.
  - `/participant-dashboard`, `/participant-home`, `/reservations`,
    `/reservations/<id>/cancel` → participant only.

**Verified (forcing URLs directly):**

| Who | Forced request | Result |
|---|---|---|
| Not logged in | `GET /guide-dashboard` | `302 → /signin?next=…` |
| Participant | `GET /guide-dashboard` | `302 → /participant-dashboard` |
| Participant | `GET /admin-dashboard` | `403` |
| Participant | `POST /guide/tours` | `403` |
| Guide | `POST /reservations` | `403` |
| Guide | `GET /admin-dashboard` | `403` |

---

## 3. Error handling when the user forces paths / submits incorrect data directly

**Question (to professor):** Do we need exceptions/notifications even when a user
manually forces paths or enters incorrect data in the address bar, or is it
enough to validate the visible buttons/interactions?

**Professor's answer:** Yes — but Flask-Login manages it through the
`@login_required` decorator.

**Status:** ✅ Already implemented (in three layers).

**How it is done:**
1. **Authentication layer** — `@login_required` redirects unauthenticated
   requests to `/signin?next=…` (Flask-Login).
2. **Authorization layer** — role guards return `403` (or redirect) when the
   logged-in role does not match the route (see item 2).
3. **Validation & ownership layer** — backend functions validate the request
   regardless of how it arrives and raise human-readable `ValueError`s returned
   as `400` JSON, or `404`/`403` where appropriate. Examples:
   - Booking a past/invalid date, an out-of-schedule date, an over-capacity
     party, or a same-day/overlapping conflict → `400` with a message.
   - Wrong number of tour photos, missing required fields → `400`.
   - Unknown tour slug → `404`.
   - **Ownership checks:** a guide editing another guide's tour → `400`
     ("You can only edit your own tours"); a participant cancelling a reservation
     that is not theirs → rejected.

**Verified:** Tomas POSTing an update to Petru's tour returned `400`
("You can only edit your own tours"); forced participant/guide cross-role
requests returned `403`/redirects as in item 2.

---

# Mandatory Requirements — Full Audit

Each official requirement, its status, and how it is satisfied. All items below
were verified against the running application.

## Req 1 — Guide registration (name, email, languages; 5 languages; unique email)
**Status:** ✅ Implemented.
- Guide registration collects **first name, last name, email, spoken languages**
  (`register_user`, role `guide`, in `app/backend.py`; form in
  `app/templates/register.html`).
- Languages are limited to the **five** options — `VALID_LANGUAGES = {Italian,
  English, Spanish, Portuguese, German}` — and at least one is required; invalid
  languages are rejected server-side.
- Email is **unique within the guides table** (`UNIQUE` constraint) and is the
  login identifier (see item 1 above for the cross-role detail).

## Req 2 — Participant registration (name, email; unique) + reserve without overlap
**Status:** ✅ Implemented.
- Participant registration collects **first name, last name, email**
  (`register_user`, role `participant`); email is unique within the
  participants table and is the login identifier.
- A participant may reserve **one or more tours as long as their schedules do not
  overlap**: `create_reservation` rejects a new booking whose time window
  `[start, start+duration)` **overlaps** any of the participant's existing active
  upcoming bookings (`app/backend.py`).

## Req 3 — A participant cannot become a guide; a guide cannot reserve
**Status:** ✅ Implemented (see item 3 above).
- Accounts live in separate tables and login is role-scoped; there is no
  "upgrade" path from participant to guide.
- `POST /reservations` returns **403** for any non-participant, and guides never
  see a booking panel on tour pages.

## Req 4 — Mandatory tour information (incl. ≤1 start time/day, language ∈ guide's)
**Status:** ✅ Implemented.
- A tour stores: **title, guide (single owner), weekly schedule (weekday +
  start time), meeting point, duration (minutes), language, max participants,
  stops (≥4), description, exactly 5 photos** — schema + `create_guide_tour`
  (`app/backend.py`).
- **At most one start time per day** is enforced: `create_guide_tour` raises
  "Only one start time is allowed per day" if a weekday repeats.
- **Tour language must be one of the guide's languages**: raises "You can only
  offer tours in languages you speak" otherwise.
- **Verified:** the detail page exposes title, guide, meeting point, duration,
  max participants, 7 stops (≥4), 5 photos, and the weekly schedule.

## Req 5 — Tours editable until first reservation; then essential info locked
**Status:** ✅ Implemented.
- `tour_has_reservations(tour_id)` decides the lock. In `update_guide_tour`, the
  **essential fields — weekly schedule, meeting point, duration, language, max
  participants — are only written inside an `if not locked:` block**, so once any
  date is reserved they can no longer change. Non-essential fields
  (title/description/stops/themes/photos) remain editable.
- The guide UI also reflects the lock: a booked tour shows a padlock and the
  Edit button is disabled (a conservative, stricter-than-required choice).

## Req 6 — All tours public; brief homepage; filters (date/duration/language); full view
**Status:** ✅ Implemented.
- The homepage route `/` is **public** (no `@login_required`) and shows a
  **brief card** per tour (`app/templates/index.html`).
- **Filters for Date, Duration, and Language** are present (date picker,
  Duration section, and the five language checkboxes) and applied client-side in
  `app/static/js/main.js`.
- Clicking a card opens the **full tour view** (`/tours/<slug>`) with all
  mandatory information.

## Req 7 — Participant reserves a specific date from the weekly schedule
**Status:** ✅ Implemented.
- Bookable dates are derived from the tour's weekly schedule (lazy-occurrence
  model). The detail calendar lets the participant pick a specific **date** for a
  schedule slot; the booking is sent as `(schedule_id, date)` and validated
  against the schedule's weekday (`create_reservation`, `/reservations`).

## Req 8 — 1–4 people per reservation; cannot exceed remaining places
**Status:** ✅ Implemented.
- A reservation is for the participant by default, plus **up to 3 named guests**
  (first + last name) → 1–4 people; `create_reservation` rejects parties outside
  1–4.
- Capacity is enforced per **date**: remaining places = `max_participants −
  people already booked on that occurrence`; an over-capacity party is rejected
  with a message stating how many places (and guests) are allowed.

## Req 9 — Cancellation only ≥ 24 h before start
**Status:** ✅ Implemented.
- `cancel_reservation` raises "Cancellation deadline has passed" when
  `now > start − 24h`; the participant UI only shows a Cancel control while it is
  still allowed.

## Req 10 — Participant profile shows reserved tours with full details
**Status:** ✅ Implemented.
- `participant_dashboard_data` returns, per reservation: **date, start time,
  meeting point, number of people, and the names of any additional
  participants** (verified: keys `date, start_time, meeting_point, people,
  additional_participants`). Cancelled reservations are removed from this page.

## Req 11 — Guide profile lists their tours, reservations, and expected totals per date
**Status:** ✅ Implemented.
- `guide_dashboard_data` lists every tour the guide created; for each scheduled
  (booked) date it provides the **list of reservations** and the **total expected
  participants** (`expected` vs `max_participants`) — verified keys `date,
  expected, max_participants, reservations`.

## Req 12 — Post-tour reporting (attendance + one evidence photo)
**Status:** ✅ Implemented.
- For each date that **has already taken place and had ≥1 reservation**, the
  guide clicks **"Mark as done"** (`mark_occurrence_done`, gated to started,
  not-finished, owned tours) which opens a **pending report**.
- The guide then **declares actual attendance and uploads one evidence photo**
  (`create_guide_report`; photo required when attendance ≥ 1). Reports appear in
  Tours History and Past Reports — verified keys `actual, evidence_photo,
  expected`.

## Req 13 — Platform administrator (Prova finale)
**Status:** ✅ Implemented (single admin account).
- The admin neither creates tours nor reserves. The dedicated admin page
  (`/admin-dashboard`, admin-only) shows, via `admin_dashboard_data`:
  - the **list of all guides** with **first name, last name, email, spoken
    languages** (verified guide fields `name, email, languages`);
  - each guide's **tours with full detail** (admin opens any tour at
    `/tours/<slug>?mode=admin`);
  - **statistics**: total guides, participants, tours, reservations, and
    **reservations per language** (verified: 3 guides, 6 participants, 10 tours,
    22 reservations, per-language breakdown present).
