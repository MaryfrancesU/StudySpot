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
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

# web stuff
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisstotallysecretyall!'
Bootstrap(app)

# database stuff
appdir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = \
    'sqlite:///'+ os.path.join(appdir, 'library.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

#config values for the mail   
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME='urstudyspot@gmail.com',
    MAIL_PASSWORD='study1/spot'
    )

mail = Mail(app)

#serializer for the confirmation email token 
serial = URLSafeTimedSerializer(app.config['SECRET_KEY'])

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
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
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
    email = StringField('Email Address', validators=[InputRequired(message='You must have an email!'), Email(message='Invalid email! Accepted format: example@example.com'), Length(max=50, message='too long')])
    def validate_email(form,self):
        if User.query.filter_by(email = self.data).first() != None:
            self.errors.append('An account has already been associated with this email!')
            return False

        return True

    emailConfirm = StringField('Confirm Email', validators=[InputRequired(message='This field cannot be empty!'), EqualTo('email', message='Emails need to match!')])

    username = StringField('Username', validators=[InputRequired(message='You must have a username!'), Length(min=4, max=15, message='Invalid username! Min no of characters:4. Max no of characters:15')])
    def validate_username(form,self):
        if User.query.filter_by(username = self.data).first() != None:
            self.errors.append('username already exists')
            return False

        return True

    password = PasswordField('Password', validators=[InputRequired(message='This field cannot be empty!'), Length(min=8, max=25,message='Invalid password! Min no of characters:8. Max no of characters:25')])
    passwordConfirm = PasswordField('Confirm Password', validators=[InputRequired(message='This field cannot be empty!'), EqualTo('password', message='Passwords need to match')])


class ResendConfirmationForm(FlaskForm):
    email = StringField('Email',validators=[InputRequired(),Email()])
    def validate_email(form,self):
        if User.query.filter_by(email = self.data).first() == None:
            self.errors.append('Your email is not registered')
            return False

        return True




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
            if check_password_hash(user.password, form.password.data) and user.confirmed == True:
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
            if user.confirmed == False:
                flash('Your email has not been confirmed!')
                return redirect(url_for('resendconfirmation'))

        flash('Incorrect password or username')
        return redirect(url_for('login'))

    return render_template('SignInPage.html', form=form)


#function that creates and sends the email
def sendEmail(email,username):
    tokenval = serial.dumps(email)
    message= Message('EMAIL CONFIRMATION - STUDY SPOT', sender='urstudyspot@gmail.com', recipients=[email])
    confirm_link = url_for('email_confirmation', token = tokenval, _external=True)
    message.body = "Hi {}! Welcome to study spot.Please click the link to confirm your e-mail to have login access. Your link is {}".format(username,confirm_link)
    mail.send(message)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        email = form.email.data;
        username = form.username.data;
        new_user = User(username=username, email=email, password=hashed_password)
        sendEmail(email,username)
        db.session.add(new_user)
        db.session.commit()
        flash('New user has been created')
        flash('Before you login, please check your inbox and confirm your email through the confirmation link')
        return redirect(url_for('login'))
        # return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
    if request.method == 'POST' and not form.validate_on_submit():
    	flash('Unsuccessful registration')
    	
    return render_template('SignUpPage.html', form=form)

#email confirmation route
@app.route('/email_confrmation/<token>')
def email_confirmation(token):
    try:
        email = serial.loads(token, max_age=3600)
    except SignatureExpired:
        flash('Token is expired')
        redirect(url_for('login'))
    flash('Your email has been succesfully confirmed')
    user = User.query.filter_by(email=email).first_or_404()
    user.confirmed = True
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login'))

#email confirmation resent link route
@app.route('/resend-confirmation', methods=['GET','POST'])
def resendconfirmation():
    form = ResendConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        email = user.email
        username = user.username
        sendEmail(email,username)
        flash('Email confirmation link is resent. Please check your inbox.')
        return redirect(url_for('login'))

    if request.method == 'POST' and not form.validate_on_submit():
        flash('Email confirmation link is not sent. Try again')

    return render_template('resend-confirmation.html',form=form)


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
