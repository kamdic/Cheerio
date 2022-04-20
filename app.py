import re
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
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
    __tablename__="User"
    id = db.Column(db.Integer, primary_key = True)
    firstName = db.Column(db.String(50),nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    dob = db.Column(db.DateTime, nullable = False)    
    start_date = db.Column(db.DateTime, nullable = True, default=date.today())
    email = db.Column(db.String(70), nullable = False)
    password = db.Column(db.String(255), nullable = False)
    usertype = db.Column(db.Integer, default = -1)
    verified = db.Column(db.Integer, default = 0)
    #usertype = {0:athlete, 1:athlete/coach, 2:coach, 3:admin}

    def get_id(self):
        return self.id
    
    def get_first_name(self):
        return self.firstName
    
    def get_surname(self):
        return self.surname
    
    def get_dob(self):
        return self.dob
    
    def get_start_date(self):
        return self.start_date
    
    def get_email(self):
        return self.email
    
    def get_password_hash(self):
        return self.password
    
    def get_usertype(self):
        return self.usertype

    def get_verified(self):
        return self.verified
    
    def get_age(self):
        dob = self.get_dob().rstrip("00:00:00.0000000").split("-")
        today = str(date.today()).split("-")
        if (today[1].strip() == dob[1].strip()) and (today[2].strip() == dob[2].strip()):
            birthday_age = age(dob)
        return birthday_age
    
    def get_anniversary(self):
        dob = self.get_dob().rstrip("00:00:00.0000000").split("-")
        today = str(date.today()).split("-")    
        year = int(today[0]) - int((self.get_start_date().split("-")[0]))
        return year

class Fees(db.Model):
    __tablename__ = "Fees"
    fees_id = db.Column(db.Integer, primary_key= True)
    athlete_id = db.Column(db.Integer)
    amount = db.Column(db.Float, nullable = False)
    paid_date = db.Column(db.DateTime, nullable = True)
    paid = db.Column(db.Integer, default=0)

    def get_fees_id(self):
        return self.fees_id

    def get_athlete_id(self):
        return self.athlete_id

    def get_amount(self):
        return self.amount

    def get_paid_date(self):
        return self.paid_date

    def get_paid(self):
        return self.paid

class Team_Details(db.Model):
    __tablename__ = "Team_Details"
    team_id = db.Column(db.Integer, primary_key= True)
    coach_id = db.Column(db.Integer)
    team_name= db.Column(db.String(20), nullable= False)
    max_age = db.Column(db.Integer, nullable=True)

    def get_team_id(self):
        return self.team_id

    def get_coach_id(self):
        return self.coach_id

    def get_team_name(self):
        return self.team_name

    def get_max_age(self):
        return self.max_age

class Team_Events(db.Model): #The coach decides they want to make a team for this event so will use the teamsheet id, the id of the event they want the team for and the team the sheet is being created for
    __tablename__ = "Team_Events"
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer)
    team_id = db.Column(db.Integer)
    size = db.Column(db.Integer, nullable=False)

    def get_team_sheet_id(self):
        return self.team_sheet_id

    def get_eventid(self):
        return self.event_id

    def get_team_id(self):
        return self.team_id

    def get_size(self):
        return self.size

class Team_Members(db.Model): 
    __tablename__ = "Team_Members"
    team_id = db.Column(db.Integer, primary_key = True) 
    athlete_id = db.Column(db.Integer, primary_key= True)

    def get_team_id(self):
        return self.team_id

    def get_athlete_id(self):
        return self.athlete_id

class Team_Sheet(db.Model): #Will add each athlete to the teamsheet from team members
    __tablename__ = "Team_Sheet"
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    athlete_id= db.Column(db.Integer, primary_key= True)
    role= db.Column(db.String(10), default = 'Tumbler')

    def get_team_sheet_id(self):
        return self.team_sheet_id

    def get_athlete_id(self):
        return self.athlete_id

    def get_role(self):
        return self.role
    
class Contacts(db.Model):
    __tablename__ = "Contacts"
    contacts_id= db.Column(db.Integer, primary_key=True)
    athlete_id= db.Column(db.Integer)
    firstName= db.Column(db.String(50), nullable = False)
    surname= db.Column(db.String(50), nullable = False)
    number= db.Column(db.String(15), nullable = False)

    def get_contacts_id(self):
        return self.contacts_id

    def get_athlete_id(self):
        return self.athlete_id

    def get_first_name(self):
        return self.firstName

    def get_surname(self):
        return self.surname

    def get_number(self):
        return self.number

class Events(db.Model): #1. an event is made
    __tablename__ = "Events"
    events_id= db.Column(db.Integer, primary_key=True)
    event_name= db.Column(db.Text, nullable =False)
    event_start_date= db.Column(db.DateTime, nullable = False)
    event_end_date = db.Column(db.DateTime, nullable=False)

    def get_events_id(self):
        return self.events_id

    def get_event_name(self):
        return self.event_name

    def get_event_start_date(self):
        return self.event_start_date

    def get_event_end_date(self):
        return self.event_end_date

def eligibity_age(born):
    year = (str(date.today()).split("-"))[0]
    today = [year,5,31]
    born = born.split("-")
    return int(today[0]) - int(born[0]) - (((int(today[1]), int(today[2]))) < ((int(born[1]), int(born[2]))))

