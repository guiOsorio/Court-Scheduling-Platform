import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import StringField, SelectField
from datetime import datetime

# Initialize app
app = Flask(__name__)

# Configure for flask_wtf
app.config["SECRET_KEY"] = "secret"

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
    "21:00"
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
    "19:00"
]

# Form fields
class BookingForm(FlaskForm):
    name = StringField('Name')
    people = SelectField('People', choices=numofpeople)
    court = SelectField('Court', choices=courts)
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())
    time = SelectField('Time (open from 09:00 to 22:00)', choices=possibletimes, default="Choose a time")



@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/form", methods=["GET", "POST"])
def form():
    # Initialize form
    form = BookingForm()

    # if request is POST and form fields are validated
    if form.validate_on_submit():
        name = form.name.data # string
        people = form.people.data # string
        court = form.court.data # string
        date = form.date.data # datetime.date
        time = form.time.data # string

        if name == "" or people == "" or court == "" or date == "" or time == "Choose a time":
            flash("Please fill out all fields")
            return render_template("form.html", form=form)

        selected_date_str = date.strftime("%Y-%m-%d") # string selected date 
        current_time_str = datetime.now().strftime("%H:%M") # string
        selected_weekday = date.strftime("%a") # string current day of the week abbreviation (3 characters)

        # selected date/time data in int
        selected_hour = int(time[:2])
        selected_minute = int(time[3:])
        selected_year = int(selected_date_str[:4])
        selected_month = int(selected_date_str[5:7])
        selected_day = int(selected_date_str[8:])

        # current date/time data in int
        current_hour = int(current_time_str[:2]) # int
        current_minute = int(current_time_str[3:]) # int
        current_year = datetime.now().year # int
        current_month = datetime.now().month # int
        current_day = datetime.now().day # int

        # Own validation
        if people not in numofpeople:
            flash("Only 2 to 4 people are allowed per court")
            return render_template("form.html", form=form)
        elif court not in courts:
            flash("Please select a valid court")
            return render_template("form.html", form=form)
        elif ((selected_weekday == "Sat" or selected_weekday == "Sun") and time not in possibletimesweekend) or time not in possibletimes:
            flash("The club is not open at this time. Week hours are 09:00 to 22:00. Weekend hours are 09:00 to 20:00 (reservations are allowed until 1 hour before closing)")
            return render_template("form.html", form=form)
        elif selected_year < current_year or (selected_year == current_year and (selected_month < current_month) or (selected_month == current_month and selected_day < current_day)):
            flash("Please provide a valid date")
            return render_template("form.html", form=form)
        elif selected_year == current_year and selected_month == current_month and selected_day == current_day and selected_hour <= current_hour + 1:
            if selected_hour == current_hour + 1 and (60 + selected_minute - current_minute) <= 30:
                flash("Online reservations can only be made at least 30 minutes prior to palying time")
                return render_template("form.html", form=form)
            elif selected_hour == current_hour + 1 and (60 + selected_minute - current_minute) > 30:
                return render_template("data.html", name=name, people=people, court=court, date=date, time=time)
            else:
                flash("Please select a valid time")
                return render_template("form.html", form=form)
        else:
            return render_template("data.html", name=name, people=people, court=court, date=date, time=time)

    return render_template("form.html", form=form)


# REQUIREMENTS
    # form 
        # displays a calendar daypicker but withinvalid dates disabled (already past dates, days where club is closed, days more than a month from today)
        # displays only options of valid times (from 09:00 to 22:00, with a step of 30 minutes) (only enable to pick available times for the specific court)
        # if reservation is for Saturday or Sunday, possibletimes are until 20:00 only (use possibletimesweekend array for choices)
        # validation with date and time restrictions included (reservations need to be made a minimum of 30 minutes before playing time)
    # database
        # define schema (consider admin type)
        # create tables
        # insert SQL statements in app.py, where needed
        # a booking is for 1 hour (after booking is done, make the time for that specific day and court unavailable)
        # have action for user to cancel booking, which makes the times of it available again
        # maximum of 2 reservations per day per person (2 hours) (except for admin)
        # create indexes where useful
    # admin page
        # user needs to login in order to access this page
        # show all reservations for each court for the selected day (default for today)
        # admin has the ability to delete any reservation for any day and to book a court for an extended period of time (more than 1 hour)
        # admin has the ability to close club for a certain period of time desired
    # more
        # send me an email when an appointment or cancellation is made, with the action's info
        # if there are appointments in the next hour, send me an email with all the appointments
        # schedule Python code to run every 6 months to remove bookings from database and other features if needed

