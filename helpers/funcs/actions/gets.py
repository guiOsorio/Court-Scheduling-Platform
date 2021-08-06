import psycopg2
import datetime as dt

from datetime import datetime
from helpers.variables.others import POSTGRE_URI

def getUserType(id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT type FROM users WHERE id = %(id)s;", {"id": id})
    type = cur.fetchone()[0]

    con.close()

    return type


def getAllUsernames():
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # Get all usernames
    cur.execute("SELECT username FROM users;")
    usernames = cur.fetchall()

    con.close()

    return usernames


def getCurrDate():
    # current_date in same format as added to db (string and %Y-%m-%d)
    current_date = datetime.now()
    return current_date.strftime("%Y-%m-%d")

def getCurrTime():
    return datetime.now().strftime("%H:%M") # string


def getUpcomingUserBookings(user_id, current_date_str):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # get number of upcoming bookings for the current user
    cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id = %(user_id)s AND date >= %(current_date)s;", {"user_id": user_id, "current_date": current_date_str})
    upcoming_user_bookings = cur.fetchone()[0]

    con.close()

    return upcoming_user_bookings


def getUserBookingsData(user_id, selected_date, showAll = False):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    if showAll:
        current_date_str = getCurrDate()
        # Find all bookings for logged in user
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = %(user_id)s AND date >= %(current_date)s ORDER BY date, time;""", {"user_id": user_id, "current_date": current_date_str})
        bookings_data = cur.fetchall()
    else:
        # Find bookings for logged in user for a specific date
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = %(user_id)s AND date = %(date)s ORDER BY time;""", {"user_id": user_id, "date": selected_date})
        bookings_data = cur.fetchall()

    con.close()

    return bookings_data


def getBookingsData(court, selected_date):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # Find upcoming bookings for that day if all courts option is provided
    if court == "All courts":
        cur.execute(""" SELECT username, week_day, date, time, court, people, booking_id FROM bookings
                    JOIN users ON user_id = id
                    WHERE date = %(date)s ORDER BY time; """, {"date": selected_date})
    else:
        cur.execute(""" SELECT username, week_day, date, time, court, people, booking_id FROM bookings
                    JOIN users ON user_id = id
                    WHERE date = %(date)s AND court = %(court)s ORDER BY time; """, {"date": selected_date, "court": court})
    bookings_data = cur.fetchall() # populate data to display

    con.close()

    return bookings_data


def getDayBookingsCount(court, selected_date_str):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # if "All courts" option selected, show number of bookings for all courts
    if court == "All courts":
        cur.execute("SELECT COUNT(*) FROM bookings WHERE date = %(date)s;", {"date": selected_date_str})
        day_count = cur.fetchone()[0]
    # else, count number of bookings for the selected day and court
    else:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE date = %(date)s AND court = %(court)s;", {"date": selected_date_str, "court": court})
        day_count = cur.fetchone()[0]

    con.close()

    return day_count

def getAllBookingsCount(input_range, court, current_time_str):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()
    
    isRangeValid = True
    # count number of all bookings based on input
    if input_range == "upcoming": # only count bookings for today and the future
        current_date_str = getCurrDate()
        if court == "All courts":
            cur.execute("SELECT COUNT(*) FROM bookings WHERE date > %(current_date)s;", {"current_date": current_date_str})
            total_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM bookings WHERE date = %(current_date)s AND time > %(current_time)s;", {"current_date": current_date_str, "current_time": current_time_str})
            total_count += cur.fetchone()[0]
        else:
            cur.execute("SELECT COUNT(*) FROM bookings WHERE date > %(current_date)s AND court = %(court)s;", {"current_date": current_date_str, "court": court})
            total_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM bookings WHERE date = %(current_date)s AND court = %(court)s AND time > %(current_time)s;",
                        {"current_date": current_date_str, "court": court, "current_time": current_time_str})
            total_count += cur.fetchone()[0]
    elif input_range == "total": # count all bookings regardless of date
        if court == "All courts":
            cur.execute("SELECT COUNT(*) FROM bookings")
            total_count = cur.fetchone()[0]
        else:
            cur.execute("SELECT COUNT(*) FROM bookings WHERE court = %(court)s;", {"court": court})
            total_count = cur.fetchone()[0]
    else:
        isRangeValid = False

    return_data = [isRangeValid, total_count]

    con.close()

    return return_data


def getUserEmail(user_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT email FROM users WHERE id = %(id)s;", {"id": user_id})
    email = cur.fetchone()[0]

    con.close()

    return email


def getBookingInfo(booking_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT court, date, time FROM bookings WHERE booking_id = %(booking_id)s;", {"booking_id": booking_id})
    booking_info = cur.fetchall()

    con.close()

    return booking_info


def getUserId(booking_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT id FROM users JOIN bookings ON id = user_id WHERE booking_id = %(booking_id)s;", {"booking_id": booking_id})
    id = cur.fetchone()[0]

    con.close()

    return id


def getBookingId(court, selected_date, time):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT booking_id FROM bookings WHERE court = %(court)s AND date = %(selected_date)s AND time = %(time)s;",
                {"court": court, "selected_date": selected_date, "time": time})
    booking_id = cur.fetchone()[0]

    con.close()

    return booking_id


def getUsername(user_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT username FROM users WHERE id = %(user_id)s;", {"user_id": user_id})
    username = cur.fetchone()[0]

    con.close()

    return username


# Function to return a list of strings to represent the time options for a certain club
def getRegPossibleTimes(opening, close):
    possibletimes = ["Choose a time"]

    for i in range(opening, close):
        if i < 10:
            t = dt.time(i, 0)
            possibletimes.append("0{}:{}0".format(t.hour, t.minute))
            if i != close - 1: # for the last hour, only have a booking starting at :00, none at :30
                t2 = dt.time(i, 30)
                possibletimes.append("0{}:{}".format(t2.hour, t2.minute))
        else:
            t = dt.time(i, 0)
            possibletimes.append("{}:{}0".format(t.hour, t.minute))
            if i != close - 1: # for the last hour, only have a booking starting at :00, none at :30
                t2 = dt.time(i, 30)
                possibletimes.append("{}:{}".format(t2.hour, t2.minute))
    return possibletimes

# Function which returns a list of all the courts from a club, all options set to true adds "All courts" entry to the list
def getRegCourts(numofcourts, all = False):
    courts = []
    for i in range(1, numofcourts + 1):
        courts.append(str(i))
    if all:
        courts.append("All courts")
    return courts

def getPrevTime(time):
    if time[3:5] == "00":
        # Get the previous hour
        currhour = int(time[0:2])
        prevhour = str(currhour - 1)
        # Add a 0 to the start of the prevhour string to match the possibletimes array
        if int(prevhour) < 10:
            prevhour = "0" + prevhour
        prevtime = prevhour + ":30"
    elif time[3:5] == "30":
        prevtime = time[0:3] + "00"
    
    return prevtime


def getNextTime(time):
    if time[3:5] == "00":
        nexttime = time[0:3] + "30"
    elif time[3:5] == "30":
        # Get the next hour
        currhour = int(time[0:2])
        nexthour = str(currhour + 1)
        # Add a 0 to the start of the nexthour string to match the possibletimes array
        if int(nexthour) < 10:
            nexthour = "0" + nexthour
        nexttime = nexthour + ":00"
    
    return nexttime

def getUserAccountData(user_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    cur.execute("SELECT username, email, type FROM users WHERE id = %(user_id)s;", {"user_id": user_id})
    data = cur.fetchone()

    con.close()

    return data