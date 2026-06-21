import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


DB_NAME = "walk_prague.sqlite3"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_backend(app):
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)
    app.config.setdefault("DATABASE", str(instance_path / DB_NAME))
    app.teardown_appcontext(close_db)
    with app.app_context():
        create_schema()
        seed_database()
        ensure_project_people()


def create_schema():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL CHECK(role IN ('participant', 'guide', 'admin')),
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guide_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            bio TEXT NOT NULL,
            specialty TEXT NOT NULL,
            profile_photo TEXT,
            active_since INTEGER NOT NULL,
            rating_average REAL NOT NULL DEFAULT 0,
            total_reviews INTEGER NOT NULL DEFAULT 0,
            guests_guided INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS guide_languages (
            guide_id INTEGER NOT NULL REFERENCES guide_profiles(id) ON DELETE CASCADE,
            language TEXT NOT NULL,
            PRIMARY KEY (guide_id, language)
        );

        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guide_id INTEGER NOT NULL REFERENCES guide_profiles(id) ON DELETE CASCADE,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            meeting_point TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            max_participants INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            wheelchair_accessible INTEGER NOT NULL DEFAULT 0,
            suitable_for_children INTEGER NOT NULL DEFAULT 0,
            pet_friendly INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tour_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_id INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
            image_path TEXT NOT NULL,
            is_cover INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tour_stops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_id INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
            stop_order INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tour_themes (
            tour_id INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
            theme TEXT NOT NULL,
            PRIMARY KEY (tour_id, theme)
        );

        CREATE TABLE IF NOT EXISTS tour_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_id INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
            weekday INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            language TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            max_participants INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS tour_occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL REFERENCES tour_schedules(id) ON DELETE CASCADE,
            starts_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            max_participants INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            UNIQUE(schedule_id, starts_at)
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            occurrence_id INTEGER NOT NULL REFERENCES tour_occurrences(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cancelled_at TEXT
        );

        CREATE TABLE IF NOT EXISTS reservation_guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_id INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
            occurrence_id INTEGER REFERENCES tour_occurrences(id) ON DELETE SET NULL,
            participant_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            rating REAL NOT NULL,
            title TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guide_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurrence_id INTEGER NOT NULL UNIQUE REFERENCES tour_occurrences(id) ON DELETE CASCADE,
            guide_id INTEGER NOT NULL REFERENCES guide_profiles(id) ON DELETE CASCADE,
            expected_participants INTEGER NOT NULL,
            actual_participants INTEGER NOT NULL,
            evidence_photo_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    db.commit()


