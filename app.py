import os
import json
import sqlite3
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from openai import OpenAI
from twilio.rest import Client

app = Flask(__name__)
client = OpenAI()

DB_PATH = os.path.join(os.path.dirname(__file__), "afroed.db")
pending_signups = {}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                verified_at TEXT NOT NULL
            )
            """
        )


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


def upsert_user(name, phone):
    verified_at = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO users (name, phone, verified_at)
            VALUES (?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
                name = excluded.name,
                verified_at = excluded.verified_at
            """,
            (name, phone, verified_at),
        )


def fetch_users():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT name, phone, verified_at
            FROM users
            ORDER BY verified_at DESC
            """
        ).fetchall()

    users = []
    for row in rows:
        verified_at = row["verified_at"]
        try:
            verified_dt = datetime.fromisoformat(verified_at)
            verified_display = verified_dt.strftime("%b %d, %Y · %H:%M UTC")
        except ValueError:
            verified_display = verified_at

        name = row["name"]
        initials = "".join([part[0].upper() for part in name.split()[:2]]) or "AE"
        users.append(
            {
                "name": name,
                "phone": row["phone"],
                "verified_at": verified_at,
                "verified_display": verified_display,
                "initials": initials,
            }
        )

    return users


init_db()

@app.route("/")
def index():
    return render_template(
        "landing.html",
        year=datetime.now().year
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        return jsonify({"error": "Use the OTP endpoints for signup."}), 405
    return render_template("signup.html")

@app.route("/signup/profile")
def signup_profile():
    return render_template(
        "signup_profile.html",
        year=datetime.now().year,
    )


@app.route("/signup/confirmation")
def signup_confirmation():
    return render_template(
        "signup_confirmation.html",
        year=datetime.now().year,
    )


@app.route("/users")
def users_dashboard():
    users = fetch_users()
    total_users = len(users)
    newest = users[0]["verified_display"] if users else "No signups yet"
    return render_template(
        "users.html",
        users=users,
        total_users=total_users,
        newest=newest,
        year=datetime.now().year,
        updated_at=datetime.utcnow().strftime("%b %d, %Y · %H:%M UTC"),
    )


@app.route("/api/signup/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name or not phone:
        return jsonify({"error": "Name and phone are required."}), 400

    try:
        client = get_twilio_client()
        service_sid = get_verify_service_sid()
        client.verify.v2.services(service_sid).verifications.create(
            to=phone,
            channel="sms",
        )
        pending_signups[phone] = name
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
        client = get_twilio_client()
        service_sid = get_verify_service_sid()
        verification = client.verify.v2.services(service_sid).verification_checks.create(
            to=phone,
            code=code,
        )
        if verification.status != "approved":
            return jsonify({"error": "Invalid verification code."}), 400

        name = pending_signups.pop(phone, "AfroED User")
        upsert_user(name, phone)
        return jsonify({"status": "verified"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    app.run(debug=True)

# ============= PATHWAYS ==============

SUBJECTS = [
    "Mathematics", "Economics", "Computer Science", "Biology", "Chemistry",
    "Physics", "Statistics", "Literature", "History", "Geography",
    "Business", "Accounting", "Law", "Art & Design", "Psychology"
]

@app.route("/pathways")
def pathways():
    return render_template("pathways.html", subjects=SUBJECTS)

@app.route("/api/pathways", methods=["POST"])
def api_pathways():
    data = request.get_json(force=True, silent=True) or {}
    subjects = data.get("subjects", [])

    # Basic validation (keep V1 robust)
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
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        payload = json.loads(content)

        # Defensive cleanup: ensure expected keys exist
        if "pathways" not in payload or not isinstance(payload["pathways"], list):
            return jsonify({"error": "Model returned unexpected format."}), 500

        return jsonify(payload)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
