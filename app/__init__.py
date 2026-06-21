import json

from flask import Flask, jsonify, render_template, request

from .backend import (
    admin_dashboard_data,
    cancel_reservation,
    create_guide_report,
    create_reservation,
    get_public_tours,
    get_tour_detail,
    guide_dashboard_data,
    init_backend,
    participant_dashboard_data,
)


TOURS = {
    "complete-prague-free-tour": {
        "slug": "complete-prague-free-tour",
        "title": "Complete Prague Free Tour",
        "provider": "I Love Praag",
        "guide": "Tomas Novak",
        "rating": "9.1",
        "reviews": "1034",
        "duration": "3 hours",
        "meeting_point": "Metrostation Malostranska",
        "languages": "English, French, Spanish, Portuguese, Italian, German",
        "guide_email": "tomas.novak@email.cz",
        "image": "img/tours/free-walking-tour-prague-old-town-castle-02.webp",
        "gallery": [
            "img/tours/free-walking-tour-prague-old-town-castle-02.webp",
            "img/tours/free-walking-tour-prague-old-town-castle-03.webp",
            "img/tours/free-walking-tour-prague-old-town-castle-01.jpg",
            "img/tours/free-walking-tour-prague-old-town-castle-08.jpg",
            "img/tours/free-walking-tour-prague-old-town-castle-06.webp",
        ],
    },
    "original-free-tour-prague": {
        "slug": "original-free-tour-prague",
        "title": "The Original Free Tour of Prague",
        "provider": "Walk Prague",
        "guide": "Eva Horakova",
        "rating": "9.2",
        "reviews": "28047",
        "duration": "2h 30min",
        "meeting_point": "Old Town Square",
        "languages": "English, Spanish",
        "guide_email": "eva.horakova@email.cz",
        "image": "https://images.unsplash.com/photo-1519677100203-a0e668c92439?auto=format&fit=crop&w=1600&q=80",
    },
    "castle-district-hidden-courtyards": {
        "slug": "castle-district-hidden-courtyards",
        "title": "Castle District & Hidden Courtyards",
        "provider": "Walk Prague",
        "guide": "Tomas Dvorak",
        "rating": "8.4",
        "reviews": "842",
        "duration": "2 hours",
        "meeting_point": "Hradcanske Square",
        "languages": "German, English, French",
        "guide_email": "tomas.dvorak@email.cz",
        "image": "https://images.unsplash.com/photo-1600623471616-8c1966c91ff6?auto=format&fit=crop&w=1600&q=80",
    },
    "ghost-legends-alchemy-night-walk": {
        "slug": "ghost-legends-alchemy-night-walk",
        "title": "Ghost Legends & Alchemy Night Walk",
        "provider": "Walk Prague",
        "guide": "Klara Vesela",
        "rating": "9.1",
        "reviews": "612",
        "duration": "90 min",
        "meeting_point": "Old Town Bridge Tower",
        "languages": "English, German",
        "guide_email": "klara.vesela@email.cz",
        "image": "https://images.unsplash.com/photo-1551867633-194f125bddfa?auto=format&fit=crop&w=1600&q=80",
    },
    "beer-markets-czech-bites": {
        "slug": "beer-markets-czech-bites",
        "title": "Beer, Markets & Czech Bites",
        "provider": "Walk Prague",
        "guide": "Mateo Costa",
        "rating": "8.6",
        "reviews": "438",
        "duration": "2 hours",
        "meeting_point": "Namesti Republiky",
        "languages": "English, Portuguese, Italian",
        "guide_email": "mateo.costa@email.cz",
        "image": "https://images.unsplash.com/photo-1574094985345-fc6a821b96da?auto=format&fit=crop&w=1600&q=80",
    },
    "art-nouveau-architecture-route": {
        "slug": "art-nouveau-architecture-route",
        "title": "Art Nouveau & Architecture Route",
        "provider": "Walk Prague",
        "guide": "Sofia Laurent",
        "rating": "9.0",
        "reviews": "719",
        "duration": "2h 15min",
        "meeting_point": "Municipal House",
        "languages": "French, English, Spanish",
        "guide_email": "sofia.laurent@email.cz",
        "image": "https://images.unsplash.com/photo-1562624475-96c2bc08fab9?auto=format&fit=crop&w=1600&q=80",
    },
}


