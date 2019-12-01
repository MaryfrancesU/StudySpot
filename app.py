import os
from flask import Flask, flash, render_template, redirect, url_for, request, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from marshmallow import Schema, fields
from marshmallow_sqlalchemy import ModelSchema

# web stuff
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisstotallysecretyall!'
Bootstrap(app)
auth = HTTPBasicAuth()

# database stuff
appdir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = \
    f"sqlite:///{os.path.join(appdir, 'library.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# config values for the mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME='urstudyspot@gmail.com',
    MAIL_PASSWORD='study1/spot'
)
mail = Mail(app)

# serializer for the confirmation email token
serial = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    bookings = db.relationship("Booking", backref="User")


class Spot(db.Model):
    __tablename__ = "Spots"
    spot_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    spot_name = db.Column(db.Unicode(64), nullable=False)
    spot_noiselevel = db.Column(db.Integer(), nullable=False)
    spot_food = db.Column(db.Boolean(), nullable=False)
    spot_computers = db.Column(db.Boolean(), nullable=False)
    spot_booking = db.relationship("Booking", backref="Spot")


class Booking(db.Model):
    __tablename__ = "Bookings"
    booking_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    # the datetime will be in format of: datetime.strptime("08/30/1797 6:30 AM", '%m/%d/%Y %I:%M %p')
    booking_startdatetime = db.Column(db.DateTime(), nullable=False)
    booking_enddatetime = db.Column(db.DateTime(), nullable=False)
    booking_user = db.Column(db.Integer(), db.ForeignKey("Users.id"))
    booking_spot = db.Column(db.Integer(), db.ForeignKey("Spots.spot_id"))


db.drop_all()
db.create_all()


class ViewBK():
    def __init__(self, spot_name, starttime, endtime):
        self.spot_name = spot_name
        self.starttime = starttime
        self.endtime = endtime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember Me')


class SignUpForm(FlaskForm):
    email = StringField('Email Address', validators=[InputRequired(message='You must have an email!'), Email(
        message='Invalid email! Accepted format: example@example.com'), Length(max=50, message='too long')])

    def validate_email(form, self):
        if User.query.filter_by(email=self.data).first() != None:
            self.errors.append('An account has already been associated with this email!')
            return False

        return True

    emailConfirm = StringField('Confirm Email', validators=[InputRequired(message='This field cannot be empty!'),
                                                            EqualTo('email', message='Emails need to match!')])

    username = StringField('Username', validators=[InputRequired(message='You must have a username!'),
                                                   Length(min=4, max=15,
                                                          message='Invalid username! Min no of characters:4. Max no of characters:15')])

    def validate_username(form, self):
        if User.query.filter_by(username=self.data).first() != None:
            self.errors.append('username already exists')
            return False

        return True

    password = PasswordField('Password', validators=[InputRequired(message='This field cannot be empty!'),
                                                     Length(min=8, max=25,
                                                            message='Invalid password! Min no of characters:8. Max no of characters:25')])
    passwordConfirm = PasswordField('Confirm Password',
                                    validators=[InputRequired(message='This field cannot be empty!'),
                                                EqualTo('password', message='Passwords need to match')])


class ResendConfirmationForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

    def validate_email(form, self):
        if User.query.filter_by(email=self.data).first() == None:
            self.errors.append('Your email is not registered')
            return False

        return True


class EditProfileForm(FlaskForm):
    cpassword = PasswordField('Current Password', validators=[InputRequired(message='This field cannot be empty!')])
    password = PasswordField('New Password')
    email = StringField('New Email')