def age(born):
    today = str(date.today()).split("-")
    return int(today[0]) - int(born[0]) - (((int(today[1]), int(today[2]))) < ((int(born[1]), int(born[2]))))

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def isValid(email):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    if re.fullmatch(regex, email):
      return True
    else:
      return False
  
def password(passwd):
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,}$"
    pat = re.compile(reg)               
    mat = re.search(pat, passwd)
    # validating conditions
    if mat:
        return True
    else:
        return False

@app.errorhandler(404)#complete
def not_found(error):
    return render_template('error.html', error= error)

@app.errorhandler(500)#complete
def server_error(error):
    return render_template('error.html', error=error)

@app.route('/')#complete
def index():
    return redirect(url_for('login'))

@app.route('/signup',  methods=['GET', 'POST']) #complete
def signup():
    if request.method == 'POST':
        email = (request.form.get('email')).lower()
        firstName = request.form.get('firstName')
        surname = request.form.get('surname')
        dob = request.form.get("dob")
        start_date= request.form.get("start_date")
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            flash('There is already an account using this email', category='error')
        elif len(email) <= 3:
            flash('Your email is too short.', category='error')
        elif not isValid(email):
            flash("Your email is invalid",category='error')
        elif not password(password1):
            flash('Your password must be at least 6 characters, include one number, one uppercase letter, a lowercase letter, and a special symbol', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            dob = dob.split("-")
            new_user = User(email=email.lower(), firstName=firstName, surname=surname, dob = datetime(int(dob[0]), int(dob[1]), int(dob[2])), start_date=start_date, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created. Wait for the admin user to verify it.', category='success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])#complete
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.get_password_hash(), password):
                if user.get_verified() == 1:
                    login_user(user)
                    if -1 < user.usertype < 3:
                        return redirect(url_for('view_teams',user=current_user))
                    elif user.get_usertype() == 3:
                        return redirect(url_for('admin'))
                    else:
                        return render_template('error.html',error="You are not authorised to view this page")
                else:
                    flash('Your details have yet to be verified by the Admin', category='error')
            else:
                flash('Password is incorrect, try again', category='error')
        else:
            flash('There is no existing user with this email', category='error')
    return render_template('login.html')

@app.route('/logout')#complete
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')#complete
@login_required
def admin():
    if current_user.get_usertype() !=3:
        return render_template('error.html',error="You are not authorised to view this page")
    query = db.engine.execute('SELECT id, firstName, surname, dob, start_date FROM user ORDER BY start_date DESC')
    birthdays = {}
    anniversaries = {} 
    for user in query:
        dob = user[3].rstrip("00:00:00.0000000").split("-")
        today = str(date.today()).split("-")
        if (today[1].strip() == dob[1].strip()) and (today[2].strip() == dob[2].strip()):
            birthday_age = age(dob)
            birthdays[user[0]] = [user[1] + " " + user[2], birthday_age]
        year = int(today[0]) -int((user[4].split("-")[0]))
        if year > 1:
            anniversaries[user.get_id()] = [user.get_first_name() + " " + user.get_surname(), user.get_anniversary()]
    return render_template('admin.html',birthdays=birthdays, anniversaries= anniversaries)

@app.route('/users', methods= ['GET', 'POST'])#complete
@login_required
def verify_users():
    if current_user.usertype < 3:
        return render_template('error.html',error="You are not authorised to view this page")
    unverified_users = {}
    query = db.engine.execute('SELECT id, firstName, surname, email FROM user WHERE verified < {}'.format(1))
    for user in query:
        unverified_users[user[0]] = [user[1],user[2],user[3]]
    valid = False
    for item in request.values:
        item.split(("_"))
        if "_" in item:
            items = item.split("_")
            if len(items) == 2 and items[0].lower() == "usertype":
                try:
                    int(items[1])
                    valid = item
                except:
                    redirect(url_for('verify_users'))
    if valid:
        usertype = request.form.get(valid)
        userid = valid.split("_")[1]
        if request.method == 'POST':
            if usertype == 'Select user type':
                flash('You must select a usertype',category='error')
            else:
                query = db.engine.execute('UPDATE user SET usertype = {}, verified = {} WHERE id = {}'.format(usertype, 1,userid))
                db.session.commit()
                return redirect(url_for('verify_users'))
    verified_users = {}
    query = db.engine.execute('SELECT id, firstName, surname, email, usertype, start_date FROM user WHERE verified = {} ORDER BY id'.format(1))
    for user in query:
        if current_user.id != user[0]:
            verified_users[user[0]] = [user[1], user[2], user[3],user[4],user[5].rstrip('00:00:00.000000')]
    usertypes = {0: 'Athlete', 1: 'Athlete/Coach', 2: 'Coach', 3:'Admin'}
    return render_template('users.html', unverified_users=unverified_users, verified_users= verified_users, usertypes = usertypes)

