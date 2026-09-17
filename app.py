from flask import Flask, render_template, request, redirect, url_for, session, abort
from models import User, ScoreCard, Category, Goal, ScorecardInit, WeeklyCategoryScore, db, Base, UsersConfig
from flask_migrate import Migrate
from sqlalchemy import select
import google.oauth2.credentials
import google_auth_oauthlib.flow
import secrets
import os 
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)
migrate = Migrate(app, db)
app.secret_key=secrets.token_hex()

# --- Stub data (replace with SQLAlchemy in Sprint 1 Week 2) ---
weeks = [
    {"week_number": i, "goal1_score": None, "goal2_score": None, "goal3_score": None, "overall": None, "reflection": None}
    for i in range(1, 14)
]


# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html', weeks=weeks)


@app.route('/log', methods=['GET', 'POST'])
def log_week():
    if request.method == 'POST':
        week_num = int(request.form['week_number'])
        g1 = request.form.get('goal1_score')
        g2 = request.form.get('goal2_score')
        g3 = request.form.get('goal3_score')
        reflection = request.form.get('reflection')

        # Find and update the matching week in stub data
        for week in weeks:
            if week['week_number'] == week_num:
                week['goal1_score'] = g1
                week['goal2_score'] = g2
                week['goal3_score'] = g3
                week['reflection'] = reflection
                break

        return redirect(url_for('index'))

    return render_template('log_week.html')




@app.route('/authorize')
def auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar.readonly'])
    flow.redirect_uri = 'http://127.0.0.1:5000/oauth2callback'
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent')
    session['state'] = state
    session['code_verifier'] = flow.code_verifier
    return redirect(authorization_url)


@app.route('/oauth2callback')
def callback():
    if session['state'] != request.args.get('state'):
        abort(400)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar.readonly'])
    flow.redirect_uri = 'http://127.0.0.1:5000/oauth2callback'
    flow.code_verifier = session['code_verifier']
    flow.fetch_token(authorization_response=request.url)
    existing = db.session.execute(select(UsersConfig).where(UsersConfig.user_id==1)).scalars().first()
    if existing:
        existing.access_token = flow.credentials.token
        existing.refresh_token = flow.credentials.refresh_token
        existing.expiry = flow.credentials.expiry
        db.session.commit()
    else:
        config = UsersConfig(
                user_id=1,
                access_token=flow.credentials.token,
                refresh_token=flow.credentials.refresh_token,
                token_uri=flow.credentials.token_uri,
                client_id=flow.credentials.client_id,
                client_secret=flow.credentials.client_secret,
                scopes=flow.credentials.scopes,
                expiry=flow.credentials.expiry
            )
        db.session.add(config)
        db.session.commit() 

if __name__ == '__main__':
    app.run(debug=True)