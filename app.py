from array import *
from gzip import READ
import json
import re
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, make_response
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
    id = db.Column(db.Integer, primary_key = True)
    firstName = db.Column(db.String(50),nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    dob = db.Column(db.DateTime, nullable = False)    
    school_URN = db.Column(db.Integer, nullable = True)
    start_date = db.Column(db.DateTime, nullable = True, default=date.today())
    email = db.Column(db.String(70), nullable = False)
    password = db.Column(db.String(255), nullable = False)
    usertype = db.Column(db.Integer, default = -1)
    verified = db.Column(db.Integer, default = 0)
    #usertype = {0: athlete, 1: athlete/coach, 2: coach, 3: admin/coach. 4: admin}

class Fees(db.Model):
    fees_id = db.Column(db.Integer, primary_key= True)
    athlete_id = db.Column(db.Integer)
    amount = db.Column(db.Float, nullable = False)
    paid_date = db.Column(db.DateTime, nullable = True)
    paid = db.Column(db.Integer, default=0)

class Team_Details(db.Model):
    team_id = db.Column(db.Integer, primary_key= True)
    coach_id = db.Column(db.Integer)
    team_name= db.Column(db.String(20), nullable= False)
    max_age = db.Column(db.Integer, nullable=True)

class Team_Events(db.Model): #The coach decides they want to make a team for this event so will use the teamsheet id, the id of the event they want the team for and the team the sheet is being created for
    team_sheet_id= db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, primary_key= True)
    size = db.Column(db.Integer, nullable=False)

class Team_Members(db.Model): 
    team_id = db.Column(db.Integer, primary_key = True) 
    athlete_id = db.Column(db.Integer, primary_key= True)

class Team_Sheet(db.Model): #Will add each athlete to the teamsheet from team members
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

class Events(db.Model): #1. an event is made
    events_id= db.Column(db.Integer, primary_key=True)
    event_name= db.Column(db.Text, nullable =False)
    event_start_date= db.Column(db.DateTime, nullable = False)
    event_end_date = db.Column(db.DateTime, nullable=False)

def eligibity_age(born):
    today = [2022,5,31]
    born = born.split("-")
    return int(today[0]) - int(born[0]) - (((int(today[1]), int(today[2]))) < ((int(born[1]), int(born[2]))))

def age(born):
    today = str(date.today()).split("-")
    return int(today[0]) - int(born[0]) - (((int(today[1]), int(today[2]))) < ((int(born[1]), int(born[2]))))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error= error)

@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', error=error)

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
        if year > 0:
            anniversaries[user[0]] = [user[1] + " " + user[2], year]
    return render_template('admin.html',birthdays=birthdays, anniversaries= anniversaries)

@app.route('/users', methods= ['GET', 'POST'])
@login_required
def verify_users():
    if current_user.usertype < 4:
        return render_template('error.html')
    unverified_users = []
    query = db.engine.execute('SELECT id, firstName, surname, email FROM user WHERE verified < {}'.format(1))
    for user in query:
        unverified_users += user
    valid = False
    for item in request.values:
        item.split(("_"))
        if "_" in item:
            items = item.split("_")
            if len(items) == 2 and items[0].lower() == "usertype":
                try:
                    int(items[1][1])
                    valid = item
                except:
                    redirect(url_for('verify_users'))
    if valid:
        usertype = request.form.get(valid)
        userid = valid.split("_")[1][1]
        if request.method == 'POST':
            if usertype == 'Select user type':
                flash('You must select a usertype',category='error')
            else:
                query = db.engine.execute('UPDATE user SET usertype = {}, verified = {} WHERE id = {}'.format(usertype, 1,userid))
                db.session.commit()
                return redirect(url_for('verify_users'))
    verified_users = {}
    query = db.engine.execute('SELECT id, firstName, surname, email, usertype FROM user WHERE verified = {} ORDER BY id'.format(1))
    for user in query:
        if current_user.id != user[0]:
            verified_users[user[0]] = [user[1], user[2], user[3],user[4]]
    usertypes = {0: 'Athlete', 1: 'Coach', 2: 'Athlete/Coach', 3:'Admin', 4:'Admin/Coach',5:'Admin/Coach/Athlete'}
    return render_template('users.html', unverified_users=unverified_users, verified_users= verified_users, usertypes = usertypes)

