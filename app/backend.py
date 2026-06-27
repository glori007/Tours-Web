import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app, g
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


DB_NAME = "walk_prague.sqlite3"

# The three account types are stored in three separate tables.
ROLE_TABLES = {"guide": "guides", "participant": "participants", "admin": "admins"}


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


# ---------------------------------------------------------------------------
# Flask-Login User model
# ---------------------------------------------------------------------------

class User(UserMixin):
    """Wraps a row from one of the three account tables (guides / participants /
    admins). The Flask-Login id encodes the role so the loader knows which
    table to read, e.g. "guide:3"."""

    def __init__(self, row, role):
        self.id = row["id"]
        self.role = role
        self.first_name = row["first_name"]
        self.last_name = row["last_name"]
        self.email = row["email"]

    def get_id(self):
        return f"{self.role}:{self.id}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


def get_user_by_id(token):
    """Load a User from a "role:id" token (called by Flask-Login user_loader)."""
    try:
        role, raw_id = str(token).split(":", 1)
        user_id = int(raw_id)
    except (ValueError, AttributeError):
        return None
    table = ROLE_TABLES.get(role)
    if not table:
        return None
    row = get_db().execute(f"SELECT * FROM {table} WHERE id = ?", (user_id,)).fetchone()
    return User(row, role) if row else None


