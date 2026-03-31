import json
import os
from datetime import datetime

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from openai import OpenAI
from sqlalchemy import inspect, or_, text
from twilio.rest import Client
from werkzeug.security import check_password_hash, generate_password_hash

from models import Field, Opportunity, PathwayResult, Student, StudentOpportunity, db


SUBJECTS = [
    "Mathematics", "Economics", "Computer Science", "Biology", "Chemistry",
    "Physics", "Statistics", "Literature", "History", "Geography",
    "Business", "Accounting", "Law", "Art & Design", "Psychology"
]

pending_signups = {}
openai_client = OpenAI()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'afroed.db')}",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Student, int(user_id))

    with app.app_context():
        run_migrations()
        ensure_admin_user()

    register_routes(app)
    return app


def get_twilio_client():
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise ValueError("Missing Twilio credentials.")
    return Client(account_sid, auth_token)


def get_verify_service_sid():
    service_sid = os.environ.get("TWILIO_VERIFY_SERVICE_SID")
    if not service_sid:
        raise ValueError("Missing Twilio Verify service SID.")
    return service_sid


def run_migrations():
    db.create_all()

    inspector = inspect(db.engine)
    if "student" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("student")}
        if "password_hash" not in columns:
            db.session.execute(text("ALTER TABLE student ADD COLUMN password_hash VARCHAR(255)"))
        if "is_verified" not in columns:
            db.session.execute(text("ALTER TABLE student ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 0"))
        if "role" not in columns:
            db.session.execute(text("ALTER TABLE student ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'student'"))

    if "users" in inspector.get_table_names():
        rows = db.session.execute(text("SELECT name, phone, verified_at FROM users")).mappings().all()
        for row in rows:
            name = (row["name"] or "AfroED User").strip()
            name_parts = name.split(maxsplit=1)
            first_name = name_parts[0] if name_parts else "AfroED"
            last_name = name_parts[1] if len(name_parts) > 1 else "User"
            phone = (row["phone"] or "").strip()
            existing = Student.query.filter_by(phone_number=phone).first()
            if existing:
                if not existing.is_verified:
                    existing.is_verified = True
                continue
            db.session.add(
                Student(
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone,
                    is_verified=True,
                    role="student",
                    status=True,
                )
            )

    db.session.commit()


def ensure_admin_user():
    admin_phone = os.environ.get("AFROED_ADMIN_PHONE")
    admin_password = os.environ.get("AFROED_ADMIN_PASSWORD")
    if not admin_phone or not admin_password:
        return

    admin = Student.query.filter_by(phone_number=admin_phone).first()
    if not admin:
        admin = Student(
            first_name="Admin",
            last_name="User",
            phone_number=admin_phone,
            role="admin",
            is_verified=True,
            status=True,
        )
        db.session.add(admin)

    admin.password_hash = generate_password_hash(admin_password)
    admin.role = "admin"
    admin.is_verified = True
    db.session.commit()


def admin_required():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


