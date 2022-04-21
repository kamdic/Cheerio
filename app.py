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
        return str(self.start_date)
    
    def get_email(self):
        return self.email
    
    def get_password_hash(self):
        return self.password
    
    def get_usertype(self):
        return self.usertype

    def get_verified(self):
        return self.verified
    
    def get_birthday(self):
        dob= str(self.get_dob()).rstrip("00:00:00.0000000").split("-")
        today = str(date.today()).split("-")
        if (today[1].strip() == dob[1].strip()) and (today[2].strip() == dob[2].strip()):
            return True
        return False
    
    def get_age(self):
        today = str(date.today()).split("-")
        dob = str(self.get_dob()).rstrip("00:00:00.0000000").split("-")
        return int(today[0]) - int(dob[0]) - (((int(today[1]), int(today[2]))) < ((int(dob[1]), int(dob[2]))))
    
    def get_anniversary(self):
        today = str(date.today()).split("-")    
        year = int(today[0]) - int((str(self.get_start_date()).split("-")[0]))
        return year
    
    def verify_user(self,usertype):
        db.engine.execute('UPDATE user SET usertype = {}, verified = {} WHERE id = {}'.format(usertype, 1,self.get_id()))
    
    def set_usertype(self, usertype):
        db.engine.execute('UPDATE user SET usertype = {} WHERE id = {}'.format(usertype, self.get_id()))
    
    def set_start(self,startDate):
        startDate = str(("-").join(startDate)) + '00:00:00.0000000'
        db.engine.execute('UPDATE user SET start_date = "{}" WHERE id= {}'.format(startDate,self.get_id()))
    
    def delete_contact(self):
        db.engine.execute('DELETE FROM contacts WHERE athlete_id = {}'.format(self.get_id()))
    
    def delete_fee(self):
        db.engine.execute('DELETE FROM fees WHERE athlete_id = {}'.format(self.get_id()))
    
    def delete_from_members(self):
        db.engine.execute('DELETE FROM team__members WHERE athlete_id = {}'.format(self.get_id()))
    
    def delete_team(self):
        db.engine.execute('DELETE FROM team__details WHERE coach_id = {}'.format(self.get_id()))
    
    def delete_user(self):
        db.engine.execute('DELETE FROM user WHERE id = {}'.format(self.get_id()))
    

    def get_eligibility_age(self):
        year = (str(date.today()).split("-"))[0]
        today = [year,5,31]
        athlete_date = str(self.get_dob()).rstrip("00:00:00.0000000")
        born = athlete_date.split("-")
        return int(today[0]) - int(born[0]) - (((int(today[1]), int(today[2]))) < ((int(born[1]), int(born[2]))))

class Fees(db.Model):
    __tablename__ = "fees"
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
        return str(self.paid_date)

    def get_paid(self):
        return self.paid
    
    def delete_fee(self):
        db.engine.execute('DELETE FROM fees WHERE fees_id = {}'.format(self.get_fees_id()))

class Team_Details(db.Model):
    __tablename__ = 'team__details'
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
    
    def get_team_information(self):
        query = db.engine.execute("SELECT team__details.max_age, team__details.team_name, user.firstName, user.surname FROM team__details, user WHERE user.id == team__details.coach_id AND team__details.team_id = {}".format(self.get_team_id()))
        for team in query:
            return [team[0], team[1], team[2] + " " + team[3]]
    
    def delete_team(self):
        db.engine.execute('DELETE FROM team__details WHERE team_id = {}'.format(self.get_team_id()))
        query = db.engine.execute('SELECT team_sheet_id FROM team__events WHERE team_id = {}'.format(self.get_team_id()))
        for sheet in query:
            db.engine.execute('DELETE FROM team__sheet WHERE team__sheet_id = {}'.format(sheet[0]))
        db.engine.execute('DELETE FROM team__events WHERE team__events.team_id = {}'.format(self.get_team_id()))
        db.engine.execute('DELETE FROM team__members WHERE team_id = {}'.format(self.get_team_id()))
    