@app.route('/setusers', methods= ['GET', 'POST'])#complete
@login_required
def set_users():
    if current_user.usertype < 3:
        return render_template('error.html',error="You are not authorised to view this page")
    verify_users()
    valid = False
    for item in request.values:
        if "_" in item:
            items = item.split("_")
            if len(items) == 2 and items[0].lower() == "usertype":
                try:
                    int(items[1])
                    valid = item
                except:
                    redirect(url_for('verify_users'))
    if valid:
        usertype = request.form.get(valid)
        userid = valid.split("_")[1]
        if request.method == 'POST':
            if usertype == 'Select user type':
                flash('You must select a usertype',category='error')
            else:
                query = db.engine.execute('UPDATE user SET usertype = {} WHERE id = {}'.format(usertype, userid))
                db.session.commit()
                return redirect(url_for('verify_users'))
    return redirect(url_for('verify_users'))

@app.route('/setdate',methods=['GET','POST'])
@login_required
def set_start_date():
    valid = False
    for item in request.values:
        if "_" in item:
            items = item.split("_")
            if len(items) == 2 and items[0].lower() == "startdate":
                try:
                    int(items[1])
                    valid = item
                except:
                    redirect(url_for('verify_users'))
    if valid:
        startDate = request.form.get(valid).split("-")
        userid = valid.split("_")[1]
        try:
            startDate = str(date(int(startDate[0]),int(startDate[1]),int(startDate[2])))
            if request.method == 'POST':
                query = db.engine.execute('UPDATE user SET start_date = "{}" WHERE id= {}'.format(startDate,userid))
                db.session.commit()
                return redirect(url_for('verify_users'))
        except:
            return redirect(url_for('verify_users'))
        return redirect(url_for('verify_users')) 
    return redirect(url_for('verify_users'))
    
@app.route('/deleteuser/<userid>')#complete
@login_required
def delete_users(userid):
    if current_user.usertype != 3:
        return render_template('error.html',error="You are not authorised to view this page")    
    verify_users()
    try:
        query = db.engine.execute('SELECT usertype FROM user WHERE id = {}'.format(userid))
        for info in query:
            usertype = info[0]
        query = db.engine.execute('DELETE FROM contacts WHERE athlete_id = {}'.format(userid))
        query = db.engine.execute('DELETE FROM fees WHERE athlete_id = {}'.format(userid))
        if usertype == 0:
            try:
                query = db.engine.execute('DELETE FROM team__members WHERE athlete_id = {}'.format(userid))
            except:
                pass
        elif usertype == 1:
            try:
                query = db.engine.execute('DELETE FROM team__members WHERE athlete_id = {}'.format(userid))
                query = db.engine.execute('SELECT team_id FROM team__details WHERE coach_id = {}'.format(userid))
                for team in query:
                    teamid = team[0]
                delete_teams(teamid)
            except:
                pass    
        elif usertype == 2:
            try:
                query = db.engine.execute('DELETE FROM team__details WHERE coach_id = {}'.format(userid))
            except:
                pass
        elif usertype == 3:
            try:
                query = db.engine.execute('DELETE FROM team__details WHERE coach_id = {}'.format(userid))
                query = db.engine.execute('DELETE FROM team__events,team__sheet,team__members WHERE team__details.coach_id = {} AND team__events.team_sheet_id = team__sheet.team_sheet_id AND team__members.team_id = team__details.team_id'.format(userid))
            except:
                pass
        query = db.engine.execute('DELETE FROM user WHERE id = {}'.format(userid))
        db.session.commit()
    except:
        flash('There was an error when deleting this user',category='error')
    return redirect(url_for('verify_users'))

@app.route('/teams', methods=['GET','POST'])#complete
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
    if current_user.usertype == -1 or current_user.verified == 0:
        return render_template('error.html',error="You are not authorised to view this page")
    if -1 < current_user.usertype < 3:
        return render_template('teams.html', team_names = team_names, coaches = coaches)
    query = db.engine.execute("SELECT team__details.team_id, team__details.max_age, team__details.team_name, user.firstName, user.surname FROM team__details, user WHERE user.id == team__details.coach_id")
    for team in query:
        team_names[team[0]] = [team[1], team[2], team[3] + " " + team[4]]
    db.session.commit()
    return render_template('adminteams.html', team_names = team_names,coaches = coaches)

@app.route('/deleteteams/<teamid>')#complete
@login_required
def delete_teams(teamid):
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        query = db.engine.execute('DELETE FROM team__details WHERE team_id = {}'.format(teamid))
        query = db.engine.execute('DELETE FROM team__events,team__sheet WHERE team__events.team_id = {} AND team__events.team_sheet_id = team__sheet.team_sheet_id'.format(teamid))
        query = db.engine.execute('DELETE FROM team__members WHERE team_id = {}'.format(teamid))
        db.session.commit()
        flash('You have successfully deleted a team', category = 'success')
    except:
        pass
    return redirect(url_for('view_teams'))


@app.route('/createteams', methods=['GET','POST'])#complete
@login_required
def create_teams():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    if request.method == 'POST':
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user WHERE user.usertype > {}'.format(0))
        coaches = {}
        for coach in query:
            coaches[coach[0]] = [coach[1]+ " "+ coach[2]]
        coach_id = request.form.get('coach')
        team_name = request.form.get('team_name')
        max_age = request.form.get('max_age')
        existing_team = Team_Details.query.filter_by(team_name = team_name.capitalize()).first()
        existing_coach = Team_Details.query.filter_by(coach_id = coach_id).first()
        if existing_team:
            flash('There is already an existing team with this name', category='error')
        elif existing_coach:
            flash('This coach is already coaching a team',category='error')
        elif coach_id == "Select a coach:":
            flash('You must select a coach', category='error')
        elif team_name.rstrip() == "":
            flash('The team name cannot be empty', category='error')
        else:
            new_team = Team_Details(coach_id= coach_id, team_name= team_name.capitalize(), max_age= max_age)
            db.session.add(new_team)
            db.session.commit()
            flash('Your new team: {} has been created.'.format(team_name), category='success')
        return redirect(url_for('view_teams'))
    return render_template('adminteams.html', coaches = coaches)

