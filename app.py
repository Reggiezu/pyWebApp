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

# --- Routes ---

@app.route('/')
def index():
    user_scorecard = db.session.execute(select(ScoreCard).where(ScoreCard.user_id==1)).scalars().all()
    return render_template('index.html', weeks=user_scorecard)


@app.route('/log_week', methods=['GET', 'POST'])
def log_week():
    if request.method == 'POST':
        week_number = int(request.form.get('week_number') or 1)
        goal1_score = int(request.form.get('goal1_score') or 0)
        goal2_score = int(request.form.get('goal2_score') or 0)
        goal3_score = int(request.form.get('goal3_score') or 0)
        week_reflection = request.form.get('reflection') or "No reflection"
        scores = [
            (1, goal1_score),
            (2, goal2_score),
            (3, goal3_score),
        ]
        # check if row exists
        existing = db.session.execute(
            select(ScoreCard).where(ScoreCard.user_id==1, ScoreCard.week_number==week_number)
        ).scalars().first()
        if existing:
           # update scorecard
            existing.reflection_week = week_reflection
            # update each category score
            for category_id, percentage in scores:
                existing_score = db.session.execute(
                    select(WeeklyCategoryScore).where(
                        WeeklyCategoryScore.scoreCard_id == existing.id,
                        WeeklyCategoryScore.category_id == category_id
                    )
                ).scalars().first()
                
                if existing_score:
                    existing_score.category_percentage = percentage

            db.session.commit()
            return redirect(url_for('index'))
        else:
            # Find and update the matching week in stub data
            newWeek = ScoreCard(user_id=1, week_number=week_number, reflection_week=week_reflection)
            db.session.add(newWeek) 
            for category_id, percentage in scores:
                newCategoryScore = WeeklyCategoryScore(user_id=1, scoreCard_id=1, category_id=category_id,week_number=week_number,category_percentage=percentage ) 
                db.session.add(newCategoryScore)
            db.session.commit() 
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