def seed_database():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return

    password = generate_password_hash("password123")
    users = [
        ("guide", "Tomas", "Novak", "guide@walkprague.cz", password),
        ("guide", "Karolina", "Dvorak", "karolina@walkprague.cz", password),
        ("guide", "Klara", "Vesela", "klara@walkprague.cz", password),
        ("participant", "Anna", "Walker", "participant@walkprague.cz", password),
        ("admin", "Platform", "Administrator", "admin@walkprague.cz", password),
    ]
    db.executemany(
        "INSERT INTO users (role, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
        users,
    )

    guide_profiles = [
        (1, "Lead local guide and history graduate.", "History", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=220&q=80", 2018, 9.6, 124, 1840),
        (2, "Castle district specialist with a love for hidden courtyards.", "Castle District", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=220&q=80", 2020, 9.3, 88, 920),
        (3, "Night-walk storyteller focused on legends and alchemy.", "Local Legends", "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=220&q=80", 2019, 9.1, 52, 740),
    ]
    db.executemany(
        """
        INSERT INTO guide_profiles
        (user_id, bio, specialty, profile_photo, active_since, rating_average, total_reviews, guests_guided)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        guide_profiles,
    )
    guide_languages = [
        (1, "English"), (1, "German"), (1, "Italian"), (1, "Spanish"), (1, "Portuguese"),
        (2, "English"), (2, "German"), (2, "French"),
        (3, "English"), (3, "German"),
    ]
    db.executemany("INSERT INTO guide_languages (guide_id, language) VALUES (?, ?)", guide_languages)

    tours = [
        (1, "complete-prague-free-tour", "Complete Prague Free Tour", "Explore Prague's Old Town, Lesser Town, Jewish Quarter and Charles Bridge with local stories and practical tips.", "Metrostation Malostranska", 180, 15, "active", 1, 1, 1),
        (1, "prague-castle-morning-walk", "Prague Castle Morning Walk", "A calmer castle walk through Hradcany, viewpoints, courtyards and stories from Prague's royal route.", "Hradcanske Square", 120, 12, "active", 1, 1, 0),
        (3, "ghost-legends-alchemy-night-walk", "Ghost Legends & Alchemy Night Walk", "A night route through Old Town legends, alchemy stories and mysterious courtyards.", "Old Town Bridge Tower", 90, 15, "active", 0, 0, 0),
        (2, "castle-district-hidden-courtyards", "Castle District & Hidden Courtyards", "Walk through hidden castle-side passages, monasteries and panoramic viewpoints.", "Hradcanske Square", 120, 12, "active", 1, 1, 0),
        (1, "beer-markets-czech-bites", "Beer, Markets & Czech Bites", "Taste the city through markets, old pubs, snacks and everyday food culture.", "Namesti Republiky", 120, 14, "active", 0, 1, 0),
        (2, "art-nouveau-architecture-route", "Art Nouveau & Architecture Route", "Compare Gothic, Baroque, Cubist and Art Nouveau Prague through facades and passages.", "Municipal House", 135, 16, "active", 1, 1, 0),
    ]
    db.executemany(
        """
        INSERT INTO tours
        (guide_id, slug, title, description, meeting_point, duration_minutes, max_participants, status,
         wheelchair_accessible, suitable_for_children, pet_friendly)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tours,
    )

    photos = [
        (1, "img/tours/free-walking-tour-prague-old-town-castle-02.webp", 1),
        (1, "img/tours/free-walking-tour-prague-old-town-castle-03.webp", 0),
        (1, "img/tours/free-walking-tour-prague-old-town-castle-01.jpg", 0),
        (1, "img/tours/free-walking-tour-prague-old-town-castle-08.jpg", 0),
        (1, "img/tours/free-walking-tour-prague-old-town-castle-06.webp", 0),
        (2, "https://images.unsplash.com/photo-1600623471616-8c1966c91ff6?auto=format&fit=crop&w=1600&q=80", 1),
        (3, "https://images.unsplash.com/photo-1551867633-194f125bddfa?auto=format&fit=crop&w=1600&q=80", 1),
        (4, "https://images.unsplash.com/photo-1600623471616-8c1966c91ff6?auto=format&fit=crop&w=1600&q=80", 1),
        (5, "https://images.unsplash.com/photo-1574094985345-fc6a821b96da?auto=format&fit=crop&w=1600&q=80", 1),
        (6, "https://images.unsplash.com/photo-1562624475-96c2bc08fab9?auto=format&fit=crop&w=1600&q=80", 1),
    ]
    db.executemany("INSERT INTO tour_photos (tour_id, image_path, is_cover) VALUES (?, ?, ?)", photos)

    themes = [
        (1, "Historical"), (1, "Architectural"), (1, "Local legends & traditions"),
        (2, "Historical"), (2, "Architectural"),
        (3, "Local legends & traditions"), (3, "Alternative"),
        (4, "Historical"), (4, "Architectural"),
        (5, "Gastronomic"), (5, "Alternative"),
        (6, "Artistic"), (6, "Architectural"),
    ]
    db.executemany("INSERT INTO tour_themes (tour_id, theme) VALUES (?, ?)", themes)

    stop_rows = []
    default_stops = [
        ("Old Town Square", "The beating heart of Prague, surrounded by Gothic, Baroque and Renaissance architecture."),
        ("Astronomical Clock", "Stories behind the hourly procession and the clock's 600-year history."),
        ("Church of Our Lady before Tyn", "The iconic twin Gothic towers that define the Prague skyline."),
        ("Charles Bridge", "River views, statues and legends from Prague's medieval life."),
        ("Jewish Quarter", "Synagogues, old lanes and the history of Josefov."),
        ("Powder Gate & Republic Square", "A Royal Route ending with recommendations for what to explore next."),
    ]
    for tour_id in range(1, 7):
        for index, (title, description) in enumerate(default_stops[:4 if tour_id != 1 else 6], start=1):
            stop_rows.append((tour_id, index, title, description))
    db.executemany(
        "INSERT INTO tour_stops (tour_id, stop_order, title, description) VALUES (?, ?, ?, ?)",
        stop_rows,
    )

    schedules = [
        (1, 0, "09:00", "English", 180, 15),
        (1, 4, "14:00", "Italian", 180, 15),
        (1, 0, "19:00", "Spanish", 180, 15),
        (2, 3, "11:00", "German", 120, 12),
        (3, 6, "19:00", "English", 90, 15),
        (4, 5, "15:30", "English", 120, 12),
        (5, 2, "17:00", "Portuguese", 120, 14),
        (6, 1, "10:30", "French", 135, 16),
    ]
    db.executemany(
        "INSERT INTO tour_schedules (tour_id, weekday, start_time, language, duration_minutes, max_participants) VALUES (?, ?, ?, ?, ?, ?)",
        schedules,
    )
    db.commit()

    generate_occurrences(days_back=7, days_forward=45)
    seed_reservations_reviews_reports()


def ensure_project_people():
    guides = [
        {
            "first_name": "Jan",
            "last_name": "Novák",
            "email": "jan.novak@walkprague.cz",
            "password": "Prague2026!jan",
            "bio": "Local Prague guide focused on classic historical walks and city stories.",
            "specialty": "Historical",
            "languages": ["English", "German"],
        },
        {
            "first_name": "Petr",
            "last_name": "Horák",
            "email": "petr.horak@walkprague.cz",
            "password": "Prague2026!petr",
            "bio": "Multilingual guide with a focus on gastronomy, culture and hidden local routes.",
            "specialty": "Gastronomic",
            "languages": ["Italian", "Spanish", "French"],
        },
        {
            "first_name": "Eliška",
            "last_name": "Svobodová",
            "email": "eliska.svobodova@walkprague.cz",
            "password": "Prague2026!eliska",
            "bio": "Guide for international visitors who enjoy architecture, traditions and relaxed city walks.",
            "specialty": "Architectural",
            "languages": ["English", "Spanish", "Portuguese"],
        },
        {
            "first_name": "Kateřina",
            "last_name": "Němcová",
            "email": "katerina.nemcova@walkprague.cz",
            "password": "Prague2026!katerina",
            "bio": "Experienced guide for historical and cultural walks through Prague's central districts.",
            "specialty": "Historical",
            "languages": ["English", "German", "French"],
        },
    ]
    participants = [
        ("Jakub", "Novotný", "jakub.novotny@email.cz", "Pass123!jakub"),
        ("Martin", "Černý", "martin.cerny@seznam.cz", "Pass123!martin"),
        ("Ondřej", "Kučera", "ondrej.kucera@centrum.cz", "Pass123!ondrej"),
        ("Tereza", "Dvořáková", "tereza.dvorakova@email.cz", "Pass123!tereza"),
        ("Anna", "Procházková", "anna.prochazkova@seznam.cz", "Pass123!anna"),
        ("Adéla", "Veselá", "adela.vesela@centrum.cz", "Pass123!adela"),
    ]

    db = get_db()
    for guide in guides:
        user_id = upsert_user(
            "guide",
            guide["first_name"],
            guide["last_name"],
            guide["email"],
            guide["password"],
        )
        db.execute(
            """
            INSERT INTO guide_profiles
            (user_id, bio, specialty, profile_photo, active_since, rating_average, total_reviews, guests_guided)
            VALUES (?, ?, ?, '', 2026, 0, 0, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                bio = excluded.bio,
                specialty = excluded.specialty
            """,
            (user_id, guide["bio"], guide["specialty"]),
        )
        guide_id = db.execute("SELECT id FROM guide_profiles WHERE user_id = ?", (user_id,)).fetchone()["id"]
        db.execute("DELETE FROM guide_languages WHERE guide_id = ?", (guide_id,))
        db.executemany(
            "INSERT INTO guide_languages (guide_id, language) VALUES (?, ?)",
            [(guide_id, language) for language in guide["languages"]],
        )

    for first_name, last_name, email, password in participants:
        upsert_user("participant", first_name, last_name, email, password)

    db.commit()


def upsert_user(role, first_name, last_name, email, password):
    db = get_db()
    db.execute(
        """
        INSERT INTO users (role, first_name, last_name, email, password_hash)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            role = excluded.role,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            password_hash = excluded.password_hash
        """,
        (role, first_name, last_name, email, generate_password_hash(password)),
    )
    return db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]


def generate_occurrences(days_back=0, days_forward=60):
    db = get_db()
    today = datetime(2026, 6, 20)
    schedules = db.execute("SELECT * FROM tour_schedules WHERE active = 1").fetchall()
    for schedule in schedules:
        for offset in range(-days_back, days_forward + 1):
            day = today + timedelta(days=offset)
            if day.weekday() != schedule["weekday"]:
                continue
            hours, minutes = map(int, schedule["start_time"].split(":"))
            starts_at = day.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            ends_at = starts_at + timedelta(minutes=schedule["duration_minutes"])
            db.execute(
                """
                INSERT OR IGNORE INTO tour_occurrences
                (schedule_id, starts_at, ends_at, max_participants, status)
                VALUES (?, ?, ?, ?, 'scheduled')
                """,
                (schedule["id"], starts_at.isoformat(), ends_at.isoformat(), schedule["max_participants"]),
            )
    db.commit()


def seed_reservations_reviews_reports():
    db = get_db()
    participant_id = db.execute("SELECT id FROM users WHERE role = 'participant' LIMIT 1").fetchone()["id"]
    occurrence_rows = db.execute(
        """
        SELECT o.id, t.slug, o.starts_at
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        ORDER BY o.starts_at
        """
    ).fetchall()
    wanted = [
        ("complete-prague-free-tour", "2026-06-19", [("Ana", "Kovac"), ("Luca", "Bianchi")]),
        ("complete-prague-free-tour", "2026-06-22", [("Sara", "Miller")]),
        ("ghost-legends-alchemy-night-walk", "2026-06-21", [("Daniel", "Kim"), ("Marta", "Ruiz")]),
        ("prague-castle-morning-walk", "2026-06-18", [("Lea", "Wagner")]),
    ]
    for slug, date_prefix, guests in wanted:
        occurrence = next((row for row in occurrence_rows if row["slug"] == slug and row["starts_at"].startswith(date_prefix)), None)
        if not occurrence:
            continue
        cur = db.execute(
            "INSERT INTO reservations (participant_id, occurrence_id, status) VALUES (?, ?, 'active')",
            (participant_id, occurrence["id"]),
        )
        reservation_id = cur.lastrowid
        db.executemany(
            "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?, ?, ?)",
            [(reservation_id, first, last) for first, last in guests],
        )

    reviews = [
        (1, 1, participant_id, 9.8, "Friendly and memorable guide", "Aleks gave a clear, relaxed walk through the old city."),
        (1, 1, participant_id, 9.6, "Excellent Prague introduction", "The route was entertaining and well researched."),
        (3, 3, participant_id, 9.1, "Atmospheric night walk", "The stories were easy to follow and the evening route worked well."),
    ]
    db.executemany(
        "INSERT INTO reviews (tour_id, occurrence_id, participant_id, rating, title, comment) VALUES (?, ?, ?, ?, ?, ?)",
        reviews,
    )

    past_occurrence = db.execute(
        """
        SELECT o.id, t.guide_id
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE t.slug = 'complete-prague-free-tour' AND o.starts_at LIKE '2026-06-19%'
        LIMIT 1
        """
    ).fetchone()
    if past_occurrence:
        db.execute(
            """
            INSERT INTO guide_reports
            (occurrence_id, guide_id, expected_participants, actual_participants, evidence_photo_path, status)
            VALUES (?, ?, 3, 3, ?, 'approved')
            """,
            (past_occurrence["id"], past_occurrence["guide_id"], "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1400&q=80"),
        )
    db.commit()


def full_name(row):
    return f"{row['first_name']} {row['last_name']}"


def duration_label(minutes):
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}min" if hours else f"{mins} min"


