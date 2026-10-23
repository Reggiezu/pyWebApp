# 12 Week Year Tracker

![CI](https://github.com/Reggiezu/pyWebApp/actions/workflows/ci.yml/badge.svg)

A Flask web app for running a [12 Week Year](https://12weekyear.com/) productivity cycle: weekly scoring against goals, a 13-week scorecard, and a live view into Google Calendar so planned time and logged results sit in one place instead of two.

Built to go deep on backend fundamentals that are easy to skip with a framework or a managed auth provider: a hand-built OAuth2 flow, relational schema design, and running the same app across dev, CI, and a self-hosted deployment.

## Why this project

Most personal-project auth is "add Firebase, npm install, done." This one isn't. The Google Calendar integration is built directly on Google's OAuth2 endpoints, with no auth-as-a-service wrapper hiding the protocol. Understanding why a redirect URI has to be pre-registered, why PKCE exists, and why a refresh token is a different credential from an access token is a different skill than importing a package that handles it silently.

## Stack

- **Backend:** Python 3.12, Flask, SQLAlchemy, Flask-Migrate (Alembic)
- **Database:** MySQL 8.4 (SQLite was used in early development)
- **Auth:** Google OAuth2 authorization code grant with PKCE, via `google-auth-oauthlib` and `google-auth`
- **Frontend:** Jinja2 templates, hand-written CSS, vanilla JS
- **Infrastructure:** Docker and Docker Compose, GitHub Actions CI, self-hosted and reachable over a private tailnet only
- **Tooling:** Postman (protocol verification before any code), Git/GitHub with feature branches and PRs

## What's built

**Core tracker**
- Relational schema: `User`, `ScoreCard`, `ScorecardInit`, `Category`, `Goal`, `WeeklyCategoryScore`, `UsersConfig`
- Weekly logging with upsert semantics, so logging the same week twice updates the record instead of duplicating it
- 13-week scorecard view reading live from the database
- Schema changes managed through Alembic migrations

**Google Calendar integration**
- Authorization code flow implemented directly: `/authorize` builds the consent URL, `/oauth2callback` verifies state and exchanges the code for tokens
- CSRF protection through the OAuth `state` parameter, checked server-side before any token exchange
- PKCE handled explicitly: the code verifier created at `/authorize` is stored in the session and re-applied at `/oauth2callback`
- Tokens persisted in a dedicated `UsersConfig` table, separate from `User`
- `get_valid_credentials()` checks expiry on every use and refreshes silently from the stored refresh token
- Calendar list and event fetching with defensive parsing; an API failure degrades to an empty event list instead of a 500

**Deployment and CI**
- Dockerfile and Compose stack (Flask + MySQL) with a healthcheck on a dedicated `/health` route
- Configuration comes from environment variables: database host and port, and the session secret key
- The app is published only to localhost on its host and exposed to my own devices over a private tailnet. Nothing is open to the public internet
- Nightly database dump to a second machine, with a restore test
- GitHub Actions runs on every PR and push to `master`: installs dependencies, checks the app imports, and runs the migrations against a throwaway MySQL 8.4 service container

## Architecture decisions

- **Credentials live in their own table.** Same pattern as `ScorecardInit`: identity and integration config stay separate, so `User` doesn't accumulate provider-specific columns.
- **Protocol first, code second.** The full OAuth2 exchange was walked by hand in Postman before any Flask code, so the implementation translated a flow I already understood.
- **SQLite hid problems MySQL caught.** Moving to MySQL exposed two things SQLite let through: `VARCHAR` columns require an explicit length, and foreign keys are actually enforced (OAuth failed until a `users` row existed). Running migrations against real MySQL in CI means these surface on a pull request, not on the server.
- **MySQL DDL isn't transactional.** A migration that failed partway left tables behind while Alembic's version table stayed empty, so the next run tried to recreate them. Recovery meant resetting the database so the schema and Alembic's ledger agreed again.
- **A stable secret key, and a loud failure without one.** Flask signs session cookies with the secret key, and the OAuth handshake stores `state` and the PKCE verifier in the session. A key regenerated on every start breaks that handshake after any restart, and breaks it intermittently with multiple worker processes. The key is now read from the environment, and the app refuses to start if it's missing.
- **Healthchecks must be able to fail.** The container healthcheck hits a trivial `/health` route, not `/`, which queries the database and Google on every call. It was verified to fail on a bad response before it was trusted.

## Running locally

You need Python 3.12, Docker, and a Google Cloud project with the Calendar API enabled and OAuth2 credentials saved as `client_secret.json` in the project root.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values
```

Start a throwaway MySQL (port 3307 avoids clashing with a MySQL already on 3306):

```bash
docker run -d --name 12wy-dev-mysql -p 127.0.0.1:3307:3306 \
  -e MYSQL_ROOT_PASSWORD=dev-root \
  -e MYSQL_DATABASE=twelvewy \
  -e MYSQL_USER=twelvewy_app \
  -e MYSQL_PASSWORD=dev-pass \
  mysql:8.4
```

Set `MYSQL_PASSWORD=dev-pass`, `MYSQL_HOST=127.0.0.1`, and `MYSQL_PORT=3307` in `.env`, along with a `SECRET_KEY` generated with `python -c "import secrets; print(secrets.token_hex(32))"`.

```bash
flask db upgrade
```

The app currently assumes a single user with `id = 1`, so insert one before connecting Google Calendar:

```bash
docker exec -it 12wy-dev-mysql mysql -u twelvewy_app -pdev-pass twelvewy \
  -e "INSERT INTO users (id, username) VALUES (1, 'your-name');"
```

```bash
flask run
```

`OAUTHLIB_INSECURE_TRANSPORT=1` is set in `app.py` so the OAuth flow works over plain HTTP at `127.0.0.1`. It is not appropriate for a public deployment; making it conditional is on the roadmap.

## Configuration

Copy `.env.example` to `.env`. The app reads `SECRET_KEY`, `MYSQL_PASSWORD`, `MYSQL_HOST` (default `12wy-mysql`, the Compose service name), and `MYSQL_PORT` (default `3306`). `MYSQL_ROOT_PASSWORD` and `MYSQL_USER` are used by the MySQL container only.

## Roadmap

Planned, not yet built:
- Gunicorn in place of Flask's development server, plus proxy-header handling for HTTPS
- OAuth redirect URI configurable per environment
- pytest suite running in CI
- Seeding the initial user through a migration or CLI command instead of by hand
- Demo mode with sample data
- Write-side Calendar events