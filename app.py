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
courts_all = ["1", "2", "3", "All courts"]
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
class CourtDayForm(FlaskForm):
    court = SelectField('Court', choices=courts_all)
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

            return redirect("/booking")


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

    # Forget any user_id
    session.clear()

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

    # current_date in same format as added to db (string and %Y-%m-%d)
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")

    # get number of upcoming bookings for the current user
    cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id = :user_id AND date >= :current_date", {"user_id": user_id, "current_date": current_date_str})
    upcoming_user_bookings = cur.fetchone()[0]

    # check if there are any upcoming bookings, if not, return no upcoming bookings for {user}
    if upcoming_user_bookings == 0:
        msg = "You have no upcoming bookings"
        return render_template("mybookings.html", form=form, msg=msg)

    if "show_day" in request.form and form.validate_on_submit():

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
        
        # Find bookings for logged in user and add them to page
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = :user_id AND date >= :current_date ORDER BY date, time""", {"user_id": user_id, "current_date": current_date_str})
        bookings_data = cur.fetchall()

        return render_template("mybookings.html", form=form, bd=bookings_data)
    
    if "delete_booking" in request.form and request.method == "POST":
        booking_id = request.form.get("id")

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
            return redirect("/mybookings")
    
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
    form_check = CourtDayForm()
    form_bookday = CourtDayForm()

    user_id = session["user_id"] # store current user's id

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()
    
    # POST request for searching bookings for a certain day (default for today)
    if "show_day" in request.form and form_check.validate_on_submit():
        court = form_check.court.data
        date = form_check.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        # Find upcoming bookings for that day if all courts option is provided
        if court == "All courts":
            cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                        WHERE date = :date ORDER BY time """, {"date": selected_date})
        else:
            cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                        WHERE date = :date AND court = :court ORDER BY time """, {"date": selected_date, "court": court})
        bookings_data = cur.fetchall() # populate data to display
        if not bookings_data:
            if court == "All courts":
                msg = "No bookings for the selected day"
                return render_template("admin.html", form_check=form_check, msg=msg, form_bookday=form_bookday)
            else:
                msg = "No bookings for this court on the selected day"
                return render_template("admin.html", form_check=form_check, msg=msg, form_bookday=form_bookday)
        else:
            return render_template("admin.html", form_check=form_check, bd=bookings_data, form_bookday=form_bookday)

    if "delete_booking" in request.form and request.method == "POST":
        booking_id = request.form.get("id")

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
            return redirect("/mybookings")

    if "create_index" in request.form and request.method == "POST":

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
    
    # admin has the ability to delete bookings for the selected day (if any exists) and disable bookings for that day
    if "book_day" in request.form and form_bookday.validate_on_submit(): 

        court = form_bookday.court.data # pass this into query
        date = form_bookday.date.data
        selected_date = date.strftime("%Y-%m-%d") # pass this into query
        selected_weekday = date.strftime("%a") # pass this into query
        people = 4 # default when admin makes a booking

        # check if date is not in the past
        current_date = datetime.today().strftime('%Y-%m-%d')
        if selected_date < current_date:
            flash("Invalid date", "danger")
            return redirect("/admin")

        # delete every booking for the selected_date and court
        cur.execute("DELETE FROM bookings WHERE date = :date AND court = :court", {"date": selected_date, "court": court})
        con.commit()


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


    return render_template("admin.html", form_check=form_check, form_bookday=form_bookday)


# NEXT TODOS
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# have admin be able to search how many bookings there are for a specific day and show them and how many upcoming bookings there are in total and total bookings (past plus upcoming)
# session not ending properly when I restart flask
# admin registering
# store admin in session as a boolean isAdmin if type is admin when logging in
# admin_required
# create helpers folder with files such as validations.py (to store validation functions), required.py (to store required functions like login_required), and more if necessary
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------