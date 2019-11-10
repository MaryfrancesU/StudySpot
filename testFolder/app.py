import os
from flask import Flask, flash, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

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

# login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))


db.drop_all()
db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(message='Please enter your username'), Length(min=4, max=15, message='Invalid username')])
    password = PasswordField('Password', validators=[InputRequired(message='Please enter your password'), Length(min=8, max=80, message='Invalid password')])
    remember = BooleanField('Remember Me')


class SignUpForm(FlaskForm):
    email = StringField('Email Address', validators=[InputRequired(message='You must have an email'), Email(message='Invalid email'), Length(max=50)])
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
    return render_template('BookingPage.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