def fetch_tour_by_slug(slug):
    return get_db().execute(
        """
        SELECT t.*, gp.rating_average, gp.total_reviews, gp.profile_photo, gp.specialty,
               u.first_name, u.last_name, u.email AS guide_email
        FROM tours t
        JOIN guide_profiles gp ON gp.id = t.guide_id
        JOIN users u ON u.id = gp.user_id
        WHERE t.slug = ?
        """,
        (slug,),
    ).fetchone()


def tour_cover(tour_id):
    row = get_db().execute(
        "SELECT image_path FROM tour_photos WHERE tour_id = ? ORDER BY is_cover DESC, id LIMIT 1",
        (tour_id,),
    ).fetchone()
    return row["image_path"] if row else "img/prague-empty.svg"


def tour_languages(tour_id):
    rows = get_db().execute(
        "SELECT DISTINCT language FROM tour_schedules WHERE tour_id = ? ORDER BY language",
        (tour_id,),
    ).fetchall()
    return [row["language"] for row in rows]


def get_public_tours():
    rows = get_db().execute(
        """
        SELECT t.*, gp.rating_average, gp.total_reviews, gp.profile_photo, u.first_name, u.last_name
        FROM tours t
        JOIN guide_profiles gp ON gp.id = t.guide_id
        JOIN users u ON u.id = gp.user_id
        WHERE t.status = 'active'
        ORDER BY t.id
        """
    ).fetchall()
    tours = []
    for row in rows:
        tours.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "description": row["description"],
                "rating": f"{row['rating_average']:.1f}",
                "reviews": row["total_reviews"],
                "duration": duration_label(row["duration_minutes"]),
                "meeting_point": row["meeting_point"],
                "languages": tour_languages(row["id"]),
                "guide": full_name(row),
                "guide_photo": row["profile_photo"],
                "image": tour_cover(row["id"]),
            }
        )
    return tours


