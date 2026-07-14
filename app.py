from flask import Flask, render_template, request, redirect, url_for
from models import User, ScoreCard, Category, Goal, ScorecardInit, WeeklyCategoryScore, db, Base
from flask_migrate import Migrate


app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)
migrate = Migrate(app, db)


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


if __name__ == '__main__':
    app.run(debug=True)