import sqlite3

from werkzeug.security import generate_password_hash
from flask import flash

def createIndex(columns, name, table):
    # Connect to database
    con = sqlite3.connect("scheduling.db", check_same_thread=False)
    cur = con.cursor()

    num_of_columns = len(columns)
    if num_of_columns == 1:
        cur.execute("CREATE UNIQUE INDEX "+name+" ON "+table+" ("+columns[0]+")")
    elif num_of_columns == 2:
        cur.execute("CREATE UNIQUE INDEX "+name+" ON "+table+" ("+columns[0]+", "+columns[1]+")")
    elif num_of_columns == 3:
        cur.execute("CREATE UNIQUE INDEX "+name+" ON "+table+" ("+columns[0]+", "+columns[1]+", "+columns[2]+")")
    elif num_of_columns == 4:
        cur.execute("CREATE UNIQUE INDEX "+name+" ON "+table+" ("+columns[0]+", "+columns[1]+", "+columns[2]+", "+columns[3]+")")
    elif num_of_columns == 5:
        cur.execute("CREATE UNIQUE INDEX "+name+" ON "+table+" ("+columns[0]+", "+columns[1]+", "+columns[2]+", "+columns[3]+", "+columns[4]+")")
    else:
        flash("Too many columns", "danger")
        return

    con.commit()
    flash("Index created successfully", "success")

    con.close()

    return


def createBooking(date, user_id, selected_date, time, court, people):
    # Connect to database
    con = sqlite3.connect("scheduling.db", check_same_thread=False)
    cur = con.cursor()

    selected_weekday = date.strftime("%A") # string current day of the week

    cur.execute("""INSERT INTO bookings (user_id, week_day, date, time, court, people) 
                VALUES (:user_id, :week_day, :date, :time, :court, :people)""", 
                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court, "people": people})
    con.commit()

    flash("Booking successful!!", "success")

    con.close()

    return


def createUser(username):
    # Connect to database
    con = sqlite3.connect("scheduling.db", check_same_thread=False)
    cur = con.cursor()

    # Get id of user who logged in to store in the session
    cur.execute("SELECT * FROM users WHERE username = :username", {"username": username})
    id = cur.fetchone()[0]

    # Greet user
    flash(f"Welcome, {username} !!", "success")

    con.close()

    return id


# returns the newly created user's id
def createAccount(password, username, email, isAdmin = False):
    # Connect to database
    con = sqlite3.connect("scheduling.db", check_same_thread=False)
    cur = con.cursor()

    hashed_password = generate_password_hash(password) # hash 
    if isAdmin:
        type = "admin"
        cur.execute(""" INSERT INTO users (username, hash, email, type) VALUES (:username, :hashed_password, :email, :type) """,
                    {"username": username, "hashed_password": hashed_password, "email": email, "type": type})
        con.commit()
    else:
        cur.execute("INSERT INTO users (username, hash, email) VALUES (:username, :hash, :email)", {"username": username, "hash": hashed_password, "email": email})
        con.commit()
    flash("Account successfully created!", "success")

    # Get id of user who logged in to store in the session
    cur.execute("SELECT * FROM users WHERE username = :username", {"username": username})
    id = cur.fetchone()[0]

    con.close()

    return id


def bookAllDay(selected_weekday, possibletimesweekend, user_id, selected_date_str, court, people, possibletimes):
    # Connect to database
    con = sqlite3.connect("scheduling.db", check_same_thread=False)
    cur = con.cursor()

    # use a for loop to make a booking for every possible time in the day for the selected court
    # (use array possibletimes for week days and possibletimesweekend if the selected_weekday is a weekend day)
    if selected_weekday == "Sat" or selected_weekday == "Sun":
        for time in possibletimesweekend:
            if time == "Choose a time":
                continue
            else:
                cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court, people) VALUES (:user_id, :week_day, :date, :time, :court, :people)",
                            {"user_id": user_id, "week_day": selected_weekday, "date": selected_date_str, "time": time, "court": court, "people": people})
                con.commit()
    else:
        for time in possibletimes:
            if time == "Choose a time":
                continue
            else:
                cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court, people) VALUES (:user_id, :week_day, :date, :time, :court, :people)",
                            {"user_id": user_id, "week_day": selected_weekday, "date": selected_date_str, "time": time, "court": court, "people": people})
                con.commit()
    flash(f"Court succesfully booked for {selected_date_str}", "success")

    con.close()

    return