def authenticate_user(email, password, expected_role):
    """Return a User if email/password match an account of the expected role."""
    table = ROLE_TABLES.get(expected_role)
    if not table:
        return None
    row = get_db().execute(
        f"SELECT * FROM {table} WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    if row is None:
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return User(row, expected_role)


VALID_LANGUAGES = {"Italian", "English", "Spanish", "Portuguese", "German"}

# Specialties are free-form themes related to guiding (multi-select, up to 4).
VALID_SPECIALTIES = {
    "Alternative & Street Art", "Architecture", "Art & Culture", "Castle District",
    "Communism & Cold War", "Gastronomy", "History", "Jewish Heritage", "Local Legends",
}


DEFAULT_PROFILE_PHOTO = "/static/img/default-profile.png"


def get_profile_photo_url(raw_photo):
    raw_photo = (raw_photo or "").strip()
    if raw_photo.startswith("http"):
        return raw_photo
    if raw_photo.startswith("img/"):
        rel = raw_photo
    elif raw_photo:
        rel = f"img/{raw_photo}"
    else:
        return DEFAULT_PROFILE_PHOTO
    try:
        static_dir = Path(current_app.root_path) / "static"
        full = static_dir / rel
        if full.exists():
            return f"/static/{rel}"
        # Accept any common image extension for the same path stem, so a guide
        # photo saved as .jpg/.jpeg/.png/.webp all resolve without code changes.
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            alt = full.with_suffix(ext)
            if alt.exists():
                return f"/static/{alt.relative_to(static_dir).as_posix()}"
        # File not present yet → default avatar (no broken image).
        return DEFAULT_PROFILE_PHOTO
    except RuntimeError:
        return f"/static/{rel}"


DEFAULT_TOUR_IMAGE = "/static/img/prague-castle.svg"


def resolve_tour_image(raw):
    """Return a usable URL for a stored tour image path. Falls back to a generic
    placeholder until the real file is uploaded, and accepts any common image
    extension for the same path stem."""
    raw = (raw or "").strip()
    if raw.startswith("http"):
        return raw
    if not raw:
        return DEFAULT_TOUR_IMAGE
    try:
        static_dir = Path(current_app.root_path) / "static"
        full = static_dir / raw
        if full.exists():
            return f"/static/{raw}"
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            alt = full.with_suffix(ext)
            if alt.exists():
                return f"/static/{alt.relative_to(static_dir).as_posix()}"
        return DEFAULT_TOUR_IMAGE
    except RuntimeError:
        return f"/static/{raw}"


def register_user(role, first_name, last_name, email, password, languages=None,
                  profile_photo_file=None, specialties=None):
    """
    Create a new guide or participant account.
    Returns the new User on success.
    Raises ValueError with a human-readable message on validation failure.
    """
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()
    specialties = [s.strip() for s in (specialties or []) if s.strip()]

    # --- back-end validation ---
    if not first_name or not last_name:
        raise ValueError("First name and last name are required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if role not in ("guide", "participant"):
        raise ValueError("Invalid role.")
    if role == "guide":
        if not languages:
            raise ValueError("Please select at least one language.")
        bad = set(languages) - VALID_LANGUAGES
        if bad:
            raise ValueError(f"Invalid language(s): {', '.join(bad)}")
        if len(specialties) > 4:
            raise ValueError("You can select up to 4 specialties.")
        bad_spec = set(specialties) - VALID_SPECIALTIES
        if bad_spec:
            raise ValueError(f"Invalid specialty(ies): {', '.join(bad_spec)}")

    db = get_db()
    # Email must be unique *within a role* only: the same person may hold both a
    # participant account and a guide account under the same email (they are two
    # separate accounts, in two separate tables, and the role chosen at sign-in
    # decides which one they log into).
    role_table = ROLE_TABLES[role]
    if db.execute(f"SELECT 1 FROM {role_table} WHERE email = ?", (email,)).fetchone():
        raise ValueError(f"A {role} account with that email address already exists.")

    if role == "participant":
        cur = db.execute(
            "INSERT INTO participants (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (first_name, last_name, email, generate_password_hash(password)),
        )
        db.commit()
        row = db.execute("SELECT * FROM participants WHERE id = ?", (cur.lastrowid,)).fetchone()
        return User(row, "participant")

    # --- guide ---
    photo_path = "img/default-profile.png"
    if profile_photo_file and profile_photo_file.filename:
        import uuid
        ext = Path(profile_photo_file.filename).suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            raise ValueError("Profile photo must be a valid image file (png, jpg, jpeg, webp, gif).")
        unique_name = f"guide_{uuid.uuid4().hex}{ext}"
        guides_dir = Path(current_app.root_path) / "static" / "img" / "guides"
        guides_dir.mkdir(parents=True, exist_ok=True)
        profile_photo_file.save(str(guides_dir / unique_name))
        photo_path = f"img/guides/{unique_name}"

    cur = db.execute(
        """
        INSERT INTO guides
        (first_name, last_name, email, password_hash, profile_photo,
         active_since, rating_average, total_reviews, guests_guided)
        VALUES (?, ?, ?, ?, ?, strftime('%Y', 'now'), 8.0, 0, 0)
        """,
        (first_name, last_name, email, generate_password_hash(password), photo_path),
    )
    guide_id = cur.lastrowid
    db.executemany(
        "INSERT INTO guide_languages (guide_id, language) VALUES (?, ?)",
        [(guide_id, lang) for lang in languages],
    )
    db.executemany(
        "INSERT INTO guide_specialties (guide_id, specialty) VALUES (?, ?)",
        [(guide_id, spec) for spec in specialties],
    )
    db.commit()
    row = db.execute("SELECT * FROM guides WHERE id = ?", (guide_id,)).fetchone()
    return User(row, "guide")


def init_backend(app):
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)
    app.config.setdefault("DATABASE", str(instance_path / DB_NAME))
    app.teardown_appcontext(close_db)
    with app.app_context():
        create_schema()
        seed_database()


def create_schema():
    db = get_db()
    db.executescript(
        """
        -- Guides, participants and admins are three separate account tables.
        CREATE TABLE IF NOT EXISTS guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            profile_photo TEXT,
            active_since INTEGER NOT NULL DEFAULT 2026,
            rating_average REAL NOT NULL DEFAULT 0,
            total_reviews INTEGER NOT NULL DEFAULT 0,
            guests_guided INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        -- NOTE: `bio` was removed (it was never displayed). Ratings/reviews here
        -- and on tours are static placeholders until a real review system exists.

        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guide_languages (
            guide_id INTEGER NOT NULL REFERENCES guides(id) ON DELETE CASCADE,
            language TEXT NOT NULL,
            PRIMARY KEY (guide_id, language)
        );

        CREATE TABLE IF NOT EXISTS guide_specialties (
            guide_id INTEGER NOT NULL REFERENCES guides(id) ON DELETE CASCADE,
            specialty TEXT NOT NULL,
            PRIMARY KEY (guide_id, specialty)
        );

        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guide_id INTEGER NOT NULL REFERENCES guides(id) ON DELETE CASCADE,
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
            rating REAL NOT NULL DEFAULT 0,
            review_count INTEGER NOT NULL DEFAULT 0,
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
            title TEXT NOT NULL
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
            finished INTEGER NOT NULL DEFAULT 0,
            UNIQUE(schedule_id, starts_at)
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
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
            participant_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
            rating REAL NOT NULL,
            title TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guide_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurrence_id INTEGER NOT NULL UNIQUE REFERENCES tour_occurrences(id) ON DELETE CASCADE,
            guide_id INTEGER NOT NULL REFERENCES guides(id) ON DELETE CASCADE,
            expected_participants INTEGER NOT NULL,
            actual_participants INTEGER NOT NULL,
            evidence_photo_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            finished INTEGER NOT NULL DEFAULT 0,
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    db.commit()


def seed_database():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM guides").fetchone()[0]:
        return

    # --- Platform administrator (kept so the admin dashboard works) ---
    db.execute(
        "INSERT INTO admins (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)",
        ("Platform", "Administrator", "admin@walkprague.cz", generate_password_hash("password123")),
    )

    # --- Guides. Tours and participants are added later by the instructor. ---
    # Profile photos live under app/static/img/guides/ (see README).
    guides = [
        {
            "first_name": "Tomas", "last_name": "Novak",
            "email": "tomas.novak@gmail.com", "password": "tomas1234",
            "photo": "img/guides/tomas-novak.jpg",
            "rating": 9.0, "reviews": 125,
            "languages": ["English", "Spanish", "Portuguese"],
            "specialties": ["Architecture", "Castle District", "History"],
        },
        {
            "first_name": "Klara", "last_name": "Vesela",
            "email": "veselaklara344@yahoo.com", "password": "chicken1234",
            "photo": "img/guides/klara-vesela.jpg",
            "rating": 8.7, "reviews": 225,
            "languages": ["English", "Italian", "German", "Spanish"],
            "specialties": ["Local Legends", "Communism & Cold War", "Gastronomy"],
        },
        {
            "first_name": "Petru", "last_name": "Svobodova",
            "email": "petrusvb@icloud.com", "password": "petruelectronics1234",
            "photo": "img/guides/petru-svobodova.jpg",
            "rating": 8.9, "reviews": 335,
            "languages": ["English", "Portuguese", "German", "Spanish"],
            "specialties": ["Architecture", "Gastronomy", "Local Legends"],
        },
    ]
    for g in guides:
        cur = db.execute(
            """
            INSERT INTO guides
            (first_name, last_name, email, password_hash, profile_photo,
             active_since, rating_average, total_reviews, guests_guided)
            VALUES (?, ?, ?, ?, ?, 2026, ?, ?, 0)
            """,
            (g["first_name"], g["last_name"], g["email"], generate_password_hash(g["password"]),
             g["photo"], g["rating"], g["reviews"]),
        )
        guide_id = cur.lastrowid
        db.executemany(
            "INSERT INTO guide_languages (guide_id, language) VALUES (?, ?)",
            [(guide_id, lang) for lang in g["languages"]],
        )
        db.executemany(
            "INSERT INTO guide_specialties (guide_id, specialty) VALUES (?, ?)",
            [(guide_id, spec) for spec in g["specialties"]],
        )

    db.commit()
    seed_tours()
    seed_participants()
    seed_past_data()


# weekday: Monday=0 ... Sunday=6
SEED_TOURS = [
    {
        "guide": 1, "slug": "complete-prague-tour", "title": "Complete Prague Tour",
        "meeting_point": "Metrostation Malostranska", "duration": 120, "max": 17,
        "rating": 8.5, "reviews": 125, "wheelchair": 1, "children": 0, "pet": 1,
        "themes": ["Historical", "Architectural", "Literary"],
        "stops": ["Mala Strana", "Čůrající postavy", "Lennon Wall", "Charles Bridge",
                  "Jewish Quarter", "Old-New Synagogue", "Old Town Square"],
        "schedules": [(0, "09:00", "English"), (0, "16:00", "Spanish"),
                      (2, "11:00", "English"), (4, "18:00", "Portuguese")],
        "description": ("Want to start your holiday in Prague well? Join our 2-in-1 tour. The tour that "
                        "actually includes 2 tours. Discover the Old Town, Lesser Town, Jewish Quarter and "
                        "Charles Bridge with us!\n\n"
                        "When you talk about \"The Old Town,\" you are talking about the old historical part of "
                        "Prague. There was little bombing here during the Second World War, so almost all "
                        "buildings are still standing and in their original condition. Prague's Old Town is truly "
                        "an impressive open-air museum. During the tour, you will explore exciting places such as "
                        "Old Town Square, the Astronomical Clock, Charles Bridge, and the Jewish Quarter.\n\n"
                        "What are you waiting for, join us."),
    },
    {
        "guide": 1, "slug": "original-free-tour-of-prague", "title": "Original Free Tour of Prague",
        "meeting_point": "Old Town Square, the corner of Parizska Street", "duration": 180, "max": 10,
        "rating": 8.7, "reviews": 225, "wheelchair": 0, "children": 1, "pet": 1,
        "themes": ["Historical", "Political", "Gastronomic"],
        "stops": ["Old Town Square & Astronomical Clock", "Charles Bridge",
                  "House of the Black Madonna & Museum of Cubism", "Wenceslas Square",
                  "Statue of Jan Hus", "Powder Tower"],
        "schedules": [(1, "10:00", "Spanish"), (2, "16:00", "Spanish"),
                      (3, "17:00", "English"), (4, "11:00", "English"), (6, "10:00", "English")],
        "description": ("From medieval kings to revolutions and resistance, Prague is a city shaped by centuries "
                        "of powerful stories — and there's no better way to uncover them than on foot.\n\n"
                        "On this 3-hour walking tour, explore the historic heart of the Czech capital with a "
                        "passionate local guide. Discover must-see landmarks like the Astronomical Clock, the "
                        "elegant Rudolfinum, and the atmospheric Old Jewish Quarter, while wandering through the "
                        "city's most picturesque streets.\n\n"
                        "Along the way, dive into Prague's rich history — from royal dynasties and Bohemian "
                        "culture to the hardships of Nazi occupation and life behind the Iron Curtain, all the way "
                        "to the peaceful Velvet Revolution.\n\n"
                        "More than just a tour, it's the perfect introduction to Prague — helping you get your "
                        "bearings, understand the city, and make the most of your stay with insider tips from a "
                        "local.\n\nRain or shine, tours run as scheduled."),
    },
    {
        "guide": 1, "slug": "royal-road-to-prague", "title": "Royal Road to Prague: Old Town, Charles Bridge and Castle",
        "meeting_point": "Torre de la Polvora", "duration": 90, "max": 10,
        "rating": 7.7, "reviews": 400, "wheelchair": 1, "children": 1, "pet": 0,
        "themes": ["Architectural", "Musical", "Alternative"],
        "stops": ["The Powder Tower", "St. George's Basilica", "Old Royal Palace",
                  "Charles Bridge", "Prague Astronomical Clock"],
        "schedules": [(0, "12:00", "Portuguese"), (1, "16:00", "Spanish"), (2, "08:00", "English")],
        "description": ("A complete experience of historical Prague. Following the path of the kings on the day "
                        "of their coronation, travelers will be fully immersed in a walk through the culture, "
                        "history, legends and traditions of the city. Starting at the old city wall gate, the "
                        "Powder Tower, passing through the Old Town Square, seeing along the way places such as the "
                        "mint, the cubist museum, several churches and the famous Astronomical Clock.\n\n"
                        "We will continue across the Charles Bridge and, after a short break in a bohemian cafe, "
                        "we will head to Prague Castle. The summer route will start at the Summer Palace, in winter "
                        "at the castle itself. We will enter the palace complex where we will see the place where "
                        "the presidential office is located next to the main gate of the castle."),
    },
    {
        "guide": 2, "slug": "free-tour-new-town-wwii-communism",
        "title": "Free Tour New Town of Prague, WWII & Communism",
        "meeting_point": "Náměstí Míru", "duration": 60, "max": 12,
        "rating": 8.7, "reviews": 505, "wheelchair": 1, "children": 1, "pet": 0,
        "themes": ["Architectural", "Gastronomic", "Local legends & traditions", "Alternative"],
        "stops": ["Church of St. Ludmila", "Wenceslas Square", "Národní muzeum",
                  "St. Vitus Cathedral", "Dancing House",
                  "National Memorial to the Heroes of the Heydrich Terror"],
        "schedules": [(0, "10:00", "Spanish"), (1, "09:00", "English"), (1, "12:00", "Spanish"),
                      (1, "16:00", "German"), (2, "16:00", "German"), (3, "09:00", "English")],
        "description": ("When you talk about Prague, you usually talk about the old town because the idea is that "
                        "all the history of the city is hidden there. Nothing could be further from the truth.\n\n"
                        "The new city is almost as old and was actually built only 100 years later. There is, "
                        "therefore, just as much to see in the new city, if not even more than in the old city. The "
                        "tour starts at the St. Ludmilla Church, the most important and special church in Prague "
                        "after St. Vitus Cathedral.\n\n"
                        "The tour then continues towards Wenceslas Square to admire the special National Museum "
                        "and, of course, to get to know the whole background and history of Saint Wenceslas. During "
                        "the tour, we also passed some works of art by the most famous and infamous Czech artist, "
                        "David Cerny. To end the tour, we dive into Operation Anthropoid, one of the most important "
                        "operations in Czech history.\n\n"
                        "The attack on SS commander Reinhard Heydrich was, in any case, the most important event in "
                        "the Czech Republic during the Second World War. Since we were in the area, we ended the "
                        "tour at the dancing house. Tired from the tour? No problem because you are at Naplavka, the "
                        "nicest terraces on the quay of the Vltava River."),
    },
    {
        "guide": 2, "slug": "free-tour-around-prague-castle",
        "title": "Free Tour Around the Prague Castle: Explore the world biggest castle",
        "meeting_point": "Prague Castle", "duration": 150, "max": 20,
        "rating": 8.3, "reviews": 123, "wheelchair": 1, "children": 1, "pet": 1,
        "themes": ["Architectural", "Gastronomic", "Local legends & traditions", "Alternative"],
        "stops": ["Lobkowicz Palace", "St. George's Basilica", "The Golden Lane",
                  "Strahov Monastery", "St. Vitus Cathedral", "Prague Castle"],
        "schedules": [(0, "16:00", "Italian"), (1, "18:00", "Italian"), (2, "09:00", "Spanish"),
                      (3, "17:00", "English"), (4, "11:00", "English")],
        "description": ("Don't forget to check out and possibly book our other tours in the \"Old Town & Jewish "
                        "Quarter\" and the \"New Town\" of Prague.\n\n"
                        "Prague has the largest castle complex in the world. It consists of several palaces, "
                        "churches, gardens, and many other special buildings. Prague Castle has a rich history, and "
                        "you will learn about it during this tour.\n\n"
                        "We start the tour at the Strahov Monastery and then visit all the special buildings in the "
                        "castle, such as St. Vitus Cathedral, St. George's Basilica, the famous Golden Lane, and, of "
                        "course, the Lobkowicz Palace.\n\n"
                        "Of course, also see a big change in the guards. In the summer, we also visit one of the "
                        "well-known special palace gardens. Will you delve with us into the history of the largest "
                        "castle complex in the world?"),
    },
    {
        "guide": 2, "slug": "walking-tour-old-town-jewish-quarter",
        "title": "Walking Tour: Old Town & Jewish Quarter",
        "meeting_point": "Prague Castle", "duration": 90, "max": 14,
        "rating": 8.1, "reviews": 185, "wheelchair": 0, "children": 1, "pet": 1,
        "themes": ["Architectural", "Gastronomic", "Political"],
        "stops": ["Rudolfinum", "The House at the Black Madonna", "Old Town Square",
                  "The Estates Theatre", "Prague Jewish Quarter", "Faculty of Arts",
                  "Týnský dvůr - Ungelt"],
        "schedules": [(0, "12:00", "English"), (2, "18:00", "English"), (4, "18:00", "Italian")],
        "description": ("Come for an immersive experience that tells the history of Prague's Old Town through its "
                        "stories, myths, legends, rumors, and gossip. We'll see the Old Town Square, the "
                        "Astronomical Clock, the oldest university in Central Europe, the Jewish Quarter, a palace "
                        "complex, and then finish at Bethlehem Square.\n\n"
                        "We'll cover the history of the city from the 6th Century, with special emphasis on the "
                        "Middle Ages, where tales abound, and many stories can be told in different ways. We'll also "
                        "go through numerous historic characters, from Emperor Charles IV to the foundational "
                        "religious reformer Jan Hus, to the celebrated writer Franz Kafka. So, please come along; "
                        "there's a lot to tell."),
    },
    {
        "guide": 2, "slug": "prague-free-tour-old-town-jewish-quarter-clock",
        "title": "Prague Free Tour: Old Town & Jewish Quarter, Incl Astronomical Clock",
        "meeting_point": "Rudolfinum", "duration": 120, "max": 10,
        "rating": 8.9, "reviews": 120, "wheelchair": 1, "children": 1, "pet": 0,
        "themes": ["Architectural", "Historical", "Gastronomic"],
        "stops": ["Old Jewish Cemetery", "The Powder Tower", "Old Town Square",
                  "Statue of Franz Kafka", "Prague Astronomical Clock", "Charles University",
                  "The Old-New Synagogue"],
        "schedules": [(3, "11:00", "English"), (3, "20:00", "Italian"), (4, "15:00", "Italian")],
        "description": ("Want to learn more about this fascinating city?\n\n"
                        "Then put aside the travel guide and join us in one of the most enchanting cities in the "
                        "world! Walk through Prague's beautiful streets and enjoy learning about its history.\n\n"
                        "On this tour you will visit the most important monuments of the historical center of "
                        "Prague, you will learn about its history, transcendental characters, and anecdotes that "
                        "will help you understand this city."),
    },
    {
        "guide": 3, "slug": "welcome-to-prague-freetour",
        "title": "Welcome to Prague: Old Town, Jewish Quarter & Charles Bridge Freetour",
        "meeting_point": "In front of the Powder Gate at Na Prikope 28", "duration": 60, "max": 12,
        "rating": 8.8, "reviews": 184, "wheelchair": 1, "children": 0, "pet": 1,
        "themes": ["Historical", "Gastronomic", "Political"],
        "stops": ["Old Town Square", "Prague Jewish Quarter", "Charles Bridge", "John Lennon Wall"],
        "schedules": [(0, "09:00", "English"), (0, "10:30", "Spanish"), (2, "14:00", "German"),
                      (3, "09:30", "English"), (3, "17:00", "Portuguese"), (4, "13:00", "Spanish")],
        "description": ("Do you want to explore Prague with locals and certified expert guides? We've got you "
                        "covered!\n\n"
                        "On this free tour, you will explore the most important parts of Prague's historic center: "
                        "Old Town, the Jewish Quarter, and Charles Bridge. You will learn how to read the "
                        "Astronomical Clock, the significance behind the Czechs' historical tradition of throwing "
                        "people out of windows, and the must-see and must-avoid activities in Prague. You will also "
                        "cross Charles Bridge and finish the tour at the John Lennon Wall.\n\n"
                        "We offer three other free tours in Prague, check out our profile to find out more.\n\n"
                        "IMPORTANT!\nWe cannot wait for the latecomers!\nWe do not go inside the synagogues and the "
                        "Old Jewish Cemetery."),
    },
    {
        "guide": 3, "slug": "classic-prague-castle-free-tour",
        "title": "Classic Prague Castle Free Tour, Strahov Monastery & Castle District",
        "meeting_point": "Josef Manes Statue", "duration": 120, "max": 10,
        "rating": 8.7, "reviews": 198, "wheelchair": 1, "children": 1, "pet": 1,
        "themes": ["Historical", "Gastronomic", "Political", "Local legends & traditions"],
        "stops": ["Prague Castle", "Old Royal Palace", "Strahov Monastery",
                  "St. Vitus Cathedral", "Hradcany Square"],
        "schedules": [(0, "12:30", "Portuguese"), (1, "10:00", "English"), (1, "13:00", "Spanish"),
                      (2, "16:00", "Spanish"), (3, "11:30", "Portuguese"), (4, "10:00", "English")],
        "description": ("The largest castle complex in the world awaits you! No trip to Prague is complete without "
                        "visiting the castle & its fantastic views. We cover every courtyard in the castle complex, "
                        "St. Vitus Cathedral, the best vistas, and the changing of the guards!\n\n"
                        "We start this tour by the river but hop on a tram for a short journey to Prague's Castle "
                        "District. Your guide will cover the royal tales and mysterious histories of the capital.\n\n"
                        "A tram ticket (30czk) is needed for the tour – if you cannot buy before, please arrive "
                        "early to ask your guide for help. Like all free castle tours, we will explore inside the "
                        "castle complex but not the paid museums."),
    },
    {
        "guide": 3, "slug": "panoramic-vltava-river-cruise", "title": "Panoramic Vltava River Cruise",
        "meeting_point": "Look for the boat: Classic River, pier 17, Dvořákovo nábřeží",
        "duration": 90, "max": 15,
        "rating": 8.4, "reviews": 233, "wheelchair": 1, "children": 1, "pet": 1,
        "themes": ["Historical", "Gastronomic", "Local legends & traditions"],
        "stops": ["Prague Castle", "Strahov Monastery", "Charles Bridge", "Dancing House"],
        "schedules": [(0, "15:30", "English"), (1, "16:00", "German"), (2, "09:00", "English"),
                      (2, "11:00", "Portuguese"), (3, "15:00", "Spanish"),
                      (4, "15:00", "English"), (4, "17:30", "Spanish")],
        "description": ("The Panoramic Vltava River Cruise is a 1h 30 min cruise that is created especially for "
                        "families with small children or anyone who wants to sail on the Vltava river and see the "
                        "city from another view, including monuments such as Charles Bridge and Prague Castle.\n\n"
                        "There is a bar on board the boat where you can order cold drinks, coffee, and small "
                        "refreshments, and humble servers that will serve you both from the upper and lower deck.\n\n"
                        "It is also available inside the salon which is air-conditioned in the summertime and heated "
                        "in the wintertime."),
    },
]


def seed_tours():
    """Insert the platform's sample tours. Each tour expects 5 photos named
    tour{n}_{m}.jpg in static/img/tours/ (n = tour number, m = 1..5). Until those
    files are uploaded, a placeholder image is shown automatically."""
    db = get_db()
    for n, t in enumerate(SEED_TOURS, start=1):
        cur = db.execute(
            """
            INSERT INTO tours
            (guide_id, slug, title, description, meeting_point, duration_minutes, max_participants,
             status, wheelchair_accessible, suitable_for_children, pet_friendly, rating, review_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """,
            (t["guide"], t["slug"], t["title"], t["description"], t["meeting_point"],
             t["duration"], t["max"], t["wheelchair"], t["children"], t["pet"], t["rating"], t["reviews"]),
        )
        tour_id = cur.lastrowid
        db.executemany(
            "INSERT INTO tour_themes (tour_id, theme) VALUES (?, ?)",
            [(tour_id, theme) for theme in t["themes"]],
        )
        db.executemany(
            "INSERT INTO tour_stops (tour_id, stop_order, title) VALUES (?, ?, ?)",
            [(tour_id, order, stop) for order, stop in enumerate(t["stops"])],
        )
        db.executemany(
            """
            INSERT INTO tour_schedules
            (tour_id, weekday, start_time, language, duration_minutes, max_participants, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            [(tour_id, wd, start, lang, t["duration"], t["max"]) for wd, start, lang in t["schedules"]],
        )
        db.executemany(
            "INSERT INTO tour_photos (tour_id, image_path, is_cover) VALUES (?, ?, ?)",
            [(tour_id, f"img/tours/tour{n}_{m}.jpg", 1 if m == 1 else 0) for m in range(1, 6)],
        )
    db.commit()
    # Occurrences are created lazily (on booking), so nothing to pre-generate
    # here — the seeded reservations below will materialise the dates they need.


# Sample participants with upcoming reservations. Dates use the week that
# starts Tuesday 30 June 2026 (Tue=06-30, Wed=07-01, Thu=07-02, Fri=07-03,
# and Mon falls on the following Monday 07-06). Each booking is matched to the
# real tour occurrence by tour slug + date + start time + language.
# Each booking is (slug, date, start_time, language, guests) where guests is a
# list of (first, last) for additional people (0-3, so the party stays within
# the 1-4 people limit). Guests are spread across participants with varying
# counts (1, 2 and 3). Dates: Mon=06-29, Tue=06-30, Wed=07-01, Thu=07-02, Fri=07-03.
SEED_PARTICIPANTS = [
    {
        "first": "Anna", "last": "Walker",
        "email": "annawalker@gmail.com", "password": "annaaa1111",
        "bookings": [
            ("complete-prague-tour", "2026-06-29", "09:00", "English",
             [("Liam", "Walker"), ("Sophie", "Walker"), ("Noah", "Brooks")]),
            ("free-tour-new-town-wwii-communism", "2026-06-30", "09:00", "English",
             [("Emma", "Walker")]),
            ("panoramic-vltava-river-cruise", "2026-07-01", "09:00", "English", []),
            ("prague-free-tour-old-town-jewish-quarter-clock", "2026-07-02", "11:00", "English", []),
            ("classic-prague-castle-free-tour", "2026-07-03", "10:00", "English", []),
            # Sunday 5 July departure used to fill "Original Free Tour" to capacity.
            ("original-free-tour-of-prague", "2026-07-05", "10:00", "English",
             [("Nora", "Klein"), ("Aldo", "Ricci"), ("Sven", "Park")]),
        ],
    },
    {
        "first": "Martin", "last": "Cerny",
        "email": "martincerny@gmail.com", "password": "ghostmarty007",
        "bookings": [
            ("free-tour-new-town-wwii-communism", "2026-06-29", "10:00", "Spanish", []),
            ("original-free-tour-of-prague", "2026-06-30", "10:00", "Spanish",
             [("Petra", "Cerny"), ("Jakub", "Cerny")]),
            ("free-tour-around-prague-castle", "2026-07-02", "17:00", "English", []),
            ("welcome-to-prague-freetour", "2026-07-03", "13:00", "Spanish",
             [("Lucie", "Novak"), ("Tomas", "Marek"), ("Eva", "Cerny")]),
        ],
    },
    {
        "first": "Teresa", "last": "Dvorazoka",
        "email": "dvorazoka.teresa@gmail.com", "password": "teresaflyinginsky",
        "bookings": [
            ("free-tour-around-prague-castle", "2026-06-29", "16:00", "Italian",
             [("Elena", "Dvorazoka")]),
            ("panoramic-vltava-river-cruise", "2026-06-30", "16:00", "German",
             [("Marco", "Rossi"), ("Giulia", "Bianchi")]),
            ("prague-free-tour-old-town-jewish-quarter-clock", "2026-07-03", "15:00", "Italian", []),
            ("original-free-tour-of-prague", "2026-07-05", "10:00", "English",
             [("Ivana", "Krause"), ("Diego", "Lupo"), ("Mira", "Sole")]),
        ],
    },
    {
        "first": "Adela", "last": "Vesela",
        "email": "adela.vesela@gmail.com", "password": "ADELAsinging1234",
        "bookings": [
            ("classic-prague-castle-free-tour", "2026-06-29", "12:30", "Portuguese", []),
            ("complete-prague-tour", "2026-07-03", "18:00", "Portuguese",
             [("Karel", "Vesely"), ("Marie", "Vesela"), ("Jan", "Horak")]),
            ("original-free-tour-of-prague", "2026-07-05", "10:00", "English",
             [("Petr", "Blazek")]),
        ],
    },
]


def seed_participants():
    """Insert the sample participants and their upcoming reservations (some with guests)."""
    db = get_db()
    for p in SEED_PARTICIPANTS:
        cur = db.execute(
            "INSERT INTO participants (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (p["first"], p["last"], p["email"], generate_password_hash(p["password"])),
        )
        participant_id = cur.lastrowid
        for slug, date, start_time, language, guests in p["bookings"]:
            hours, minutes = map(int, start_time.split(":"))
            year, month, day = map(int, date.split("-"))
            starts_at = datetime(year, month, day, hours, minutes)
            # Match the schedule by weekday too: a tour may run the same time +
            # language on several weekdays, so start_time + language alone is
            # ambiguous.
            schedule = db.execute(
                """
                SELECT s.id
                FROM tour_schedules s
                JOIN tours t ON t.id = s.tour_id
                WHERE t.slug = ? AND s.start_time = ? AND s.language = ? AND s.weekday = ?
                LIMIT 1
                """,
                (slug, start_time, language, starts_at.weekday()),
            ).fetchone()
            if schedule is None:
                raise ValueError(f"No schedule for {slug} on {date} ({start_time} {language})")
            occurrence_id = get_or_create_occurrence(schedule["id"], starts_at)
            res = db.execute(
                "INSERT INTO reservations (participant_id, occurrence_id, status) VALUES (?, ?, 'active')",
                (participant_id, occurrence_id),
            )
            db.executemany(
                "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?, ?, ?)",
                [(res.lastrowid, gf, gl) for gf, gl in guests],
            )
    db.commit()


# Two extra participants whose bookings live in the PAST, so the instructor can
# test the post-tour reporting flow without waiting for a real date to pass.
# Each tuple is (slug, language, start_time, weeks_ago, guests, attended):
#   - weeks_ago: how many weeks before today the departure took place (lands in
#     the previous month).
#   - guests: extra people on the reservation.
#   - attended: how many actually showed up (drives the guide's report).
SEED_PAST_PARTICIPANTS = [
    {
        "first": "Lukas", "last": "Horak",
        "email": "lukas.horak@gmail.com", "password": "lukaspast2026",
        "reported": [
            ("complete-prague-tour", "English", "09:00", 6,
             [("Eva", "Horak")], 2, "img/reports/report-lukas-complete-prague-tour.jpg"),
            ("free-tour-around-prague-castle", "English", "17:00", 5,
             [("Petr", "Horak"), ("Jana", "Horak")], 3, "img/reports/report-lukas-prague-castle.jpg"),
            ("panoramic-vltava-river-cruise", "English", "09:00", 4,
             [], 1, "img/reports/report-lukas-vltava-cruise.jpg"),
        ],
    },
    {
        "first": "Marie", "last": "Kralova",
        "email": "marie.kralova@gmail.com", "password": "mariepast2026",
        "reported": [
            ("welcome-to-prague-freetour", "Spanish", "13:00", 6,
             [("Anna", "Kralova"), ("Jakub", "Kral")], 3, "img/reports/report-marie-welcome-prague.jpg"),
            ("free-tour-new-town-wwii-communism", "English", "09:00", 5,
             [("Tomas", "Kral")], 2, "img/reports/report-marie-newtown-communism.jpg"),
            ("original-free-tour-of-prague", "English", "17:00", 4,
             [], 1, "img/reports/report-marie-original-free-tour.jpg"),
        ],
    },
]

# Departures whose most recent occurrence has already STARTED (within the last
# week) but are not yet reported, so the guide's "Mark as done" button is live
# for them. (slug, language, start_time, booker_email, guests).
SEED_MARKABLE = [
    ("classic-prague-castle-free-tour", "English", "10:00", "lukas.horak@gmail.com",
     [("Eva", "Horak")]),
    ("complete-prague-tour", "English", "11:00", "marie.kralova@gmail.com",
     [("Jakub", "Kral")]),
]


def _schedule_for(slug, language, start_time):
    """Resolve the single tour_schedule matching (slug, language, start_time)."""
    schedule = get_db().execute(
        """
        SELECT s.id, s.weekday, s.tour_id
        FROM tour_schedules s JOIN tours t ON t.id = s.tour_id
        WHERE t.slug = ? AND s.language = ? AND s.start_time = ?
        LIMIT 1
        """,
        (slug, language, start_time),
    ).fetchone()
    if schedule is None:
        raise ValueError(f"No schedule for {slug} {start_time} {language}")
    return schedule


def _past_starts_at(weekday, start_time, weeks_ago):
    """A concrete datetime ``weeks_ago`` weeks before today, on the schedule's
    weekday and start time (so it matches a real recurring departure)."""
    hours, minutes = map(int, start_time.split(":"))
    now = datetime.now()
    days_back = (now.weekday() - weekday) % 7
    recent = (now - timedelta(days=days_back)).replace(
        hour=hours, minute=minutes, second=0, microsecond=0
    )
    return recent - timedelta(weeks=weeks_ago)


def _recent_started_starts_at(weekday, start_time):
    """The most recent departure on the schedule's weekday that has already
    started (strictly in the past, within the last 7 days)."""
    hours, minutes = map(int, start_time.split(":"))
    now = datetime.now()
    days_back = (now.weekday() - weekday) % 7
    candidate = (now - timedelta(days=days_back)).replace(
        hour=hours, minute=minutes, second=0, microsecond=0
    )
    if candidate >= now:  # today's slot hasn't started yet (or is in the future)
        candidate -= timedelta(days=7)
    return candidate


def seed_past_data():
    """Seed the two past-data participants: completed + reported tours (for Tours
    History and Past Reports) and a couple of this-week departures whose guides
    can still click "Mark as done"."""
    db = get_db()

    def participant_id_for(email):
        return db.execute("SELECT id FROM participants WHERE email = ?", (email,)).fetchone()["id"]

    # --- Past, reported departures (Tours History + Past Reports) ---
    for person in SEED_PAST_PARTICIPANTS:
        cur = db.execute(
            "INSERT INTO participants (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (person["first"], person["last"], person["email"], generate_password_hash(person["password"])),
        )
        participant_id = cur.lastrowid
        for slug, language, start_time, weeks_ago, guests, attended, photo in person["reported"]:
            schedule = _schedule_for(slug, language, start_time)
            starts_at = _past_starts_at(schedule["weekday"], start_time, weeks_ago)
            occurrence_id = get_or_create_occurrence(schedule["id"], starts_at)
            # The tour already took place: mark it done so it leaves the timetable
            # and moves into Tours History.
            db.execute(
                "UPDATE tour_occurrences SET finished = 1, status = 'finished' WHERE id = ?",
                (occurrence_id,),
            )
            res = db.execute(
                "INSERT INTO reservations (participant_id, occurrence_id, status) VALUES (?, ?, 'active')",
                (participant_id, occurrence_id),
            )
            db.executemany(
                "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?, ?, ?)",
                [(res.lastrowid, gf, gl) for gf, gl in guests],
            )
            guide_id = db.execute("SELECT guide_id FROM tours WHERE slug = ?", (slug,)).fetchone()["guide_id"]
            expected = reservation_count_for_occurrence(occurrence_id)
            # File the post-tour report (attendance + evidence photo).
            db.execute(
                """
                INSERT OR REPLACE INTO guide_reports
                (occurrence_id, guide_id, expected_participants, actual_participants,
                 evidence_photo_path, status, finished)
                VALUES (?, ?, ?, ?, ?, 'pending', 1)
                """,
                (occurrence_id, guide_id, expected, attended, photo),
            )

    # --- This-week departures still awaiting "Mark as done" ---
    for slug, language, start_time, email, guests in SEED_MARKABLE:
        schedule = _schedule_for(slug, language, start_time)
        starts_at = _recent_started_starts_at(schedule["weekday"], start_time)
        occurrence_id = get_or_create_occurrence(schedule["id"], starts_at)
        res = db.execute(
            "INSERT INTO reservations (participant_id, occurrence_id, status) VALUES (?, ?, 'active')",
            (participant_id_for(email), occurrence_id),
        )
        db.executemany(
            "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?, ?, ?)",
            [(res.lastrowid, gf, gl) for gf, gl in guests],
        )
    db.commit()


# ---------------------------------------------------------------------------
# Lazy occurrences
#
# A tour_occurrence (a dated instance of a recurring weekly schedule) is NOT
# pre-generated for every possible date. Instead the bookable dates shown to
# visitors are computed on the fly from the weekly rules, and an occurrence row
# is materialised only when it is actually needed — i.e. when a participant
# books that date (or the guide marks it done). This keeps the table small even
# with thousands of tours and means the calendar never runs out of future dates.
# ---------------------------------------------------------------------------

def tour_schedule_departures(tour_id, days_forward=120, from_dt=None):
    """Compute the upcoming departures for a tour straight from its weekly
    schedule. Returns a list of ``(schedule_row, starts_at_datetime)`` ordered by
    date — no occurrence rows are read or created."""
    db = get_db()
    now = from_dt or datetime.now()
    horizon = now + timedelta(days=days_forward)
    schedules = db.execute(
        "SELECT * FROM tour_schedules WHERE tour_id = ? AND active = 1",
        (tour_id,),
    ).fetchall()
    departures = []
    for schedule in schedules:
        hours, minutes = map(int, schedule["start_time"].split(":"))
        # First matching weekday on/after today, then step forward a week at a time.
        days_ahead = (schedule["weekday"] - now.weekday()) % 7
        current = (now + timedelta(days=days_ahead)).replace(
            hour=hours, minute=minutes, second=0, microsecond=0
        )
        while current <= horizon:
            if current > now:
                departures.append((schedule, current))
            current += timedelta(days=7)
    departures.sort(key=lambda pair: pair[1])
    return departures


def reservation_people_for_slot(schedule_id, starts_at_iso):
    """People (participants + guests) already booked on a departure identified by
    (schedule, start datetime). A slot with no occurrence row yet returns 0."""
    row = get_db().execute(
        """
        SELECT
            (SELECT COUNT(*)
             FROM reservations r
             JOIN tour_occurrences o ON o.id = r.occurrence_id
             WHERE o.schedule_id = ? AND o.starts_at = ? AND r.status = 'active')
            +
            (SELECT COUNT(g.id)
             FROM reservation_guests g
             JOIN reservations r ON r.id = g.reservation_id
             JOIN tour_occurrences o ON o.id = r.occurrence_id
             WHERE o.schedule_id = ? AND o.starts_at = ? AND r.status = 'active')
        AS people
        """,
        (schedule_id, starts_at_iso, schedule_id, starts_at_iso),
    ).fetchone()
    return row["people"] or 0


def get_or_create_occurrence(schedule_id, starts_at):
    """Return the occurrence id for (schedule, start datetime), creating the row
    on demand. Validates that the date actually belongs to the schedule so a
    visitor cannot book an arbitrary date. Does not commit — the caller does."""
    db = get_db()
    schedule = db.execute(
        "SELECT * FROM tour_schedules WHERE id = ? AND active = 1", (schedule_id,)
    ).fetchone()
    if schedule is None:
        raise ValueError("Departure not found.")
    hours, minutes = map(int, schedule["start_time"].split(":"))
    if starts_at.weekday() != schedule["weekday"] or (starts_at.hour, starts_at.minute) != (hours, minutes):
        raise ValueError("That date is not part of this tour's schedule.")
    starts_iso = starts_at.replace(second=0, microsecond=0).isoformat()
    ends_iso = (starts_at.replace(second=0, microsecond=0)
                + timedelta(minutes=schedule["duration_minutes"])).isoformat()
    db.execute(
        """
        INSERT OR IGNORE INTO tour_occurrences
        (schedule_id, starts_at, ends_at, max_participants, status)
        VALUES (?, ?, ?, ?, 'scheduled')
        """,
        (schedule_id, starts_iso, ends_iso, schedule["max_participants"]),
    )
    return db.execute(
        "SELECT id FROM tour_occurrences WHERE schedule_id = ? AND starts_at = ?",
        (schedule_id, starts_iso),
    ).fetchone()["id"]


def full_name(row):
    return f"{row['first_name']} {row['last_name']}"


def duration_label(minutes):
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}min" if hours else f"{mins} min"


def guide_languages_list(guide_id):
    return [r["language"] for r in get_db().execute(
        "SELECT language FROM guide_languages WHERE guide_id = ? ORDER BY language", (guide_id,)
    ).fetchall()]


def guide_specialties_list(guide_id):
    return [r["specialty"] for r in get_db().execute(
        "SELECT specialty FROM guide_specialties WHERE guide_id = ? ORDER BY specialty", (guide_id,)
    ).fetchall()]


def fetch_tour_by_slug(slug):
    return get_db().execute(
        """
        SELECT t.*, g.rating_average, g.total_reviews, g.profile_photo,
               g.active_since, g.guests_guided, g.first_name, g.last_name, g.email AS guide_email
        FROM tours t
        JOIN guides g ON g.id = t.guide_id
        WHERE t.slug = ?
        """,
        (slug,),
    ).fetchone()


def tour_cover(tour_id):
    row = get_db().execute(
        "SELECT image_path FROM tour_photos WHERE tour_id = ? ORDER BY is_cover DESC, id LIMIT 1",
        (tour_id,),
    ).fetchone()
    # A tour always has 5 photos (enforced on create/edit), so the fallback is
    # effectively unreachable; it points at the same placeholder as DEFAULT_TOUR_IMAGE.
    return row["image_path"] if row else "img/prague-castle.svg"


def tour_languages(tour_id):
    rows = get_db().execute(
        "SELECT DISTINCT language FROM tour_schedules WHERE tour_id = ? ORDER BY language",
        (tour_id,),
    ).fetchall()
    return [row["language"] for row in rows]


def get_public_tours():
    db = get_db()
    rows = db.execute(
        """
        SELECT t.*, g.rating_average, g.total_reviews, g.profile_photo, g.first_name, g.last_name
        FROM tours t
        JOIN guides g ON g.id = t.guide_id
        WHERE t.status = 'active'
        ORDER BY t.id
        """
    ).fetchall()
    tours = []
    for row in rows:
        # Upcoming departures derived from the weekly schedule (lazy model).
        departures = tour_schedule_departures(row["id"])
        dates = sorted({dt.strftime("%Y-%m-%d") for _, dt in departures})
        start_times = sorted({sch["start_time"] for sch, _ in departures})

        # People already booked on this tour's existing occurrences (one query),
        # so remaining places per date can be computed without a query per slot.
        booked_map = {}
        for occ in db.execute(
            """
            SELECT o.schedule_id, o.starts_at,
                (SELECT COUNT(*) FROM reservations r
                 WHERE r.occurrence_id = o.id AND r.status = 'active')
                + (SELECT COUNT(g.id) FROM reservation_guests g
                   JOIN reservations r ON r.id = g.reservation_id
                   WHERE r.occurrence_id = o.id AND r.status = 'active') AS people
            FROM tour_occurrences o
            JOIN tour_schedules s ON s.id = o.schedule_id
            WHERE s.tour_id = ?
            """,
            (row["id"],),
        ).fetchall():
            booked_map[(occ["schedule_id"], occ["starts_at"])] = occ["people"]

        # Remaining places per calendar date = best (max) across that date's
        # departures. The homepage availability filter evaluates this map against
        # the selected date range, so it only becomes meaningful once a date range
        # narrows the window (otherwise some far-off date is always free).
        availability_by_date = {}
        for schedule, dt in departures:
            booked = booked_map.get((schedule["id"], dt.isoformat()), 0)
            left = max(0, schedule["max_participants"] - booked)
            key = dt.strftime("%Y-%m-%d")
            if left > availability_by_date.get(key, -1):
                availability_by_date[key] = left
        places_left = max(availability_by_date.values()) if availability_by_date else 0

        themes = [
            th["theme"]
            for th in db.execute("SELECT theme FROM tour_themes WHERE tour_id = ?", (row["id"],)).fetchall()
        ]
        accessibility = []
        if row["wheelchair_accessible"]:
            accessibility.append("Wheelchair accessible")
        if row["suitable_for_children"]:
            accessibility.append("Suitable for children")
        if row["pet_friendly"]:
            accessibility.append("Pet friendly")

        tours.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "description": row["description"],
                "rating": f"{row['rating']:.1f}",
                "reviews": row["review_count"],
                "duration": duration_label(row["duration_minutes"]),
                "duration_minutes": row["duration_minutes"],
                "meeting_point": row["meeting_point"],
                "languages": tour_languages(row["id"]),
                "dates": dates,
                "start_times": start_times,
                "places_left": max(0, places_left),
                "availability_by_date": availability_by_date,
                "themes": themes,
                "accessibility": accessibility,
                "guide": full_name(row),
                "guide_photo": get_profile_photo_url(row["profile_photo"]),
                "image": resolve_tour_image(tour_cover(row["id"])),
            }
        )
    return tours


