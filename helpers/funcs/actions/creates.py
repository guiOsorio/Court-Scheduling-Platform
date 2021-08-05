import psycopg2 ###########

from werkzeug.security import generate_password_hash
from flask import flash
from helpers.variables.others import POSTGRE_URI #########
from helpers.funcs.others import showDateToUserFormat

con = psycopg2.connect(POSTGRE_URI)   #########

def createSchema():
    con = psycopg2.connect(POSTGRE_URI)
    with con:
        with con.cursor() as cur: 
            # cur.execute("DROP TABLE bookings")
            # con.commit()
            # cur.execute("DROP TABLE users")
            # con.commit()
            cur.execute("""CREATE TABLE users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(50) NOT NULL,
                            hash VARCHAR(255) NOT NULL,
                            email VARCHAR(50) NOT NULL,
                            type VARCHAR(20) DEFAULT 'user'
                        );""")
            con.commit()
            cur.execute("""CREATE TABLE bookings (
                            booking_id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            week_day VARCHAR(10) NOT NULL,
                            date DATE NOT NULL,
                            time VARCHAR(10) NOT NULL,
                            court INTEGER NOT NULL,
                            people INTEGER NOT NULL,
                            made_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        );""")
            con.commit()



def createIndex(columns, name, table):                          ############## FIGURE THIS OUT ON POSTGRES
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
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
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    selected_weekday = date.strftime("%A") # string current day of the week

    if people == "Not specified":
        cur.execute("""INSERT INTO bookings (user_id, week_day, date, time, court) 
                VALUES (%(user_id)s, %(week_day)s, %(date)s, %(time)s, %(court)s)""", 
                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court})
        con.commit()
    else:  
        cur.execute("""INSERT INTO bookings (user_id, week_day, date, time, court, people) 
                VALUES (%(user_id)s, %(week_day)s, %(date)s, %(time)s, %(court)s, %(people)s)""", 
                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date, "time": time, "court": court, "people": people})
        con.commit()
    

    flash("Booking successful!!", "success")

    con.close()

    return


def createUser(username):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # Get id of user who logged in to store in the session
    cur.execute("SELECT * FROM users WHERE username = %(username)s", {"username": username})
    id = cur.fetchone()[0]

    # Greet user
    flash(f"Welcome, {username} !!", "success")

    con.close()

    return id


# returns the newly created user's id
def createAccount(password, username, email, isAdmin = False):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    hashed_password = generate_password_hash(password) # hash 
    if isAdmin:
        type = "admin"
        cur.execute(""" INSERT INTO users (username, hash, email, type) VALUES (%(username)s, %(hashed_password)s, %(email)s, %(type)s) """,
                    {"username": username, "hashed_password": hashed_password, "email": email, "type": type})
        con.commit()
    else:
        cur.execute("INSERT INTO users (username, hash, email) VALUES (%(username)s, %(hash)s, %(email)s)", {"username": username, "hash": hashed_password, "email": email})
        con.commit()
    flash("Account successfully created!", "success")

    # Get id of user who logged in to store in the session
    cur.execute("SELECT * FROM users WHERE username = %(username)s", {"username": username})
    id = cur.fetchone()[0]

    con.close()

    return id


def bookAllDay(selected_weekday, possibletimesweekend, user_id, selected_date_str, court, people, possibletimes):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # use a for loop to make a booking for every possible time in the day for the selected court
    # (use array possibletimes for week days and possibletimesweekend if the selected_weekday is a weekend day)
    if selected_weekday == "Sat" or selected_weekday == "Sun":
        for time in possibletimesweekend:
            if time == "Choose a time":
                continue
            else:
                if people == "Not specified":
                    cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court) VALUES (%(user_id)s, %(week_day)s, %(date)s, %(time)s, %(court)s)",
                            {"user_id": user_id, "week_day": selected_weekday, "date": selected_date_str, "time": time, "court": court})
                    con.commit()
                else:
                    cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court, people) VALUES (%(user_id)s, %(week_day)s, %(date)s, %(time)s, %(court)s, %(people)s)",
                                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date_str, "time": time, "court": court, "people": people})
                    con.commit()
    else:
        for time in possibletimes:
            if time == "Choose a time":
                continue
            else:
                if people == "Not specified":
                    cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court) VALUES (%(user_id)s, %(week_day)s, %(date)s, %(time)s, %(court)s)",
                            {"user_id": user_id, "week_day": selected_weekday, "date": selected_date_str, "time": time, "court": court})
                    con.commit()
                else:
                    cur.execute("INSERT INTO bookings (user_id, week_day, date, time, court, people) VALUES (%(user_id)s, %(week_day)s, %(date)s, %(time)s, %(court)s, %(people)s)",
                                {"user_id": user_id, "week_day": selected_weekday, "date": selected_date_str, "time": time, "court": court, "people": people})
                    con.commit()
    selected_date_str_showuser = showDateToUserFormat(selected_date_str)
    flash(f"Court succesfully booked for {selected_date_str_showuser}", "success")

    con.close()

    return