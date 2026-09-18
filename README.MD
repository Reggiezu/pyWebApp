# 12 Week Year Tracker

A Flask web app for running a [12 Week Year](https://12weekyear.com/) productivity cycle — weekly scoring against goals, a 13-week scorecard, and a live view into Google Calendar so planned time and logged results sit in one place instead of two.

Built to go deep on backend fundamentals that are easy to skip past with a framework or a managed auth provider: real OAuth2 implementation, relational schema design, and SQL from first principles.

## Why this project

Most personal-project auth is "add Firebase, npm install, done." This one isn't. The Google Calendar integration is built directly against Google's OAuth2 endpoints — no Firebase, no `next-auth`, no wrapper library abstracting the protocol away. That was a deliberate choice: understanding *why* a redirect URI has to be pre-registered, *why* PKCE exists, and *why* a refresh token is a different credential from an access token is a different skill than importing a package that handles it silently. The section below on the auth implementation goes into what that actually involved.

## Stack

- **Backend:** Flask, SQLAlchemy, Flask-Migrate (Alembic)
- **Database:** SQLite (dev) — MySQL migration planned for deployment
- **Auth:** Google OAuth2 (authorization code grant), implemented directly against `google-auth-oauthlib` and `google-auth`, no third-party auth wrapper
- **Frontend:** Jinja2 templates, hand-written CSS
- **Tooling:** Postman (manual protocol verification before any code), Git/GitHub with feature branches

## What's built

**Core tracker**
- Relational schema: `User`, `ScoreCard`, `ScorecardInit`, `Category`, `Goal`, `WeeklyCategoryScore`
- Weekly logging with upsert semantics — logging the same week twice updates the existing record instead of duplicating it
- 13-week scorecard view reading live from the database
- Schema migrations managed through Flask-Migrate/Alembic rather than hand-edited tables

**Google Calendar integration**
- Full OAuth2 authorization code flow implemented from scratch: `/authorize` builds the consent URL and redirects; `/oauth2callback` handles the return trip, verifies state, and exchanges the code for tokens
- CSRF protection via the OAuth `state` parameter, verified server-side against the session before any token exchange happens
- PKCE (Proof Key for Code Exchange) handled explicitly — the code verifier generated at `/authorize` is persisted and re-applied at `/oauth2callback`, since each route runs as a separate request with its own `Flow` object and no shared memory
- Access and refresh tokens persisted to a dedicated `UsersConfig` table (decoupled from `User` by design), rather than kept only in a browser session
- A `get_valid_credentials()` helper checks token expiry on every use and silently refreshes via the stored refresh token — no re-authorization prompt once a user has connected once
- Calendar list and event fetching against the real Calendar API (`AuthorizedSession`-based authenticated requests), with defensive parsing (`.get()` over direct key access) after hitting real-world malformed events — a cancelled, titleless meeting — that a naive implementation would crash on
- Dashboard UI: a "Connect Google Calendar" / "Connected ✓" indicator in the nav (via a Flask context processor, so the state is consistent across every page), and a live dropdown of upcoming events pulled straight from the API

## Architecture notes

A few decisions worth calling out, since the reasoning behind them matters more than the code itself:

- **Auth credentials live in their own table, not on `User`.** Same pattern as `ScorecardInit` — config and identity data are kept separate from the core user record, so the `User` model doesn't grow a dozen Google-specific columns it has no reason to know about.
- **Manual protocol testing came before any application code.** The full OAuth2 exchange — authorization URL, consent, code, token — was walked by hand in Postman first, so the Flask implementation was translating a flow that was already understood, not debugging the protocol and the framework at the same time.
- **API failures are isolated, not fatal.** An early version let a single malformed calendar event take down the entire dashboard route, including data that had nothing to do with Google Calendar. The fetch is now wrapped so a Calendar API failure degrades to an empty events list instead of a 500.

## Roadmap

This project follows an 8-week sprint plan. Sprints 1 (core tracker) and 2 (Calendar OAuth2 + read-side integration) are complete. Remaining work — Docker/MySQL/CI deployment, write-side Calendar events, and dashboard polish — is tracked internally and will be reflected here as it ships.

## Running locally

```bash
pip install -r requirements.txt
flask db upgrade
flask run
```

You'll need your own Google Cloud project with the Calendar API enabled and OAuth2 credentials downloaded as `client_secret.json` in the project root. `OAUTHLIB_INSECURE_TRANSPORT=1` is set for local HTTP development only — never in production.