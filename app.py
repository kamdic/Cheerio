from operator import itemgetter
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, login_user, login_required, logout_user, LoginManager, current_user
from werkzeug.utils import redirect
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
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    firstName = db.Column(db.String(50),nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    dob = db.Column(db.DateTime, nullable = False)    
    school_URN = db.Column(db.Integer, nullable = True)
    start_date = db.Column(db.DateTime, nullable = True, default=datetime.utcnow)
    email = db.Column(db.String(70), nullable = False)
    password = db.Column(db.String(255), nullable = False)
    usertype = db.Column(db.Integer, default = -1)
    verified = db.Column(db.Integer, default = 0)
    #usertype = {0: athlete, 1: coach, 2: athlete/coach, 3: admin. 4: admin/coach}

class Fees(db.Model):
    fees_id = db.Column(db.Integer, primary_key= True)
    admin_id = db.Column(db.Integer)
    athlete_id = db.Column(db.Integer)
    amount = db.Column(db.Float, nullable = False)
    paid_date = db.Column(db.DateTime, nullable = False, default= 'N/A')

class Team_Details(db.Model):
    team_id = db.Column(db.Integer, primary_key= True)
    coach_id = db.Column(db.Integer)
    team_name= db.Column(db.String(20), nullable= False)
    max_age = db.Column(db.Integer, nullable=True)

class Team_Events(db.Model):
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, primary_key= True)
    section = db.Column(db.Integer)
    #section = {0: opening, 1: stunt 1, 2:jumps, 3:baskets, 4:stunt 2, 5:pyramid 6:tumble run 7:dance}

class Team_Members(db.Model):
    team_id = db.Column(db.Integer, primary_key = True) 
    athlete_id = db.Column(db.Integer, primary_key= True)

class Team_Sheet(db.Model):
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    athlete_id= db.Column(db.Integer, primary_key= True)
    role= db.Column(db.String(10), default = 'Tumbler')
    