class Team_Events(db.Model): #The coach decides they want to make a team for this event so will use the teamsheet id, the id of the event they want the team for and the team the sheet is being created for
    __tablename__ = "team__events"
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

    def get_size(self,key):
        sizes = {0:"X Small (5-14)",1:"Small (15-22)",2:"Medium (23-32)",3:"Large (33-38)"}
        return sizes[key]
    
    
    def get_athletes(self):
        athletes = []
        query = db.engine.execute('SELECT user.firstName, user.surname, team__sheet.role,user.id FROM team__sheet,user WHERE team__sheet.team_sheet_id = {} AND user.id = team__sheet.athlete_id'.format(self.get_team_sheet_id()))
        for athlete in query:
            athlete = User.query.filter_by(id = athlete[3]).first()
            team_sheet = Team_Sheet.query.filter_by(team_sheet_id = self.get_team_sheet_id(),athlete_id = athlete.get_id()).first()
            athlete = (athlete.get_first_name(), athlete.get_surname(),team_sheet.role, athlete.get_id())
            athletes.append(athlete)
        return athletes
    
    def delete_teamsheet(self):
        db.engine.execute("DELETE FROM team__events WHERE team_sheet_id = {}".format(self.get_team_sheet_id()))
        db.engine.execute("DELETE FROM team__sheet WHERE team_sheet_id = {}".format(self.get_team_sheet_id()))

class Team_Members(db.Model): 
    __tablename__ = "team__members"
    team_id = db.Column(db.Integer, primary_key = True) 
    athlete_id = db.Column(db.Integer, primary_key= True)

    def get_team_id(self):
        return self.team_id

    def get_athlete_id(self):
        return self.athlete_id
    
    def get_athletes(self,teamid):
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__members WHERE user.id = team__members.athlete_id AND team__members.team_id = {}'.format(teamid))
        athletes = []
        for athlete in query:
            athlete = User.query.filter_by(id = athlete[0]).first()
            athletes.append(athlete.get_first_name() + " " + athlete.get_surname())
        return athletes
    
    def delete_from_members(self,teamid,athleteid):
        db.engine.execute('DELETE FROM team__members WHERE (team_id = {} AND athlete_id = {})'.format(teamid, athleteid))

class Team_Sheet(db.Model): #Will add each athlete to the teamsheet from team members
    __tablename__ = "team__sheet"
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    athlete_id= db.Column(db.Integer, primary_key= True)
    role= db.Column(db.String(10), default = 'Tumbler')

    def get_team_sheet_id(self):
        return self.team_sheet_id

    def get_athlete_id(self):
        return self.athlete_id

    def get_role(self):
        return self.role
    
    def delete_from_team(self):
        db.engine.execute('DELETE FROM team__sheet WHERE team_sheet_id = {} AND athlete_id = {}'.format(self.get_team_sheet_id(),self.get_athlete_id()))
    
class Contacts(db.Model):
    __tablename__ = "contacts"
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
    
    def delete_contact(self):
        db.engine.execute('DELETE FROM contacts WHERE contacts_id = {}'.format(self.get_contacts_id()))

    

class Events(db.Model): #1. an event is made
    __tablename__ = "events"
    events_id= db.Column(db.Integer, primary_key=True)
    event_name= db.Column(db.Text, nullable =False)
    event_start_date= db.Column(db.DateTime, nullable = False)
    event_end_date = db.Column(db.DateTime, nullable=False)

    def get_events_id(self):
        return self.events_id

    def get_event_name(self):
        return self.event_name

    def get_event_start_date(self):
        return str(self.event_start_date)

    def get_event_end_date(self):
        return str(self.event_end_date)
    
    def delete_event(self):
        db.engine.execute('DELETE FROM Events WHERE events_id = {}'.format(self.get_events_id()))



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
        user = User.query.filter_by(id = user[0]).first()
        if user.get_birthday():
            birthdays[user.get_id()] = [user.get_first_name() + " " + user.get_surname(), user.get_age()]
        if user.get_anniversary() > 1:
            anniversaries[user.get_id()] = [user.get_first_name() + " " + user.get_surname(), user.get_anniversary()]
    return render_template('admin.html',birthdays=birthdays, anniversaries= anniversaries)

