# dont worry abt this doc for now. Im trying to rememeber how to do this sad face
# eventually ill figure it out hopefully

import os
from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "h5djHHUDE9iKIHjuhyuf7"
appdir = os.path.abspath(os.path.dirname(__file__))
# configure app’s database access
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(appdir, 'library.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the SQLAlchemy database adaptor
db = SQLAlchemy(app)

class User(db.Model):
	__tablename__="Users"
	user_id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
	user_username = db.Column(db.Unicode(64), nullable = False)
	user_firstname = db.Column(db.Unicode(64), nullable = False)
    # user_lastname = db.Column(db.Unicode(64), nullable = False)
    # user_hashedpass = db.Column(db.Unicode(64), nullable = False)

class Spot(db.Model):
    __tablename__="Spots"
    spot_id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    spot_name = db.Column(db.Unicode(64), nullable = False)
    spot_location = db.Column(db.Unicode(64), nullable = False)
    spot_noiselevel = db.Column(db.Integer(), nullable = False)
    spot_food = db.Column(db.Integer(), nullable = False)
    spot_computers = db.Column(db.Integer(), nullable = False)

# drop any existing tables in the database
db.drop_all()

# create all the tables necessary according to my db.Model subclasses
db.create_all()


@app.route("/")
def homepage():
    return "this is the homepage", 200
    #   return render_template("homepage.html"), 200

# @login_required
@app.route("/selection")
def selectionpage():
    return render_template("Booking Page.html"), 200


# [[ Create and Add Example Data ]]
user1 = User(user_username="userperson", user_firstname="Henry")
spot1 = Spot(spot_name="spot1", spot_location="gleason", spot_noiselevel=0, spot_food=0, spot_computers=0)

# add all of these items to the database session
db.session.add_all([user1])
db.session.add_all([spot1])

# commit these changes to the database
db.session.commit()