@app.route('/athletes')#complete
@login_required
def view_athletes():
    try:
        if current_user.usertype not in [0,1,2,3] or current_user.verified != 1:
            return render_template('error.html',error="You are not authorised to view this page")
        elif  current_user.usertype == 0:
            members = {}
            query = db.engine.execute('SELECT team__details.team_id, team__details.team_name FROM team__members, team__details WHERE team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.id))
            for team in query:
                athletes =[]
                query = db.engine.execute('SELECT user.firstName, user.surname FROM user, team__members WHERE user.id = team__members.athlete_id AND team__members.team_id = {}'.format(team[0]))
                for athlete in query:
                    athletes.append(athlete[0] + " " + athlete[1])
                members[team[0]] = [team[1],athletes]
            return render_template('athletes.html',members=members)
        elif  current_user.usertype == 1:
            team_members = {}
            query = db.engine.execute('SELECT team__details.team_id, team__details.team_name FROM team__members, team__details WHERE team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.id))
            for team in query:
                athletes =[]
                query = db.engine.execute('SELECT user.firstName, user.surname FROM user, team__members WHERE user.id = team__members.athlete_id AND team__members.team_id = {}'.format(team[0]))
                for athlete in query:
                    athletes.append(athlete[0] + " " + athlete[1])
                team_members[team[0]] = [team[1],athletes]
            coach_members = {}
            athletes = []
            query = db.engine.execute('SELECT team__details.team_name, user.firstName, user.surname FROM team__details, user, team__members WHERE team__details.team_id = team__members.team_id AND team__details.coach_id = {} AND user.id = team__members.athlete_id'.format(current_user.id))
            for member in query:
                team_name = member[0]
                athletes.append(member[1] + " " + member[2])   
            coach_members[team_name] = athletes           
            return render_template('coachathleteathletes.html',team_members=team_members,coach_members=coach_members)
        elif  current_user.usertype == 2:
            members = {}
            athletes = []
            query = db.engine.execute('SELECT team__details.team_name, user.firstName, user.surname FROM team__details, user, team__members WHERE team__details.team_id = team__members.team_id AND team__details.coach_id = {} AND user.id = team__members.athlete_id'.format(current_user.id))
            for member in query:
                team_name = member[0]
                athletes.append(member[1] + " " + member[2])   
            members[team_name] = athletes   
            return render_template('coachathletes.html',members = members)           
        elif current_user.usertype == 3:
            team_count = db.engine.execute("SELECT COUNT(team_id) FROM team__details")
            teams = {}
            count = 1
            index = 0
            for amount in team_count:
                team_count = amount[0]
            for team in range(team_count):
                query = db.engine.execute("SELECT user.id, user.firstName, user.surname, user.dob FROM user, team__members WHERE user.id = team__members.athlete_id AND team__members.team_id = {}".format(count))
                athletes = []
                for athlete in query:
                    element = [str(index) +athlete[1] + " " + athlete[2]]
                    athletes += element
                    index +=1
                if len(athletes) > 0:
                    teams[count] = athletes
                count +=1
            team_names = []
            query = db.engine.execute("SELECT team_name FROM team__details")
            for team_name in query:
                team_names.append(team_name)
            possible_athletes = {}
            query = db.engine.execute('SELECT team_id, max_age FROM team__details')
            for team in query:
                max_age = team[1]
                eligible_athletes = []
                athletes = db.engine.execute('SELECT id, firstName, surname, dob FROM user WHERE usertype = {} OR usertype = {}'.format(0,1))
                if max_age:
                    for athlete in athletes:
                        athlete_date = athlete[3].rstrip("00:00:00.0000000")
                        athlete_age = eligibity_age(athlete_date)
                        if max_age >= athlete_age:
                            eligible_athletes += [str(athlete[0])+athlete[1] + " "+ athlete[2]]  
                else:
                    for athlete in athletes:
                        eligible_athletes += [str(athlete[0])+athlete[1] + " "+ athlete[2]]  
                possible_athletes[team[0]] = eligible_athletes
            return render_template('adminathletes.html',team_count= team_count,teams=teams, team_names=team_names,possible_athletes=possible_athletes)
    except:
        return render_template('error.html',error="You do not have a team to create a teamsheet for, consult an admin to create one")  

@app.route('/deleteathletes/<teammemberid>')#complete
@login_required
def delete_athletes(teammemberid):
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        ids = []
        query = db.engine.execute('SELECT * FROM team__members ORDER BY team_id ASC')
        for id in query:
            ids.append(id)
        teammemberid = re.sub("[^0-9]", "", teammemberid)
        team_id = ids[int(teammemberid)][0]
        athlete_id = ids[int(teammemberid)][1]
        query = db.engine.execute('DELETE FROM team__members WHERE (team_id = {} AND athlete_id = {})'.format(team_id, athlete_id))
        flash('You have successfully deleted a team member', category = 'success')
        db.session.commit() 
    except:
        flash('There was a problem deleting this athlete from the team', category='error')   
    return redirect(url_for('view_athletes'))

@app.route('/createathletes', methods=['GET','POST'])#complete
@login_required
def create_athletes():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")    
    if request.method == 'POST':
        view_athletes()
        teammemberid = request.form.get('athlete').split('_')
        if teammemberid[0] == "Select an athlete:":
            flash('You must select an athlete',category='error')
        else:
            team_id = teammemberid[0]
            athlete_id = teammemberid[1]
            athlete_id = re.sub("[^0-9]", "", athlete_id)
            try:
                query = db.engine.execute("INSERT INTO team__members VALUES ('{}','{}')".format(team_id,athlete_id))
                db.session.commit()
            except:
                flash('This athlete is already on the team', category='error')
        return redirect(url_for('view_athletes'))
    return render_template('adminathletes.html')
    
@app.route('/events')#complete
@login_required
def view_events():
    cal_events = {}
    query = db.engine.execute("SELECT events_id, event_name, event_start_date, event_end_date FROM Events")
    for event in query:
        cal_events[event[0]] = [event[1],event[2],event[3]]    
    if current_user.usertype not in [0,1,2,3] or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    if -1 < current_user.usertype < 3:
        return render_template('events.html', events=cal_events)
    elif current_user.usertype >2: 
        return render_template('adminevents.html', events=cal_events)

@app.route('/createevents', methods= ['GET','POST'])#complete
@login_required
def create_events():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:  
        req = request.get_json()
        name = req['title']
        start = req['start']
        end = req['end']
        start = start.strip("Z").split("T")
        end = end.strip("Z").split("T")
        start = (" ").join(start)
        end = (" ").join(end)
        query = db.engine.execute("SELECT COUNT(events_id) FROM Events WHERE event_name = '{}' AND event_start_date = '{}' AND event_end_date = '{}'".format(name,start,end))
        for num in query:
            existing = num[0]
        if existing > 0:
            flash('There is already an existing event with this name, at the same time', category='error')
        else:
            query = db.engine.execute("INSERT INTO Events (event_name, event_start_date, event_end_date) VALUES ('{}','{}','{}')".format(name,start,end))
            db.session.commit()
    except:
        flash('Was not able to add this event', category='error')
    return redirect(url_for('view_events'))

@app.route('/deleteevents', methods= ['GET','POST'])#complete
@login_required
def delete_events():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:  
        req = request.get_json()
        name = req['title']
        start = req['start']
        end = req['end']
        start = start.strip("Z").split("T")
        end = end.strip("Z").split("T")
        start = str((" ").join(start))
        end = str((" ").join(end))    
        query = db.engine.execute('SELECT * FROM Events')
        events = []
        for event in query:
            if event[2] == start and event[3] == end and event[1] == name:
                events.append(event[0])
        if len(events) == 1:
            query = db.engine.execute('DELETE FROM Events WHERE events_id = {}'.format(events[0]))
            db.session.commit()
    except:
        flash('Was not able to delete this event', category='error')
    return redirect(url_for('view_events'))

@app.route('/fees')#complete
@login_required
def view_fees():
    if current_user.usertype not in [0,1,2,3] or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    if -1< current_user.usertype < 3:
        query = db.engine.execute('SELECT fees.fees_id, fees.amount, fees.paid_date, fees.paid FROM fees WHERE fees.athlete_id = {} ORDER BY fees.paid_date DESC'.format(current_user.id))
        fees={}
        for fee in query:
            if fee[3] != 1:
                fees[fee[0]] = [fee[1],fee[2],"No",fee[3]]
            else:
                fees[fee[0]] = [fee[1],fee[2],"Yes",fee[3]]
        return render_template('fees.html', fees=fees)
    elif current_user.usertype == 3:
        users = db.engine.execute('SELECT id, firstName, surname FROM user')
        athletes = {}
        for athlete in users:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]        
        query = db.engine.execute('SELECT fees.fees_id, user.firstName, user.surname, fees.amount, fees.paid_date, fees.paid FROM fees, user WHERE user.id = fees.athlete_id ORDER BY fees.paid_date DESC')
        return render_template('adminfees.html', fees=query, athletes=athletes)

@app.route('/createfees', methods= ['GET','POST'])#complete
@login_required
def create_fees():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    if request.method == "POST":
        users = db.engine.execute('SELECT id, firstName, surname FROM user')
        athletes = {}
        for athlete in users:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]   
        athlete_id = request.form.get('athlete')
        amount = request.form.get('amount')
        check = isfloat(amount)
        if athlete_id == "Select an athlete:":
            flash('You must select an athlete',category='error')
        elif not check:
            flash('The input must be numeric',category='error')
        else:
            query = db.engine.execute("INSERT INTO fees (athlete_id, amount) VALUES ('{}','{}')".format(athlete_id, amount))
            db.session.commit()
        return redirect(url_for('view_fees'))
    return render_template('adminfees.html', athletes=athletes)