GUIDE_DASHBOARD = {
    "name": "Tomas Novak",
    "email": "tomas.novak@walkprague.cz",
    "rating": "9.6/10",
    "active_tours": 3,
    "expected_participants": 42,
    "pending_reports": 2,
    "tours": [
        {
            "title": "Complete Prague Free Tour",
            "slug": "complete-prague-free-tour",
            "status": "Active",
            "languages": "English, Spanish, Italian, Portuguese",
            "meeting_point": "Metrostation Malostranska",
            "schedules": [
                {
                    "date": "Fri, June 19, 2026",
                    "time": "2:00 PM",
                    "language": "Italian",
                    "reserved_groups": 4,
                    "expected": 7,
                    "max_participants": 15,
                    "state": "upcoming",
                    "reservations": [
                        {"name": "Ana Kovac", "people": 2, "email": "ana@example.com"},
                        {"name": "Luca Bianchi", "people": 1, "email": "luca@example.com"},
                        {"name": "Nina Ferri", "people": 3, "email": "nina@example.com"},
                        {"name": "Marco Conti", "people": 1, "email": "marco@example.com"},
                    ],
                },
                {
                    "date": "Mon, June 22, 2026",
                    "time": "9:00 AM",
                    "language": "English",
                    "reserved_groups": 5,
                    "expected": 9,
                    "max_participants": 15,
                    "state": "upcoming",
                    "reservations": [
                        {"name": "Sara Miller", "people": 2, "email": "sara@example.com"},
                        {"name": "Ben Carter", "people": 1, "email": "ben@example.com"},
                        {"name": "Julia Stone", "people": 2, "email": "julia@example.com"},
                        {"name": "Ethan Brooks", "people": 3, "email": "ethan@example.com"},
                        {"name": "Maya Chen", "people": 1, "email": "maya@example.com"},
                    ],
                },
                {
                    "date": "Wed, June 17, 2026",
                    "time": "10:00 AM",
                    "language": "English",
                    "reserved_groups": 3,
                    "expected": 6,
                    "max_participants": 15,
                    "state": "completed",
                    "reservations": [
                        {"name": "Carlos Wei", "people": 2, "email": "carlos@example.com"},
                        {"name": "Paulette Barnard", "people": 1, "email": "paulette@example.com"},
                        {"name": "Orit Cohen", "people": 3, "email": "orit@example.com"},
                    ],
                },
            ],
        },
        {
            "title": "Prague Castle Morning Walk",
            "slug": "castle-district-hidden-courtyards",
            "status": "Draft review",
            "languages": "English, German",
            "meeting_point": "Hradcanske Square",
            "schedules": [
                {
                    "date": "Thu, June 18, 2026",
                    "time": "11:00 AM",
                    "language": "German",
                    "reserved_groups": 2,
                    "expected": 4,
                    "max_participants": 12,
                    "state": "completed",
                    "reservations": [
                        {"name": "Lea Wagner", "people": 2, "email": "lea@example.com"},
                        {"name": "Jonas Klein", "people": 2, "email": "jonas@example.com"},
                    ],
                },
                {
                    "date": "Sat, June 27, 2026",
                    "time": "3:30 PM",
                    "language": "English",
                    "reserved_groups": 0,
                    "expected": 0,
                    "max_participants": 12,
                    "state": "upcoming",
                    "reservations": [],
                },
            ],
        },
        {
            "title": "Legends of Old Prague",
            "slug": "ghost-legends-alchemy-night-walk",
            "status": "Active",
            "languages": "English",
            "meeting_point": "Old Town Bridge Tower",
            "schedules": [
                {
                    "date": "Sun, June 21, 2026",
                    "time": "7:00 PM",
                    "language": "English",
                    "reserved_groups": 6,
                    "expected": 13,
                    "max_participants": 15,
                    "state": "upcoming",
                    "reservations": [
                        {"name": "Laura Evans", "people": 2, "email": "laura@example.com"},
                        {"name": "Daniel Kim", "people": 3, "email": "daniel@example.com"},
                        {"name": "Marta Ruiz", "people": 1, "email": "marta@example.com"},
                        {"name": "Peter Holm", "people": 2, "email": "peter@example.com"},
                        {"name": "Olivia Smith", "people": 4, "email": "olivia@example.com"},
                        {"name": "Noah Brown", "people": 1, "email": "noah@example.com"},
                    ],
                },
            ],
        },
    ],
}


