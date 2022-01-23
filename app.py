from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from flask_login import UserMixin, login_user, login_required, logout_user, current_user,  LoginManager
from werkzeug.utils import redirect, secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cheer.db'
app.config['SECRET_KEY'] = '70fdcfe8c41540718a930927'
db = SQLAlchemy(app)

login_manager= LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    firstName = db.Column(db.String(50),nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    
    #dob = db.Column(db.DateTime, nullable = True)    
    school_URN = db.Column(db.Integer, nullable = True)
    #start_date = db.Column(db.DateTime, nullable = True, default=datetime.utcnow)
    
    email = db.Column(db.String(70), nullable = False)
    password = db.Column(db.String(255), nullable = False)
    usertype = db.Column(db.Integer, default = 0)
    #usertype = {0: athlete, 1: coach, 2: athlete/coach, 3: admin. 4: admin/coach}

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

class Team_Sheet(db.Model):
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
    firstName= db.Column(db.String(50), nullable = False)
    surname= db.Column(db.String(50), nullable = False)
    number= db.Column(db.String(15), nullable = False)

class Events(db.Model):
    events_id= db.Column(db.Integer, primary_key=True)
    team_id= db.Column(db.Integer)
    event_name= db.Column(db.Text, nullable =False)
    event_start_date= db.Column(db.Date, nullable = False)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup',  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data=request.form
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        surname = request.form.get('surname')
        dob = request.form.get("dob")
        school_URN= request.form.get("school_URN")
        start_date= request.form.get("start_date")
        usertype= request.form.get("usertype")
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = Users.query.filter_by(email=email).first()
        if user:
            flash('There is already an account using this email', category='error')
        elif len(email) <= 3:
            flash('Your email is too short.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            new_user = Users(email=email, firstName=firstName, surname=surname, school_URN=school_URN, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created.', category='success')
            return redirect(url_for('index'))
        print(data)
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Login Successful', category='success')
                login_user(user)
                return redirect(url_for('manage_teams'))
            else:
                flash('Password is incorrect, try again', category='error')
        else:
            flash('There is no existing user with this email', category='error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/events')
def events():
    return 'This is the page of events'

@app.route('/admin')
def admin():
    return 'This is the admin index page'

@app.route('/admin/fees')
def manage_fees():
    return 'This is where the admin views everyone\'s fees'

@app.route('/teams', methods=['GET','POST'])
@login_required
def manage_teams():
    if request.method == 'POST':
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
       return render_template('index.html')

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