def get_tour_detail(slug):
    row = fetch_tour_by_slug(slug) or fetch_tour_by_slug("complete-prague-free-tour")
    gallery = [
        photo["image_path"]
        for photo in get_db().execute(
            "SELECT image_path FROM tour_photos WHERE tour_id = ? ORDER BY is_cover DESC, id",
            (row["id"],),
        )
    ]
    occurrences = []
    for occurrence in get_db().execute(
        """
        SELECT o.id, o.starts_at, o.max_participants, s.language
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        WHERE s.tour_id = ? AND o.starts_at >= ?
        ORDER BY o.starts_at
        LIMIT 8
        """,
        (row["id"], "2026-06-20T00:00:00"),
    ).fetchall():
        reserved = reservation_count_for_occurrence(occurrence["id"])
        occurrences.append(
            {
                "id": occurrence["id"],
                "starts_at": occurrence["starts_at"],
                "language": occurrence["language"],
                "available_left": max(0, occurrence["max_participants"] - reserved),
            }
        )
    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "provider": "Walk Prague",
        "guide": full_name(row),
        "rating": f"{row['rating_average']:.1f}",
        "reviews": str(row["total_reviews"]),
        "duration": duration_label(row["duration_minutes"]),
        "meeting_point": row["meeting_point"],
        "languages": ", ".join(tour_languages(row["id"])),
        "guide_email": row["guide_email"],
        "image": gallery[0] if gallery else "img/prague-empty.svg",
        "gallery": gallery or ["img/prague-empty.svg"],
        "occurrences": occurrences,
    }