class ForgotMyPassword(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

    def validate_email(form, self):
        if User.query.filter_by(email=self.data).first() == None:
            self.errors.append('Your email is not registered')
            return False

        return True


class EditPassword(FlaskForm):
    password = PasswordField('New Password', validators=[InputRequired(message='This field cannot be empty!')])
    passwordConfirm = PasswordField('Confirm Password',
                                    validators=[InputRequired(message='This field cannot be empty!'),
                                                EqualTo('password', message='Passwords need to match')])


@app.route('/')
def home():
    return render_template('HomePage.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data) and user.confirmed == True:
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
            if user.confirmed == False:
                flash('Your email has not been confirmed!')
                return redirect(url_for('resendconfirmation'))

        flash('Incorrect password or username')
        return redirect(url_for('login'))

    return render_template('SignInPage.html', form=form)


# function that creates and sends the account confirmation email
def sendEmail(email, username):
    tokenval = serial.dumps(email)
    message = Message('EMAIL CONFIRMATION - STUDY SPOT', sender='urstudyspot@gmail.com', recipients=[email])
    confirm_link = url_for('email_confirmation', token=tokenval, _external=True)
    message.body = "Hi {}! Welcome to Study Spot. Please click the link to confirm your e-mail to have login access. Your link is {}".format(
        username, confirm_link)
    mail.send(message)


# function that creates and sends the confirmation email
def sendPasswordEmail(email, username):
    tokenval = serial.dumps(email)
    message = Message('CHANGE YOUR PASSWORD - STUDY SPOT', sender='urstudyspot@gmail.com', recipients=[email])
    confirm_link = url_for('passwordchange', token=tokenval, _external=True)
    message.body = "Hi {}! Welcome to study spot.Please click the link to change your password. Your link is {}".format(
        username, confirm_link)
    mail.send(message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        email = form.email.data
        username = form.username.data
        new_user = User(username=username, email=email, password=hashed_password)
        sendEmail(email, username)
        db.session.add(new_user)
        db.session.commit()
        flash('New user has been created')
        flash('Before you login, please check your inbox and confirm your email through the confirmation link')
        return redirect(url_for('login'))
    if request.method == 'POST' and not form.validate_on_submit():
        flash('Unsuccessful registration')

    return render_template('SignUpPage.html', form=form)


@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    form = ForgotMyPassword()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
        except:
            flash('Unregistered email adress!')
            return redirect(url_for('forgotpassword'))
        email = user.email
        username = user.username
        sendPasswordEmail(email, username)
        flash('Password change link is sent.Please check your inbox.')
        return redirect(url_for('login'))

    if request.method == 'POST' and not form.validate_on_submit():
        flash('Password change link is not sent. Try again')

    return render_template('ForgotMyPassword.html', form=form)


# password change route
@app.route('/passwordchange/<token>', methods=['GET', 'POST'])
def passwordchange(token):
    try:
        email = serial.loads(token, max_age=60)
    except SignatureExpired:
        flash('Link is expired')
        return redirect(url_for('login'))

    form = EditPassword()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            flash('Broken link or email is unregistered')
            flash('Try again')
            return redirect(url_for('login'))
        user.password = generate_password_hash(form.password.data, method='sha256')
        db.session.add(user)
        db.session.commit()
        flash('Your password has been succesfully updated')
        return redirect(url_for('login'))

    return render_template('EditPassword.html', form=form, token=token)


# email confirmation route
@app.route('/email_confirmation/<token>')
def email_confirmation(token):
    try:
        email = serial.loads(token, max_age=60)
        flash('Your email has been successfully confirmed')
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            flash('Invalid email')
            return redirect(url_for('resendconfirmation'))
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
    except SignatureExpired:
        flash('Link is expired')
        return redirect(url_for('resendconfirmation'))

    return redirect(url_for('login'))


# email confirmation resent link route
@app.route('/resend-confirmation', methods=['GET', 'POST'])
def resendconfirmation():
    form = ResendConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        email = user.email
        username = user.username
        sendEmail(email, username)
        flash('Email confirmation link is resent. Please check your inbox.')
        return redirect(url_for('login'))

    if request.method == 'POST' and not form.validate_on_submit():
        flash('Email confirmation link is not sent. Try again')

    return render_template('resend-confirmation.html', form=form)


@app.route('/book')
@login_required
def dashboard():
    return render_template('BookingPage.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/explore-libraries')
def explore():
    return render_template('ExploreLibraries.html')


@app.route('/view-bookings')
@login_required
def bookings():
    user = current_user
    bookings = db.session.query(Booking).filter(Booking.booking_user == user.id)
    info_list = list()
    for names in bookings:
        sp = db.session.query(Spot).filter(Spot.spot_id == names.booking_spot).first_or_404()
        info = ViewBK(sp.spot_name, names.booking_startdatetime, names.booking_enddatetime)
        info_list.append(info)
    # send = db.session.query(Spot).filter(Spot.spot_id.in_(spot_names)).all()

    return render_template('ViewBookings.html', user=user, info_list=info_list)


@app.route('/view-profile')
@login_required
def viewProfile():
    user = current_user
    return render_template('UserProfile.html', user=user)


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def editProfile():
    form = EditProfileForm()
    user = current_user

    if form.validate_on_submit():
        if user:
            if check_password_hash(user.password, form.cpassword.data):

                # update user
                newem = form.email.data
                newpa = form.password.data
                if newem != '':
                    emailEditEmail(user.email, user.username, newem)
                    user.email = newem
                    user.confirmed = False
                    sendEmail(user.email, user.username)
                    db.session.add(user)
                    db.session.commit()
                    flash('your email has been updated!')
                    flash('Before you login, please check your inbox and confirm your email through the confirmation link')
                    return redirect(url_for('login'))
                if newpa != '':
                    passwordEditEmail(user.email,user.username)
                    hashed_password = generate_password_hash(form.password.data, method='sha256')
                    user.password = hashed_password

                db.session.commit()

                # go back to view profile
                return redirect(url_for('viewProfile'))

    if request.method == 'POST' and not check_password_hash(user.password, form.cpassword.data):
        flash('Incorrect password. Please enter your current password to continue.')
        return redirect(url_for('editProfile'))

    return render_template('EditProfile.html', user=user, form=form)


# send email change alert to old email
def emailEditEmail(email, username, newemail):
    message = Message('PROFILE CHANGE CONFIRMATION - STUDY SPOT', sender='urstudyspot@gmail.com', recipients=[email])
    message.body = "Hi " + username + " from StudySpot! " \
                                      "We're just sending this email to let you know that your StudySpot email " \
                                      "has been changed to " + newemail + "!"
    mail.send(message)


# send password change alert to old email
def passwordEditEmail(email, username):
    message = Message('PROFILE CHANGE CONFIRMATION - STUDY SPOT', sender='urstudyspot@gmail.com', recipients=[email])
    message.body = "Hi " + username + " from StudySpot! " \
                                      "We're just sending this email to let you know that your StudySpot password " \
                                      "has been updated!"
    mail.send(message)


@app.route('/selection', methods=['POST'])
# @login_required  # double-check if it breaks something
def selection():
    print("The request is sent: " + request.form.get("stime"))
    date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")  # dictionary
    stime = datetime.strptime(request.form.get("stime"), "%H:%M").time()
    etime = datetime.strptime(request.form.get("etime"), "%H:%M").time()
    foodchoice = request.form.get("food") == "true"
    compchoice = request.form.get("comp") == "true"
    silencechoice = request.form.get("quiet") == "true"
    whisperchoice = request.form.get("whisper") == "true"

    # getting the noise level desired
    if silencechoice and not whisperchoice:
        noiselevel = 0
    elif not silencechoice and whisperchoice:
        noiselevel = 1
    else:
        noiselevel = 2

    # first get all spots that have the specified characteristsics --> Check if set syntax is good
    if foodchoice and compchoice:
        prefSpots = list(db.session.query(Spot).filter(Spot.spot_food == foodchoice, Spot.spot_computers == compchoice,
                                                       Spot.spot_noiselevel <= noiselevel))
    elif not foodchoice and not compchoice:
        prefSpots = list(db.session.query(Spot).filter(Spot.spot_noiselevel <= noiselevel))
    elif foodchoice:
        prefSpots = list(
            db.session.query(Spot).filter(Spot.spot_food == foodchoice, Spot.spot_noiselevel <= noiselevel))
    elif compchoice:
        prefSpots = list(
            db.session.query(Spot).filter(Spot.spot_computers == compchoice, Spot.spot_noiselevel <= noiselevel))

    print("Preferred Spots: ")
    print(prefSpots)

    # check each booking in the table and see if each spot in the list already
    # has a reservation at the specificed time and remove from list
    startdt = datetime.combine(date, stime)
    endt = datetime.combine(date, etime)

    # make a list associating the integers with the spots
    integers = list()
    for sp in prefSpots:
        integers.append(sp.spot_id)

    # gets all bookings whose spot is in the list
    # currBooking = Booking.query.filter(Booking.booking_spot.in_(integers)).all()
    currBooking = db.session.query(Booking).filter(Booking.booking_spot.in_(integers)).all()
    print("Current Bookings are: ")
    print(currBooking)

    # goes thru all those bookings and checks if the requested time is between an already existing reservation
    for bk in currBooking:
        if (bk.booking_startdatetime <= startdt and startdt <= bk.booking_enddatetime) or (
                endt >= bk.booking_startdatetime and endt <= bk.booking_enddatetime):
            prefSpots.remove(Spot.query.filter_by(spot_id=bk.booking_spot).first())
            print("I get activated :) ")

    # initializes the list of spots
    serialized_names = list()

    for spots in prefSpots:
        serialized = spots.spot_name
        serialized_names.append(serialized)

    # return the list of available spots in terms of JSON
    return jsonify({
        'availablespots': serialized_names
    }), 200


@app.route('/actualbooking', methods=['POST'])
@login_required  # double-check if it breaks something
def actualbooking():
    spname = request.form.get("spotname").strip()
    print("The name is " + spname)
    spot = db.session.query(Spot).filter(Spot.spot_name == spname).first_or_404()
    spotid = spot.spot_id
    user = current_user
    userid = user.id

    date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")  # dictionary
    stime = datetime.strptime(request.form.get("stime"), "%H:%M").time()
    etime = datetime.strptime(request.form.get("etime"), "%H:%M").time()
    startdt = datetime.combine(date, stime)
    endt = datetime.combine(date, etime)

    booking = Booking(booking_startdatetime=startdt, booking_enddatetime=endt, booking_user=userid, booking_spot=spotid)
    db.session.add(booking)

    # commit database changes
    db.session.commit()

    return {
               "first": "hi"
           }, 200


# [[ Create and Add Example Data ]]
user1 = User(username="userperson", email="person@example.com",
             password="sha256$vhSHEyRj$21e523d553832ce4f3a4639164cb190e0866bff73380870995f67f32e888da49")


# Art&Music Library
spot1 = Spot(spot_name="Art&Music Library Viewing Room A", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot2 = Spot(spot_name="Art&Music Library Viewing Room B", spot_noiselevel=1, spot_food=True, spot_computers=True)

spot3 = Spot(spot_name="Art&Music Library Carrel Desk 1", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot4 = Spot(spot_name="Art&Music Library Carrel Desk 2", spot_noiselevel=1, spot_food=True, spot_computers=True)

spot5 = Spot(spot_name="Art&Music Library Booth 1", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot6 = Spot(spot_name="Art&Music Library Booth 2", spot_noiselevel=1, spot_food=True, spot_computers=True)

# Carlson Floor 1
spot7 = Spot(spot_name="Carlson Floor 1 Table 1", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot8 = Spot(spot_name="Carlson Floor 1 Table 2", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot9 = Spot(spot_name="Carlson Floor 1 Table 3", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot10 = Spot(spot_name="Carlson Floor 1 Table 4", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot11 = Spot(spot_name="Carlson Floor 1 Table 5", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot12 = Spot(spot_name="Carlson Floor 1 Zone A", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot13 = Spot(spot_name="Carlson Floor 1 Zone B", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot14 = Spot(spot_name="Carlson Floor 1 Zone C", spot_noiselevel=1, spot_food=True, spot_computers=True)

# Carlson Floor 2
spot15 = Spot(spot_name="Carlson Floor 2 Table 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot16 = Spot(spot_name="Carlson Floor 2 Table 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot17 = Spot(spot_name="Carlson Floor 2 Table 3", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot18 = Spot(spot_name="Carlson Floor 2 Table 4", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot19 = Spot(spot_name="Carlson Floor 2 Table 5", spot_noiselevel=2, spot_food=True, spot_computers=True)

# Carlson Floor 3
spot20 = Spot(spot_name="Carlson Floor 3 Table 1", spot_noiselevel=0, spot_food=True, spot_computers=True)
spot21 = Spot(spot_name="Carlson Floor 3 Table 2", spot_noiselevel=0, spot_food=True, spot_computers=True)
spot22 = Spot(spot_name="Carlson Floor 3 Table 3", spot_noiselevel=0, spot_food=True, spot_computers=True)
spot23 = Spot(spot_name="Carlson Floor 3 Table 4", spot_noiselevel=0, spot_food=True, spot_computers=True)
spot24 = Spot(spot_name="Carlson Floor 3 Table 5", spot_noiselevel=0, spot_food=True, spot_computers=True)

# Douglass
spot25 = Spot(spot_name="Douglass Room 301", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot26 = Spot(spot_name="Douglass Room 302", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot27 = Spot(spot_name="Douglass Room 401", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot28 = Spot(spot_name="Douglass Room 402", spot_noiselevel=2, spot_food=True, spot_computers=False)

# Gleason
spot29 = Spot(spot_name="Gleason Table 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot30 = Spot(spot_name="Gleason Table 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot31 = Spot(spot_name="Gleason Table 3", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot32 = Spot(spot_name="Gleason Booth 1", spot_noiselevel=2, spot_food=True, spot_computers=True)

# iZone
spot33 = Spot(spot_name="iZone Table 1", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot34 = Spot(spot_name="iZone Table 2", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot35 = Spot(spot_name="iZone Table 3", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot36 = Spot(spot_name="iZone Booth 1", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot37 = Spot(spot_name="iZone Booth 2", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot38 = Spot(spot_name="iZone Booth 3", spot_noiselevel=2, spot_food=True, spot_computers=False)

# PRR
spot39 = Spot(spot_name="PRR", spot_noiselevel=0, spot_food=True, spot_computers=False)

# Q&i
spot40 = Spot(spot_name="Q&i Table 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot41 = Spot(spot_name="Q&i Table 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot42 = Spot(spot_name="Q&i Table 3", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot43 = Spot(spot_name="Q&i Booth 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot44 = Spot(spot_name="Q&i Booth 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot45 = Spot(spot_name="Q&i Booth 3", spot_noiselevel=2, spot_food=True, spot_computers=True)

# Rettner
spot46 = Spot(spot_name="Rettner Table 1", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot47 = Spot(spot_name="Rettner Table 2", spot_noiselevel=1, spot_food=True, spot_computers=True)
spot48 = Spot(spot_name="Rettner Table 3", spot_noiselevel=1, spot_food=True, spot_computers=True)

# Stacks
spot49 = Spot(spot_name="Stacks Floor 5 Table 1", spot_noiselevel=0, spot_food=True, spot_computers=False)
spot50 = Spot(spot_name="Stacks Floor 5 Table 2", spot_noiselevel=0, spot_food=True, spot_computers=False)
spot51 = Spot(spot_name="Stacks Floor 5 Table 3", spot_noiselevel=0, spot_food=True, spot_computers=False)
spot52 = Spot(spot_name="Stacks Floor 6 Table 1", spot_noiselevel=0, spot_food=True, spot_computers=False)
spot53 = Spot(spot_name="Stacks Floor 6 Table 2", spot_noiselevel=0, spot_food=True, spot_computers=False)
spot54 = Spot(spot_name="Stacks Floor 6 Table 3", spot_noiselevel=0, spot_food=True, spot_computers=False)

# Wegmans
spot55 = Spot(spot_name="Wegmans Floor 2 Table 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot56 = Spot(spot_name="Wegmans Floor 2 Table 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot57 = Spot(spot_name="Wegmans Floor 2 Table 3", spot_noiselevel=2, spot_food=True, spot_computers=True)

spot58 = Spot(spot_name="Wegmans Floor 3 Table 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot59 = Spot(spot_name="Wegmans Floor 3 Table 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot60 = Spot(spot_name="Wegmans Floor 3 Table 3", spot_noiselevel=2, spot_food=True, spot_computers=True)

spot61 = Spot(spot_name="Wegmans Floor 4 Table 1", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot62 = Spot(spot_name="Wegmans Floor 4 Table 2", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot63 = Spot(spot_name="Wegmans Floor 4 Table 3", spot_noiselevel=2, spot_food=True, spot_computers=True)

# Welles Brown
spot64 = Spot(spot_name="Welles Brown", spot_noiselevel=1, spot_food=True, spot_computers=False)


# dt format: datetime.strptime("08/30/1797 6:30 AM", '%m/%d/%Y %I:%M %p')
booking1 = Booking(booking_startdatetime = datetime.strptime("2019-11-30_06:30 AM", "%Y-%m-%d_%I:%M %p"),
                    booking_enddatetime =datetime.strptime("2019-11-30_08:30 AM", "%Y-%m-%d_%I:%M %p"),
                    booking_user=1, booking_spot=1)
booking2 = Booking(booking_startdatetime=datetime.strptime("2019-11-30_06:30 AM", "%Y-%m-%d_%I:%M %p"),
                    booking_enddatetime=datetime.strptime("2019-11-30_08:30 AM", "%Y-%m-%d_%I:%M %p"),
                    booking_user=1, booking_spot=2)


# add all of these items to the database session
db.session.add_all([user1])
db.session.add_all([spot1, spot2, spot3, spot4, spot5, spot6, spot7, spot8, spot9, spot10, spot11, spot12, spot13, spot14, spot15, spot16,
                    spot17, spot18, spot19, spot20, spot21, spot22, spot23, spot24, spot25, spot26, spot27, spot28, spot29, spot30, spot31,
                    spot32, spot33, spot34, spot35, spot36, spot37, spot38, spot39, spot40, spot41, spot42, spot43, spot44, spot45, spot46,
                    spot47, spot48, spot49, spot50, spot51, spot51, spot52, spot53, spot54, spot55, spot56, spot57, spot58, spot59, spot60,
                    spot61, spot62, spot63, spot64])
db.session.add_all([booking1, booking2])

# commit database changes
db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