@app.route('/setfees', methods=["GET","POST"])#complete
@login_required
def set_fees_date():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    view_fees()
    valid = False
    for item in request.values:
        if "_" in item:
            items = item.split("_")
            if len(items) == 2 and items[0].lower() == "paiddate":
                try:
                    int(items[1])
                    valid = item
                except:
                    redirect(url_for('view_fees'))
    if valid:
        paidDate = request.form.get(valid).split("-")
        feesid = valid.split("_")[1]
        try:
            paidDate = str(date(int(paidDate[0]),int(paidDate[1]),int(paidDate[2])))
            if request.method == 'POST':
                query = db.engine.execute('UPDATE fees SET paid_date = "{}", paid = {} WHERE fees_id= {}'.format(paidDate,1,feesid))
                db.session.commit()
                return redirect(url_for('view_fees'))
        except:
            return redirect(url_for('view_fees'))
        return redirect(url_for('view_fees'))
    return redirect(url_for('view_fees'))

@app.route('/deletefees/<feeid>')#complete
@login_required
def delete_fees(feeid):
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    try:
        query = db.engine.execute('DELETE FROM fees WHERE fees_id = {}'.format(feeid))
        db.session.commit()
    except:        
        flash('Was not able to delete this fee', category='error')
    return redirect(url_for('view_fees'))

