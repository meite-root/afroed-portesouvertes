# AfroED Flask Refactor

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

- `FLASK_SECRET_KEY`
- `DATABASE_URL` (optional, defaults to local `afroed.db`)
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VERIFY_SERVICE_SID`
- `AFROED_ADMIN_PHONE` (optional bootstrap admin)
- `AFROED_ADMIN_PASSWORD` (optional bootstrap admin)
- `OPENAI_API_KEY`

## Run

```bash
python app.py
```

Startup automatically runs schema-compatible migrations:
- Creates the schema from `models.py`
- Adds auth/pathway columns/tables if missing
- Migrates legacy `users` rows into `student` records without deleting existing data

## Auth and OTP flow

1. Student signs up on `/signup` with name, phone, password, and consent.
2. Twilio Verify sends OTP (`/api/signup/send-otp`).
3. OTP verification (`/api/signup/verify-otp`) marks account verified, stores hashed password, logs student in.
4. Student can later login at `/login` with phone/email + password.

## Role-based routes

- Public: `/`, `/signup`, OTP endpoints, `/login`
- Student-only: `/dashboard`, `/pathways`, `/api/pathways`
- Admin-only: `/admin`, `/admin/students`, `/admin/students/<id>`

Events/calendar components were removed from the landing page and app routes.
