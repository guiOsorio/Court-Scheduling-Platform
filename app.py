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

        timenow = datetime.now().strftime("%H:%M") # string
        yearnow = datetime.now().year # int
        monthnow = datetime.now().month # int
        daynow = datetime.now().day # int

        # Own validation
        if name == "" or people == "" or court == "" or date == "" or time == "Choose a time":
            flash("Please fill out all fields")
            return render_template("form.html", form=form)
        elif people not in numofpeople:
            flash("Only 2 to 4 people are allowed per court")
            return render_template("form.html", form=form)
        elif court not in courts:
            flash("Please select a valid court")
            return render_template("form.html", form=form)

        # TODO: date and time validation (only allow for reservations after the current time)

        else:
            return render_template("data.html", name=name, people=people, court=court, date=date, time=time)

    return render_template("form.html", form=form)


# REQUIREMENTS
    # form 
        # displays a calendar daypicker but withinvalid dates disabled (already past dates, days where club is closed, days more than a month from today)
        # displays only options of valid times (from 09:00 to 22:00, with a step of 30 minutes) (only enable to pick available times for the specific court)
        # a booking is for 1 hour (after booking is done, make the time for that specific day and court unavailable)
        # have action for user to cancel booking, which makes the times of it available again
        # whenever an appointment or cancellation is made, send me an email to gosorio@sandiego.edu with the info of what happened
        # maximum of 2 reservations per day per person (2 hours) (except for admin)
        # if reservation is for Saturday or Sunday, possibletimes are until 20:00 only (use possibletimesweekend array for choices)
    # database
        # define schema
        # create tables
        # insert SQL statements in app.py, where needed
        # create indexes where useful
    # admin page
        # user needs to login in order to access this page
        # show all reservations for each court for the selected day (default for today)
        # admin has the ability to delete any reservation for any day and to book a court for an extended period of time (more than 1 hour)
    # more
        # send me an email when an appointment is made with the appointment's info
        # if there are appointments in the next hour, send me an email with all the appointments
        # schedule Python code to run every 6 months to remove bookings from database and other features if needed