def participant_dashboard_data():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE role = 'participant' ORDER BY id LIMIT 1").fetchone()
    reservations = db.execute(
        """
        SELECT r.id, r.status, o.starts_at, t.title, t.slug, t.meeting_point, s.language
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE r.participant_id = ?
        ORDER BY o.starts_at DESC
        """,
        (user["id"],),
    ).fetchall()
    items = []
    now = datetime(2026, 6, 20, 12, 0)
    for reservation in reservations:
        guests = db.execute(
            "SELECT first_name, last_name FROM reservation_guests WHERE reservation_id = ?",
            (reservation["id"],),
        ).fetchall()
        starts_at = datetime.fromisoformat(reservation["starts_at"])
        can_cancel = reservation["status"] == "active" and now <= starts_at - timedelta(hours=24)
        items.append(
            {
                "id": reservation["id"],
                "tour": reservation["title"],
                "slug": reservation["slug"],
                "date": starts_at.strftime("%a, %B %-d, %Y"),
                "start_time": starts_at.strftime("%-I:%M %p"),
                "meeting_point": reservation["meeting_point"],
                "people": 1 + len(guests),
                "additional_participants": [full_name(guest) for guest in guests],
                "language": reservation["language"],
                "status": "Confirmed" if reservation["status"] == "active" else "Cancelled",
                "can_cancel": can_cancel,
                "cancel_note": "Cancellation available until " + (starts_at - timedelta(hours=24)).strftime("%b %-d, %Y at %-I:%M %p") if can_cancel else "Less than 24 hours before start time",
            }
        )
    return {"name": user["first_name"], "email": user["email"], "reservations": items}