@app.route('/setusers', methods= ['GET', 'POST'])
@login_required
def set_users():
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

@app.route('/deleteuser/<userid>')
@login_required
def delete_users(userid):
    verify_users()
    query = db.engine.execute('DELETE FROM user WHERE id = {}'.format(userid))
    query = db.engine.execute('DELETE FROM team__details WHERE coach_id = {}'.format(userid))
    db.session.commit()
    return redirect(url_for('verify_users'))

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
    return render_template('adminteams.html', team_names = team_names,coaches = coaches)

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
        coach_id = request.form.get('coach')
        team_name = request.form.get('team_name')
        max_age = request.form.get('max_age')
        existing_team = Team_Details.query.filter_by(team_name = team_name).first()
        existing_coach = Team_Details.query.filter_by(coach_id = coach_id).first()
        if existing_team:
            flash('There is already an existing team with this name', category='error')
        elif existing_coach:
            flash('This coach is already coaching a team')
        elif coach_id == "Select a coach:":
            flash('You must select a coach', category='error')
        elif team_name.rstrip() == "":
            flash('The team name cannot be empty', category='error')
        else:
            new_team = Team_Details(coach_id= coach_id, team_name= team_name, max_age= max_age)
            db.session.add(new_team)
            db.session.commit()
            flash('Your new team: {} has been created.'.format(team_name), category='success')
        return redirect(url_for('view_teams'))
    return render_template('adminteams.html', coaches = coaches)

@app.route('/athletes')
@login_required
def view_athletes():
    if -1 < current_user.usertype < 3:
        #need the team name, coach name, and all athlete names
        #you can get the team id from team members where the athlete id is the user id, and then for each team create a list which will have the team name and coach name
        #do the same query, but instead, get the team ids where the user id is the coach id
        #for each team, you will use the team id again to search team members, and find the names of each athlete in the team and store the names in a separate list
        #make the key a list and it will contain the team name and coach name, and the value will be the list of athlete names
        query = db.engine.execute('SELECT team__details.team_id FROM team__members,team__details WHERE team__members.athlete_id = {} AND team__details.team_id = team__members.team_id OR team__details.coach_id = {}'.format(current_user.id,current_user.id))
        teams = []
        for team in query:
            teams.append(team[0])
        teams = set(teams)
        team_members = {}
        for team in teams:
            athletes = []
            team_details = db.engine.execute('SELECT team__details.team_name, user.firstName, user.surname FROM team__details, user WHERE team__details.team_id = {}'.format(team))
            query = db.engine.execute('SELECT user.firstName, user.surname FROM user, team__details WHERE team__details.team_id = {}'.format(team))
            for athlete in query:
                print(athlete)
                athletes.append(athlete[0] + " " + athlete[1])
            for team_detail in team_details:
                athletes.insert(0,team_detail[1] + " " + team_detail[2])
                name = team_detail[0]
            team_members[name] = athletes
        print(team_members)
        return render_template('athletes.html')
    elif current_user.usertype > 2:
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
            athletes = db.engine.execute('SELECT id, firstName, surname, dob FROM user')
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
    else:
        return "You are not authorised to view this page"

@app.route('/deleteathletes/<teammemberid>')
@login_required
def delete_athletes(teammemberid):
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
    return redirect(url_for('view_athletes'))

@app.route('/createathletes', methods=['GET','POST'])
@login_required
def create_athletes():
    if request.method == 'POST':
        view_athletes()
        teammemberid = request.form.get('athlete').split('_')
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
    
