import os
import sqlite3

from flask import Flask, flash, redirect, render_template, session, request
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import StringField, SelectField
from datetime import datetime
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import generate_password_hash

from helpers import login_required, validateBooking, validateLogin, validateRegistration

# Initialize app
app = Flask(__name__)

# Configure for flask_wtf
app.config["SECRET_KEY"] = "secret"

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Arrays for SelectField choices
numofpeople = ["2", "3", "4"]
courts = ["1", "2", "3"]
possibletimes = ["Choose a time",
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    "13:00", "13:30",
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
    "17:00", "17:30",
    "18:00", "18:30",
    "19:00", "19:30",
    "20:00", "20:30",
    "21:00", "21:30"
]
possibletimesweekend = ["Choose a time",
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    "13:00", "13:30",
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
    "17:00", "17:30",
    "18:00", "18:30",
    "19:00", "19:30"
]

# Booking form
class BookingForm(FlaskForm):
    people = SelectField('Number of people', choices=numofpeople)
    court = SelectField('Court', choices=courts)
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())
    time = SelectField('Time (open from 09:00 to 22:00)', choices=possibletimes, default="Choose a time")

# Adming check bookings form
class CheckBookingsForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())



@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")


@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():

    # Initialize form
    form = BookingForm()

    user_id = session["user_id"] # store current user's id

    # if request is POST and form fields are validated
    if form.validate_on_submit():
        people = form.people.data # string
        court = form.court.data # string
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string
        time = form.time.data # string

        if validateBooking(people, court, date, time, numofpeople, courts, possibletimesweekend, possibletimes, user_id):

            # Connect to database
            con = sqlite3.connect("scheduling.db")
            cur = con.cursor()

            selected_weekday = date.strftime("%A") # string current day of the week abbreviation (3 characters)

            cur.execute("""INSERT INTO bookings (user_id, week_day, date, time, court, people) 
                        VALUES (:user_id, :week_day, :date, :time, :court, :people)""", 
                        {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court, "people": people})
            con.commit()

            flash("Booking successful!!")

            return redirect("/")


    return render_template("booking.html", form=form)



@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not validateLogin(username, password):
            return render_template("login.html")
        
        # Connect to database
        con = sqlite3.connect("scheduling.db")
        cur = con.cursor()

        # Get id of user who logged in to store in the session
        cur.execute("SELECT * FROM users WHERE username = :username", {"username": username})
        id = cur.fetchone()[0]

        # Greet user
        flash(f"Welcome, {username} !!")

        # Remember which user has logged in
        session["user_id"] = id

        return redirect("/")

    return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("pswdconf")

        # Connect to database
        con = sqlite3.connect("scheduling.db")
        cur = con.cursor()

        cur.execute("SELECT username FROM users")
        usernames = cur.fetchall()

        if not validateRegistration(usernames, username, password, confirmation):
            return render_template("register.html")

        # Successful registering
        else:
            hashed_password = generate_password_hash(password) # hash password
            cur.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username": username, "hash": hashed_password})
            con.commit()
            flash("Account successfully created!")

            # Get id of user who logged in to store in the session
            cur.execute("SELECT * FROM users WHERE username = :username", {"username": username})
            id = cur.fetchone()[0]

            # Remember which user has logged in
            session["user_id"] = id

            return redirect("/")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/upcoming", methods=["GET", "POST"])
def upcoming():

    user_id = session["user_id"] # store current user's id

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    if request.method == "POST":
        id = request.form.get("id")
        cur.execute("DELETE FROM bookings WHERE booking_id = :id", {"id": id})
        con.commit()
        flash("Successfully deleted!!")

    # Find upcoming bookings for logged in user
    cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                WHERE user_id = :user_id """, {"user_id": user_id})
    bookings_data = cur.fetchall()

    if not bookings_data:
        msg = "No upcoming bookings"
        return render_template("upcoming.html", msg=msg)
    else:
        return render_template("upcoming.html", bd=bookings_data)


@app.route("/admin", methods=["GET", "POST"])
def admin():

    # Initialize form
    form = CheckBookingsForm()

    user_id = session["user_id"] # store current user's id
    
    # POST request for searching bookings for a certain day (default for today)
    if form.validate_on_submit():
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        # Connect to database
        con = sqlite3.connect("scheduling.db")
        cur = con.cursor()

        # Find upcoming bookings for that day
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE date = :date """, {"date": selected_date})
        bookings_data = cur.fetchall()

        if not bookings_data:
            msg = "No bookings for that day"
            return render_template("admin.html", form=form, msg=msg)
        else:
            return render_template("admin.html", form=form, bd=bookings_data)

    return render_template("admin.html", form=form)


@app.route("/delete", methods=["POST"])
def delete():

    id = request.form.get("id")

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Delete booking
    cur.execute("DELETE FROM bookings WHERE booking_id = :id", {"id": id})
    con.commit()
    flash("Succesfully deleted")

    return redirect("/admin")


@app.route("/createindex", methods=["POST"])
def createindex():

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    name = request.form.get("name")
    table = request.form.get("table")
    columns = request.form.get("columns") # transform into list, then depending on its size, pass each column to the query

    # FORM VALIDATION

    # CREATE INDEX

# delete route (only accepts POST) - delete a booking
# makeindex route (only accepts POST) - create an index CREATE UNIQUE INDEX unique_com_id ON company (com_id,com_name);
# daybooking route (only accepts POST) - deletes bookings for the selected day (if any exists) and disables bookings for that day



# APP REQUIREMENTS
    # form 
        # displays a calendar daypicker but with invalid dates disabled (already past dates, days where club is closed, days more than a month from today)
        # displays only options of valid times (from 09:00 to 22:00, with a step of 30 minutes) (only enable to pick available times for the specific court)
        # if reservation is for Saturday or Sunday, possibletimes are until 20:00 only (use possibletimesweekend array for choices)
        # validation with date and time restrictions included (bookings need to be made a minimum of 30 minutes before playing time)
        # bookings can only be made for the current and the next month
    # database
        # define schema (consider admin type)
        # create tables
        # insert SQL statements in app.py, where needed
        # maximum of 2 bookings per day per person (1 hour) (except for admin)
        # a booking is for 30 minutes (after booking is done, make the time for that specific day and court unavailable)
        # have action for user to cancel booking, which makes the times of it available again
        # create indexes where useful
    # admin 
        # have way to register an admin with a special login
        # admin logs in as a regular user
        # create function on helpers.py to restrict admin page to be accesible by admin only (similar to login_required
        # admin is able to create indexes on tables
        # show all bookings for each court for the selected day (default for today)
        # admin has the ability to delete any reservation for any day and to book a court for an extended period of time (more than 1 hour)
        # admin has the ability to close club for a specified day
    # more
        # send me an email when an appointment or cancellation is made, with the action's info
        # if there are appointments in the next hour, send me an email with all the appointments
        # schedule Python code to run every 6 months to remove bookings from database and other features if needed
        # page which shows all current bookings for the logged in account

