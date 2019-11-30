import os
from flask import Flask, flash, render_template, redirect, url_for, request, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from flask_httpauth import HTTPBasicAuth
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
    bookings = db.relationship("Booking", backref="User")


class Spot(db.Model):
    __tablename__ = "Spots"
    spot_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    spot_name = db.Column(db.Unicode(64), nullable=False)
    spot_noiselevel = db.Column(db.Integer(), nullable=False)
    spot_food = db.Column(db.Boolean(), nullable=False)
    spot_computers = db.Column(db.Boolean(), nullable=False)
    spot_booking = db.relationship("Booking", backref="Spot")


class SpotSchema(Schema):
    class Meta:
        fields = ('spot_name', 'spot_id')

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
    if request.method == 'POST' and not form.validate_on_submit():
        flash('Unsuccessful registration')

    return render_template('SignUpPage.html', form=form)


@app.route('/book')
# @login_required --> need to put it back in
def dashboard():
    spots = Spot.query.all()
    return render_template('BookingPage.html', spots=spots)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/explore-libraries')
def explore():
    return render_template('ExploreLibraries.html')


@app.route('/selection', methods=['POST'])
# @login_required  # double-check if it breaks something
def selection():
    print("The request is sent: " + request.form.get("stime"))
    date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")# dictionary
    stime = datetime.strptime(request.form.get("stime"), "%H:%M").time()
    etime = datetime.strptime(request.form.get("etime"), "%H:%M").time()
    foodchoice = request.form.get("food") == "true"
    print("Foodchoice:")
    print(foodchoice)
    compchoice = request.form.get("comp") == "true"
    print("Computer choice:")
    print(compchoice)

    # first get all spots that have the specified characteristsics --> Check if set syntax is good

    prefSpots = list(db.session.query(Spot).filter(Spot.spot_food==foodchoice, Spot.spot_computers==compchoice))

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
    #currBooking = Booking.query.filter(Booking.booking_spot.in_(integers)).all()
    currBooking = db.session.query(Booking).filter(Booking.booking_spot.in_(integers)).all()
    print("Current Bookings are: ")
    print(currBooking)

    # goes thru all those bookings and checks if the requested time is between an already existing reservation
    for bk in currBooking:
        if (bk.booking_startdatetime <= startdt and startdt <= bk.booking_enddatetime) or (endt >= bk.booking_startdatetime and endt <= bk.booking_enddatetime):
            prefSpots.remove(Spot.query.filter_by(spot_id=bk.booking_spot).first())
            print("I get activated :) ")

    # initializes the list of spots
    spot_schema = SpotSchema()
    serialized_names = list()

    for spots in prefSpots:
        serialized = spots.spot_name
        serialized_names.append(spots)



    # adds each availible spot into the list
    # for sp in prefSpots:
    #    splist.spots.append(sp)

    # print(splist)
    # serializes the list
    # result = SpotListSchema().dump(splist)
    #
    # print(result)

    # return the list of avilible spots in terms of JSON
    return jsonify({
        'availablespots': serialized_names
    }), 200


# [[ Create and Add Example Data ]]
user1 = User(username="userperson", email="person@example.com",
             password="sha256$vhSHEyRj$21e523d553832ce4f3a4639164cb190e0866bff73380870995f67f32e888da49")
spot1 = Spot(spot_name="Gleason", spot_noiselevel=2, spot_food=True, spot_computers=True)
spot2 = Spot(spot_name="Rettner", spot_noiselevel=1, spot_food=False, spot_computers=True)
spot3 = Spot(spot_name="iZone", spot_noiselevel=2, spot_food=True, spot_computers=False)
spot4 = Spot(spot_name="Well Browns", spot_noiselevel=0, spot_food=False, spot_computers=False)

# dt format: datetime.strptime("08/30/1797 6:30 AM", '%m/%d/%Y %I:%M %p')
booking1 = Booking(booking_startdatetime=datetime.strptime("2019-11-30_06:30 AM", "%Y-%m-%d_%I:%M %p"),
                   booking_enddatetime=datetime.strptime("2019-11-30_08:30 AM", "%Y-%m-%d_%I:%M %p"),
                   booking_user=1, booking_spot=1)
booking2 = Booking(booking_startdatetime=datetime.strptime("2019-11-30_06:30 AM", "%Y-%m-%d_%I:%M %p"),
                   booking_enddatetime=datetime.strptime("2019-11-30_08:30 AM", "%Y-%m-%d_%I:%M %p"),
                   booking_user=1, booking_spot=2)

# add all of these items to the database session
db.session.add_all([user1])
db.session.add_all([spot1, spot2, spot3, spot4])
db.session.add_all([booking1, booking2])

# commit database changes
db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)

    # user: eyang13
    # Password: Password
