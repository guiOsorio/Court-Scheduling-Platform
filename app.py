import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import StringField, SelectField
from datetime import datetime

from validation import validate

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

# Reservation Form
class BookingForm(FlaskForm):
    name = StringField('Name')
    people = SelectField('Number of people', choices=numofpeople)
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

        if validate(name, people, court, date, time, numofpeople, courts, possibletimesweekend, possibletimes):
            return render_template("data.html", name=name, people=people, court=court, date=date, time=time)
            

    return render_template("form.html", form=form)


# REQUIREMENTS
    # implement login
    # form 
        # displays a calendar daypicker but with invalid dates disabled (already past dates, days where club is closed, days more than a month from today)
        # displays only options of valid times (from 09:00 to 22:00, with a step of 30 minutes) (only enable to pick available times for the specific court)
        # if reservation is for Saturday or Sunday, possibletimes are until 20:00 only (use possibletimesweekend array for choices)
        # validation with date and time restrictions included (reservations need to be made a minimum of 30 minutes before playing time)
        # reservations can only be made for the current and the next month
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

