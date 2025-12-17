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
