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

from helpers import login_required, validateBooking, validateLogin, validateRegistration, validateIndex, makeIndex

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

# Check bookings form
class CheckBookingsForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())

# Admin book a court for a day form
class BookDayForm(FlaskForm):
    court = SelectField('Court', choices=courts)
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

    # if request is POST and form fields are validated
    if form.validate_on_submit():
        user_id = session["user_id"] # store current user's id
        people = form.people.data # string
        court = form.court.data # string
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string
        time = form.time.data # string

        if validateBooking(people, court, date, time, numofpeople, courts, possibletimesweekend, possibletimes, user_id):

            # Connect to database
            con = sqlite3.connect("scheduling.db")
            cur = con.cursor()

            selected_weekday = date.strftime("%A") # string current day of the week

            cur.execute("""INSERT INTO bookings (user_id, week_day, date, time, court, people) 
                        VALUES (:user_id, :week_day, :date, :time, :court, :people)""", 
                        {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court, "people": people})
            con.commit()

            flash("Booking successful!!", "success")

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
        flash(f"Welcome, {username} !!", "success")

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
        email = request.form.get("email")

        # Connect to database
        con = sqlite3.connect("scheduling.db")
        cur = con.cursor()

        # get all usernames
        cur.execute("SELECT username FROM users")
        usernames = cur.fetchall()

        if not validateRegistration(usernames, username, password, confirmation, email):
            return render_template("register.html")

        # Successful registering
        else:
            hashed_password = generate_password_hash(password) # hash password
            cur.execute("INSERT INTO users (username, hash, email) VALUES (:username, :hash, :email)", {"username": username, "hash": hashed_password, "email": email})
            con.commit()
            flash("Account successfully created!", "success")

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

    user_id = session["user_id"] # store current user's id


    # Forget any user_id
    session.clear()

    flash("Goodbye", "info")

    # Redirect user to login form
    return redirect("/login")