def reservation_count_for_occurrence(occurrence_id):
    row = get_db().execute(
        """
        SELECT COUNT(r.id) + COUNT(g.id) AS people
        FROM reservations r
        LEFT JOIN reservation_guests g ON g.reservation_id = r.id
        WHERE r.occurrence_id = ? AND r.status = 'active'
        """,
        (occurrence_id,),
    ).fetchone()
    return row["people"] or 0


def guide_dashboard_data():
    db = get_db()
    guide = db.execute(
        """
        SELECT gp.*, u.first_name, u.last_name, u.email
        FROM guide_profiles gp
        JOIN users u ON u.id = gp.user_id
        ORDER BY gp.id LIMIT 1
        """
    ).fetchone()
    tours = db.execute("SELECT * FROM tours WHERE guide_id = ? ORDER BY id", (guide["id"],)).fetchall()
    tour_items = []
    total_bookings = 0
    total_people = 0
    for tour in tours:
        schedules = db.execute(
            """
            SELECT o.id AS occurrence_id, o.starts_at, o.max_participants, s.language, s.duration_minutes
            FROM tour_occurrences o
            JOIN tour_schedules s ON s.id = o.schedule_id
            WHERE s.tour_id = ?
            ORDER BY o.starts_at
            """,
            (tour["id"],),
        ).fetchall()
        schedule_items = []
        for schedule in schedules:
            people = reservation_count_for_occurrence(schedule["occurrence_id"])
            groups = db.execute(
                "SELECT COUNT(*) FROM reservations WHERE occurrence_id = ? AND status = 'active'",
                (schedule["occurrence_id"],),
            ).fetchone()[0]
            if people:
                total_bookings += groups
                total_people += people
            starts_at = datetime.fromisoformat(schedule["starts_at"])
            schedule_items.append(
                {
                    "date": starts_at.strftime("%a, %B %-d, %Y"),
                    "time": starts_at.strftime("%-I:%M %p"),
                    "language": schedule["language"],
                    "reserved_groups": groups,
                    "expected": people,
                    "max_participants": schedule["max_participants"],
                    "state": "completed" if starts_at < datetime(2026, 6, 20, 12, 0) else "upcoming",
                    "reservations": [],
                }
            )
        tour_items.append(
            {
                "title": tour["title"],
                "slug": tour["slug"],
                "status": tour["status"].title(),
                "languages": ", ".join(tour_languages(tour["id"])),
                "meeting_point": tour["meeting_point"],
                "image": tour_cover(tour["id"]),
                "themes": [row["theme"] for row in db.execute("SELECT theme FROM tour_themes WHERE tour_id = ?", (tour["id"],))],
                "schedules": schedule_items,
            }
        )
    reports = db.execute("SELECT COUNT(*) FROM guide_reports WHERE guide_id = ?", (guide["id"],)).fetchone()[0]
    return {
        "name": full_name(guide),
        "email": guide["email"],
        "rating": f"{guide['rating_average']:.1f}/10",
        "active_tours": len(tour_items),
        "expected_participants": total_people,
        "pending_reports": reports,
        "total_bookings": total_bookings,
        "tours": tour_items,
    }