@app.route('/contacts')#complete
@login_required
def view_contacts():
    if current_user.usertype not in [0,1,2,3] or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    elif current_user.usertype == 0:
        query = db.engine.execute('SELECT firstName, surname, number FROM contacts WHERE contacts.athlete_id == {}'.format(current_user.id))
        return render_template('contacts.html', contacts=query)
    elif current_user.usertype == 1:
        own_contacts = db.engine.execute('SELECT firstName, surname, number FROM contacts WHERE contacts.athlete_id == {}'.format(current_user.id))
        team = db.engine.execute('SELECT team__members.athlete_id FROM team__members,team__details WHERE team__details.coach_id == {} AND team__details.team_id = team__members.team_id'.format(current_user.id))
        athletes = {}
        for athlete in team:
            info = db.engine.execute('SELECT user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id == {} AND contacts.athlete_id == {}'.format(athlete[0],athlete[0]))
            for details in info:
                athletes[athlete[0]] = [details[0], details[1],details[2],details[3],details[4]]
        query = db.engine.execute('SELECT team_name FROM team__details WHERE coach_id = {}'.format(current_user.id))
        for name in query:
            name = name[0]
        return render_template('coachathletecontacts.html', own_contacts = own_contacts, athletes = athletes, name = name)
    elif current_user.usertype == 2:
        team = db.engine.execute('SELECT team__members.athlete_id FROM team__members,team__details WHERE team__details.coach_id == {} AND team__details.team_id = team__members.team_id'.format(current_user.id))
        athletes = {}
        for athlete in team:
            info = db.engine.execute('SELECT user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id == {} AND contacts.athlete_id == {}'.format(athlete[0],athlete[0]))
            for details in info:
                athletes[athlete[0]] = [details[0], details[1],details[2],details[3],details[4]]
        query = db.engine.execute('SELECT team_name FROM team__details WHERE coach_id = {}'.format(current_user.id))
        for name in query:
            name = name[0]
        return render_template('coachcontacts.html', athletes=athletes, name=name)
    elif current_user.usertype == 3:
        query = db.engine.execute('SELECT id, firstName, surname FROM user WHERE usertype == {} OR usertype == {}'.format(0,1))
        athletes = {}
        for athlete in query:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]       
        query = db.engine.execute('SELECT contacts.contacts_id, user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id = contacts.athlete_id')
        return render_template('admincontacts.html', contacts=query, athletes=athletes)

@app.route('/createcontacts/', methods= ['GET','POST'])#complete
@login_required
def create_contacts():
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")    
    if request.method == 'POST':
        try:
            athlete_id = request.form.get('athlete')
            firstName = request.form.get('firstName')
            surname = request.form.get('surname')
            number = (request.form.get('number')).replace(" ","")
            query = db.engine.execute("SELECT COUNT(contacts_id) FROM Contacts WHERE athlete_id = '{}' AND firstName = '{}' AND surname  = '{}' AND number='{}'".format(athlete_id, firstName.capitalize(), surname.capitalize(), number))
            for num in query:
                existing = num[0]
            if existing > 0:
                flash('This contact has already been made for this athlete', category='error')
            elif athlete_id == 'Select an athlete:':
                flash('You must select an athlete', category='error')
            elif firstName.strip()== "":
                flash('You cannot leave the contact name empty', category='error')
            elif surname.strip()== "":
                flash('You cannot leave the contact name empty', category='error') 
            elif number.strip()== "":
                flash('You cannot leave the contact number empty', category='error')
            elif not number.isnumeric() :
                flash('The phone number must be strictly numeric', category='error')
            else:
                query = db.engine.execute("INSERT INTO contacts (athlete_id, firstName, surname, number) VALUES ('{}','{}', '{}', '{}')".format(athlete_id, firstName.capitalize(),surname.capitalize(),number))
                db.session.commit()
        except:
            pass                  
        return redirect(url_for('view_contacts'))
    return redirect(url_for('view_contacts'))

