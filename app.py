from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from datetime import datetime

from werkzeug.utils import redirect, secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cheer.db'
db = SQLAlchemy(app)

class Admin(db.Model):#add password
    admin_id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(50), nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    email_address = db.Column(db.String(70), nullable = False)

class Coach(db.Model): #add password
    coach_id= db.Column(db.Integer, primary_key= True)
    forename= db.Column(db.String(50),nullable = False)
    surname= db.Column(db.String(50),nullable = False)
    email= db.Column(db.String(70), nullable = False)

class Athlete(db.Model):#add password
    athlete_id = db.Column(db.Integer, primary_key = True)
    forename = db.Column(db.String(50),nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    dob = db.Column(db.Date, nullable = False)
    school_URN = db.Column(db.Integer, nullable = True)
    start_date = db.Column(db.Date, nullable = False, default=datetime.utcnow)
    email = db.Column(db.String(70), nullable = False)

class Fees(db.Model):
    fees_id = db.Column(db.Integer, primary_key= True)
    admin_id = db.Column(db.Integer)
    athlete_id = db.Column(db.Integer)
    amount = db.Column(db.Float, nullable = False)
    paid_date = db.Column(db.DateTime, nullable = False, default= 'N/A')

class Teams(db.Model):
    team_id = db.Column(db.Integer, primary_key= True)
    coach_id = db.Column(db.Integer)
    athlete_id = db.Column(db.Integer)
    team_name= db.Column(db.String(20), nullable= False)
    max_age = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return 'Team' +str(self.team_id)

class Team_Sheet(db.Model):#add default time
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    team_id= db.Column(db.Integer)
    athlete_id= db.Column(db.Integer)
    role= db.Column(db.String(10), default = 'Tumbler')
    
    
class Training(db.Model):
    training_id= db.Column(db.Integer, primary_key=True)
    team_id= db.Column(db.Integer)
    coach_id= db.Column(db.Integer)
    athlete_id= db.Column(db.Integer)
    start_date_time= db.Column(db.DateTime, nullable = False)
    attendance= db.Column(db.Boolean, nullable = False)

class Contacts(db.Model):
    contacts_id= db.Column(db.Integer, primary_key=True)
    athlete_id= db.Column(db.Integer)
    forename= db.Column(db.String(50), nullable = False)
    surname= db.Column(db.String(50), nullable = False)
    number= db.Column(db.String(15), nullable = False)

class Events(db.Model):
    events_id= db.Column(db.Integer, primary_key=True)
    team_id= db.Column(db.Integer)
    event_name= db.Column(db.Text, nullable =False)
    event_start_date= db.Column(db.Date, nullable = False)




all_posts =[
    {
      'title':'Post 1',
      'content': 'This is the content of post 1. Lalalalalla',
      'author': 'Kamdi'
    },
    {
      'title':'Post 2',
      'content': 'This is the content of post 2. Lalalalalla'  
    }
]

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/posts')
# def posts():
#     return render_template('posts.html', posts=all_posts)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/events')
def events():
    return 'This is the page of events'

@app.route('/admin')
def admin():
    return 'This is the admin index page'

@app.route('/admin/fees')
def manage_fees():
    return 'This is where the admin views everyone\'s fees'

@app.route('/admin/teams', methods=['GET','CREATE'])
def manage_teams():
    if request.method == 'CREATE':
        team_name= request.form['team_name']
        team_id= request.form['team_id']
        coach_id= request.form['coach_id']
        athlete_id= request.form['athlete_id']
        max_age= request.form['max_age']
        new_team = Teams(team_id=team_id, coach_id=coach_id, athlete_id=athlete_id, team_name=team_name, max_age=max_age)
        db.session.add(new_team)
        db.session.commit()
        return redirect('/admin/teams')
    else:
       all_teams = Teams.query.all()
       return render_template('teams.html')

@app.route('/admin/training')
def manage_training():
    return 'This is where the admin manages all training sessions'

@app.route('/admin/contacts')
def manage_contacts():
    return 'This is where the admin views all contact information'

@app.route('/coach')
def coach():
    return 'This is the coach index page'

@app.route('/coach/team')
def team1():
    return 'This is the team both coaches and athletes will see'

@app.route('/coach/teamsheet')
def create_teamsheet():
    return 'Allow coach to create teamsheet'

@app.route('/coach/training')
def view_training1():
    return 'View team training sessions'

@app.route('/coach/contacts')
def view_contacts():
    return 'View contacts for the team'

@app.route('/athlete')
def athlete():
    return 'This is the athlete index page'

@app.route('/athlete/team')
def team2():
    return 'This is the team both coaches and athletes will see'

@app.route('/athlete/teamsheet')
def view_teamsheet():
    return 'Allow athlete to view teamsheet'

@app.route('/athlete/training')
def view_training2():
    return 'Allow athlete to see their upcoming and previous training sessions'

@app.route('/athlete/fees')
def view_fees():
    return 'Allow athlete to manage own fees'

if __name__ == "__main__":
    app.run(debug=True)
