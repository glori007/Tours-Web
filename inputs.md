# Walk Prague — Sample Data & Test Credentials

This file lists every sample account preloaded into the application so the
instructor can log in and test it. The database is seeded automatically the
first time the app runs (see `seed_database()` in `app/backend.py`).

## How to run the application

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app run.py run --debug   # or: python run.py
```

Then open **`http://127.0.0.1:5000`**. The SQLite database
(`instance/walk_prague.sqlite3`) ships pre-seeded and is included in the
submission; if it is deleted it is re-created and seeded automatically on the
next run.

Login is at **`/signin`** (guides & participants) and **`/admin-access`** (administrator).
The email address is the unique identifier for every account.

---

## 1. Platform Administrator

| Role  | Name                   | Email                  | Password      |
|-------|------------------------|------------------------|---------------|
| Admin | Platform Administrator | `admin@walkprague.cz`  | `password123` |

The administrator does not create tours or reservations. The admin dashboard
shows all guides, all tours, all reservations, and platform statistics.

---

## 2. Guides

Three guides. A guide can create/manage tours but **cannot make reservations**.

### Guide 1 — Tomas Novak
- **Email / Password:** `tomas.novak@gmail.com` / `tomas1234`
- **Languages:** English, Spanish, Portuguese
- **Tours created:**
  1. Complete Prague Tour
  2. Original Free Tour of Prague
  3. Royal Road to Prague: Old Town, Charles Bridge and Castle

### Guide 2 — Klara Vesela
- **Email / Password:** `veselaklara344@yahoo.com` / `chicken1234`
- **Languages:** English, Italian, German, Spanish
- **Tours created:**
  1. Free Tour New Town of Prague, WWII & Communism
  2. Free Tour Around the Prague Castle: Explore the world biggest castle
  3. Walking Tour: Old Town & Jewish Quarter
  4. Prague Free Tour: Old Town & Jewish Quarter, Incl Astronomical Clock

### Guide 3 — Petru Svobodova
- **Email / Password:** `petrusvb@icloud.com` / `petruelectronics1234`
- **Languages:** English, Portuguese, German, Spanish
- **Tours created:**
  1. Welcome to Prague: Old Town, Jewish Quarter & Charles Bridge Freetour
  2. Classic Prague Castle Free Tour, Strahov Monastery & Castle District
  3. Panoramic Vltava River Cruise

> Tours **Royal Road to Prague** (Tomas) and **Walking Tour: Old Town & Jewish
> Quarter** (Klara) intentionally have **no reservations yet** — useful for
> testing that a guide can still freely edit a tour that nobody has booked.

---

## 3. Participants

Four participants. A participant can make reservations but **cannot create tours**.
A reservation includes 1–4 people (the participant + up to 3 extra guests).

### Participant 1 — Anna Walker
- **Email / Password:** `annawalker@gmail.com` / `annaaa1111`
- **Reservations:**

  | Tour | Guide | Date | Time | Language | People (extra guests) |
  |------|-------|------|------|----------|-----------------------|
  | Complete Prague Tour | Tomas Novak | 2026-06-29 | 09:00 | English | 4 (Liam Walker, Sophie Walker, Noah Brooks) |
  | Free Tour New Town of Prague, WWII & Communism | Klara Vesela | 2026-06-30 | 09:00 | English | 2 (Emma Walker) |
  | Panoramic Vltava River Cruise | Petru Svobodova | 2026-07-01 | 09:00 | English | 1 |
  | Prague Free Tour: Old Town & Jewish Quarter, Incl Astronomical Clock | Klara Vesela | 2026-07-02 | 11:00 | English | 1 |
  | Classic Prague Castle Free Tour | Petru Svobodova | 2026-07-03 | 10:00 | English | 1 |

### Participant 2 — Martin Cerny
- **Email / Password:** `martincerny@gmail.com` / `ghostmarty007`
- **Reservations:**

  | Tour | Guide | Date | Time | Language | People (extra guests) |
  |------|-------|------|------|----------|-----------------------|
  | Free Tour New Town of Prague, WWII & Communism | Klara Vesela | 2026-06-29 | 10:00 | Spanish | 1 |
  | Original Free Tour of Prague | Tomas Novak | 2026-06-30 | 10:00 | Spanish | 3 (Petra Cerny, Jakub Cerny) |
  | Free Tour Around the Prague Castle | Klara Vesela | 2026-07-02 | 17:00 | English | 1 |
  | Welcome to Prague: Old Town, Jewish Quarter & Charles Bridge Freetour | Petru Svobodova | 2026-07-03 | 13:00 | Spanish | 4 (Lucie Novak, Tomas Marek, Eva Cerny) |

### Participant 3 — Teresa Dvorazoka
- **Email / Password:** `dvorazoka.teresa@gmail.com` / `teresaflyinginsky`
- **Reservations:**

  | Tour | Guide | Date | Time | Language | People (extra guests) |
  |------|-------|------|------|----------|-----------------------|
  | Free Tour Around the Prague Castle | Klara Vesela | 2026-06-29 | 16:00 | Italian | 2 (Elena Dvorazoka) |
  | Panoramic Vltava River Cruise | Petru Svobodova | 2026-06-30 | 16:00 | German | 3 (Marco Rossi, Giulia Bianchi) |
  | Prague Free Tour: Old Town & Jewish Quarter, Incl Astronomical Clock | Klara Vesela | 2026-07-03 | 15:00 | Italian | 1 |

