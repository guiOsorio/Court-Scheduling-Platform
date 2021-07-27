import sqlite3

from flask import flash, redirect, session
from datetime import datetime
from functools import wraps
from werkzeug.security import check_password_hash


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Login required")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def validateReservation(people, court, date, time, numofpeople, courts, ptw, pt):
    if people == "" or court == "" or date == "" or time == "Choose a time":
            flash("Please fill out all fields")
            return False

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
        return False
    elif court not in courts:
        flash("Please select a valid court")
        return False
    elif ((selected_weekday == "Sat" or selected_weekday == "Sun") and time not in ptw) or time not in pt:
        flash("The club is not open at this time. Week hours are 09:00 to 22:00. Weekend hours are 09:00 to 20:00 (reservations are allowed until 1 hour before closing)")
        return False
    elif selected_year < current_year or (selected_year == current_year and (selected_month < current_month) or (selected_month == current_month and selected_day < current_day)):
        flash("Please provide a valid date")
        return False
    elif selected_year == current_year and selected_month == current_month and selected_day == current_day and selected_hour <= current_hour + 1:
        if selected_hour == current_hour + 1 and (60 + selected_minute - current_minute) <= 30:
            flash("Online reservations can only be made at least 30 minutes prior to palying time")
            return False
        elif selected_hour == current_hour + 1 and (60 + selected_minute - current_minute) > 30:
            return True #######################
        else:
            flash("Please select a valid time")
            return False
    elif selected_month > current_month + 1:
        flash("Reservations are only allowed for the current and the next month")
        return False
    elif selected_year > current_year:
        if current_month == 12 and selected_month == 1:
            return True ###############################
        else:
            flash("Reservations are only allowed for the current and the next month")
            return False
    else:
        return True #################################


def validateLogin(username, password):
    # Ensure username was submitted
    if not username:
        flash("Must have a username")
        return False

    # Ensure password was submitted
    elif not password:
        flash("Must have a password")
        return False

    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE username = :username", {"username": username})
    user = cur.fetchone()

    if not user:
        flash("Username doesn't exist")
        return False

    # Ensure username exists and password is correct
    table_hash = user[2]
    if not check_password_hash(table_hash, password):
        flash("Invalid password")
        return False

    return True


def validateRegistration(usernames, username, password, confirmation):
    # Handles username already existing
        for user in usernames:
            if username in user:
                flash("This username is already taken")
                return False

        # Handles username or password fields being blank
        if username.strip() == "" or password.strip() == "" or confirmation.strip() == "":
            flash("All items need a value")
            return False
        
        # Handles password and password confirmation not matching
        elif password != confirmation:
            flash("Password and confirmation fields don't match")
            return False
        
        return True