@app.route('/users', methods= ['GET', 'POST'])#complete
@login_required
def verify_users():
    if current_user.get_usertype() < 3:
        return render_template('error.html',error="You are not authorised to view this page")
    unverified_users = {}
    query = db.engine.execute('SELECT id, firstName, surname, email FROM user WHERE verified < {}'.format(1))
    for user in query:
        user = User.query.filter_by(id = user[0]).first()
        unverified_users[user.get_id()] = [user.get_first_name(),user.get_surname(),user.get_email()]
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
                user_to_change = User.query.filter_by(id = userid).first()
                user_to_change.verify_user(usertype)
                db.session.commit()
                return redirect(url_for('verify_users'))
    verified_users = {}
    query = db.engine.execute('SELECT id, firstName, surname, email, usertype, start_date FROM user WHERE verified = {} ORDER BY id'.format(1))
    for user in query:
        user = User.query.filter_by(id = user[0]).first()
        if current_user.get_id() != user.get_id():
            verified_users[user.get_id()] = [user.get_first_name(), user.get_surname(), user.get_email(),user.get_usertype(),user.get_start_date().rstrip('00:00:00.000000')]
    usertypes = {0: 'Athlete', 1: 'Athlete/Coach', 2: 'Coach', 3:'Admin'}
    return render_template('users.html', unverified_users=unverified_users, verified_users= verified_users, usertypes = usertypes)

@app.route('/setusers', methods= ['GET', 'POST'])#complete
@login_required
def set_users():
    if current_user.get_usertype() < 3:
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
                user = User.query.filter_by(id = userid).first()
                user.set_usertype(usertype)
                db.session.commit()
                return redirect(url_for('verify_users'))
    return redirect(url_for('verify_users'))

@app.route('/setdate',methods=['GET','POST'])#complete
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
        startDate = str(request.form.get(valid)).split("-")
        userid = valid.split("_")[1]
        try:
            if request.method == 'POST':
                user = User.query.filter_by(id =userid).first()
                user.set_start(startDate)
                db.session.commit()
                return redirect(url_for('verify_users'))
        except:
            return redirect(url_for('verify_users'))
        return redirect(url_for('verify_users')) 
    return redirect(url_for('verify_users'))
    
@app.route('/deleteuser/<userid>')#complete
@login_required
def delete_users(userid):
    if current_user.get_usertype() != 3:
        return render_template('error.html',error="You are not authorised to view this page")    
    verify_users()
    try:
        user_to_delete = User.query.filter_by(id = userid).first()
        user_to_delete.delete_contact()
        user_to_delete.delete_fee()
        if user_to_delete.get_usertype() == 0:
            try:
                user_to_delete.delete_from_members()
            except:
                pass
        elif user_to_delete.get_usertype() == 1:
            try:
                user_to_delete.delete_from_members()
                query = db.engine.execute('SELECT team_id FROM team__details WHERE coach_id = {}'.format(userid))
                for team in query:
                    teamid = team[0]
                delete_teams(teamid)
            except:
                pass    
        elif user_to_delete.get_usertype() == 2:
            try:
                user_to_delete.delete_team()
            except:
                pass
        elif user_to_delete.get_usertype() == 3:
            try:
                user_to_delete.delete_from_members()
                query = db.engine.execute('SELECT team_id FROM team__details WHERE coach_id = {}'.format(userid))
                for team in query:
                    teamid = team[0]
                delete_teams(teamid)
            except:
                pass
        user_to_delete.delete_user()
        db.session.commit()
    except:
        pass
    return redirect(url_for('verify_users'))

@app.route('/teams', methods=['GET','POST'])#complete
@login_required
def view_teams():
    team_names = {}
    coaches = {}
    query = db.engine.execute("SELECT team__details.team_id, team__details.max_age, team__details.team_name, user.firstName, user.surname FROM team__details, user WHERE user.id == team__details.coach_id ")
    for team in query:
        team = Team_Details.query.filter_by(team_id = team[0]).first()
        team_names[team.get_team_id()] = team.get_team_information()
    query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user WHERE user.usertype > {}'.format(0))
    coaches = {}
    for coach in query:
        coach = User.query.filter_by(id = coach[0]).first()
        coaches[coach.get_id()] = [coach.get_first_name()+ " "+ coach.get_surname()]
    if current_user.get_usertype() == -1 or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    if -1 < current_user.get_usertype() < 3:
        return render_template('teams.html', team_names = team_names, coaches = coaches)
    db.session.commit()
    return render_template('adminteams.html', team_names = team_names,coaches = coaches)

@app.route('/deleteteams/<teamid>')#complete
@login_required
def delete_teams(teamid):
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        team = Team_Details.query.filter_by(team_id = teamid).first()
        team.delete_team()
        db.session.commit()
        flash('You have successfully deleted a team', category = 'success')
    except:
        pass
    return redirect(url_for('view_teams'))


