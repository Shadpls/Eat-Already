from os import getenv
from dotenv import load_dotenv, find_dotenv
from flask import Flask, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
import json
import random
import requests
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    logout_user,
    current_user,
)
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length, ValidationError, NumberRange
from wtforms.widgets import TextArea
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt

load_dotenv(find_dotenv())

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SECRET_KEY"] = getenv("COOKIE_KEY")
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Person.query.get(int(user_id))


class Person(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.LargeBinary(60), nullable=False)


with app.app_context():
    db.create_all()


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = Person.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                "That username exists. Please select another username."
            )


class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Login")

    def validate_username(self, username):
        existing_user_username = Person.query.filter_by(username=username.data).first()
        if not existing_user_username:
            raise ValidationError("That username does not exist. Please try again.")

class EatWhatForm(FlaskForm):
    user_local = StringField(
        validators=[InputRequired(), Length(min=2, max=30)],
        render_kw={"placeholder": "Enter your location (city, zip-code)"},
    )
    category = StringField(
        validators=[InputRequired(), Length(min=3, max=40)],
        render_kw={"placeholder": "Enter a category (e.g. Italian, Chinese, etc)"},
    )
    submit = SubmitField("Decide for me")
        
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Person.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("movie"))
    user = Person.query.filter_by(username=form.username.data).first()

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = Person(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    user = Person.query.filter_by(username=form.username.data).first()
    if user:
        flash("This username is taken. Try again")

    return render_template("signup.html", form=form)

@app.route("/main", methods=["GET", "POST"])
@login_required
def main():
    form = EatWhatForm()
    if form.validate_on_submit():
        user_local = form.user_local.data
        category = form.category.data
        decide_4me(user_local, category)
    return render_template("main.html", form=form)

def decide_4me(user_local, category):
    
    BASE_YELP_URL = "https://api.yelp.com/v3/businesses/search"
    HEADERS = {'Authorization': 'Bearer %s' % getenv("FOOD_SELECTOR_API")}
    PARAMS={'location' : user_local,
            'term' : category,
            'radius' : 6500, # need to convert miles to meters -> for submit field
            'open_now' : True,
            'limit' : 1, # depending on pure goal of app we want 1 or 3 #
    }

    yelp_response = requests.get(
        BASE_YELP_URL, params=PARAMS, headers=HEADERS
    )
    addr = yelp_response.json()['businesses'][0]['location']['display_address']
    img_url = yelp_response.json()['businesses'][0]['url']
    phone = yelp_response.json()['businesses'][0]['display_phone']
    rest_url = yelp_response.json()['businesses'][0]['url']
    
    eat_this_dict = {"Address": addr, "Image": img_url, "Phone": phone, "URL": rest_url}
    print(eat_this_dict)

app.run()
