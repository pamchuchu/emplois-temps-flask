# Emplois du temps — Web + API (Option B)

Application complète (Flask backend + REST API) prête à déployer sur Render/Railway/Heroku.
Conçue pour un usage scolaire (Cameroun). Fournit:
- Admin web UI (templates)
- REST API endpoints (CRUD pour classes, subjects, rooms, timeslots, users, schedule)
- Authentification JWT (login/register)
- Postgres-ready (via DATABASE_URL) or SQLite for local testing
- CORS enabled for mobile app consumption

## Quick start (local)
1. `python3 -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and adjust DATABASE_URL
4. `python init_db.py`
5. `python app.py` (or `gunicorn app:app`)

## Deploy
- Push to GitHub, connect Render/Railway/Heroku.
- Use Render: New Web Service → select repo → set start command `gunicorn app:app`
- Set environment variable `DATABASE_URL` (Postgres URL) and `SECRET_KEY`

## API (examples)
- POST /api/auth/register {email, full_name, password}
- POST /api/auth/login {email, password} -> returns access_token
- GET /api/classes (auth optional)
- POST /api/schedule (Authorization: Bearer <token>) -> creates schedule entry with conflict checks

