from os import getenv
from dotenv import load_dotenv, find_dotenv
from flask import Flask, redirect, url_for, render_template, flash, session
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
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
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
    category = SelectField(
        validators=[],
        choices=[
            ("", "Food Type(Any)"),
            ("italian", "Italian"),
            ("chinese", "Chinese"),
            ("mexican", "Mexican"),
            ("american", "American"),
            ("indian", "Indian"),
            ("japanese", "Japanese"),
            ("thai", "Thai"),
            ("healthy", "Healthy"),
        ],
        render_kw={"placeholder": "Select a category"},
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
                return redirect(url_for("search"))
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


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    form = EatWhatForm()
    if form.validate_on_submit():
        user_local = form.user_local.data
        # category = form.category.data

        if not check_valid_location(user_local):
            return redirect(url_for("search"))

        eat_this_dict = decide_4me(user_local, "")
        session["name"] = eat_this_dict["Name"]
        session["addr"] = eat_this_dict["Address"]
        session["image"] = eat_this_dict["Image"]
        session["phone"] = eat_this_dict["Phone"]
        session["url"] = eat_this_dict["URL"]
        return redirect(url_for("results"))
    return render_template("search.html", form=form)


@app.route("/results", methods=["GET", "POST"])
@login_required
def results():
    name = session.get("name")
    addr = session.get("addr")
    image = session.get("image")
    phone = session.get("phone")
    url = session.get("url")
    return render_template(
        "results.html", name=name, addr=addr, image=image, url=url, phone=phone
    )


def decide_4me(user_local, category):
    BASE_YELP_URL = "https://api.yelp.com/v3/businesses/search"
    HEADERS = {"Authorization": "Bearer %s" % getenv("FOOD_SELECTOR_API")}
    PARAMS = {
        "term": "restaurant",
        "location": str(user_local),
        "term": category,
        "radius": 6500,  # need to convert miles to meters -> for submit field
        "limit": 50,  # depending on pure goal of app we want 1 or 3 #
    }

    yelp_response = requests.get(BASE_YELP_URL, params=PARAMS, headers=HEADERS)

    data = yelp_response.json()

    restaurant = random.choice(data["businesses"])

    addr = restaurant["location"]["display_address"]
    name = restaurant["name"]
    img_url = restaurant["image_url"]
    phone = restaurant["display_phone"]
    rest_url = restaurant["url"]

    eat_this_dict = {
        "Name": name,
        "Address": addr,
        "Image": img_url,
        "Phone": phone,
        "URL": rest_url,
    }
    return eat_this_dict


def check_valid_location(location):
    BASE_YELP_URL = "https://api.yelp.com/v3/businesses/search"
    HEADERS = {"Authorization": "Bearer %s" % getenv("FOOD_SELECTOR_API")}
    PARAMS = {"location": location, "term": "food"}

    response = requests.get(BASE_YELP_URL, params=PARAMS, headers=HEADERS)

    if response.ok:
        data = response.json()
        if data.get("businesses"):
            return True  # Location is a valid city name

    BASE_ZIP_URL = "https://www.zipcodeapi.com/rest/%s/info.json/%s/degrees" % (
        getenv("ZIPCODE_API_KEY"),
        location,
    )

    response = requests.get(BASE_ZIP_URL)
    if response.ok:
        data = response.json()
        if data.get("city"):
            return True  # Location is a valid zip code

    return False  # Location is not valid city or zip code


# Uncomment to run locally comment back to deploy
# app.run(debug=True)