@app.route('/events')
@login_required
def view_events():
    if -1 < current_user.usertype < 3:
        return render_template('events.html')
    elif current_user.usertype >2:
        cal_events = {}
        query = db.engine.execute("SELECT events_id, event_name, event_start_date, event_end_date FROM Events")
        for event in query:
            cal_events[event[0]] = [event[1],event[2],event[3]]     
        return render_template('adminevents.html', events=cal_events)

@app.route('/createevents', methods= ['GET','POST'])
@login_required
def create_events():
    req = request.get_json()
    print(req)
    name = req['title']
    start = req['start']
    end = req['end']
    start = start.strip("Z").split("T")
    end = end.strip("Z").split("T")
    start = (" ").join(start)
    end = (" ").join(end)
    query = db.engine.execute("INSERT INTO Events (event_name, event_start_date, event_end_date) VALUES ('{}','{}','{}')".format(name,start,end))
    db.session.commit()
    return redirect(url_for('view_events'))

@app.route('/deleteevents', methods= ['GET','POST'])
@login_required
def delete_events():
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
    return redirect(url_for('view_events'))

@app.route('/fees')
@login_required
def view_fees():
    if -1< current_user.usertype < 4:
        query = db.engine.execute('SELECT fees.fees_id, fees.amount, fees.paid_date, fees.paid FROM fees WHERE fees.athlete_id = {} ORDER BY fees.paid_date DESC'.format(current_user.id))
        fees={}
        for fee in query:
            if fee[3] == 0:
                fees[fee[0]] = [fee[1],fee[2],"No",fee[3]]
            else:
                fees[fee[0]] = [fee[1],fee[2],"Yes",fee[3]]
        return render_template('fees.html', fees=fees)
    elif current_user.usertype > 3:
        users = db.engine.execute('SELECT id, firstName, surname FROM user')
        athletes = {}
        for athlete in users:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]        
        query = db.engine.execute('SELECT fees.fees_id, user.firstName, user.surname, fees.amount, fees.paid_date, fees.paid FROM fees, user WHERE user.id = fees.athlete_id ORDER BY fees.paid_date DESC')
        return render_template('adminfees.html', fees=query, athletes=athletes)
    else:
        return 'You are not verified'

@app.route('/createfees', methods= ['GET','POST'])
@login_required
def create_fees():
    if request.method == "POST":
        users = db.engine.execute('SELECT id, firstName, surname FROM user')
        athletes = {}
        for athlete in users:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]   
        athlete_id = request.form.get('athlete')
        amount = request.form.get('amount')
        check = amount.isnumeric()
        if athlete_id == "Select an athlete:":
            flash('You must select an athlete',category='error')
        elif not check:
            flash('You must add a numeric number')
        else:
            print(True)
            query = db.engine.execute("INSERT INTO fees (athlete_id, amount) VALUES ('{}','{}')".format(athlete_id, amount))
            db.session.commit()
        return redirect(url_for('view_fees'))
    return render_template('adminfees.html', athletes=athletes)

@app.route('/setfees', methods=["GET","POST"])
@login_required
def set_fees_date():
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
            print(paidDate)
            if request.method == 'POST':
                query = db.engine.execute('UPDATE fees SET paid_date = "{}", paid = {} WHERE fees_id= {}'.format(paidDate,1,feesid))
                db.session.commit()
                return redirect(url_for('view_fees'))
        except:
            return redirect(url_for('view_fees'))
        return redirect(url_for('view_fees'))
    return redirect(url_for('view_fees'))

@app.route('/deletefees/<feeid>')
@login_required
def delete_fees(feeid):
    if current_user.usertype < 3:
        return "You're not authorised to view this page"
    else:
        query = db.engine.execute('DELETE FROM fees WHERE fees_id = {}'.format(feeid))
        db.session.commit()        
        return redirect(url_for('view_fees'))