@app.route('/deletecontacts/<contactid>')#complete
@login_required
def delete_contacts(contactid):
    if current_user.usertype != 3 or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:  
        query = db.engine.execute('DELETE FROM contacts WHERE contacts_id = {}'.format(contactid))
        flash('You have successfully deleted a contact', category = 'success')
        db.session.commit()
    except:
        flash('Was not able to delete this contact successfully', category='error')
    return redirect(url_for('view_contacts'))

@app.route('/teamsheet')#complete
@login_required
def view_teamsheet():
    if current_user.usertype not in [0,1,2,3] or current_user.verified != 1:
        return "You're not authorised to view this page"
    elif current_user.usertype == 0:
        team_sheets = {}
        events = []
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name, team__details.team_name FROM events, team__events, team__details, team__members WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.id))
        for event in query:
            events.append(event)
        for event in events:
            team_sheet_id = event[0]
            athletes = []
            query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(team_sheet_id))
            for athlete in query:
                athletes.append(athlete)
            team_sheets[event[0]] = [event[1], event[2],athletes]
        return render_template('teamsheet.html',team_sheets=team_sheets)
    elif current_user.usertype == 1:
        own_team_sheets = {}
        events = []
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name, team__details.team_name FROM events, team__events, team__details, team__members WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.id))
        for event in query:
            events.append(event)
        for event in events:
            team_sheet_id = event[0]
            athletes = []
            query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(team_sheet_id))
            for athlete in query:
                athletes.append(athlete)
            own_team_sheets[event[0]] = [event[1], event[2],athletes]
        coach_team_sheets = {}
        events = []
        options = {}
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.id))
        for event in query:
            events.append(event)
        for event in events:
            team_sheet_id = event[0]
            athletes = []
            query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(team_sheet_id))
            for athlete in query:
                athletes.append(athlete)
            coach_team_sheets[event[0]] = [event[1],athletes]
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__events, team__details,team__members WHERE team__events.team_id = team__details.team_id AND team__details.coach_id = {} AND team__members.team_id = team__details.team_id AND user.id = team__members.athlete_id'.format(current_user.id))
        for athlete in query:
            options[athlete[0]] = [athlete[1] + " " + athlete[2]]
        return render_template('coachathleteteamsheet.html',own_team_sheets=own_team_sheets,coach_team_sheets=coach_team_sheets,athletes=options)
    elif  current_user.usertype == 2:
        team_sheets = {}
        events = []
        options = {}
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.id))
        for event in query:
            events.append(event)
        for event in events:
            team_sheet_id = event[0]
            athletes = []
            query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(team_sheet_id))
            for athlete in query:
                athletes.append(athlete)
            team_sheets[event[0]] = [event[1],athletes]
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__events, team__details,team__members WHERE team__events.team_id = team__details.team_id AND team__details.coach_id = {} AND team__members.team_id = team__details.team_id AND user.id = team__members.athlete_id'.format(current_user.id))
        for athlete in query:
            options[athlete[0]] = [athlete[1] + " " + athlete[2]]
        return render_template('coachteamsheet.html', team_sheets=team_sheets,athletes=options)
    other_team_sheets = {}
    events = []
    query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name,team__details.team_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND NOT team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.id))
    for event in query:
        events.append(event)
    for event in events:
        team_sheet_id = event[0]
        athletes = []
        query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(team_sheet_id))
        for athlete in query:
            athletes.append(athlete)
        other_team_sheets[event[0]] = [event[1],event[2],athletes]
    own_team_sheets = {}
    events = []
    options = {}
    query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.id))
    for event in query:
        events.append(event)
    for event in events:
        team_sheet_id = event[0]
        athletes = []
        query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(team_sheet_id))
        for athlete in query:
            athletes.append(athlete)
        own_team_sheets[event[0]] = [event[1],athletes]    
    query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__events, team__details,team__members WHERE team__events.team_id = team__details.team_id AND team__details.coach_id = {} AND team__members.team_id = team__details.team_id AND user.id = team__members.athlete_id'.format(current_user.id))
    for athlete in query:
        options[athlete[0]] = [athlete[1] + " " + athlete[2]]
    return render_template('adminteamsheet.html',own_team_sheets = own_team_sheets,athletes=options,other_team_sheets=other_team_sheets)