ADMIN_DASHBOARD = {
    "last_updated": "June 9, 2026",
    "stats": [
        {"value": "11", "label": "Guides", "accent": "blue", "icon": "▣"},
        {"value": "247", "label": "Participants", "accent": "green", "icon": "♙"},
        {"value": "14", "label": "Tours", "accent": "purple", "icon": "◉"},
        {"value": "318", "label": "Reservations", "accent": "orange", "icon": "✓"},
        {"value": "4.2k", "label": "Total walkers", "accent": "red", "icon": "☑"},
        {"value": "203", "label": "Reports filed", "accent": "cyan", "icon": "▤"},
    ],
    "languages": [
        {"name": "English", "flag": "🇬🇧", "count": 142, "accent": "blue", "percent": 86},
        {"name": "German", "flag": "🇩🇪", "count": 97, "accent": "green", "percent": 58},
        {"name": "Spanish", "flag": "🇪🇸", "count": 63, "accent": "purple", "percent": 35},
        {"name": "French", "flag": "🇫🇷", "count": 39, "accent": "orange", "percent": 22},
        {"name": "Portuguese", "flag": "🇵🇹", "count": 28, "accent": "cyan", "percent": 16},
    ],
    "guides": [
        {"name": "Tomáš Novák", "email": "tomas.novak@email.cz", "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=120&q=80", "initial": "T", "color": "blue", "languages": "🇬🇧 EN  🇩🇪 DE", "language_names": "English, German", "tours": 3, "bookings": 67, "rating": "9.6/10", "reviews": 124, "guests": "1,840", "specialty": "History"},
        {"name": "Karolína Dvořák", "email": "karolina.dvorak@email.cz", "avatar": "", "initial": "K", "color": "green", "languages": "🇬🇧 EN  🇫🇷 FR  🇨🇿 CZ", "language_names": "English, French, Czech", "tours": 2, "bookings": 41, "rating": "9.3/10", "reviews": 88, "guests": "920", "specialty": "Castle District"},
        {"name": "Martin Procházka", "email": "martin.prochazka@email.cz", "avatar": "", "initial": "M", "color": "purple", "languages": "🇩🇪 DE  🇪🇸 ES", "language_names": "German, Spanish", "tours": 4, "bookings": 112, "rating": "9.1/10", "reviews": 147, "guests": "2,130", "specialty": "Jewish Quarter"},
        {"name": "Lucie Kratochvílová", "email": "lucie.k@email.cz", "avatar": "", "initial": "L", "color": "orange", "languages": "🇬🇧 EN  🇮🇹 IT  🇨🇿 CZ", "language_names": "English, Italian, Czech", "tours": 1, "bookings": 18, "rating": "8.9/10", "reviews": 52, "guests": "440", "specialty": "Communist Era"},
    ],
    "tours": [
        {"title": "Old Town & Astronomical Clock Walk", "slug": "complete-prague-free-tour", "guide": "Tomáš Novák", "language": "EN", "duration": "120 min", "max": 15, "reservations": 67},
        {"title": "Charles Bridge & Lesser Town Secrets", "slug": "original-free-tour-prague", "guide": "Tomáš Novák", "language": "DE", "duration": "90 min", "max": 12, "reservations": 0},
        {"title": "Prague Castle & Hradčany District", "slug": "castle-district-hidden-courtyards", "guide": "Karolína Dvořák", "language": "EN", "duration": "150 min", "max": 10, "reservations": 41},
        {"title": "Josefov: Prague's Jewish Quarter", "slug": "art-nouveau-architecture-route", "guide": "Martin Procházka", "language": "ES", "duration": "100 min", "max": 18, "reservations": 33},
        {"title": "Velvet Revolution & Communist Prague", "slug": "ghost-legends-alchemy-night-walk", "guide": "Lucie Kratochvílová", "language": "EN", "duration": "110 min", "max": 14, "reservations": 28},
    ],
    "reservations": [
        {"participant": "Ana Kovac", "tour": "Old Town & Astronomical Clock Walk", "guide": "Tomáš Novák", "date": "Jun 19, 2026", "people": 2, "status": "Confirmed"},
        {"participant": "Milan Ševčík", "tour": "Prague Castle & Hradčany District", "guide": "Karolína Dvořák", "date": "Jun 20, 2026", "people": 3, "status": "Confirmed"},
        {"participant": "Elena Vítková", "tour": "Josefov: Prague's Jewish Quarter", "guide": "Martin Procházka", "date": "Jun 22, 2026", "people": 1, "status": "Cancelled"},
        {"participant": "Lucas Müller", "tour": "Velvet Revolution & Communist Prague", "guide": "Lucie Kratochvílová", "date": "Jun 24, 2026", "people": 4, "status": "Confirmed"},
    ],
}


