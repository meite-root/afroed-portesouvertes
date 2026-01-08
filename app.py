import os
import json
from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
from openai import OpenAI
import secrets

app = Flask(__name__)
client = OpenAI()

# For now, just store "users" in memory (later: DB)
users = []
pending_verifications = {}

COUNTRIES = [
    {"name": "Cote d’Ivoire", "code": "+225"},
    {"name": "Ghana", "code": "+233"},
    {"name": "Senegal", "code": "+221"},
    {"name": "Nigeria", "code": "+234"},
    {"name": "Benin", "code": "+229"},
]

@app.route("/")
def index():
    return render_template(
        "landing.html",
        year=datetime.now().year
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", countries=COUNTRIES, step="enter_phone")

    # POST: user submitted form
    step = request.form.get("step", "enter_phone")
    country = request.form.get("country", "").strip()
    phone = request.form.get("phone", "").strip()
    phone_clean = phone.replace(" ", "")

    if step == "enter_phone":
        if not country or not phone:
            return render_template(
                "signup.html",
                countries=COUNTRIES,
                step="enter_phone",
                error="Country and phone number are required.",
            )

        if not phone_clean.isdigit():
            return render_template(
                "signup.html",
                countries=COUNTRIES,
                step="enter_phone",
                error="Please enter digits only for your phone number.",
            )

        if any(u["phone"] == phone_clean and u["country"] == country for u in users):
            return render_template(
                "signup.html",
                countries=COUNTRIES,
                step="enter_phone",
                error="This phone number is already registered.",
            )

        code = str(secrets.randbelow(100000)).zfill(5)
        pending_verifications[(country, phone_clean)] = code

        return render_template(
            "signup.html",
            countries=COUNTRIES,
            step="verify",
            country=country,
            phone=phone,
        )

    verification_code = request.form.get("verification_code", "").strip()
    stored_code = pending_verifications.get((country, phone_clean))

    if not stored_code or verification_code != stored_code:
        return render_template(
            "signup.html",
            countries=COUNTRIES,
            step="verify",
            country=country,
            phone=phone,
            error="The verification code is invalid. Please try again.",
        )

    users.append({"country": country, "phone": phone_clean})
    pending_verifications.pop((country, phone_clean), None)
    print("Current users:", users)  # just to see it working in the console

    return render_template(
        "signup.html",
        countries=COUNTRIES,
        step="success",
        country=country,
        phone=phone,
    )

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