def admin_dashboard_data():
    db = get_db()
    guide_count = db.execute("SELECT COUNT(*) FROM guide_profiles").fetchone()[0]
    participant_count = db.execute("SELECT COUNT(*) FROM users WHERE role = 'participant'").fetchone()[0]
    tour_count = db.execute("SELECT COUNT(*) FROM tours").fetchone()[0]
    reservation_count = db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    report_count = db.execute("SELECT COUNT(*) FROM guide_reports").fetchone()[0]
    people_count = db.execute("SELECT COUNT(r.id) + COUNT(g.id) FROM reservations r LEFT JOIN reservation_guests g ON g.reservation_id = r.id WHERE r.status = 'active'").fetchone()[0] or 0
    language_rows = db.execute(
        """
        SELECT s.language, COUNT(r.id) + COUNT(g.id) AS people
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        LEFT JOIN reservation_guests g ON g.reservation_id = r.id
        WHERE r.status = 'active'
        GROUP BY s.language
        ORDER BY people DESC
        """
    ).fetchall()
    accents = ["blue", "green", "purple", "orange", "cyan"]
    flags = {"English": "🇬🇧", "German": "🇩🇪", "Spanish": "🇪🇸", "French": "🇫🇷", "Portuguese": "🇵🇹", "Italian": "🇮🇹"}
    languages = [
        {
            "name": row["language"],
            "flag": flags.get(row["language"], "🏳"),
            "count": row["people"],
            "accent": accents[index % len(accents)],
            "percent": min(100, int((row["people"] / max(people_count, 1)) * 100)),
        }
        for index, row in enumerate(language_rows)
    ]
    if not any(item["name"] == "Portuguese" for item in languages):
        languages.append({"name": "Portuguese", "flag": "🇵🇹", "count": 0, "accent": "cyan", "percent": 0})

    guides = []
    for guide in db.execute("SELECT gp.*, u.first_name, u.last_name, u.email FROM guide_profiles gp JOIN users u ON u.id = gp.user_id ORDER BY gp.id").fetchall():
        guide_tours = db.execute("SELECT COUNT(*) FROM tours WHERE guide_id = ?", (guide["id"],)).fetchone()[0]
        guide_bookings = db.execute(
            """
            SELECT COUNT(r.id)
            FROM reservations r
            JOIN tour_occurrences o ON o.id = r.occurrence_id
            JOIN tour_schedules s ON s.id = o.schedule_id
            JOIN tours t ON t.id = s.tour_id
            WHERE t.guide_id = ?
            """,
            (guide["id"],),
        ).fetchone()[0]
        guides.append(
            {
                "name": full_name(guide),
                "email": guide["email"],
                "avatar": guide["profile_photo"],
                "initial": guide["first_name"][0],
                "color": "blue",
                "languages": " ".join(db.execute("SELECT language FROM guide_languages WHERE guide_id = ?", (guide["id"],)).fetchall()[i]["language"][:2].upper() for i in range(len(db.execute("SELECT language FROM guide_languages WHERE guide_id = ?", (guide["id"],)).fetchall()))),
                "language_names": ", ".join(row["language"] for row in db.execute("SELECT language FROM guide_languages WHERE guide_id = ?", (guide["id"],)).fetchall()),
                "tours": guide_tours,
                "bookings": guide_bookings,
                "rating": f"{guide['rating_average']:.1f}/10",
                "reviews": guide["total_reviews"],
                "guests": f"{guide['guests_guided']:,}",
                "specialty": guide["specialty"],
            }
        )

    tours = []
    for tour in db.execute("SELECT t.*, u.first_name, u.last_name FROM tours t JOIN guide_profiles gp ON gp.id = t.guide_id JOIN users u ON u.id = gp.user_id ORDER BY t.id").fetchall():
        reservations = db.execute(
            """
            SELECT COUNT(r.id)
            FROM reservations r
            JOIN tour_occurrences o ON o.id = r.occurrence_id
            JOIN tour_schedules s ON s.id = o.schedule_id
            WHERE s.tour_id = ?
            """,
            (tour["id"],),
        ).fetchone()[0]
        tours.append({"title": tour["title"], "slug": tour["slug"], "guide": full_name(tour), "language": "ALL", "reservations": reservations})

    reservations = []
    for row in db.execute(
        """
        SELECT r.id, u.first_name, u.last_name, t.title, gu.first_name AS guide_first, gu.last_name AS guide_last,
               o.starts_at, COUNT(g.id) AS extra_guests, r.status
        FROM reservations r
        JOIN users u ON u.id = r.participant_id
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        JOIN guide_profiles gp ON gp.id = t.guide_id
        JOIN users gu ON gu.id = gp.user_id
        LEFT JOIN reservation_guests g ON g.reservation_id = r.id
        GROUP BY r.id
        ORDER BY o.starts_at DESC
        LIMIT 12
        """
    ).fetchall():
        starts_at = datetime.fromisoformat(row["starts_at"])
        reservations.append(
            {
                "participant": f"{row['first_name']} {row['last_name']}",
                "tour": row["title"],
                "guide": f"{row['guide_first']} {row['guide_last']}",
                "date": starts_at.strftime("%b %-d, %Y"),
                "people": row["extra_guests"],
                "status": "Confirmed" if row["status"] == "active" else "Cancelled",
            }
        )

    return {
        "last_updated": "June 20, 2026",
        "stats": [
            {"value": str(guide_count), "label": "Guides", "accent": "blue", "icon": "▣"},
            {"value": str(participant_count), "label": "Participants", "accent": "green", "icon": "♙"},
            {"value": str(tour_count), "label": "Tours", "accent": "purple", "icon": "◉"},
            {"value": str(reservation_count), "label": "Reservations", "accent": "orange", "icon": "✓"},
            {"value": str(people_count), "label": "Total walkers", "accent": "red", "icon": "☑"},
            {"value": str(report_count), "label": "Reports filed", "accent": "cyan", "icon": "▤"},
        ],
        "languages": languages,
        "guides": guides,
        "tours": tours,
        "reservations": reservations,
    }