### Participant 4 — Adela Vesela
- **Email / Password:** `adela.vesela@gmail.com` / `ADELAsinging1234`
- **Reservations:**

  | Tour | Guide | Date | Time | Language | People (extra guests) |
  |------|-------|------|------|----------|-----------------------|
  | Classic Prague Castle Free Tour | Petru Svobodova | 2026-06-29 | 12:30 | Portuguese | 1 |
  | Complete Prague Tour | Tomas Novak | 2026-07-03 | 18:00 | Portuguese | 4 (Karel Vesely, Marie Vesela, Jan Horak) |

---

## 3b. Past-Data Participants (for testing the reporting flow)

Two extra participants whose bookings are in the **past** so the post-tour
reporting features (Tours History + Past Reports) are populated out of the box.
The exact dates are computed at seed time to fall in **the previous month**
(roughly 4–6 weeks ago), on each tour's real weekday.

### Participant 5 — Lukas Horak
- **Email / Password:** `lukas.horak@gmail.com` / `lukaspast2026`
- **Past completed & reported tours:**

  | Tour | Guide | Weekday/Time | Language | People (extra guests) | Attended (reported) |
  |------|-------|--------------|----------|-----------------------|---------------------|
  | Complete Prague Tour | **Tomas Novak** | Mon 09:00 | English | 2 (Eva Horak) | 2 |
  | Free Tour Around the Prague Castle | **Klara Vesela** | Thu 17:00 | English | 3 (Petr Horak, Jana Horak) | 3 |
  | Panoramic Vltava River Cruise | **Petru Svobodova** | Wed 09:00 | English | 1 | 1 |

### Participant 6 — Marie Kralova
- **Email / Password:** `marie.kralova@gmail.com` / `mariepast2026`
- **Past completed & reported tours:**

  | Tour | Guide | Weekday/Time | Language | People (extra guests) | Attended (reported) |
  |------|-------|--------------|----------|-----------------------|---------------------|
  | Welcome to Prague Freetour | **Petru Svobodova** | Fri 13:00 | Spanish | 3 (Anna Kralova, Jakub Kral) | 3 |
  | Free Tour New Town of Prague, WWII & Communism | **Klara Vesela** | Tue 09:00 | English | 2 (Tomas Kral) | 2 |
  | Original Free Tour of Prague | **Tomas Novak** | Thu 17:00 | English | 1 | 1 |

Each of these six tours appears in its guide's **Tours History** and **Past
Reports History**. Per guide, that's **2 reported tours each** for Tomas, Klara,
and Petru.

---

## 3c. "Mark as done" Test Departures (this week, already started)

Two departures took place earlier **this week** and are **not yet reported**, so
the owning guide's **"Mark as done"** button is live. Log in as the guide to use it.

| Tour | Guide | Weekday/Time | Booked by | People | Purpose |
|------|-------|--------------|-----------|--------|---------|
| Classic Prague Castle Free Tour | **Petru Svobodova** | Tue 10:00 (English) | Lukas Horak | 2 (Eva Horak) | One to **test now** |
| Complete Prague Tour | **Tomas Novak** | Wed 11:00 (English) | Marie Kralova | 2 (Jakub Kral) | One to **leave for the test day** |

> To test: sign in as **Petru Svobodova** → guide dashboard → the Classic Prague
> Castle row shows **"Mark as done"**. After marking it done it moves to Tours
> History and a *pending report* appears for you to file (attendance + photo).
> Leave the **Complete Prague Tour** row (Tomas Novak) untouched for the demo day.

---

## 3d. Report Evidence Photos — where to upload

The six past reports reference evidence photos stored under
**`app/static/uploads/reports/`**. Placeholder images are already in place so
nothing is broken; **replace each file** (keep the same filename) with a real
"participants on the tour" photo:

| File to replace (`app/static/uploads/reports/…`) | Report it belongs to |
|--------------------------------------------------|----------------------|
| `report-lukas-complete-prague-tour.jpg` | Lukas → Complete Prague Tour (Tomas Novak) |
| `report-lukas-prague-castle.jpg` | Lukas → Free Tour Around the Prague Castle (Klara Vesela) |
| `report-lukas-vltava-cruise.jpg` | Lukas → Panoramic Vltava River Cruise (Petru Svobodova) |
| `report-marie-welcome-prague.jpg` | Marie → Welcome to Prague Freetour (Petru Svobodova) |
| `report-marie-newtown-communism.jpg` | Marie → Free Tour New Town, WWII & Communism (Klara Vesela) |
| `report-marie-original-free-tour.jpg` | Marie → Original Free Tour of Prague (Tomas Novak) |

Keep the `.jpg` extension (or update the path in the DB if you use a different
format). New reports filed through the UI upload their photo automatically to
the same folder.

---

## 4. Totals

- **1** administrator
- **3** guides
- **6** participants (4 with upcoming bookings + 2 with past/reported bookings)
- **10** tours (across English, Spanish, German, Italian, Portuguese)
- **22** reservations (14 upcoming + 6 past-reported + 2 this-week awaiting report)
- **6** post-tour reports filed (2 per guide)