PARTICIPANT_DASHBOARD = {
    "name": "Anna",
    "email": "anna.walker@email.com",
    "reservations": [
        {
            "tour": "Complete Prague Free Tour",
            "slug": "complete-prague-free-tour",
            "date": "Mon, June 22, 2026",
            "start_time": "9:00 AM",
            "meeting_point": "Metrostation Malostranska",
            "people": 3,
            "additional_participants": ["Mira Walker", "Leo Walker"],
            "language": "English",
            "status": "Confirmed",
            "can_cancel": True,
            "cancel_note": "Cancellation available until Jun 21, 2026 at 9:00 AM",
        },
        {
            "tour": "Ghost Legends & Alchemy Night Walk",
            "slug": "ghost-legends-alchemy-night-walk",
            "date": "Sun, June 21, 2026",
            "start_time": "7:00 PM",
            "meeting_point": "Old Town Bridge Tower",
            "people": 2,
            "additional_participants": ["Sara Klein"],
            "language": "English",
            "status": "Confirmed",
            "can_cancel": True,
            "cancel_note": "Cancellation available until Jun 20, 2026 at 7:00 PM",
        },
        {
            "tour": "Old Town Evening Introduction",
            "slug": "complete-prague-free-tour",
            "date": "Sat, June 20, 2026",
            "start_time": "8:00 PM",
            "meeting_point": "Old Town Square",
            "people": 1,
            "additional_participants": [],
            "language": "Spanish",
            "status": "Locked",
            "can_cancel": False,
            "cancel_note": "Less than 24 hours before start time",
        },
    ],
}


def create_app():
    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    init_backend(app)

    @app.route("/")
    def index():
        return render_template("index.html", participant_view=False, tours=get_public_tours())

    @app.route("/participant-home")
    def participant_home():
        return render_template(
            "index.html",
            participant_view=True,
            participant=participant_dashboard_data(),
            tours=get_public_tours(),
        )

    @app.route("/auth")
    @app.route("/signin")
    def signin():
        return render_template("signin.html")

    @app.route("/register")
    def register():
        return render_template("register.html")

    @app.route("/admin-access")
    def admin_access():
        return render_template("admin_access.html")

    @app.route("/admin-dashboard")
    def admin_dashboard():
        return render_template("admin_dashboard.html", admin=admin_dashboard_data())

    @app.route("/guide-dashboard")
    def guide_dashboard():
        return render_template("guide_dashboard.html", guide=guide_dashboard_data())

    @app.route("/participant-dashboard")
    def participant_dashboard():
        return render_template("participant_dashboard.html", participant=participant_dashboard_data())

    @app.route("/tours/<slug>")
    def tour_detail(slug):
        tour = get_tour_detail(slug)
        admin_view = request.args.get("mode") == "admin"
        participant_view = request.args.get("mode") == "participant"
        return render_template("tour_detail.html", tour=tour, admin_view=admin_view, participant_view=participant_view)

    @app.post("/reservations")
    def reservation_create():
        payload = request.get_json(silent=True) or request.form
        occurrence_id = int(payload.get("occurrence_id"))
        guests_raw = payload.get("guests", [])
        if isinstance(guests_raw, str):
            try:
                guests = json.loads(guests_raw)
            except ValueError:
                guests = [item.strip() for item in guests_raw.split(",") if item.strip()]
        else:
            guests = list(guests_raw)
        try:
            reservation_id = create_reservation(occurrence_id, guests)
        except ValueError as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True, "reservation_id": reservation_id})

    @app.post("/reservations/<int:reservation_id>/cancel")
    def reservation_cancel(reservation_id):
        try:
            cancel_reservation(reservation_id)
        except ValueError as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True})

    @app.post("/guide/reports")
    def guide_report_create():
        payload = request.get_json(silent=True) or request.form
        try:
            create_guide_report(
                int(payload.get("occurrence_id")),
                int(payload.get("actual_participants")),
                payload.get("evidence_photo_path") or "uploads/evidence-placeholder.jpg",
            )
        except (TypeError, ValueError) as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True})

    return app