LANGUAGE_CODES = {
    "English": "en", "German": "de", "Spanish": "es",
    "Italian": "it", "Portuguese": "pt", "French": "fr",
}


def flag_url(language):
    """URL of the circular flag image for a language."""
    return f"/static/img/flags/{LANGUAGE_CODES.get(language, 'xx')}.svg"


def get_tour_detail(slug):
    """Return the full, DB-driven detail for a single tour, or None if the slug
    does not exist (the caller turns that into a 404)."""
    db = get_db()
    row = fetch_tour_by_slug(slug)
    if row is None:
        return None

    gallery = [
        resolve_tour_image(photo["image_path"])
        for photo in db.execute(
            "SELECT image_path FROM tour_photos WHERE tour_id = ? ORDER BY is_cover DESC, id",
            (row["id"],),
        )
    ]

    stops = [
        stop["title"]
        for stop in db.execute(
            "SELECT title FROM tour_stops WHERE tour_id = ? ORDER BY stop_order",
            (row["id"],),
        ).fetchall()
    ]

    # Calendar availability: every upcoming departure within a wide window,
    # grouped by date. Dates come from the weekly schedule (lazy model); a date
    # is identified to the booking endpoint by (schedule_id, date) rather than a
    # pre-existing occurrence row. We pre-fetch the people already booked on this
    # tour's *existing* occurrences in one query, so remaining capacity is exact
    # without a query per date.
    now = datetime.now()
    booked_map = {}
    for occ in db.execute(
        """
        SELECT o.schedule_id, o.starts_at,
            (SELECT COUNT(*) FROM reservations r
             WHERE r.occurrence_id = o.id AND r.status = 'active')
            + (SELECT COUNT(g.id) FROM reservation_guests g
               JOIN reservations r ON r.id = g.reservation_id
               WHERE r.occurrence_id = o.id AND r.status = 'active') AS people
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        WHERE s.tour_id = ?
        """,
        (row["id"],),
    ).fetchall():
        booked_map[(occ["schedule_id"], occ["starts_at"])] = occ["people"]

    availability = {}
    for schedule, starts_at in tour_schedule_departures(row["id"], days_forward=120, from_dt=now):
        starts_iso = starts_at.isoformat()
        reserved = booked_map.get((schedule["id"], starts_iso), 0)
        available_left = max(0, schedule["max_participants"] - reserved)
        language = schedule["language"]
        date_key = starts_at.strftime("%Y-%m-%d")
        availability.setdefault(date_key, []).append(
            {
                "schedule_id": schedule["id"],
                "date": date_key,
                "time": starts_at.strftime("%-I:%M %p"),
                "language": language,
                "flag": flag_url(language),
                "left": available_left,
                "max": schedule["max_participants"],
                "date_label": starts_at.strftime("%a, %-d %B %Y"),
                "summary": f"{starts_at.strftime('%a, %B %-d, %Y')} · {starts_at.strftime('%-I:%M %p')} · {language}",
            }
        )

    DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_schedule = [
        {
            "weekday": DAYS_OF_WEEK[sch["weekday"]] if 0 <= sch["weekday"] < 7 else "—",
            "start_time": datetime.strptime(sch["start_time"], "%H:%M").strftime("%-I:%M %p"),
            "language": sch["language"],
            "flag": flag_url(sch["language"]),
        }
        for sch in db.execute(
            "SELECT weekday, start_time, language FROM tour_schedules WHERE tour_id = ? AND active = 1 ORDER BY weekday, start_time",
            (row["id"],),
        ).fetchall()
    ]

    guide_langs = guide_languages_list(row["guide_id"])
    specialties = guide_specialties_list(row["guide_id"])
    guide_tour_count = db.execute(
        "SELECT COUNT(*) FROM tours WHERE guide_id = ?", (row["guide_id"],)
    ).fetchone()[0]
    # Real "guests guided" = total participants who actually attended this
    # guide's reported tours.
    guide_guests_count = db.execute(
        "SELECT COALESCE(SUM(actual_participants), 0) FROM guide_reports WHERE guide_id = ? AND actual_participants >= 1",
        (row["guide_id"],),
    ).fetchone()[0]

    # The guide's other active tours (for the "More Tours by ..." section).
    more_tours = []
    for other in db.execute(
        "SELECT id, slug, title, duration_minutes FROM tours WHERE guide_id = ? AND id != ? AND status = 'active' ORDER BY id",
        (row["guide_id"], row["id"]),
    ).fetchall():
        other_langs = tour_languages(other["id"])
        more_tours.append({
            "slug": other["slug"],
            "title": other["title"],
            "image": resolve_tour_image(tour_cover(other["id"])),
            "flags": [flag_url(lang) for lang in other_langs],
            "duration": duration_label(other["duration_minutes"]),
        })

    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "provider": "Walk Prague",
        "description": row["description"],
        "guide": full_name(row),
        "guide_photo": get_profile_photo_url(row["profile_photo"]),
        "guide_languages": [{"name": lang, "flag": flag_url(lang)} for lang in guide_langs],
        "guide_specialty": ", ".join(specialties),
        "guide_active_since": row["active_since"],
        "guide_tour_count": guide_tour_count,
        "guide_guests": f"{guide_guests_count:,}",
        "guide_rating": f"{row['rating_average']:.1f}",
        "guide_reviews": str(row["total_reviews"]),
        "more_tours": more_tours,
        "rating": f"{row['rating']:.1f}",
        "reviews": str(row["review_count"]),
        "duration": duration_label(row["duration_minutes"]),
        "duration_minutes": row["duration_minutes"],
        "max_participants": row["max_participants"],
        "meeting_point": row["meeting_point"],
        "languages": ", ".join(tour_languages(row["id"])),
        "guide_email": row["guide_email"],
        "image": gallery[0] if gallery else DEFAULT_TOUR_IMAGE,
        "gallery": gallery or [DEFAULT_TOUR_IMAGE],
        "stops": stops,
        "weekly_schedule": weekly_schedule,
        "availability": availability,
        "has_availability": bool(availability),
        "today": now.strftime("%Y-%m-%d"),
        "accessibility": {
            "wheelchair_accessible": bool(row["wheelchair_accessible"]),
            "suitable_for_children": bool(row["suitable_for_children"]),
            "pet_friendly": bool(row["pet_friendly"]),
        },
    }


