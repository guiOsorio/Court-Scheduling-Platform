import psycopg2
import re # regex
import datetime as dt

from flask import flash
from datetime import datetime
from werkzeug.security import check_password_hash # (hash, password) checks if password matches the hash
from helpers.variables.others import POSTGRE_URI


def validateBooking(people, court, date, time, numofpeople, courts, ptw, pt, user_id):
    if people == "" or court == "" or date == "" or time == "Choose a time":
            flash("Please fill out all fields", "danger")
            return False

    selected_date = date.strftime("%Y-%m-%d") # string
    current_time_str = datetime.now().strftime("%H:%M") # string
    selected_weekday = date.strftime("%a") # string current day of the week abbreviation (3 characters)

    # selected date/time data in int
    selected_hour = int(time[:2])
    selected_minute = int(time[3:])
    selected_year = int(selected_date[:4])
    selected_month = int(selected_date[5:7])
    selected_day = int(selected_date[8:])

    # current date/time data in int
    current_hour = int(current_time_str[:2]) # int
    current_minute = int(current_time_str[3:]) # int
    current_year = datetime.now().year # int
    current_month = datetime.now().month # int
    current_day = datetime.now().day # int

    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # Check number of bookings and if user is an admin
    cur.execute("""SELECT COUNT(*) FROM bookings JOIN users ON user_id = id
                WHERE user_id = %(user_id)s AND date = %(date)s""", {"user_id": user_id, "date": selected_date})
    selected_day_bookings = cur.fetchone()[0]
    cur.execute("""SELECT type FROM users WHERE id = %(user_id)s""", {"user_id": user_id})
    user_type = cur.fetchone()[0]


    # Check if that time is already booked
    cur.execute("""SELECT * FROM bookings
                WHERE date = %(date)s AND time = %(time)s AND court = %(court)s""", {"date": selected_date, "time": time, "court": court})
    is_booked = cur.fetchone()

    # Own validation
    if people not in numofpeople:
        flash("Only 2 to 4 people are allowed per court", "danger")
        return False
    elif court not in courts:
        flash("Please select a valid court", "danger")
        return False
    elif ((selected_weekday == "Sat" or selected_weekday == "Sun") and time not in ptw) or time not in pt:
        flash("The club is not open at this time. Week hours are 09:00 to 22:00. Weekend hours are 09:00 to 20:00 (bookings are allowed until 1 hour before closing)", "danger")
        return False
    elif selected_year < current_year or (selected_year == current_year and (selected_month < current_month) or (selected_month == current_month and selected_day < current_day)):
        flash("Please provide a valid date", "danger")
        return False
    elif selected_day_bookings >= 2 and user_type != "admin":
        flash("A maximum of 2 bookings per person per day is allowed", "danger")
        return False
    elif is_booked:
        flash("This court is already booked at this time. Please select a different court or time", "danger")
        return False
    elif selected_year == current_year and selected_month == current_month and selected_day == current_day and selected_hour <= current_hour + 1:
        if selected_hour == current_hour + 1 and (60 + selected_minute - current_minute) <= 30:
            flash("Online bookings can only be made at least 30 minutes prior to playing time", "danger")
            return False
        elif selected_hour == current_hour + 1 and (60 + selected_minute - current_minute) > 30:
            return True #######################
        else:
            flash("Please select a valid time", "danger")
            return False
    elif selected_month > current_month + 1:
        flash("Bookings are only allowed for the current and the next month", "danger")
        return False
    elif selected_year > current_year:
        if current_month == 12 and selected_month == 1:
            return True ###############################
        else:
            flash("Bookings are only allowed for the current and the next month", "danger")
            return False
    else:
        return True #################################


def validateLogin(username, password):
    # Ensure username was submitted
    if not username:
        flash("Must have a username", "danger")
        return False

    # Ensure password was submitted
    elif not password:
        flash("Must have a password", "danger")
        return False

    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE username = %(username)s", {"username": username})
    user = cur.fetchone()

    if not user:
        flash("Username doesn't exist", "danger")
        return False

    # Ensure username exists and password is correct
    table_hash = user[2]
    if not check_password_hash(table_hash, password):
        flash("Invalid password", "danger")
        return False

    return True

# Regex for validating an email
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
 
# Function for validating an email
def validateEmail(email):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # check if email already exists
    cur.execute("SELECT * FROM users WHERE email = %(email)s", {"email": email})
    query_email = cur.fetchone()

    if query_email:
        flash("Email already taken", "danger")
        return False
    # pass the regular expression
    # and the string in search() method
    if(re.match(regex, email)):
        return True
    else:
        flash("Invalid email", "danger")
        return False


def validateRegistration(usernames, username, password, confirmation, email):
    # Handles username already existing
        for user in usernames:
            if username in user:
                flash("This username is already taken", "danger")
                return False

        # Handles username or password fields being blank
        if username.strip() == "" or password.strip() == "" or confirmation.strip() == "":
            flash("All items need a value", "danger")
            return False
        
        # Handles password and password confirmation not matching
        elif password != confirmation:
            flash("Password and confirmation fields don't match", "danger")
            return False

        elif not validateEmail(email):
            return False
        
        return True


def validateIndex(name, table, columns_input, columns):
    # CREATE INDEX VALIDATION

    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    if name == "" or table.strip() == "" or columns_input.strip() == "":
        flash("All fields need a value", "danger")
        return False

    # if table doesn't exist - table needs to exist and have at least one row to have an index created
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")                                ##################### FIGURE THIS OUT
    tables_in_db = cur.fetchall()

    # check if table exists
    num_of_tables = len(tables_in_db)
    z = 0
    
    for t in tables_in_db:
        if t[0] == table:
            break
        elif z == num_of_tables - 1: # no corresponding table found in db
            flash("Table does not exist", "danger")
            return False
        else:
            z += 1
    
    # if any of the columns do not belong to the table - for loop for every column field
    for column in columns:
        cur.execute("SELECT 1 FROM PRAGMA_TABLE_INFO(:table) WHERE name = :column", {"table": table, "column": column})             ##################### FIGURE THIS OUT
        if cur.fetchone() is None:
            flash("Column does not exist", "danger")
            return False

    return True


def validateDate(field):
    if field.data < dt.date.today():
        flash("The date cannot be in the past!", "danger")
        return False
    else:
        return True