def create_reservation(occurrence_id, guest_names):
    db = get_db()
    participant = db.execute("SELECT id FROM users WHERE role = 'participant' LIMIT 1").fetchone()
    occurrence = db.execute("SELECT * FROM tour_occurrences WHERE id = ?", (occurrence_id,)).fetchone()
    if not occurrence:
        raise ValueError("Occurrence not found.")
    reserved = reservation_count_for_occurrence(occurrence_id)
    requested = 1 + len(guest_names)
    if reserved + requested > occurrence["max_participants"]:
        raise ValueError("Reservation exceeds available places.")
    cur = db.execute(
        "INSERT INTO reservations (participant_id, occurrence_id, status) VALUES (?, ?, 'active')",
        (participant["id"], occurrence_id),
    )
    reservation_id = cur.lastrowid
    for guest in guest_names:
        parts = guest.strip().split(" ", 1)
        db.execute(
            "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?, ?, ?)",
            (reservation_id, parts[0], parts[1] if len(parts) > 1 else ""),
        )
    db.commit()
    return reservation_id


def cancel_reservation(reservation_id):
    db = get_db()
    row = db.execute(
        """
        SELECT r.*, o.starts_at
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        WHERE r.id = ?
        """,
        (reservation_id,),
    ).fetchone()
    if not row:
        raise ValueError("Reservation not found.")
    now = datetime(2026, 6, 20, 12, 0)
    starts_at = datetime.fromisoformat(row["starts_at"])
    if now > starts_at - timedelta(hours=24):
        raise ValueError("Cancellation deadline has passed.")
    db.execute(
        "UPDATE reservations SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP WHERE id = ?",
        (reservation_id,),
    )
    db.commit()


def create_guide_report(occurrence_id, actual_participants, evidence_photo_path):
    db = get_db()
    occurrence = db.execute(
        """
        SELECT o.id, t.guide_id
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE o.id = ?
        """,
        (occurrence_id,),
    ).fetchone()
    if not occurrence:
        raise ValueError("Occurrence not found.")
    expected = reservation_count_for_occurrence(occurrence_id)
    if expected < 1:
        raise ValueError("Reports require at least one reservation.")
    db.execute(
        """
        INSERT OR REPLACE INTO guide_reports
        (occurrence_id, guide_id, expected_participants, actual_participants, evidence_photo_path, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        """,
        (occurrence_id, occurrence["guide_id"], expected, actual_participants, evidence_photo_path),
    )
    db.commit()
