import os
import time
from flask import Flask, flash, render_template, redirect, url_for, request, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

# web stuff
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisstotallysecretyall!'
Bootstrap(app)

# database stuff
appdir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = \
    f"sqlite:///{os.path.join(appdir, 'library.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    __tablename__="Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(15), unique=True, nullable = False)
    email = db.Column(db.String(50), unique=True, nullable = False)
    password = db.Column(db.String(80), nullable = False)
    bookings = db.relationship("Booking", backref = "User")

class Spot(db.Model):
    __tablename__="Spots"
    spot_id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    spot_name = db.Column(db.Unicode(64), nullable = False)
    spot_location = db.Column(db.Unicode(64), nullable = False)
    spot_noiselevel = db.Column(db.Integer(), nullable = False)
    spot_food = db.Column(db.Integer(), nullable = False)
    spot_computers = db.Column(db.Integer(), nullable = False)
    spot_booking = db.relationship("Booking", backref = "Spot")

class Booking(db.Model):
    __tablename__="Bookings"
    booking_id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    #the datetime will be in format of: datetime.date(datetime.strptime("08/30/1797 16:30", '%m/%d/%Y %H:%M'))
    booking_datetime = db.Column(db.DateTime(), nullable = False)
    booking_user = db.Column(db.Integer(), db.ForeignKey("Users.id"))
    booking_spot = db.Column(db.Integer(), db.ForeignKey("Spots.spot_id"))

db.drop_all()
db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember Me')


class SignUpForm(FlaskForm):
    email = StringField('Email Address', validators=[InputRequired(message='You must have an email'), Email(message='Invalid email'), Length(max=50, message='too long')])
    def validate_email(form,self):
        if User.query.filter_by(email = self.data).first() != None:
            self.errors.append('an account has already been associated with this email')
            return False

        return True

    emailConfirm = StringField('Confirm Email', validators=[InputRequired(message='This field cannot be empty'), Email(message='Invalid email'), EqualTo('email', message='emails need to match')])

    username = StringField('Username', validators=[InputRequired(message='You must have a username'), Length(min=4, max=15, message='Invalid username')])
    def validate_username(form,self):
        if User.query.filter_by(username = self.data).first() != None:
            self.errors.append('username already exists')
            return False

        return True

    password = PasswordField('Password', validators=[InputRequired(message='This field cannot be empty'), Length(min=8, max=80,message='Invalid password')])
    passwordConfirm = PasswordField('Confirm Password', validators=[InputRequired(message='This field cannot be empty'), Length(min=8,max=80, message ='Invalid password'), EqualTo('password', message='passwords need to match')])

# class BookingForm(FlaskForm):
#     date = DateField()
#     starttime = TimeField

@app.route('/')
def home():
    return render_template('HomePage.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        flash('Incorrect password or username')
        return redirect(url_for('login'))

    return render_template('SignInPage.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('New user has been created. You can log in now')
        return redirect(url_for('login'))
        # return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('SignUpPage.html', form=form)


@app.route('/book')
@login_required
def dashboard():
    # date = request.form['date']
    # print(date)

    # localtime = time.localtime(time.time())
    spots = Spot.query.all()
    return render_template('BookingPage.html',spots=spots)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/explore-libraries')
def explore():
    return render_template('ExploreLibraries.html')

# [[ Create and Add Example Data ]]
user1 = User(username="userperson", email="person@example.com", password="sha256$vhSHEyRj$21e523d553832ce4f3a4639164cb190e0866bff73380870995f67f32e888da49")
spot1 = Spot(spot_name="spot1", spot_location="gleason", spot_noiselevel=0, spot_food=0, spot_computers=0)
spot2 = Spot(spot_name="spot2", spot_location="Q&i", spot_noiselevel=1, spot_food=1, spot_computers=1)
spot3 = Spot(spot_name="spot3", spot_location="iZone", spot_noiselevel=5, spot_food=1, spot_computers=0)
spot4 = Spot(spot_name="spot4", spot_location="RR", spot_noiselevel=0, spot_food=0, spot_computers=0)

booking1 = Booking(booking_datetime= datetime.date(datetime.strptime("1797-12-30_06:30", "%Y-%m-%d_%H:%M")), booking_user=1, booking_spot=1)

# add all of these items to the database session
db.session.add_all([user1])
db.session.add_all([spot1, spot2, spot3, spot4])
db.session.add_all([booking1])

#commit database changes
db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)

    # user: eyang13
    # Password: Password