def participant_dashboard_data(participant_id):
    """Return dashboard data for the participant identified by participants.id."""
    db = get_db()
    user = db.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
    reservations = db.execute(
        """
        SELECT r.id, r.status, o.starts_at, t.title, t.slug, t.meeting_point, s.language
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE r.participant_id = ? AND r.status = 'active'
        ORDER BY o.starts_at DESC
        """,
        (participant_id,),
    ).fetchall()
    items = []
    now = datetime.now()
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
    """Total number of people (primary participants + guests) for an occurrence."""
    row = get_db().execute(
        """
        SELECT
            (SELECT COUNT(*)
             FROM reservations
             WHERE occurrence_id = ? AND status = 'active')
            +
            (SELECT COUNT(g.id)
             FROM reservation_guests g
             JOIN reservations r ON r.id = g.reservation_id
             WHERE r.occurrence_id = ? AND r.status = 'active')
        AS people
        """,
        (occurrence_id, occurrence_id),
    ).fetchone()
    return row["people"] or 0


def occurrence_attendees(occurrence_id):
    """List of {participant, email, guests, total_spots} for an occurrence."""
    db = get_db()
    res_rows = db.execute(
        """
        SELECT r.id, p.first_name, p.last_name, p.email
        FROM reservations r
        JOIN participants p ON p.id = r.participant_id
        WHERE r.occurrence_id = ? AND r.status = 'active'
        ORDER BY r.id
        """,
        (occurrence_id,),
    ).fetchall()
    attendees = []
    for res in res_rows:
        guests = db.execute(
            "SELECT first_name, last_name FROM reservation_guests WHERE reservation_id = ?",
            (res["id"],),
        ).fetchall()
        attendees.append({
            "participant": f"{res['first_name']} {res['last_name']}",
            "email": res["email"],
            "guests": [f"{g['first_name']} {g['last_name']}" for g in guests],
            "total_spots": 1 + len(guests),
        })
    return attendees


