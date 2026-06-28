# Walk Prague — Credentials & Test Accounts

Every sample account preloaded into the application, so it can be logged into and
tested. Sign in at **`/signin`** (guides & participants) or **`/admin-access`**
(administrator). The **email address** is the unique identifier of each account.

The database ships pre-seeded; deleting `instance/walk_prague.sqlite3` re-creates
and re-seeds it automatically on the next run.

---

## Administrator
| Name | Email | Password |
|------|-------|----------|
| Platform Administrator | `admin@walkprague.cz` | `password123` |

The administrator only views platform information (guides, tours, reservations,
statistics) — it does not create tours or make reservations.

---

## Guides
A guide can create/manage tours but **cannot make reservations**.

| # | Name | Email | Password | Languages |
|---|------|-------|----------|-----------|
| 1 | Tomas Novak | `tomas.novak@gmail.com` | `tomas1234` | English, Spanish, Portuguese |
| 2 | Klara Vesela | `veselaklara344@yahoo.com` | `chicken1234` | English, Italian, German, Spanish |
| 3 | Petru Svobodova | `petrusvb@icloud.com` | `petruelectronics1234` | English, Portuguese, German, Spanish |

**Tours per guide:**
- **Tomas:** Complete Prague Tour · Original Free Tour of Prague · Royal Road to Prague
- **Klara:** Free Tour New Town (WWII & Communism) · Free Tour Around the Prague Castle · Walking Tour: Old Town & Jewish Quarter · Prague Free Tour: Old Town & Jewish Quarter (Astronomical Clock)
- **Petru:** Welcome to Prague Freetour · Classic Prague Castle Free Tour · Panoramic Vltava River Cruise

---

## Participants
A participant can make reservations (1–4 people each) but **cannot create tours**.

| # | Name | Email | Password |
|---|------|-------|----------|
| 1 | Anna Walker | `annawalker@gmail.com` | `annaaa1111` |
| 2 | Martin Cerny | `martincerny@gmail.com` | `ghostmarty007` |
| 3 | Teresa Dvorazoka | `dvorazoka.teresa@gmail.com` | `teresaflyinginsky` |
| 4 | Adela Vesela | `adela.vesela@gmail.com` | `ADELAsinging1234` |
| 5 | Lukas Horak | `lukas.horak@gmail.com` | `lukaspast2026` |
| 6 | Marie Kralova | `marie.kralova@gmail.com` | `mariepast2026` |

Participants **1–4** have upcoming bookings. Participants **5–6** have **past,
already-reported** tours (used to populate the guides' Tours History / Past
Reports).

---

# Which account to use to test some features

### Editing a tour (no reservations → fully editable)
Only two tours have no bookings, so they can be edited freely (schedule, photos,
everything):
- **Tomas Novak → "Royal Road to Prague"**
- **Klara Vesela → "Walking Tour: Old Town & Jewish Quarter"**

Every other tour has at least one reservation and is therefore **locked** (the
Edit button is disabled) — good for testing the post-reservation lock.

### Post-tour reporting — the "Mark as done" button
Two departures took place earlier **this week** and are not yet reported, so the
owning guide sees a live **"Mark as done"** button:
- **Petru Svobodova → "Classic Prague Castle Free Tour"** (booked by Lukas Horak)
- **Tomas Novak → "Complete Prague Tour"** (booked by Marie Kralova)

Sign in as the guide → the row shows **"Mark as done"**. Marking it done moves the
tour to **Tours History** and opens a **pending report** to file (attendance +
evidence photo).

### Tours History & Past Reports (already populated)
Each guide (**Tomas, Klara, Petru**) already has **2 past, reported tours** in
their **Tours History** and **Past Reports** sections, thanks to the bookings of
participants **Lukas Horak** and **Marie Kralova**.

### Fully-booked date ("No availability")
Open **"Original Free Tour of Prague"** (Tomas Novak) and go to the calendar for
**Sunday, 5 July 2026 at 10:00** — it is **10 / 10 booked**, so it shows **"No
availability"**, and any participant attempting to reserve it is rejected as
*fully booked*. (Filled by Anna +3, Teresa +3 and Adela +1 = 10 people.)

### Cancellation (24-hour rule)
Sign in as a participant with an **upcoming** booking (e.g. **Anna Walker**): a
booking more than 24 h away can be cancelled; within 24 h of the start time the
Cancel button is closed.

---

## Report evidence photos
The six seeded reports reference photos stored under
**`app/static/img/reports/`**. Placeholder images are already in place so nothing
is broken; to use real "participants on the tour" photos, **replace each file**
(keeping the same filename):

| File in `app/static/img/reports/` | Report it belongs to |
|-----------------------------------|----------------------|
| `report-lukas-complete-prague-tour.jpg` | Lukas → Complete Prague Tour (Tomas) |
| `report-lukas-prague-castle.jpg` | Lukas → Free Tour Around the Prague Castle (Klara) |
| `report-lukas-vltava-cruise.jpg` | Lukas → Panoramic Vltava River Cruise (Petru) |
| `report-marie-welcome-prague.jpg` | Marie → Welcome to Prague Freetour (Petru) |
| `report-marie-newtown-communism.jpg` | Marie → Free Tour New Town, WWII & Communism (Klara) |
| `report-marie-original-free-tour.jpg` | Marie → Original Free Tour of Prague (Tomas) |

Reports filed live through the UI upload their photo to the same folder
automatically.

---

## Totals (seeded data)
- **1** administrator
- **3** guides
- **6** participants (4 with upcoming bookings + 2 with past/reported bookings)
- **10** tours (English, Spanish, German, Italian, Portuguese)
- **25** reservations
- **6** post-tour reports filed (2 per guide)