@app.route("/mybookings", methods=["GET", "POST"])
@login_required
def mybookings():

    # Initialize form
    form = CheckBookingsForm()

    user_id = session["user_id"] # store current user's id

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    if "check_day" in request.form and form.validate_on_submit():

        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        # Find bookings for logged in user
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = :user_id AND date = :date ORDER BY time""", {"user_id": user_id, "date": selected_date})
        bookings_data = cur.fetchall()

        if not bookings_data:
            msg = "No bookings for the selected day"
            return render_template("mybookings.html", form=form, msg=msg)
        else:
            return render_template("mybookings.html", form=form, bd=bookings_data)

    if "show_all" in request.form:
        
        # Find bookings for logged in user
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = :user_id ORDER BY date, time""", {"user_id": user_id})
        bookings_data = cur.fetchall()

        if not bookings_data:
            msg = "No bookings for this account"
            return render_template("mybookings.html", form=form, msg=msg)
        else:
            return render_template("mybookings.html", form=form, bd=bookings_data)
    
    if "delete_day" in request.form and form.validate_on_submit:

        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        cur.execute("DELETE FROM bookings WHERE user_id = :user_id AND date = :selected_date", {"user_id": user_id, "selected_date": selected_date})
        con.commit()

        flash(f"No more bookings for {selected_date}", "success")

        return render_template("mybookings.html", form=form)
    
    if "delete_all" in request.form:

        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        cur.execute("DELETE FROM bookings WHERE user_id = :user_id", {"user_id": user_id})
        con.commit()

        flash("No more bookings for you", "success")

        return render_template("mybookings.html", form=form)
    
    return render_template("mybookings.html", form=form)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():

    # Initialize forms
    form_check = CheckBookingsForm()
    form_bookday = BookDayForm()

    user_id = session["user_id"] # store current user's id
    
    # POST request for searching bookings for a certain day (default for today)
    if form_check.validate_on_submit():
        date = form_check.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        # Connect to database
        con = sqlite3.connect("scheduling.db")
        cur = con.cursor()

        # Find upcoming bookings for that day
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE date = :date ORDER BY time """, {"date": selected_date})
        bookings_data = cur.fetchall()

        if not bookings_data:
            msg = "No bookings for that day"
            return render_template("admin.html", form_check=form_check, msg=msg, form_bookday=form_bookday)
        else:
            return render_template("admin.html", form_check=form_check, bd=bookings_data, form_bookday=form_bookday)

    return render_template("admin.html", form_check=form_check, form_bookday=form_bookday)


@app.route("/deletebooking", methods=["POST"])
@login_required
def deletebooking():

    user_id = session["user_id"] # store current user's id
    booking_id = request.form.get("id")

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Delete booking
    cur.execute("DELETE FROM bookings WHERE booking_id = :booking_id", {"booking_id": booking_id})
    con.commit()
    flash("Booking succesfully deleted", "success")

    # get type - if type is admin, redirect to admin, if not, redirect to homepage
    cur.execute("SELECT type FROM users WHERE id = :user_id", {"user_id": user_id})
    type = cur.fetchone()[0]

    if type == "admin":
        return redirect("/admin")
    else:
        return redirect("/")


@app.route("/createindex", methods=["POST"])
@login_required
def createindex():

    name = request.form.get("name")
    table = request.form.get("table")
    columns_input = request.form.get("columns")

    # transform columns into a list
    columns = columns_input.split(",")
    # remove whitespaces from each element of the list
    i = 0
    for column in columns:
        columns[i] = column.strip()
        i += 1

    # turn invalid SQL character into _
    k = 0
    for n in name:
        if n == " " or n == ";" or n == ">" or n == "<" or n == ">":
            name[k] = "_"
        k += 1

    if not validateIndex(name, table, columns_input, columns):
        return redirect("/admin")
    
    makeIndex(columns, name, table)

    return redirect("/admin")


@app.route("/bookday", methods=["POST"])
@login_required
def bookday():
    # bookday route (only accepts POST) - admin has the ability to delete bookings for the selected day (if any exists) and disable bookings for that day

    form_bookday = BookDayForm()

    user_id = session["user_id"] # store current user's id, pass this into query
    court = form_bookday.court.data # pass this into query
    date = form_bookday.date.data
    selected_date = date.strftime("%Y-%m-%d") # pass this into query
    selected_weekday = date.strftime("%a") # pass this into query
    people = 4 # default when admin makes a booking

    if form_bookday.validate_on_submit:

        # Connect to database
        con = sqlite3.connect("scheduling.db")
        cur = con.cursor()

        # delete every booking for the selected_date and court
        cur.execute("DELETE FROM bookings WHERE date = :date AND court = :court", {"date": selected_date, "court": court})
        con.commit()

        # check if date is not in the past
        current_year = datetime.now().year # int
        current_month = datetime.now().month # int
        current_day = datetime.now().day # int

        # use a for loop to make a booking for every possible time in the day for the selected court
        # (use array possibletimes for week days and possibletimesweekend if the selected_weekday is a weekend day)
        if selected_weekday == "Sat" or selected_weekday == "Sun":
            for time in possibletimesweekend:
                if time == "Choose a time":
                    continue
                else:
                    cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court, people) VALUES (:user_id, :week_day, :date, :time, :court, :people)",
                                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court, "people": people})
                    con.commit()
        else:
            for time in possibletimes:
                if time == "Choose a time":
                    continue
                else:
                    cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court, people) VALUES (:user_id, :week_day, :date, :time, :court, :people)",
                                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court, "people": people})
                    con.commit()
        flash(f"Court succesfully booked for {selected_date}", "success")

    return redirect("/admin")

# on mybookings page and admin page, only show upcoming bookings
# have admin searches be able to be by court (have "all courts" option to show results for all courts)
# have admin be able to search how many bookings there are for a specific day and show them and how many upcoming bookings there are in total and total bookings (past plus upcoming)
# session not ending properly when I restart flask
# admin registering
# admin_required
# create helpers folder with files such as validations.py (to store validation functions), required.py (to store required functions like login_required), and more if necessary


# APP REQUIREMENTS
    # version 1.0 - original implementation for Luis
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
            # show all bookings for each court for the selected day (default for today)
            # delete route (only accepts POST) - admin has the ability to delete any reservation for any day and to book a court for an extended period of time (more than 1 hour per day)
            # createindex route (only accepts POST) - admin is able to create indexes on tables
            # bookday route (only accepts POST) - admin has the ability to delete bookings for the selected day (if any exists) and disable bookings for that day
            # have way to register an admin with a special login
            # admin logs in as a regular user
            # create function on helpers.py to restrict admin page to be accesible by admin only (similar to login_required)
        # more
            # send me an email when an booking or cancellation is made, with the action's info
            # send email to user after a booking is made
            # send email to user if one of its bookings are cancelled (both by the user himself or an admin)
            # if there are bookings in the next hour, send me an email with all the bookings
            # if a user has a booking in the next hour, send him an email
            # schedule Python code to run every 6 months to remove bookings from database and other features if needed
            # page which shows all current bookings for the logged in account
            # basic styling
            # organize code
            # deploy and show to Luis
    # version 2.0 - goal is to be a platform where users can book a court for different clubs
        # change bookings to be of 1 hour instead of 30 minutes, while still allowing appointments to start at hour:00 and hour:30 (don't forget to update booking validation)
        # create new table to store different clubs (have club_name, number of courts, opening times, exact location, address)
        # update schema
        # have map (use mapbox) showing location of all courts
        # create a profile page for each tennis club
        # when booking, have option to select club (only show affiliated clubs). After selecting club, go to a new page where a booking for that club can be made
        # update queries to show results for club when relevant
        # update queries to show the club where the booking is made
        # update insert and delete queries to only delete bookings for specified club
        # have type super-admin (has the ability to do be an admin for every club in every sport)
        # admin type only allows to perform actions on the admin's specific club
        # contacts page
    # version 3.0 - have booking tennis courts be one of many possible types of bookings to be made, implement booking for other sports such as soccer, basketball, etc
    # version 4.0 - implement non-sport related bookings, such as for restaurant tables, offices (like lawyer, doctor, etc), hair salons, etc