class Training(db.Model):
    training_id= db.Column(db.Integer, primary_key=True)
    team_id= db.Column(db.Integer)
    coach_id= db.Column(db.Integer)
    athlete_id= db.Column(db.Integer)
    start_date_time= db.Column(db.DateTime, nullable = False)
    end_date_time = db.Column(db.DateTime, nullable = False)
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
    size = db.Column(db.Integer, nullable = False)


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup',  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        surname = request.form.get('surname')
        dob = request.form.get("dob")
        school_URN= request.form.get("school_URN")
        start_date= request.form.get("start_date")
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('There is already an account using this email', category='error')
        elif len(email) <= 3:
            flash('Your email is too short.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            dob = dob.split("-")
            new_user = User(email=email, firstName=firstName, surname=surname, school_URN=school_URN, dob = datetime(int(dob[0]), int(dob[1]), int(dob[2])), start_date=start_date, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created. Wait for the admin user to verify it.', category='success')
            return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                if user.verified == 1:
                    login_user(user)
                    if user.usertype < 4:
                        flash('Login Successful', category='success')
                        return redirect(url_for('view_teams',user=current_user))
                    else:
                        return redirect(url_for('admin'))
                else:
                    flash('Your details have yet to be verified by the Admin', category='error')
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

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/users', methods= ['GET', 'POST'])
@login_required
def users():
    if current_user.usertype < 4:
        return "You are not authorised to view this page"
    query = User.query.filter(User.verified < 1).all()
    valid = False
    for item in request.values:
        if "_" in item:
            items = item.split("_")
            if len(items) == 2 and items[0].lower() == "usertype":
                try:
                    int(items[1])
                    valid = item
                except:
                    continue
    if valid:
        usertype = request.form.get(valid)
        userid = valid.split("_")[1]
        if request.method == 'POST':
            user = User.query.filter_by(id = userid).first()
            user.usertype = usertype     
            user.verified = 1
            db.session.merge(user)
            db.session.commit()
            return redirect(url_for('users')) 
    return render_template('users.html', users=query)

@app.route('/teams', methods=['GET','POST'])
@login_required
def view_teams():
    team_names = {}
    coaches = {}
    query = db.engine.execute("SELECT team__details.team_id, team__details.max_age, team__details.team_name, user.firstName, user.surname FROM team__details, user WHERE user.id == team__details.coach_id ")
    for team in query:
        team_names[team[0]] = [team[1], team[2], team[3] + " " + team[4]]
    query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user WHERE user.usertype > {}'.format(0))
    coaches = {}
    for coach in query:
        coaches[coach[0]] = [coach[1]+ " "+ coach[2]]   
    if -1 < current_user.usertype < 4:
        return render_template('teams.html', team_names = team_names, coaches = coaches)
    query = db.engine.execute("SELECT team__details.team_id, team__details.max_age, team__details.team_name, user.firstName, user.surname FROM team__details, user WHERE user.id == team__details.coach_id")
    for team in query:
        team_names[team[0]] = [team[1], team[2], team[3] + " " + team[4]]
    db.session.commit()
    return render_template('teamsindex.html', team_names = team_names,coaches = coaches)

@app.route('/deleteteams/<teamid>')
@login_required
def delete_teams(teamid):
    try:
        Team_Details.query.filter(Team_Details.team_id == teamid).delete()
        db.session.commit()
        flash('You have successfully deleted a team', category = 'success')
    except:
        print("Not any teams in the database")
    return redirect(url_for('view_teams'))


@app.route('/createteams', methods=['GET','POST'])
@login_required
def create_teams():
    if request.method == 'POST':
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user WHERE user.usertype > {}'.format(0))
        coaches = {}
        for coach in query:
            coaches[coach[0]] = [coach[1]+ " "+ coach[2]]
        coach_id = request.form.get('coach_id')
        team_name = request.form.get('team_name')
        max_age = request.form.get('max_age')
        existing_team = Team_Details.query.filter_by(team_name = team_name).first()
        if existing_team:
            flash('There is already an existing team with this name', category='error')
        else:
            new_team = Team_Details(coach_id= coach_id, team_name= team_name, max_age= max_age)
            db.session.add(new_team)
            db.session.commit()
            flash('Your new team: {} has been created.'.format(team_name), category='success')
        return redirect(url_for('view_teams'))
    return render_template('teamsindex.html', coaches = coaches)

@app.route('/athletes')
@login_required
def view_athletes():
    return render_template('athletes.html')

@app.route('/createathletes')
@login_required
def create_athletes():
    return render_template('adminathletes.html')

@app.route('/events')
@login_required
def view_events():
    return render_template('events.html')

@app.route('/createevents')
@login_required
def create_events():
    return render_template('events.html')

@app.route('/deleteevents')
@login_required
def delete_events():
    return render_template('events.html')

@app.route('/fees')
@login_required
def view_fees():
    return render_template('fees.html')

@app.route('/createfees')
@login_required
def create_fees():
    return render_template('fees.html')

@app.route('/deletefees')
@login_required
def delete_fees():
    return render_template('fees.html')

@app.route('/training')
@login_required
def view_training():
    return 'This is where the admin manages all training sessions'
 
@app.route('/createtraining')
@login_required
def create_training():
    return 'This is where the admin manages all training sessions'

@app.route('/deletetraining')
@login_required
def delete_training():
    return 'This is where the admin manages all training sessions'

@app.route('/contacts')
@login_required
def view_contacts():
    return 'This is where the admin views all contact information'

@app.route('/createcontacts')
@login_required
def create_contacts():
    return 'This is where everyone creates all contact information'

@app.route('/deletecontacts')
@login_required
def delete_contacts():
    return 'Allows users to delete contact information'

@app.route('/teamsheet')
@login_required
def view_teamsheet():
    return 'Allow everyone to view teamsheet'

@app.route('/createteamsheet')
@login_required
def create_teamsheet():
    return 'Allow coach to create teamsheet'

@app.route('/deleteteamsheet')
@login_required
def delete_teamsheet():
    return 'Allow coach to delete teamsheet'



if __name__ == "__main__":
    app.run(debug=True)
