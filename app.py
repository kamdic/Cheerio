from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cheer.db'
db = SQLAlchemy(app)

class Admin(db.Model):#add password
    admin_id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(50), nullable = False)
    surname = db.Column(db.String(50), nullable = False)
    email_address = db.Column(db.String(70), nullable = False)

class Athlete(db.Model):#add password
    athlete_id = db.Column(db.Integer, primary_key = True)
    forename = db.Column(db.String(50),nullable = False )
    surname = db.Column(db.String(50), nullable = True)
    dob = db.Column(db.DateTime, nullable = False)
    school_URN = db.Column(db.Integer, nullable = True)
    start_date = db.Column(db.DateTime, nullable = False, default=datetime.utcnow)
    email = db.Column(db.String(70), nullable = False)



class Fees(db.Model):
    fee_id = db.Column(db.Integer, primary_key= True)
    admin_id = db.Column(db.Integer, foreign_key = True)
    athlete_id = db.Column(db.Integer, foreign_key = True)
    amount = db.Column(db.Real, nullable = False)
    paid_date = db.Column(db.DateTime, nullable = False, default= 'N/A')

class Team(db.Model):
    team_id = db.Column(db.Integer, primary_key= True)
    team_name= db.Column(db.String(20), nullable= False)
    max_age = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Team' +str(self.team_id)







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

@app.route('/posts')
def posts():
    return render_template('posts.html', posts=all_posts)

if __name__ == "__main__":
    app.run(debug=True)