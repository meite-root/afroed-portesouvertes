from flask import Flask, render_template, request, redirect
from datetime import datetime

app = Flask(__name__)

# For now, just store "users" in memory (later: DB)
users = []

@app.route("/")
def index():
    return render_template(
        "landing.html",
        year=datetime.now().year
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    # POST: user submitted form
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # super basic validation
    if not email or not password:
        return render_template("signup.html", error="Email and password are required.")

    # check if email already used
    if any(u["email"] == email for u in users):
        return render_template("signup.html", error="This email is already registered.")

    # TODO: hash password before storing (for now, keep it simple)
    users.append({"email": email, "password": password})

    print("Current users:", users)  # just to see it working in the console

    # later: redirect to login or dashboard
    return "Signup successful for: " + email

if __name__ == "__main__":
    app.run(debug=True)

# ============= PATHWAYS ==============
import os
import json
from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()

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