def guide_dashboard_data(guide_id):
    """Return dashboard data for the guide identified by guides.id."""
    db = get_db()
    guide = db.execute("SELECT * FROM guides WHERE id = ?", (guide_id,)).fetchone()
    if guide is None:
        return {
            "name": "", "email": "", "rating": "—",
            "profile_photo": "/static/img/default-profile.png",
            "active_tours": 0, "total_participants": 0, "total_bookings": 0,
            "tours_reported": 0, "total_reviews": 0, "tours": [],
            "pending_reports": [], "past_reports": [], "tours_history": [],
            "existing_schedules": [], "upcoming_departures": 0,
            "pending_reports_count": 0, "avg_group_size": 0, "specialty": "",
        }

    tours = db.execute("SELECT * FROM tours WHERE guide_id = ? ORDER BY id", (guide_id,)).fetchall()
    tour_items = []
    now = datetime.now()
    DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for tour in tours:
        schedules = db.execute(
            """
            SELECT o.id AS occurrence_id, o.starts_at, o.max_participants, o.finished,
                   s.language, s.duration_minutes
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
            starts_at = datetime.fromisoformat(schedule["starts_at"])
            started = starts_at <= now
            finished = bool(schedule["finished"])
            schedule_items.append(
                {
                    "occurrence_id": schedule["occurrence_id"],
                    "date": starts_at.strftime("%a, %B %-d, %Y"),
                    "time": starts_at.strftime("%-I:%M %p"),
                    "language": schedule["language"],
                    "reserved_groups": groups,
                    "expected": people,
                    "max_participants": schedule["max_participants"],
                    "state": "completed" if starts_at < now else "upcoming",
                    "started": started,
                    "finished": finished,
                    "can_mark_done": started and not finished,
                    "reservations": occurrence_attendees(schedule["occurrence_id"]),
                }
            )

        stops = [
            stop_row["title"]
            for stop_row in db.execute(
                "SELECT title FROM tour_stops WHERE tour_id = ? ORDER BY stop_order",
                (tour["id"],)
            ).fetchall()
        ]
        accessibility = {
            "wheelchair_accessible": bool(tour["wheelchair_accessible"]),
            "suitable_for_children": bool(tour["suitable_for_children"]),
            "pet_friendly": bool(tour["pet_friendly"]),
        }
        weekly_schedules = [
            {
                "weekday": DAYS_OF_WEEK[sch_row["weekday"]] if 0 <= sch_row["weekday"] < 7 else "Monday",
                "start_time": sch_row["start_time"],
                "language": sch_row["language"],
                "duration_minutes": sch_row["duration_minutes"],
                "max_participants": sch_row["max_participants"],
            }
            for sch_row in db.execute(
                "SELECT * FROM tour_schedules WHERE tour_id = ? AND active = 1 ORDER BY weekday, start_time",
                (tour["id"],)
            ).fetchall()
        ]

        photos = [
            {"id": p["id"], "url": resolve_tour_image(p["image_path"])}
            for p in db.execute(
                "SELECT id, image_path FROM tour_photos WHERE tour_id = ? ORDER BY is_cover DESC, id",
                (tour["id"],),
            ).fetchall()
        ]

        tour_items.append(
            {
                "title": tour["title"],
                "slug": tour["slug"],
                "status": tour["status"].title(),
                "languages": ", ".join(tour_languages(tour["id"])),
                "meeting_point": tour["meeting_point"],
                "duration_minutes": tour["duration_minutes"],
                "max_participants": tour["max_participants"],
                "image": resolve_tour_image(tour_cover(tour["id"])),
                "themes": [r["theme"] for r in db.execute("SELECT theme FROM tour_themes WHERE tour_id = ?", (tour["id"],))],
                "schedules": schedule_items,
                "description": tour["description"],
                "stops": stops,
                "accessibility": accessibility,
                "weekly_schedules": weekly_schedules,
                "photos": photos,
            }
        )

    # Report-based aggregates (all real, derived from filed reports):
    #   tours_reported  = number of tours the guide reported (that actually ran)
    #   total_attendees = sum of actual participants across those reports
    report_stats = db.execute(
        """
        SELECT COUNT(*) AS reported, COALESCE(SUM(actual_participants), 0) AS attendees
        FROM guide_reports
        WHERE guide_id = ? AND actual_participants >= 1
        """,
        (guide_id,),
    ).fetchone()
    reports = report_stats["reported"]
    total_attendees = report_stats["attendees"]

    # Total scheduled departures the guide has created (all dated occurrences).
    total_scheduled = db.execute(
        """
        SELECT COUNT(o.id)
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE t.guide_id = ?
        """,
        (guide_id,),
    ).fetchone()[0]

    profile_photo = get_profile_photo_url(guide["profile_photo"])
    guide_langs = guide_languages_list(guide_id)
    specialties = guide_specialties_list(guide_id)

    # -----------------------------------------------------------------------
    # Tours History / Pending reports / Past reports are driven by the
    # "finished" flag, which the guide sets by clicking "Mark as done".
    # -----------------------------------------------------------------------
    pending_reports = []
    past_reports = []
    tours_history = []
    finished_occurrences = db.execute(
        """
        SELECT o.id AS occurrence_id, o.starts_at, o.max_participants,
               s.language, t.title
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE t.guide_id = ? AND o.finished = 1
        ORDER BY o.starts_at DESC
        """,
        (guide_id,),
    ).fetchall()

    for occ in finished_occurrences:
        expected = reservation_count_for_occurrence(occ["occurrence_id"])
        starts_at = datetime.fromisoformat(occ["starts_at"])
        date_str = starts_at.strftime("%a, %B %-d, %Y @ %I:%M %p")
        report_row = db.execute(
            "SELECT * FROM guide_reports WHERE occurrence_id = ?",
            (occ["occurrence_id"],),
        ).fetchone()

        # Tours History: every finished tour, with who was present.
        tours_history.append({
            "occurrence_id": occ["occurrence_id"],
            "title": occ["title"],
            "date": date_str,
            "language": occ["language"],
            "expected": expected,
            "attendees": occurrence_attendees(occ["occurrence_id"]),
            "reported": report_row is not None,
            "actual": report_row["actual_participants"] if report_row else None,
        })

        # Pending report: finished tour with reservations and no report yet.
        if report_row is None:
            if expected >= 1:
                pending_reports.append({
                    "occurrence_id": occ["occurrence_id"],
                    "title": occ["title"],
                    "date": date_str,
                    "language": occ["language"],
                    "expected": expected,
                })
        elif report_row["finished"] and report_row["actual_participants"] >= 1:
            past_reports.append({
                "occurrence_id": occ["occurrence_id"],
                "title": occ["title"],
                "date": date_str,
                "language": occ["language"],
                "expected": report_row["expected_participants"],
                "actual": report_row["actual_participants"],
                "status": report_row["status"],
                "evidence_photo": report_row["evidence_photo_path"],
            })

    all_existing_schedules = []
    upcoming_schedules = 0
    booked_departures = 0
    for tour in tour_items:
        for schedule in tour["schedules"]:
            # Upcoming Schedules = future, not-yet-done departures that have at
            # least one participant booked. Past departures do not count.
            if schedule["state"] == "upcoming" and not schedule["finished"] and schedule["expected"] > 0:
                upcoming_schedules += 1
            if schedule["expected"] > 0:
                booked_departures += 1
        for sch in tour["weekly_schedules"]:
            all_existing_schedules.append({
                "tour": tour["slug"],
                "day": sch["weekday"],
                "start": sch["start_time"],
                "duration": sch["duration_minutes"],
                "language": sch["language"],
            })

    # Average group size = total attendees that actually showed up, divided by
    # the number of reported (completed) tours.
    avg_group_size = round(total_attendees / reports, 1) if reports else 0

    return {
        "name": full_name(guide),
        "email": guide["email"],
        "rating": f"{guide['rating_average']:.1f}/10" if guide["rating_average"] else "—",
        "profile_photo": profile_photo,
        "active_tours": len(tour_items),
        "total_participants": total_attendees,
        "total_bookings": total_scheduled,
        "tours_reported": reports,
        "total_reviews": guide["total_reviews"],
        "upcoming_departures": upcoming_schedules,
        "booked_departures": booked_departures,
        "pending_reports_count": len(pending_reports),
        "avg_group_size": avg_group_size,
        "specialty": ", ".join(specialties),
        "active_since": guide["active_since"],
        "languages": ", ".join(guide_langs),
        "languages_list": guide_langs,
        "specialties_list": specialties,
        "tours": tour_items,
        "pending_reports": pending_reports,
        "past_reports": past_reports,
        "tours_history": tours_history,
        "existing_schedules": all_existing_schedules,
    }


def admin_dashboard_data():
    db = get_db()
    guide_count = db.execute("SELECT COUNT(*) FROM guides").fetchone()[0]
    participant_count = db.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
    tour_count = db.execute("SELECT COUNT(*) FROM tours").fetchone()[0]
    reservation_count = db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    report_count = db.execute("SELECT COUNT(*) FROM guide_reports").fetchone()[0]
    # Total walkers = participants (1 per active reservation) + their guests.
    people_count = (
        db.execute("SELECT COUNT(*) FROM reservations WHERE status = 'active'").fetchone()[0]
        + db.execute(
            "SELECT COUNT(*) FROM reservation_guests g JOIN reservations r ON r.id = g.reservation_id WHERE r.status = 'active'"
        ).fetchone()[0]
    )
    # Reservations per language (counts reservation records, so they sum to the
    # total reservation count shown next to the breakdown).
    language_rows = db.execute(
        """
        SELECT s.language, COUNT(DISTINCT r.id) AS count
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        WHERE r.status = 'active'
        GROUP BY s.language
        ORDER BY count DESC
        """
    ).fetchall()
    active_reservation_count = db.execute("SELECT COUNT(*) FROM reservations WHERE status = 'active'").fetchone()[0]
    accents = ["blue", "green", "purple", "orange", "cyan"]
    flags = {"English": "🇬🇧", "German": "🇩🇪", "Spanish": "🇪🇸", "French": "🇫🇷", "Portuguese": "🇵🇹", "Italian": "🇮🇹"}
    languages = [
        {
            "name": row["language"],
            "flag": flags.get(row["language"], "🏳"),
            "count": row["count"],
            "accent": accents[index % len(accents)],
            "percent": min(100, int((row["count"] / max(active_reservation_count, 1)) * 100)),
        }
        for index, row in enumerate(language_rows)
    ]
    if not any(item["name"] == "Portuguese" for item in languages):
        languages.append({"name": "Portuguese", "flag": "🇵🇹", "count": 0, "accent": "cyan", "percent": 0})

    guides = []
    for guide in db.execute("SELECT * FROM guides ORDER BY id").fetchall():
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
        langs = guide_languages_list(guide["id"])
        specialties = guide_specialties_list(guide["id"])
        guides.append(
            {
                "name": full_name(guide),
                "email": guide["email"],
                "avatar": get_profile_photo_url(guide["profile_photo"]),
                "initial": guide["first_name"][0] if guide["first_name"] else "?",
                "color": "blue",
                "languages": ", ".join(lang[:2].upper() for lang in langs),
                "language_names": ", ".join(langs),
                "tours": guide_tours,
                "bookings": guide_bookings,
                "rating": f"{guide['rating_average']:.1f}/10",
                "reviews": guide["total_reviews"],
                "guests": f"{guide['guests_guided']:,}",
                "specialty": ", ".join(specialties),
            }
        )

    tours = []
    for tour in db.execute(
        "SELECT t.*, g.first_name, g.last_name FROM tours t JOIN guides g ON g.id = t.guide_id ORDER BY t.id"
    ).fetchall():
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
        SELECT r.id, p.first_name, p.last_name, t.title,
               gu.first_name AS guide_first, gu.last_name AS guide_last,
               o.starts_at, COUNT(g.id) AS extra_guests, r.status
        FROM reservations r
        JOIN participants p ON p.id = r.participant_id
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        JOIN guides gu ON gu.id = t.guide_id
        LEFT JOIN reservation_guests g ON g.reservation_id = r.id
        GROUP BY r.id
        ORDER BY o.starts_at DESC
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
        "guide_count": guide_count,
        "tour_count": tour_count,
        "reservation_count": reservation_count,
        "active_reservation_count": active_reservation_count,
        "total_walkers": people_count,
        "language_count": sum(1 for l in languages if l["count"] > 0),
        "languages": languages,
        "guides": guides,
        "tours": tours,
        "reservations": reservations,
    }


def participant_has_active_tour_booking(participant_id, tour_id):
    """True if the participant already has an active reservation for an upcoming,
    not-yet-finished departure of this tour. They may book it again only once that
    booked date has taken place."""
    return get_db().execute(
        """
        SELECT COUNT(*)
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        WHERE r.participant_id = ? AND s.tour_id = ? AND r.status = 'active'
          AND o.finished = 0 AND o.starts_at > ?
        """,
        (participant_id, tour_id, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
    ).fetchone()[0] > 0


def create_reservation(participant_id, schedule_id, date_str, guest_names):
    """Create a reservation for the logged-in participant on a chosen departure.

    The departure is identified by (schedule, date) — there may be no occurrence
    row yet, so one is created lazily here once the booking is validated."""
    db = get_db()
    participant = db.execute("SELECT id FROM participants WHERE id = ?", (participant_id,)).fetchone()
    if participant is None:
        raise ValueError("Only participants can make reservations.")

    schedule = db.execute(
        "SELECT * FROM tour_schedules WHERE id = ? AND active = 1", (schedule_id,)
    ).fetchone()
    if schedule is None:
        raise ValueError("Departure not found.")

    hours, minutes = map(int, schedule["start_time"].split(":"))
    try:
        year, month, day = map(int, str(date_str).split("-"))
        starts_at = datetime(year, month, day, hours, minutes)
    except (ValueError, AttributeError):
        raise ValueError("A valid departure date must be selected.")
    if starts_at.weekday() != schedule["weekday"]:
        raise ValueError("That date is not part of this tour's schedule.")
    if starts_at <= datetime.now():
        raise ValueError("This departure has already started.")

    tour_id = schedule["tour_id"]

    requested = 1 + len(guest_names)
    if requested < 1 or requested > 4:
        raise ValueError("A reservation can include between 1 and 4 people.")

    # Rule 1 — conflicts with the participant's own upcoming schedule:
    #   (a) the SAME tour cannot be booked again until the booked date has taken
    #       place (one active upcoming booking per tour);
    #   (b) two different tours whose time windows OVERLAP cannot both be booked.
    new_start = starts_at
    new_end = starts_at + timedelta(minutes=schedule["duration_minutes"])
    existing = db.execute(
        """
        SELECT o.starts_at, o.ends_at, s.tour_id
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        WHERE r.participant_id = ? AND r.status = 'active'
          AND o.finished = 0 AND o.starts_at > ?
        """,
        (participant_id, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
    ).fetchall()
    for ex in existing:
        if ex["tour_id"] == tour_id:
            raise ValueError(
                "You already have an upcoming booking for this tour. "
                "You can book it again once that date has taken place."
            )
        ex_start = datetime.fromisoformat(ex["starts_at"])
        ex_end = datetime.fromisoformat(ex["ends_at"])
        if new_start < ex_end and ex_start < new_end:
            raise ValueError(
                "This departure overlaps with another tour you have already booked "
                "at that time. Pick a time that does not clash."
            )

    # Rule 2: the party must fit in the remaining places for this departure.
    reserved = reservation_people_for_slot(schedule_id, starts_at.isoformat())
    available = schedule["max_participants"] - reserved
    if available <= 0:
        raise ValueError("This departure is fully booked.")
    if requested > available:
        max_guests = available - 1
        if max_guests <= 0:
            raise ValueError("Only 1 place left for this departure — you can book just yourself, with no extra guests.")
        raise ValueError(
            f"Only {available} places left for this departure — you can bring at most "
            f"{max_guests} extra guest{'s' if max_guests != 1 else ''}."
        )

    # Materialise the occurrence now that the booking is valid.
    occurrence_id = get_or_create_occurrence(schedule_id, starts_at)
    cur = db.execute(
        "INSERT INTO reservations (participant_id, occurrence_id, status) VALUES (?, ?, 'active')",
        (participant_id, occurrence_id),
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


def cancel_reservation(reservation_id, participant_id):
    """Cancel a reservation, but only if it belongs to ``participant_id``."""
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
    if row["participant_id"] != participant_id:
        raise ValueError("You can only cancel your own reservations.")
    if row["status"] != "active":
        raise ValueError("This reservation is already cancelled.")
    now = datetime.now()
    starts_at = datetime.fromisoformat(row["starts_at"])
    if now > starts_at - timedelta(hours=24):
        raise ValueError("Cancellation deadline has passed.")
    db.execute(
        "UPDATE reservations SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP WHERE id = ?",
        (reservation_id,),
    )
    db.commit()


def _clean_stops(stops):
    """Return the non-empty stop titles, trimmed."""
    return [t.strip() for t in (stops or []) if t and t.strip()]


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def validate_schedule_rules(guide_id, exclude_tour_id, parsed_schedules, duration_minutes):
    """Enforce the weekly-schedule rules for a guide (back-end mirror of the form
    validation):
      * within the tour — no two schedules on the same day in the same language,
        and no two schedules whose time windows overlap;
      * across the guide's OTHER tours — no schedule whose time window overlaps an
        already-scheduled one.
    "Overlap" compares full ``[start, start + duration)`` windows (same weekday),
    not just identical start times. Raises ValueError on the first conflict."""
    def to_min(value):
        hours, minutes = map(int, value.split(":"))
        return hours * 60 + minutes

    items = [
        (s["weekday"], to_min(s["start_time"]), to_min(s["start_time"]) + duration_minutes, s["language"])
        for s in parsed_schedules
    ]

    # Within this tour.
    for i in range(len(items)):
        wi, si, ei, li = items[i]
        for j in range(i + 1, len(items)):
            wj, sj, ej, lj = items[j]
            if wi != wj:
                continue
            if li == lj:
                raise ValueError(f"{_DAY_NAMES[wi]} already has this tour in {li} — the same day needs a different language.")
            if si < ej and sj < ei:
                raise ValueError(f"{_DAY_NAMES[wi]} has overlapping start times within this tour.")

    # Against the guide's other tours.
    others = get_db().execute(
        """
        SELECT s.weekday, s.start_time, s.duration_minutes
        FROM tour_schedules s JOIN tours t ON t.id = s.tour_id
        WHERE t.guide_id = ? AND s.active = 1 AND t.id != ?
        """,
        (guide_id, exclude_tour_id if exclude_tour_id is not None else -1),
    ).fetchall()
    for weekday, start, end, _lang in items:
        for other in others:
            if other["weekday"] != weekday:
                continue
            o_start = to_min(other["start_time"])
            o_end = o_start + other["duration_minutes"]
            if start < o_end and o_start < end:
                raise ValueError(f"{_DAY_NAMES[weekday]} overlaps in time with another tour you have scheduled.")


def create_guide_tour(guide_id, title, description, meeting_point, duration_minutes,
                      max_participants, themes, stops, accessibility, schedules, photo_files):
    """Create a new tour for the guide (guides.id). Returns the new slug."""
    import re
    import uuid as _uuid

    db = get_db()
    guide = db.execute("SELECT id FROM guides WHERE id = ?", (guide_id,)).fetchone()
    if guide is None:
        raise ValueError("Guide profile not found.")

    if not title or not title.strip():
        raise ValueError("Tour title is required.")
    if duration_minutes < 30:
        raise ValueError("Duration must be at least 30 minutes.")
    if max_participants < 1:
        raise ValueError("Maximum participants must be at least 1.")
    if not themes:
        raise ValueError("Select at least one theme.")
    clean_stops = _clean_stops(stops)
    if len(clean_stops) < 4:
        raise ValueError("Add at least 4 tour stops.")
    if not schedules:
        raise ValueError("Add at least one weekly schedule.")

    ALLOWED_IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    valid_photos = [
        f for f in (photo_files or [])
        if f and f.filename and Path(f.filename).suffix.lower() in ALLOWED_IMG_EXT
    ]
    if len(valid_photos) != 5:
        raise ValueError("Upload exactly 5 promotional photos (png, jpg, jpeg, webp, gif).")

    DAYS_MAP = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    guide_langs = set(guide_languages_list(guide_id))

    parsed_schedules = []
    for sch in schedules:
        day_str = sch.get("weekday", "").lower()
        if day_str not in DAYS_MAP:
            raise ValueError(f"Invalid weekday: {sch.get('weekday')}")
        weekday = DAYS_MAP[day_str]
        language = sch.get("language", "")
        if language not in VALID_LANGUAGES:
            raise ValueError(f"Invalid tour language: {language}")
        if language not in guide_langs:
            raise ValueError(f"You can only offer tours in languages you speak ({language} is not one of them).")
        parsed_schedules.append({"weekday": weekday, "start_time": sch["start_time"], "language": language})

    # Same-day/same-language and time-overlap rules (within this tour and against
    # the guide's other tours).
    validate_schedule_rules(guide_id, None, parsed_schedules, duration_minutes)

    base_slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    slug = base_slug
    counter = 1
    while db.execute("SELECT id FROM tours WHERE slug = ?", (slug,)).fetchone():
        slug = f"{base_slug}-{counter}"
        counter += 1

    acc_lower = [a.lower() for a in (accessibility or [])]
    wheelchair = 1 if any("wheelchair" in a for a in acc_lower) else 0
    children = 1 if any("children" in a for a in acc_lower) else 0
    pet = 1 if any("pet" in a for a in acc_lower) else 0

    cur = db.execute(
        """
        INSERT INTO tours
          (guide_id, slug, title, description, meeting_point, duration_minutes,
           max_participants, status, wheelchair_accessible, suitable_for_children, pet_friendly,
           rating, review_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, 8.0, 0)
        """,
        (guide_id, slug, title.strip(), description.strip(), meeting_point.strip() if meeting_point else "",
         duration_minutes, max_participants, wheelchair, children, pet),
    )
    tour_id = cur.lastrowid

    for order, stop_title in enumerate(clean_stops):
        db.execute(
            "INSERT INTO tour_stops (tour_id, stop_order, title) VALUES (?, ?, ?)",
            (tour_id, order, stop_title),
        )
    for theme in themes:
        db.execute("INSERT INTO tour_themes (tour_id, theme) VALUES (?, ?)", (tour_id, theme.strip()))
    for sch in parsed_schedules:
        db.execute(
            """
            INSERT INTO tour_schedules
              (tour_id, weekday, start_time, language, duration_minutes, max_participants, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (tour_id, sch["weekday"], sch["start_time"], sch["language"], duration_minutes, max_participants),
        )

    static_tours = Path(current_app.root_path) / "static" / "img" / "tours"
    static_tours.mkdir(parents=True, exist_ok=True)
    for index, photo_file in enumerate(valid_photos):
        ext = Path(photo_file.filename).suffix.lower()
        unique_name = f"tour_{_uuid.uuid4().hex}{ext}"
        photo_file.save(str(static_tours / unique_name))
        db.execute(
            "INSERT INTO tour_photos (tour_id, image_path, is_cover) VALUES (?, ?, ?)",
            (tour_id, f"img/tours/{unique_name}", 1 if index == 0 else 0),
        )

    db.commit()
    # Bookable dates are derived from the weekly schedule on the fly, so the new
    # tour is immediately bookable without pre-generating any occurrence rows.
    return slug


def tour_has_reservations(tour_id):
    """True if any active reservation exists for any date of the tour."""
    return get_db().execute(
        """
        SELECT COUNT(*)
        FROM reservations r
        JOIN tour_occurrences o ON o.id = r.occurrence_id
        JOIN tour_schedules s ON s.id = o.schedule_id
        WHERE s.tour_id = ? AND r.status = 'active'
        """,
        (tour_id,),
    ).fetchone()[0] > 0


def update_guide_tour(guide_id, slug, title, description, meeting_point, duration_minutes,
                      max_participants, themes, stops, accessibility, schedules, photo_files,
                      keep_photo_ids=None):
    """Update an existing tour owned by the guide. Essential fields are locked
    once a reservation exists for any date of the tour."""
    import uuid as _uuid

    db = get_db()
    tour = db.execute("SELECT * FROM tours WHERE slug = ?", (slug,)).fetchone()
    if tour is None:
        raise ValueError("Tour not found.")
    if tour["guide_id"] != guide_id:
        raise ValueError("You can only edit your own tours.")

    locked = tour_has_reservations(tour["id"])

    if not title or not title.strip():
        raise ValueError("Tour title is required.")
    if not themes:
        raise ValueError("Select at least one theme.")
    clean_stops = _clean_stops(stops)
    if len(clean_stops) < 4:
        raise ValueError("Add at least 4 tour stops.")

    acc_lower = [a.lower() for a in (accessibility or [])]
    wheelchair = 1 if any("wheelchair" in a for a in acc_lower) else 0
    children = 1 if any("children" in a for a in acc_lower) else 0
    pet = 1 if any("pet" in a for a in acc_lower) else 0

    db.execute(
        """
        UPDATE tours
        SET title = ?, description = ?, wheelchair_accessible = ?,
            suitable_for_children = ?, pet_friendly = ?
        WHERE id = ?
        """,
        (title.strip(), description.strip(), wheelchair, children, pet, tour["id"]),
    )
    db.execute("DELETE FROM tour_stops WHERE tour_id = ?", (tour["id"],))
    for order, stop_title in enumerate(clean_stops):
        db.execute(
            "INSERT INTO tour_stops (tour_id, stop_order, title) VALUES (?, ?, ?)",
            (tour["id"], order, stop_title),
        )
    db.execute("DELETE FROM tour_themes WHERE tour_id = ?", (tour["id"],))
    for theme in themes:
        db.execute("INSERT INTO tour_themes (tour_id, theme) VALUES (?, ?)", (tour["id"], theme.strip()))

    if not locked:
        if duration_minutes < 30:
            raise ValueError("Duration must be at least 30 minutes.")
        if max_participants < 1:
            raise ValueError("Maximum participants must be at least 1.")
        if not schedules:
            raise ValueError("Add at least one weekly schedule.")

        DAYS_MAP = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        guide_langs = set(guide_languages_list(guide_id))
        parsed_schedules = []
        for sch in schedules:
            day_str = sch.get("weekday", "").lower()
            if day_str not in DAYS_MAP:
                raise ValueError(f"Invalid weekday: {sch.get('weekday')}")
            weekday = DAYS_MAP[day_str]
            language = sch.get("language", "")
            if language not in VALID_LANGUAGES:
                raise ValueError(f"Invalid tour language: {language}")
            if language not in guide_langs:
                raise ValueError(f"You can only offer tours in languages you speak ({language} is not one of them).")
            parsed_schedules.append({"weekday": weekday, "start_time": sch["start_time"], "language": language})

        # Same-day/same-language and time-overlap rules — excluding this tour's own
        # schedules from the cross-tour comparison.
        validate_schedule_rules(guide_id, tour["id"], parsed_schedules, duration_minutes)

        db.execute(
            "UPDATE tours SET meeting_point = ?, duration_minutes = ?, max_participants = ? WHERE id = ?",
            (meeting_point.strip() if meeting_point else "", duration_minutes, max_participants, tour["id"]),
        )
        db.execute("DELETE FROM tour_schedules WHERE tour_id = ?", (tour["id"],))
        for sch in parsed_schedules:
            db.execute(
                """
                INSERT INTO tour_schedules
                  (tour_id, weekday, start_time, language, duration_minutes, max_participants, active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (tour["id"], sch["weekday"], sch["start_time"], sch["language"], duration_minutes, max_participants),
            )
        db.commit()
        # No occurrences to regenerate — dates derive from the schedule lazily.

    ALLOWED_IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    valid_photos = [
        f for f in (photo_files or [])
        if f and f.filename and Path(f.filename).suffix.lower() in ALLOWED_IMG_EXT
    ]
    # Photo editing: the form sends keep_photo_ids[] for every existing photo the
    # guide chose to keep, plus any new uploads. If neither is present the photo
    # set is left untouched. Otherwise the final set (kept + new) must be exactly
    # 5, so the "5 promotional photos" rule always holds.
    if keep_photo_ids is not None or valid_photos:
        existing = db.execute(
            "SELECT id, image_path FROM tour_photos WHERE tour_id = ? ORDER BY is_cover DESC, id",
            (tour["id"],),
        ).fetchall()
        keep_set = set()
        for raw in (keep_photo_ids or []):
            try:
                keep_set.add(int(raw))
            except (TypeError, ValueError):
                continue
        kept = [p for p in existing if p["id"] in keep_set]
        total = len(kept) + len(valid_photos)
        if total != 5:
            raise ValueError(
                f"A tour must have exactly 5 photos. You kept {len(kept)} and added "
                f"{len(valid_photos)} ({total} total)."
            )

        static_tours = Path(current_app.root_path) / "static" / "img" / "tours"
        static_tours.mkdir(parents=True, exist_ok=True)

        # Remove the de-selected photos. Only delete files the app uploaded itself
        # (named "tour_<uuid>") — never the committed seed images, which are named
        # "tourN_M" (e.g. tour1_1.jpg) and so never start with "tour_".
        for photo in existing:
            if photo["id"] in keep_set:
                continue
            db.execute("DELETE FROM tour_photos WHERE id = ?", (photo["id"],))
            if Path(photo["image_path"]).name.startswith("tour_"):
                file_path = Path(current_app.root_path) / "static" / photo["image_path"]
                try:
                    file_path.unlink(missing_ok=True)
                except OSError:
                    pass

        # Add the new uploads.
        for photo_file in valid_photos:
            ext = Path(photo_file.filename).suffix.lower()
            unique_name = f"tour_{_uuid.uuid4().hex}{ext}"
            photo_file.save(str(static_tours / unique_name))
            db.execute(
                "INSERT INTO tour_photos (tour_id, image_path, is_cover) VALUES (?, ?, 0)",
                (tour["id"], f"img/tours/{unique_name}"),
            )

        # Exactly one cover photo (the first remaining one).
        db.execute("UPDATE tour_photos SET is_cover = 0 WHERE tour_id = ?", (tour["id"],))
        first = db.execute(
            "SELECT id FROM tour_photos WHERE tour_id = ? ORDER BY id LIMIT 1", (tour["id"],)
        ).fetchone()
        if first:
            db.execute("UPDATE tour_photos SET is_cover = 1 WHERE id = ?", (first["id"],))

    db.commit()
    return slug


def mark_occurrence_done(guide_id, occurrence_id):
    """Mark a scheduled tour occurrence as done. It moves to Tours History and,
    if it had reservations, a pending report is created for it."""
    db = get_db()
    occ = db.execute(
        """
        SELECT o.id, o.starts_at, o.finished, t.guide_id
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE o.id = ?
        """,
        (occurrence_id,),
    ).fetchone()
    if not occ:
        raise ValueError("Occurrence not found.")
    if occ["guide_id"] != guide_id:
        raise ValueError("You can only manage your own tours.")
    if occ["finished"]:
        raise ValueError("This tour is already marked as done.")
    if datetime.fromisoformat(occ["starts_at"]) > datetime.now():
        raise ValueError("You can only mark a tour as done once it has started.")
    db.execute("UPDATE tour_occurrences SET finished = 1, status = 'finished' WHERE id = ?", (occurrence_id,))
    db.commit()


def create_guide_report(guide_id, occurrence_id, actual_participants, evidence_photo_path):
    """File a post-tour report for a finished occurrence owned by the guide.
    A photo is mandatory when at least one participant attended."""
    db = get_db()
    occurrence = db.execute(
        """
        SELECT o.id, o.finished, t.guide_id
        FROM tour_occurrences o
        JOIN tour_schedules s ON s.id = o.schedule_id
        JOIN tours t ON t.id = s.tour_id
        WHERE o.id = ?
        """,
        (occurrence_id,),
    ).fetchone()
    if not occurrence:
        raise ValueError("Occurrence not found.")
    if occurrence["guide_id"] != guide_id:
        raise ValueError("You can only report on your own tours.")
    if not occurrence["finished"]:
        raise ValueError("Mark the tour as done before filing its report.")
    if actual_participants < 0:
        raise ValueError("Attendance cannot be negative.")
    expected = reservation_count_for_occurrence(occurrence_id)
    if expected < 1:
        raise ValueError("Reports require at least one reservation.")

    if actual_participants == 0:
        # Nobody showed up: no photo required. Recorded as a finished "no-show"
        # report so it clears from pending, but it is not kept in Past Reports.
        status = "no_show"
        evidence_photo_path = ""
    else:
        if not evidence_photo_path:
            raise ValueError("An evidence photo is required when at least one participant attended.")
        status = "pending"

    db.execute(
        """
        INSERT OR REPLACE INTO guide_reports
        (occurrence_id, guide_id, expected_participants, actual_participants, evidence_photo_path, status, finished)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (occurrence_id, guide_id, expected, actual_participants, evidence_photo_path, status),
    )
    db.commit()