@app.route('/createteamsheet',methods=['GET','POST'])#complete
@login_required
def create_teamsheet():
    try:
        if current_user.usertype not in [1,2,3] or current_user.verified != 1:
            return render_template('error.html',error="You are not authorised to view this page")   
        sizes = {0:"X Small (5-14)",1:"Small (15-22)",2:"Medium (23-32)",3:"Large (33-38)"}
        query = db.engine.execute('SELECT * FROM Events')
        events = {}
        for event in query:
            event_start_date = event[2].split(" ")[0]
            event_start_date = event_start_date.split("-")
            event_start_date = date(int(event_start_date[0]),int(event_start_date[1]),int(event_start_date[2]))
            if event_start_date > date.today():
                events[event[0]] = [event[1],event[2].split(" ")[0],event[3].split(" ")[0]]
        existing_sheets = {}
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name, team__events.size FROM team__details, events, team__events WHERE team__details.team_id = team__events.team_id AND events.events_id = team__events.event_id AND team__details.coach_id = {}'.format(current_user.id))
        for team in query:
            existing_sheets[team[0]] = [team[1],sizes[team[2]]]
        query = db.engine.execute('SELECT team_id, team_name FROM team__details WHERE coach_id = {}'.format(current_user.id))
        for team in query:
            team_name =team[1]
            team_id = team[0]
        if current_user.usertype == 1:
            if request.method == 'POST':
                try:
                    event_id = request.form.get('event')
                    size= request.form.get('size')
                    query = db.engine.execute('SELECT COUNT(team_sheet_id) FROM team__events WHERE event_id = {} AND team_id = {}'.format(event_id,team_id))
                    for num in query:
                        count = num[0]
                    if count > 0:
                        flash('This team is already competing at this event',category='error')
                    else:
                        query = db.engine.execute("INSERT INTO team__events (event_id, team_id, size) VALUES ('{}','{}','{}')".format(event_id,team_id,size))
                        db.session.commit()
                        return redirect(url_for('create_teamsheet'))
                except:
                    flash('There was an error when creating this team sheet',category='error')
            return render_template('createteamsheet.html', events = events, team = team_name,sizes=sizes, team_sheets=existing_sheets, count=0)
        elif current_user.usertype == 2:
            if request.method == 'POST':
                try:
                    event_id = request.form.get('event')
                    size= request.form.get('size')
                    query = db.engine.execute('SELECT COUNT(team_sheet_id) FROM team__events WHERE event_id = {} AND team_id = {}'.format(event_id,team_id))
                    for num in query:
                        count = num[0]
                    if count > 0:
                        flash('This team is already competing at this event',category='error')
                    else:
                        query = db.engine.execute("INSERT INTO team__events (event_id, team_id, size) VALUES ('{}','{}','{}')".format(event_id,team_id,size))
                        db.session.commit()
                        return redirect(url_for('create_teamsheet'))
                except:
                    flash('There was an error when creating this team sheet',category='error')
            return render_template('createteamsheet.html', events = events, team = team_name,sizes=sizes, team_sheets=existing_sheets, count=0)
        elif current_user.usertype == 3:
            if request.method == 'POST':
                try:
                    event_id = request.form.get('event')
                    size= request.form.get('size')
                    query = db.engine.execute('SELECT COUNT(team_sheet_id) FROM team__events WHERE event_id = {} AND team_id = {}'.format(event_id,team_id))
                    for num in query:
                        count = num[0]
                    if count > 0:
                        flash('This team is already competing at this event',category='error')
                    else:
                        query = db.engine.execute("INSERT INTO team__events (event_id, team_id, size) VALUES ('{}','{}','{}')".format(event_id,team_id,size))
                        db.session.commit()
                        return redirect(url_for('create_teamsheet'))
                except:
                    flash('There was an error when creating this team sheet',category='error')        
            return render_template('admincreateteamsheet.html', events = events, team = team_name,sizes=sizes, team_sheets=existing_sheets, count=0)
    except:
        return render_template('error.html',error="You do not have a team to create a teamsheet for, consult an admin to create one")  

@app.route('/deleteteamsheet/<teamsheetid>')#complete
@login_required
def delete_teamsheet(teamsheetid):
    if current_user.usertype not in [1,2,3] or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        query = db.engine.execute("DELETE FROM team__events WHERE team_sheet_id = {}".format(teamsheetid))
        query = db.engine.execute("DELETE FROM team__sheet WHERE team_sheet_id = {}".format(teamsheetid))
        db.session.commit()
    except:
        flash('An error occured whilst trying to delete this teamsheet', category='error')
    return redirect(url_for('create_teamsheet'))

@app.route('/teamsheet/addathletes/<teamsheetid>', methods=['GET','POST'])#complete
@login_required
def add_athletes(teamsheetid):
    if current_user.usertype not in [1,2,3] or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        athlete_id= request.form.get('athlete')
        role = request.form.get('role')
        athletes = []
        query = db.engine.execute('SELECT * FROM team__sheet WHERE team_sheet_id = {} AND athlete_id = {}'.format(teamsheetid,athlete_id))
        for athlete in query:
            athletes.append(athlete)
        if athlete_id == "Select an athlete:":
            flash('You must select an athlete',category='error')
        elif role == "Enter athlete role" or role.strip() == "":
            flash('You must add a role for this athlete',category='error')
        elif len(athletes) > 0:
            flash('This athlete already has a role in the teamsheet',category='error')
        else:
            query = db.engine.execute("INSERT INTO team__sheet VALUES ('{}','{}','{}')".format(teamsheetid,athlete_id,role))
            db.session.commit()
    except:
        flash('There was an error adding this athlete into the teamsheet',category='error')
    return redirect(url_for('view_teamsheet'))

@app.route('/deletefromteamsheet/<teamsheetid>/<athleteid>')#complete
def delete_from_teamsheet(teamsheetid,athleteid):
    if current_user.usertype not in [1,2,3] or current_user.verified != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        query = db.engine.execute('DELETE FROM team__sheet WHERE team_sheet_id = {} AND athlete_id = {}'.format(teamsheetid,athleteid))
    except:
        flash('Was not able to delete this athlete from the teamsheet',catgeory='error')
    return redirect(url_for('view_teamsheet'))





if __name__ == "__main__":
    app.run(debug=True)