@app.route('/createteams', methods=['GET','POST'])#complete
@login_required
def create_teams():
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
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
        if current_user.get_usertype() not in [0,1,2,3] or current_user.get_verified() != 1:
            return render_template('error.html',error="You are not authorised to view this page")
        elif  current_user.get_usertype() == 0:
            members = {}
            query = db.engine.execute('SELECT team__details.team_id FROM team__members, team__details WHERE team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.get_id()))
            for team in query:
                team = Team_Details.query.filter_by(team_id = team[0]).first()
                team_members = Team_Members.query.filter_by(team_id = team.get_team_id()).first()
                athletes = team_members.get_athletes(team.get_team_id())
                members[team.get_team_id()] = [team.get_team_name(),athletes]
            return render_template('athletes.html',members=members)
        elif  current_user.get_usertype() == 1:
            team_members = {}
            query = db.engine.execute('SELECT team__details.team_id FROM team__members, team__details WHERE team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.get_id()))
            for team in query:
                team = Team_Details.query.filter_by(teamid = team[0])
                team_members = Team_Members.query.filter_by(team_id = team.get_team_id()).first()
                athletes = team_members.get_athletes(team.get_team_id())
                team_members[team.get_team_id()] = [team.get_team_id(),athletes]
            coach_members = {}
            query = db.engine.execute('SELECT team__details.team_id, team__details.team_name, user.firstName, user.surname FROM team__details, user, team__members WHERE team__details.team_id = team__members.team_id AND team__details.coach_id = {} AND user.id = team__members.athlete_id'.format(current_user.get_id()))
            for member in query:
                team = Team_Details.query.filter_by(team_id = member[0]).first()
                team_member = Team_Members.query.filter_by(team_id = team.get_team_id()).first()
                team_name = team.get_team_name()
                athletes = team_member.get_athletes(team.get_team_id())  
                coach_members[team_name] = athletes           
            return render_template('coachathleteathletes.html',team_members=team_members,coach_members=coach_members)
        elif  current_user.get_usertype() == 2:
            members = {}
            query = db.engine.execute('SELECT team__details.team_id, team__details.team_name, user.firstName, user.surname FROM team__details, user, team__members WHERE team__details.team_id = team__members.team_id AND team__details.coach_id = {} AND user.id = team__members.athlete_id'.format(current_user.get_id()))
            for member in query:
                team = Team_Details.query.filter_by(team_id = member[0]).first()
                team_members = Team_Members.query.filter_by(team_id = team.get_team_id()).first()
                team_name = team.get_team_name()
                athletes = team_members.get_athletes(team.get_team_id()) 
            members[team_name] = athletes   
            return render_template('coachathletes.html',members = members)           
        elif current_user.get_usertype() == 3:
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
                    athlete = User.query.filter_by(id = athlete[0]).first()
                    element = [str(index) +athlete.get_first_name() + " " + athlete.get_surname()]
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
                team = Team_Details.query.filter_by(team_id = team[0]).first()
                max_age = team.get_max_age()
                eligible_athletes = []
                athletes = db.engine.execute('SELECT id, firstName, surname, dob FROM user WHERE usertype = {} OR usertype = {}'.format(0,1))
                if max_age:
                    for athlete in athletes:
                        athlete = User.query.filter_by(id = athlete[0]).first()
                        athlete_age = athlete.get_eligibility_age()
                        if max_age >= athlete_age:
                            eligible_athletes += [str(athlete.get_id())+athlete.get_first_name() + " "+ athlete.get_surname()]  
                else:
                    for athlete in athletes:
                        athlete = User.query.filter_by(id = athlete[0]).first()
                        eligible_athletes += [str(athlete.get_id())+athlete.get_first_name() + " "+ athlete.get_surname()]  
                possible_athletes[team.get_team_id()] = eligible_athletes
            return render_template('adminathletes.html',team_count= team_count,teams=teams, team_names=team_names,possible_athletes=possible_athletes)
    except:
        return render_template('error.html',error="You do not have a team to create a teamsheet for, consult an admin to create one")  

@app.route('/deleteathletes/<teammemberid>')#complete
@login_required
def delete_athletes(teammemberid):
    if current_user.get_usertype() != 3 or current_user.get_verified()!= 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        ids = []
        query = db.engine.execute('SELECT * FROM team__members ORDER BY team_id ASC')
        for id in query:
            ids.append(id)
        teammemberid = re.sub("[^0-9]", "", teammemberid)
        team_id = ids[int(teammemberid)][0]
        athlete_id = ids[int(teammemberid)][1]
        team_member = Team_Members.query.filter_by(team_id = team_id, athlete_id = athlete_id).first()
        team_member.delete_from_members(team_id,athlete_id)
        flash('You have successfully deleted a team member', category = 'success')
        db.session.commit() 
    except:
        flash('There was a problem deleting this athlete from the team', category='error')   
    return redirect(url_for('view_athletes'))

@app.route('/createathletes', methods=['GET','POST'])#complete
@login_required
def create_athletes():
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
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
        event = Events.query.filter_by(events_id = event[0]).first()
        cal_events[event.get_events_id()] = [event.get_event_name(),event.get_event_start_date(),event.get_event_end_date()]    
    if current_user.get_usertype() not in [0,1,2,3] or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    if -1 < current_user.get_usertype() < 3:
        return render_template('events.html', events=cal_events)
    elif current_user.get_usertype() >2: 
        return render_template('adminevents.html', events=cal_events)

@app.route('/createevents', methods= ['GET','POST'])#complete
@login_required
def create_events():
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
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
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page") 
    req = request.get_json()
    name = req['title']
    start = req['start']
    end = req['end']
    start = start.strip("Z").split("T")
    end = end.strip("Z").split("T")
    start = (str((" ").join(start))).rstrip('0').rstrip('.')
    end = str((" ").join(end))  .rstrip('0').rstrip('.')  
    query = db.engine.execute('SELECT * FROM Events')
    events = []
    for event in query:
        event = Events.query.filter_by(events_id = event[0]).first()
        if str(event.get_event_start_date()) == start and str(event.get_event_end_date()) == end and event.get_event_name() == name:
            events.append(event.get_events_id())
    if len(events) == 1:
        event = Events.query.filter_by(events_id = events[0]).first()
        event.delete_event()
        db.session.commit()
    flash('Was not able to delete this event', category='error')
    return redirect(url_for('view_events'))

@app.route('/fees')#complete
@login_required
def view_fees():
    if current_user.get_usertype() not in [0,1,2,3] or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    if -1< current_user.get_usertype() < 3:
        query = db.engine.execute('SELECT fees.fees_id, fees.amount, fees.paid_date, fees.paid FROM fees WHERE fees.athlete_id = {} ORDER BY fees.paid_date DESC'.format(current_user.id))
        fees={}
        for fee in query:
            fee = Fees.query.filter_by(fees_id = fee[0]).first()
            if fee.get_paid() != 1:
                fees[fee.get_fees_id()] = [fee.get_amount(),'N/A',"No",fee.get_paid()]
            else:
                paiddate = fee.get_paid_date()
                paiddate = ("-").join(paiddate)
                fees[fee.get_fees_id()] = [fee.get_amount(),paiddate,"Yes",fee.get_paid()]
        return render_template('fees.html', fees=fees)
    elif current_user.get_usertype() == 3:
        users = db.engine.execute('SELECT id FROM user')
        athletes = {}
        for athlete in users:
            athlete = User.query.filter_by(id = athlete[0]).first()
            athletes[athlete.get_id()] = [athlete.get_first_name()+ " "+ athlete.get_surname()]        
        query = db.engine.execute('SELECT fees.fees_id, user.firstName, user.surname, fees.amount, fees.paid_date, fees.paid FROM fees, user WHERE user.id = fees.athlete_id ORDER BY fees.paid_date DESC')
        return render_template('adminfees.html', fees=query, athletes=athletes)

@app.route('/createfees', methods= ['GET','POST'])#complete
@login_required
def create_fees():
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    if request.method == "POST":
        users = db.engine.execute('SELECT id, firstName, surname FROM user')
        athletes = {}
        for athlete in users:
            athlete = User.query.filter_by(id = athlete[0]).first()
            athletes[athlete.get_id()] = [athlete.get_first_name()+ " "+ athlete.get_surname()]   
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
        paidDate = str(request.form.get(valid))
        feesid = valid.split("_")[1]
        try:
            if request.method == 'POST':
                query = db.engine.execute('UPDATE fees SET paid_date = "{}", paid = {} WHERE fees_id= {}'.format(paidDate,1,feesid))
                db.session.commit()
                return redirect(url_for('view_fees'))
        except:
            return redirect(url_for('view_fees'))
        return redirect(url_for('view_fees'))
    return redirect(url_for('view_fees'))

@app.route('/deletefees/<feeid>')#oop
@login_required
def delete_fees(feeid):
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:  
        db.engine.execute('DELETE FROM fees WHERE fees_id = {}'.format(feeid))
        db.session.commit()  
    except: 
        flash('Was not able to delete this fee', category='error')
    return redirect(url_for('view_fees'))

@app.route('/contacts')#complete
@login_required
def view_contacts():
    if current_user.get_usertype() not in [0,1,2,3] or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")  
    elif current_user.get_usertype() == 0:
        query = db.engine.execute('SELECT firstName, surname, number FROM contacts WHERE contacts.athlete_id == {}'.format(current_user.get_id()))
        return render_template('contacts.html', contacts=query)
    elif current_user.get_usertype() == 1:
        own_contacts = db.engine.execute('SELECT firstName, surname, number FROM contacts WHERE contacts.athlete_id == {}'.format(current_user.get_id()))
        team = db.engine.execute('SELECT team__members.athlete_id FROM team__members,team__details WHERE team__details.coach_id == {} AND team__details.team_id = team__members.team_id'.format(current_user.id))
        athletes = {}
        for athlete in team:
            athlete = User.query.filter_by(id = athlete[0]).first()
            info = db.engine.execute('SELECT contacts.contacts_id, user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id == {} AND contacts.athlete_id == {}'.format(athlete.get_id(),athlete.get_id()))
            for details in info:
                details = Contacts.query.filter_by(contacts_id = details[0]).first()
                athletes[athlete.get_id()] = [athlete.get_first_name(), athlete.get_surname(),details.get_first_name(),details.get_surname(),details.get_number()]
        query = db.engine.execute('SELECT team_id, team_name FROM team__details WHERE coach_id = {}'.format(current_user.get_id()))
        for name in query:
            team = Team_Details.query.filter_by(team_id = name[0]).first()
            name = team.get_team_name()
        return render_template('coachathletecontacts.html', own_contacts = own_contacts, athletes = athletes, name = name)
    elif current_user.get_usertype() == 2:
        team = db.engine.execute('SELECT team__members.athlete_id FROM team__members,team__details WHERE team__details.coach_id == {} AND team__details.team_id = team__members.team_id'.format(current_user.get_id()))
        athletes = {}
        for athlete in team:
            athlete = User.query.filter_by(id = athlete[0]).first()
            info = db.engine.execute('SELECT contacts.contacts_id, user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id == {} AND contacts.athlete_id == {}'.format(athlete.get_id(),athlete.get_id()))
            for details in info:
                details = Contacts.query.filter_by(contacts_id = details[0]).first()
                athletes[athlete.get_id()] = [athlete.get_first_name(), athlete.get_surname(),details.get_first_name(),details.get_surname(),details.get_number()]
        query = db.engine.execute('SELECT team_id, team_name FROM team__details WHERE coach_id = {}'.format(current_user.get_id()))
        for name in query:
            team = Team_Details.query.filter_by(team_id = name[0]).first()
            name = team.get_team_name()
        return render_template('coachcontacts.html', athletes=athletes, name=name)
    elif current_user.get_usertype() == 3:
        query = db.engine.execute('SELECT id, firstName, surname FROM user WHERE usertype == {} OR usertype == {}'.format(0,1))
        athletes = {}
        for athlete in query:
            athlete = User.query.filter_by(id = athlete[0]).first()
            athletes[athlete.get_id()] = [athlete.get_first_name()+ " "+ athlete.get_surname()]       
        query = db.engine.execute('SELECT contacts.contacts_id, user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id = contacts.athlete_id')
        return render_template('admincontacts.html', contacts=query, athletes=athletes)

@app.route('/createcontacts/', methods= ['GET','POST'])#complete
@login_required
def create_contacts():
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
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
    if current_user.get_usertype() != 3 or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        contact = Contacts.query.filter_by(contacts_id = contactid).first()
        contact.delete_contact()
        flash('You have successfully deleted a contact', category = 'success')
        db.session.commit()
    except:
        flash('Was not able to delete this contact successfully', category='error')
    return redirect(url_for('view_contacts'))

@app.route('/teamsheet')#complete
@login_required
def view_teamsheet():
    if current_user.get_usertype() not in [0,1,2,3] or current_user.get_verified() != 1:
        return "You're not authorised to view this page"
    elif current_user.get_usertype() == 0:
        team_sheets = {}
        events = []
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name, team__details.team_name FROM events, team__events, team__details, team__members WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.get_id()))
        for event in query:
            event = Team_Events.query.filter_by(team_sheet_id = event[0]).first()
            events.append(event)
        for event in events:
            athletes = event.get_athletes()
            event_name = Events.query.filter_by(events_id = event.get_eventid()).first()
            team_name = Team_Details.query.filter_by(team_id = event.get_team_id()).first()
            team_sheets[event.get_team_sheet_id()] = [event_name.get_event_name(), team_name.get_team_name(),athletes]
        return render_template('teamsheet.html',team_sheets=team_sheets)
    elif current_user.get_usertype() == 1:
        own_team_sheets = {}
        events = []
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name, team__details.team_name FROM events, team__events, team__details, team__members WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.team_id = team__members.team_id AND team__members.athlete_id = {}'.format(current_user.get_id()))
        for event in query:
            event = Team_Events.query.filter_by(team_sheet_id = event[0]).first()
            events.append(event)
        for event in events:
            athletes = event.get_athletes()
            event_name = Events.query.filter_by(events_id = event.get_eventid()).first()
            team_name = Team_Details.query.filter_by(team_id = event.get_team_id()).first()
            own_team_sheets[event.get_team_sheet_id()] = [event_name.get_event_name(), team_name.get_team_name(),athletes]
        coach_team_sheets = {}
        events = []
        options = {}
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.get_id()))
        for event in query:
            event = Team_Events.query.filter_by(team_sheet_id = event[0]).first()
            events.append(event)
        for event in events:
            athletes = event.get_athletes()
            event_name = Events.query.filter_by(events_id = event.get_eventid()).first()
            coach_team_sheets[event.get_team_sheet_id()] = [event_name.get_event_name(),athletes]
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__events, team__details,team__members WHERE team__events.team_id = team__details.team_id AND team__details.coach_id = {} AND team__members.team_id = team__details.team_id AND user.id = team__members.athlete_id'.format(current_user.id))
        for athlete in query:
            athlete = User.query.filter_by(id = athlete[0]).first()
            options[athlete.get_id()] = [athlete.get_first_name() + " " + athlete.get_surname()]
        return render_template('coachathleteteamsheet.html',own_team_sheets=own_team_sheets,coach_team_sheets=coach_team_sheets,athletes=options)
    elif  current_user.get_usertype() == 2:
        team_sheets = {}
        events = []
        options = {}
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.id))
        for event in query:
            event = Team_Events.query.filter_by(team_sheet_id = event[0]).first()
            events.append(event)
        for event in events:
            athletes = event.get_athletes()
            event_name = Events.query.filter_by(events_id = event.get_eventid()).first()
            team_sheets[event.get_team_sheet_id()] = [event_name.get_event_name(),athletes]
        query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__events, team__details,team__members WHERE team__events.team_id = team__details.team_id AND team__details.coach_id = {} AND team__members.team_id = team__details.team_id AND user.id = team__members.athlete_id'.format(current_user.get_id()))
        for athlete in query:
            athlete = User.query.filter_by(id = athlete[0]).first()
            options[athlete.get_id()] = [athlete.get_first_name() + " " + athlete.get_surname()]
        return render_template('coachteamsheet.html', team_sheets=team_sheets,athletes=options)
    other_team_sheets = {}
    events = []
    query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name,team__details.team_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND NOT team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.get_id()))
    for event in query:
        event = Team_Events.query.filter_by(team_sheet_id = event[0]).first()
        events.append(event)
        for event in events:
            athletes = event.get_athletes()
            event_name = Events.query.filter_by(events_id = event.get_eventid()).first()
            team_name = Team_Details.query.filter_by(team_id = event.get_team_id()).first()
        other_team_sheets[event.get_team_sheet_id()] = [event_name.get_event_name(),team_name.get_team_name(),athletes]
    own_team_sheets = {}
    events = []
    options = {}
    query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name FROM events, team__events, team__details WHERE events.events_id = team__events.event_id  AND team__details.team_id = team__events.team_id AND team__details.coach_id = {} ORDER BY team__events.team_sheet_id'.format(current_user.get_id()))
    for event in query:
        event = Team_Events.query.filter_by(team_sheet_id = event[0]).first()
        events.append(event)
        for event in events:
            team_sheet_id = event.get_team_sheet_id()
            athletes = event.get_athletes()
            event_name = Events.query.filter_by(events_id = event.get_eventid()).first()
        own_team_sheets[team_sheet_id] = [event_name.get_event_name(),athletes]    
    query = db.engine.execute('SELECT user.id, user.firstName, user.surname FROM user, team__events, team__details,team__members WHERE team__events.team_id = team__details.team_id AND team__details.coach_id = {} AND team__members.team_id = team__details.team_id AND user.id = team__members.athlete_id'.format(current_user.get_id()))
    for athlete in query:
        athlete = User.query.filter_by(id = athlete[0]).first()
        options[athlete.get_id()] = [athlete.get_first_name() + " " + athlete.get_surname()]
    return render_template('adminteamsheet.html',own_team_sheets = own_team_sheets,athletes=options,other_team_sheets=other_team_sheets)

