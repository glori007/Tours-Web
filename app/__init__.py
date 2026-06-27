import json

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from .backend import (
    admin_dashboard_data,
    authenticate_user,
    cancel_reservation,
    create_guide_report,
    create_guide_tour,
    create_reservation,
    get_public_tours,
    get_tour_detail,
    participant_has_active_tour_booking,
    get_user_by_id,
    guide_dashboard_data,
    init_backend,
    mark_occurrence_done,
    participant_dashboard_data,
    register_user,
    update_guide_tour,
)


def create_app():
    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # A secret key is mandatory for sessions and Flask-Login
    app.config["SECRET_KEY"] = "walk-prague-secret-key-change-in-production"

    # Initialise SQLite backend (schema + seed data)
    init_backend(app)

    # -----------------------------------------------------------------------
    # Flask-Login setup
    # -----------------------------------------------------------------------
    login_manager = LoginManager(app)
    login_manager.login_view = "signin"          # redirect here when @login_required fails
    login_manager.login_message = "Please sign in to access that page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # -----------------------------------------------------------------------
    # Public routes
    # -----------------------------------------------------------------------

    @app.route("/")
    def index():
        participant_view = current_user.is_authenticated and current_user.role == "participant"
        participant = participant_dashboard_data(current_user.id) if participant_view else None
        return render_template(
            "index.html",
            participant_view=participant_view,
            participant=participant,
            tours=get_public_tours(),
        )

    @app.route("/participant-home")
    @login_required
    def participant_home():
        if current_user.role != "participant":
            flash("Access denied: that page is for participants only.", "error")
            return _redirect_by_role(current_user.role)
        return render_template(
            "index.html",
            participant_view=True,
            participant=participant_dashboard_data(current_user.id),
            tours=get_public_tours(),
        )

    # -----------------------------------------------------------------------
    # Authentication routes
    # -----------------------------------------------------------------------

    @app.route("/auth")
    @app.route("/signin", methods=["GET", "POST"])
    def signin():
        # Already logged in → send to the right dashboard
        if current_user.is_authenticated:
            return _redirect_by_role(current_user.role)

        if request.method == "GET":
            return render_template("signin.html")

        # ---- POST: process sign-in ----
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role     = request.form.get("role", "participant")

        # Back-end validation
        error = None
        if not email:
            error = "Email address is required."
        elif not password:
            error = "Password is required."
        elif role not in ("guide", "participant", "admin"):
            error = "Invalid account type."

        if not error:
            user = authenticate_user(email, password, role)
            if user is None:
                error = "Incorrect email, password, or account type."

        if error:
            flash(error, "error")
            return render_template("signin.html", form_email=email, form_role=role), 400

        login_user(user, remember=True)
        # Respect Flask-Login's ?next= redirect after @login_required
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return _redirect_by_role(user.role)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return _redirect_by_role(current_user.role)

        if request.method == "GET":
            return render_template("register.html")

        # ---- POST: process registration ----
        role          = request.form.get("role", "participant")
        first_name    = request.form.get("first_name", "").strip()
        last_name     = request.form.get("last_name", "").strip()
        email         = request.form.get("email", "").strip()
        password      = request.form.get("password", "")
        confirm_pw    = request.form.get("confirm_password", "")
        # Languages sent as comma-separated hidden field by JS
        raw_languages = request.form.get("guide_languages", "")
        languages     = [lang.strip() for lang in raw_languages.split(",") if lang.strip()] if raw_languages else []

        profile_photo_file = request.files.get("profile_photo")
        # Specialties sent as comma-separated hidden field by JS (multi-select, up to 4)
        raw_specialties = request.form.get("specialties", "")
        specialties = [s.strip() for s in raw_specialties.split(",") if s.strip()] if raw_specialties else []

        # Front-end-replicable back-end checks
        error = None
        if password != confirm_pw:
            error = "Passwords do not match."

        if not error:
            try:
                user = register_user(
                    role=role,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password,
                    languages=languages if role == "guide" else None,
                    profile_photo_file=profile_photo_file if role == "guide" else None,
                    specialties=specialties if role == "guide" else None,
                )
            except ValueError as exc:
                error = str(exc)

        if error:
            flash(error, "error")
            return render_template(
                "register.html",
                form_first_name=first_name,
                form_last_name=last_name,
                form_email=email,
                form_role=role,
            ), 400

        # Log the new user in immediately
        login_user(user, remember=True)
        flash(f"Welcome to Walk Prague, {user.first_name}!", "success")
        return _redirect_by_role(user.role)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    # -----------------------------------------------------------------------
    # Dashboard / protected routes — all require login + correct role
    # -----------------------------------------------------------------------

    @app.route("/admin-access", methods=["GET", "POST"])
    def admin_access():
        # If already logged in as admin, skip straight to dashboard
        if current_user.is_authenticated and current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))

        if request.method == "GET":
            return render_template("admin_access.html")

        # ---- POST: authenticate the admin ----
        email    = request.form.get("admin_email", "").strip().lower()
        password = request.form.get("admin_password", "")

        # Back-end validation
        error = None
        if not email:
            error = "Email address is required."
        elif not password:
            error = "Password is required."

        if not error:
            user = authenticate_user(email, password, "admin")
            if user is None:
                error = "Invalid email or password."

        if error:
            flash(error, "error")
            return render_template("admin_access.html", form_email=email), 400

        login_user(user, remember=False)
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin-dashboard")
    @login_required
    def admin_dashboard():
        if current_user.role != "admin":
            abort(403)  # Guides and participants cannot see admin dashboard
        return render_template("admin_dashboard.html", admin=admin_dashboard_data())

    @app.route("/guide-dashboard")
    @login_required
    def guide_dashboard():
        if current_user.role != "guide":
            # Wrong role — send them to their own dashboard
            flash("Access denied: that page is for guides only.", "error")
            return _redirect_by_role(current_user.role)
        return render_template("guide_dashboard.html", guide=guide_dashboard_data(current_user.id))

    @app.route("/participant-dashboard")
    @login_required
    def participant_dashboard():
        if current_user.role != "participant":
            flash("Access denied: that page is for participants only.", "error")
            return _redirect_by_role(current_user.role)
        return render_template("participant_dashboard.html", participant=participant_dashboard_data(current_user.id))

    # -----------------------------------------------------------------------
    # Tour routes
    # -----------------------------------------------------------------------

    @app.route("/tours/<slug>")
    def tour_detail(slug):
        tour = get_tour_detail(slug)
        if tour is None:
            abort(404)
        admin_view = request.args.get("mode") == "admin"
        participant_view = request.args.get("mode") == "participant"
        # Guides and admins cannot make reservations, so they never see a
        # bookable panel (the backend also rejects their booking POSTs).
        staff_view = current_user.is_authenticated and current_user.role in ("guide", "admin")
        # One active upcoming booking per tour: if the participant already holds
        # one, the page shows "Booked" until that date has taken place.
        already_booked = (
            current_user.is_authenticated
            and current_user.role == "participant"
            and participant_has_active_tour_booking(current_user.id, tour["id"])
        )
        return render_template(
            "tour_detail.html", tour=tour, admin_view=admin_view,
            participant_view=participant_view, staff_view=staff_view,
            already_booked=already_booked,
        )

    # -----------------------------------------------------------------------
    # Reservation API routes
    # -----------------------------------------------------------------------

    @app.post("/reservations")
    @login_required
    def reservation_create():
        # Only participants may reserve (a guide cannot make reservations).
        if current_user.role != "participant":
            return jsonify({"ok": False, "error": "Only participants can make reservations."}), 403
        payload = request.get_json(silent=True) or request.form
        try:
            schedule_id = int(payload.get("schedule_id"))
            date_str = str(payload.get("date"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "A valid departure must be selected."}), 400
        guests_raw = payload.get("guests", [])
        if isinstance(guests_raw, str):
            try:
                guests = json.loads(guests_raw)
            except ValueError:
                guests = [item.strip() for item in guests_raw.split(",") if item.strip()]
        else:
            guests = list(guests_raw)
        try:
            reservation_id = create_reservation(current_user.id, schedule_id, date_str, guests)
        except ValueError as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True, "reservation_id": reservation_id})

    @app.post("/reservations/<int:reservation_id>/cancel")
    @login_required
    def reservation_cancel(reservation_id):
        if current_user.role != "participant":
            return jsonify({"ok": False, "error": "Access denied."}), 403
        try:
            cancel_reservation(reservation_id, current_user.id)
        except ValueError as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True})

    @app.post("/guide/reports")
    @login_required
    def guide_report_create():
        if current_user.role != "guide":
            return jsonify({"ok": False, "error": "Access denied."}), 403
        payload = request.get_json(silent=True) or request.form
        try:
            occurrence_id = int(payload.get("occurrence_id"))
            actual = int(payload.get("actual_participants"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Invalid report data."}), 400

        # Save the evidence photo (only meaningful when attendance >= 1).
        evidence_path = ""
        photo = request.files.get("evidence_photo")
        if photo and photo.filename:
            from pathlib import Path
            import uuid as _uuid
            ext = Path(photo.filename).suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                return jsonify({"ok": False, "error": "Evidence photo must be an image (png, jpg, jpeg, webp, gif)."}), 400
            reports_dir = Path(app.root_path) / "static" / "img" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            unique_name = f"report_{_uuid.uuid4().hex}{ext}"
            photo.save(str(reports_dir / unique_name))
            evidence_path = f"img/reports/{unique_name}"

        try:
            create_guide_report(current_user.id, occurrence_id, actual, evidence_path)
        except (TypeError, ValueError) as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True})

    @app.post("/guide/tours")
    @login_required
    def guide_tour_create():
        """Accept a multipart/form-data POST from the Add Tour form and persist it."""
        if current_user.role != "guide":
            return jsonify({"ok": False, "error": "Access denied."}), 403

        try:
            title        = request.form.get("tour_title", "").strip()
            description  = request.form.get("brief_description", "").strip()
            meeting_point= request.form.get("meeting_point", "").strip()
            duration_raw = request.form.get("tour_duration", "90")
            max_raw      = request.form.get("max_people", "15")
            themes       = request.form.getlist("themes")
            stops        = request.form.getlist("stops[]")
            accessibility= request.form.getlist("accessibility")
            photo_files  = request.files.getlist("tour_photos")

            # Parse schedules from parallel arrays
            days      = request.form.getlist("schedule_day[]")
            times     = request.form.getlist("schedule_time[]")
            languages = request.form.getlist("schedule_language[]")
            schedules = [
                {"weekday": d, "start_time": t, "language": l}
                for d, t, l in zip(days, times, languages)
            ]

            slug = create_guide_tour(
                guide_id        = current_user.id,
                title           = title,
                description     = description,
                meeting_point   = meeting_point,
                duration_minutes= int(duration_raw),
                max_participants = int(max_raw),
                themes          = themes,
                stops           = stops,
                accessibility   = accessibility,
                schedules       = schedules,
                photo_files     = photo_files,
            )
        except (TypeError, ValueError) as error:
            return jsonify({"ok": False, "error": str(error)}), 400

        return jsonify({"ok": True, "slug": slug})

    @app.post("/guide/tours/<slug>")
    @login_required
    def guide_tour_update(slug):
        """Update an existing tour. Essential fields are locked once a
        reservation exists (enforced in update_guide_tour)."""
        if current_user.role != "guide":
            return jsonify({"ok": False, "error": "Access denied."}), 403
        try:
            days      = request.form.getlist("schedule_day[]")
            times     = request.form.getlist("schedule_time[]")
            languages = request.form.getlist("schedule_language[]")
            schedules = [
                {"weekday": d, "start_time": t, "language": l}
                for d, t, l in zip(days, times, languages)
            ]
            new_slug = update_guide_tour(
                guide_id         = current_user.id,
                slug             = slug,
                title            = request.form.get("tour_title", "").strip(),
                description      = request.form.get("brief_description", "").strip(),
                meeting_point    = request.form.get("meeting_point", "").strip(),
                duration_minutes = int(request.form.get("tour_duration", "90")),
                max_participants = int(request.form.get("max_people", "15")),
                themes           = request.form.getlist("themes"),
                stops            = request.form.getlist("stops[]"),
                accessibility    = request.form.getlist("accessibility"),
                schedules        = schedules,
                photo_files      = request.files.getlist("tour_photos"),
                keep_photo_ids   = request.form.getlist("keep_photo_ids[]"),
            )
        except (TypeError, ValueError) as error:
            return jsonify({"ok": False, "error": str(error)}), 400

        return jsonify({"ok": True, "slug": new_slug})

    @app.post("/guide/occurrences/<int:occurrence_id>/done")
    @login_required
    def guide_mark_done(occurrence_id):
        """Mark a scheduled tour occurrence as done → moves it to Tours History
        and opens a pending report (when it had reservations)."""
        if current_user.role != "guide":
            return jsonify({"ok": False, "error": "Access denied."}), 403
        try:
            mark_occurrence_done(current_user.id, occurrence_id)
        except (TypeError, ValueError) as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        return jsonify({"ok": True})

    return app


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _redirect_by_role(role):
    """Redirect a user to their appropriate dashboard after login."""
    if role == "guide":
        return redirect(url_for("guide_dashboard"))
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("participant_dashboard"))
