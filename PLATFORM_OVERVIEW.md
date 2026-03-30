# AfroED Platform Overview

## What AfroED is
AfroED is a lightweight web platform that helps learners discover educational opportunities, sign up for updates, and get guidance on what to study next. It combines a user-friendly public website with OTP-based onboarding and AI-powered career pathway suggestions.

The product is built as a Flask app with server-rendered pages, a SQLite user store, Twilio Verify for phone validation, and OpenAI-powered recommendation logic.

## Core features

### 1) Public landing experience
- Branded landing page introducing AfroED’s mission.
- Highlights partner schools across Africa and beyond.
- Includes a simple events calendar and CTA flow to signup.

### 2) OTP-secured signup flow
- Learners can submit name + phone number.
- The backend sends a one-time verification code by SMS (Twilio Verify).
- Users confirm ownership of their number with a 6-digit code.
- Verified users are stored in a local SQLite database.

### 3) User dashboard for verified signups
- Admin/community view at `/users` listing verified learners.
- Displays total signups, most recent verification, and per-user cards.
- User cards include initials, phone, and verification timestamp.

### 4) AI Pathway Finder
- Users choose exactly three school subjects.
- AfroED calls the OpenAI API to generate five realistic career pathways.
- Each pathway includes:
  - title
  - fit score (0-100)
  - why it fits
  - typical education path
  - example roles
  - first next step
- API enforces input validation and JSON-structured outputs.

### 5) Data and privacy support in UX
- Signup screen includes privacy notice and consent checkbox.
- Front-end and backend validation are in place for safer form handling.

## Technical snapshot
- **Backend:** Flask (`app.py`)
- **Frontend:** HTML templates + vanilla JavaScript
- **Database:** SQLite (`afroed.db`)
- **Messaging/verification:** Twilio Verify (SMS OTP)
- **AI layer:** OpenAI Chat Completions API (`gpt-4.1-mini`)

## End-to-end user journey
1. User lands on AfroED home page.
2. User registers with name and phone number.
3. User verifies phone with OTP.
4. Verified profile is recorded and visible on the dashboard.
5. User can also explore pathways by selecting 3 favorite subjects.
6. Platform returns AI-generated career and education recommendations.

## Why this platform is valuable
- Reduces information gaps for students seeking educational opportunities.
- Adds trust and quality through verified user onboarding.
- Turns broad subject interests into practical career next steps.
- Keeps implementation lean and extensible for rapid iteration.