@app.route('/createteamsheet',methods=['GET','POST'])#complete
@login_required
def create_teamsheet():
    try:
        if current_user.get_usertype() not in [1,2,3] or current_user.get_verified() != 1:
            return render_template('error.html',error="You are not authorised to view this page")   
        sizes = {0:"X Small (5-14)",1:"Small (15-22)",2:"Medium (23-32)",3:"Large (33-38)"}
        query = db.engine.execute('SELECT * FROM Events')
        events = {}
        for event in query:
            event = Events.query.filter_by(events_id = event[0]).first()
            event_start_date = event.get_event_start_date().split(" ")[0]
            event_start_date = event_start_date.split("-")
            event_start_date = date(int(event_start_date[0]),int(event_start_date[1]),int(event_start_date[2]))
            if event_start_date > date.today():
                events[event.get_events_id()] = [event.get_event_name(),event.get_event_start_date().split(" ")[0],event.get_event_end_date().split(" ")[0]]
        existing_sheets = {}
        query = db.engine.execute('SELECT team__events.team_sheet_id, events.event_name, team__events.size FROM team__details, events, team__events WHERE team__details.team_id = team__events.team_id AND events.events_id = team__events.event_id AND team__details.coach_id = {}'.format(current_user.get_id()))
        for team in query:
            key = team[2]
            team_event = Team_Events.query.filter_by(team_sheet_id = team[0]).first()
            team = Team_Details.query.filter_by(team_id = team_event.get_team_id()).first()
            existing_sheets[team_event.get_team_sheet_id()] = [team.get_team_name(),team_event.get_size(key)]
        query = db.engine.execute('SELECT team_id, team_name FROM team__details WHERE coach_id = {}'.format(current_user.get_id()))
        for team in query:
            team = Team_Details.query.filter_by(team_id = team[0]).first()
            team_name =team.get_team_name()
            team_id = team.get_team_id()
        if current_user.get_usertype() == 1:
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
        elif current_user.get_usertype() == 2:
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
        elif current_user.get_usertype() == 3:
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
    if current_user.get_usertype() not in [1,2,3] or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        team_sheet = Team_Events.query.filter_by(team_sheet_id = teamsheetid).first()
        team_sheet.delete_teamsheet()
        db.session.commit()
    except:
        flash('An error occured whilst trying to delete this teamsheet', category='error')
    return redirect(url_for('create_teamsheet'))

@app.route('/teamsheet/addathletes/<teamsheetid>', methods=['GET','POST'])#complete
@login_required
def add_athletes(teamsheetid):
    if current_user.get_usertype() not in [1,2,3] or current_user.get_verified() != 1:
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
    if current_user.get_usertype() not in [1,2,3] or current_user.get_verified() != 1:
        return render_template('error.html',error="You are not authorised to view this page")
    try:
        team_sheet = Team_Sheet.query.filter_by(team_sheet_id = teamsheetid,athlete_id=athleteid).first()
        team_sheet.delete_from_team()
        query = db.engine.execute('DELETE FROM team__sheet WHERE team_sheet_id = {} AND athlete_id = {}'.format(teamsheetid,athleteid))
    except:  
        flash('Was not able to delete this athlete from the teamsheet',category='error')
    return redirect(url_for('view_teamsheet'))





if __name__ == "__main__":
    app.run(debug=True)