def register_routes(app):
    @app.route("/")
    def index():
        return render_template("landing.html", year=datetime.now().year)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            return jsonify({"error": "Use the OTP endpoints for signup."}), 405
        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            identifier = request.form.get("identifier", "").strip()
            password = request.form.get("password", "")
            user = Student.query.filter(
                or_(Student.phone_number == identifier, Student.email == identifier)
            ).first()
            if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
                flash("Identifiants invalides.", "error")
                return render_template("login.html"), 401
            if not user.is_verified:
                flash("Veuillez vérifier votre compte via OTP.", "error")
                return render_template("login.html"), 403
            login_user(user)
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/signup/profile")
    @login_required
    def signup_profile():
        return redirect(url_for("dashboard"))

    @app.route("/signup/confirmation")
    def signup_confirmation():
        return render_template("signup_confirmation.html", year=datetime.now().year)

    @app.route("/dashboard", methods=["GET", "POST"])
    @login_required
    def dashboard():
        if current_user.role != "student":
            return redirect(url_for("admin_dashboard"))

        all_fields = Field.query.order_by(Field.name).all()
        available_opportunities = Opportunity.query.filter_by(available=True).order_by(Opportunity.created_at.desc()).all()

        if request.method == "POST":
            field_ids = request.form.getlist("field_ids")
            selected_fields = Field.query.filter(Field.id.in_(field_ids)).all() if field_ids else []
            current_user.fields_of_interest = selected_fields

            track_ids = {int(v) for v in request.form.getlist("tracked_opportunity_ids") if v.isdigit()}
            existing_map = {so.opportunity_id: so for so in current_user.student_opportunities}

            for opportunity in available_opportunities:
                existing = existing_map.get(opportunity.id)
                should_track = opportunity.id in track_ids
                if existing:
                    existing.tracked = should_track
                elif should_track:
                    db.session.add(StudentOpportunity(student_id=current_user.id, opportunity_id=opportunity.id, tracked=True))

            db.session.commit()
            flash("Vos préférences ont été mises à jour.", "success")
            return redirect(url_for("dashboard"))

        pathway_history = (
            PathwayResult.query.filter_by(student_id=current_user.id)
            .order_by(PathwayResult.created_at.desc())
            .all()
        )

        return render_template(
            "dashboard.html",
            all_fields=all_fields,
            available_opportunities=available_opportunities,
            tracked_ids={so.opportunity_id for so in current_user.student_opportunities if so.tracked},
            pathway_history=pathway_history,
            year=datetime.now().year,
        )

    @app.route("/admin")
    @login_required
    def admin_dashboard():
        admin_required()
        student_count = Student.query.filter_by(role="student").count()
        verified_count = Student.query.filter_by(role="student", is_verified=True).count()
        return render_template("admin.html", student_count=student_count, verified_count=verified_count)

    @app.route("/admin/students")
    @login_required
    def admin_students():
        admin_required()
        query = request.args.get("q", "").strip()
        students_query = Student.query.filter_by(role="student")
        if query:
            students_query = students_query.filter(
                or_(
                    Student.first_name.ilike(f"%{query}%"),
                    Student.last_name.ilike(f"%{query}%"),
                    Student.phone_number.ilike(f"%{query}%"),
                    Student.email.ilike(f"%{query}%"),
                )
            )
        students = students_query.order_by(Student.created_at.desc()).all()
        return render_template("admin_students.html", students=students, q=query)

    @app.route("/admin/students/<int:student_id>")
    @login_required
    def admin_student_detail(student_id):
        admin_required()
        student = Student.query.get_or_404(student_id)
        if student.role != "student":
            abort(404)
        pathway_history = PathwayResult.query.filter_by(student_id=student.id).order_by(PathwayResult.created_at.desc()).all()
        return render_template("admin_student_detail.html", student=student, pathway_history=pathway_history)

    @app.route("/pathways")
    @login_required
    def pathways():
        return render_template("pathways.html", subjects=SUBJECTS)

    @app.route("/api/signup/send-otp", methods=["POST"])
    def send_otp():
        data = request.get_json(force=True, silent=True) or {}
        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        password = str(data.get("password", "")).strip()

        if not name or not phone or not password:
            return jsonify({"error": "Name, phone, and password are required."}), 400

        try:
            twilio_client = get_twilio_client()
            service_sid = get_verify_service_sid()
            twilio_client.verify.v2.services(service_sid).verifications.create(to=phone, channel="sms")
            pending_signups[phone] = {"name": name, "password": password}
            return jsonify({"status": "sent"})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/signup/verify-otp", methods=["POST"])
    def verify_otp():
        data = request.get_json(force=True, silent=True) or {}
        phone = str(data.get("phone", "")).strip()
        code = str(data.get("code", "")).strip()

        if not phone or not code:
            return jsonify({"error": "Phone and code are required."}), 400

        try:
            twilio_client = get_twilio_client()
            service_sid = get_verify_service_sid()
            verification = twilio_client.verify.v2.services(service_sid).verification_checks.create(to=phone, code=code)
            if verification.status != "approved":
                return jsonify({"error": "Invalid verification code."}), 400

            pending = pending_signups.pop(phone, None)
            if not pending:
                pending = {"name": "AfroED User", "password": "ChangeMe123!"}

            name_parts = pending["name"].split(maxsplit=1)
            first_name = name_parts[0] if name_parts else "AfroED"
            last_name = name_parts[1] if len(name_parts) > 1 else "User"

            user = Student.query.filter_by(phone_number=phone).first()
            if not user:
                user = Student(first_name=first_name, last_name=last_name, phone_number=phone, role="student")
                db.session.add(user)

            user.first_name = first_name
            user.last_name = last_name
            user.password_hash = generate_password_hash(pending["password"])
            user.is_verified = True
            user.status = True
            user.role = user.role or "student"
            db.session.commit()

            login_user(user)
            return jsonify({"status": "verified"})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/pathways", methods=["POST"])
    @login_required
    def api_pathways():
        data = request.get_json(force=True, silent=True) or {}
        subjects = data.get("subjects", [])

        if not isinstance(subjects, list) or len(subjects) != 3:
            return jsonify({"error": "Provide exactly 3 subjects."}), 400

        subjects = [str(s).strip() for s in subjects]
        if any(s not in SUBJECTS for s in subjects):
            return jsonify({"error": "Invalid subject in selection."}), 400

        prompt = f"""
You are AfroED's pathway suggestion engine.
Given exactly three school subjects, propose 5 realistic career pathways.
Focus on globally valid pathways and include West Africa context when relevant, without stereotypes.

Return ONLY valid JSON with this exact shape:
{{
  "pathways": [
    {{
      "title": "string",
      "fit_score": 0-100,
      "why_this_fits": "string",
      "typical_education_path": ["string", "..."],
      "example_roles": ["string", "..."],
      "first_next_step": "string"
    }}
  ]
}}

Rules:
- Provide exactly 5 pathways.
- Keep education steps concrete (e.g., "BSc in X", "MPH", "Cert in Y").
- Avoid mentioning specific universities.
- No markdown, no extra keys.

Subjects: {subjects}
""".strip()

        try:
            resp = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            payload = json.loads(resp.choices[0].message.content)
            if "pathways" not in payload or not isinstance(payload["pathways"], list) or len(payload["pathways"]) != 5:
                return jsonify({"error": "Model returned unexpected format."}), 500

            db.session.add(
                PathwayResult(
                    student_id=current_user.id,
                    selected_subjects_json=json.dumps(subjects),
                    results_json=json.dumps(payload),
                )
            )
            db.session.commit()
            return jsonify(payload)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