@app.route('/training')
@login_required
def view_training():
    if -1 < current_user.usertype < 4:
        return render_template('training.html')
    elif current_user.usertype >3:
        return render_template('admintraining.html')
    else:
        return 'You are not verified to view this page'
 
@app.route('/createtraining')
@login_required
def create_training():
    if -1 < current_user.usertype < 4:
        return render_template('training.html')
    elif current_user.usertype >3:
        return render_template('admintraining.html')
    else:
        return 'You are not verified to view this page'

@app.route('/deletetraining/<trainingid>')
@login_required
def delete_training(trainingid):
    return 'This is where the admin manages all training sessions'

@app.route('/contacts')
@login_required
def view_contacts():
    if current_user.usertype == -1:
        return "You're not authorised to view this page"
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
    elif current_user.usertype > 3:
        query = db.engine.execute('SELECT id, firstName, surname FROM user WHERE usertype == {}'.format(0))
        athletes = {}
        for athlete in query:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]        
        query = db.engine.execute('SELECT contacts.contacts_id, user.firstName, user.surname, contacts.firstName, contacts.surname, contacts.number FROM contacts, user WHERE user.id = contacts.athlete_id')
        return render_template('admincontacts.html', contacts=query, athletes=athletes)
    else:
        return 'You are not authorised to view this page'

@app.route('/createcontacts/', methods= ['GET','POST'])
@login_required
def create_contacts():
    if request.method == 'POST':
        query = db.engine.execute('SELECT id, firstName, surname FROM user')
        athletes = {}
        for athlete in query:
            athletes[athlete[0]] = [athlete[1]+ " "+ athlete[2]]
        athlete_id = request.form.get('athlete')
        firstName = request.form.get('firstName')
        surname = request.form.get('surname')
        number = request.form.get('number')
        if athlete_id == 'Select an athlete:':
            flash('You must select an athlete', category='error')
        elif firstName.strip()== "":
            flash('You cannot leave the contact name empty', category='error')
        elif surname.strip()== "":
            flash('You cannot leave the contact name empty', category='error') 
        elif number.strip()== "":
            flash('You cannot leave the contact number empty', category='error')
        else:
            query = db.engine.execute("INSERT INTO contacts (athlete_id, firstName, surname, number) VALUES ('{}','{}', '{}', '{}')".format(athlete_id, firstName,surname,number))
            db.session.commit()                  
        return redirect(url_for('view_contacts'))
    return render_template('admincontacts.html', athletes=athletes)

@app.route('/deletecontacts/<contactid>')
@login_required
def delete_contacts(contactid):
    query = db.engine.execute('DELETE FROM contacts WHERE contacts_id = {}'.format(contactid))
    flash('You have successfully deleted a contact', category = 'success')
    db.session.commit()
    return redirect(url_for('view_contacts'))

@app.route('/teamsheet')
@login_required
def view_teamsheet():
    if current_user.usertype == -1:
        return "You're not authorised to view this page"
    elif current_user.usertype == 0:
        return render_template('teamsheet.html')
    elif 0 < current_user.usertype < 3:
        
        return render_template('coachteamsheet.html')
    
    return render_template('adminteamsheet.html')

@app.route('/createteamsheet')
@login_required
def create_teamsheet():
    query = db.engine.execute('SELECT * FROM Events') #id, name, start, end
    events = {}
    for event in query:
        event_start_date = event[2].split(" ")[0]
        event_start_date = event_start_date.split("-")
        event_start_date = date(int(event_start_date[0]),int(event_start_date[1]),int(event_start_date[2]))
        print(event_start_date > date.today())
        if event_start_date > date.today():
            events[event[0]] = [event[1],event[2],event[3]]
    return render_template('createteamsheet.html', events = events)

@app.route('/deleteteamsheet/<teamsheetid>')
@login_required
def delete_teamsheet(teamsheetid):
    return 'Allow coach to delete teamsheet'



if __name__ == "__main__":
    app.run(debug=True)
