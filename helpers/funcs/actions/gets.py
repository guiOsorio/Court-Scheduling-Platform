import sqlite3

from datetime import datetime

def getUserType(id):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    cur.execute("SELECT type FROM users WHERE id = :id", {"id": id})
    type = cur.fetchone()[0]

    con.close()

    return type


def getAllUsernames():
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Get all usernames
    cur.execute("SELECT username FROM users")
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
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # get number of upcoming bookings for the current user
    cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id = :user_id AND date >= :current_date", {"user_id": user_id, "current_date": current_date_str})
    upcoming_user_bookings = cur.fetchone()[0]

    con.close()

    return upcoming_user_bookings


def getUserBookingsData(user_id, selected_date, showAll = False):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    if showAll:
        current_date_str = getCurrDate()
        # Find all bookings for logged in user
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = :user_id AND date >= :current_date ORDER BY date, time""", {"user_id": user_id, "current_date": current_date_str})
        bookings_data = cur.fetchall()
    else:
        # Find bookings for logged in user for a specific date
        cur.execute(""" SELECT week_day, date, time, court, people, booking_id FROM bookings
                    WHERE user_id = :user_id AND date = :date ORDER BY time""", {"user_id": user_id, "date": selected_date})
        bookings_data = cur.fetchall()

    con.close()

    return bookings_data


def getBookingsData(court, selected_date):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Find upcoming bookings for that day if all courts option is provided
    if court == "All courts":
        cur.execute(""" SELECT username, week_day, date, time, court, people, booking_id FROM bookings
                    JOIN users ON user_id = id
                    WHERE date = :date ORDER BY time """, {"date": selected_date})
    else:
        cur.execute(""" SELECT username, week_day, date, time, court, people, booking_id FROM bookings
                    JOIN users ON user_id = id
                    WHERE date = :date AND court = :court ORDER BY time """, {"date": selected_date, "court": court})
    bookings_data = cur.fetchall() # populate data to display

    con.close()

    return bookings_data


def getDayBookingsCount(court, selected_date_str):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # if "All courts" option selected, show number of bookings for all courts
    if court == "All courts":
        cur.execute("SELECT COUNT(*) FROM bookings WHERE date = :date", {"date": selected_date_str})
        day_count = cur.fetchone()[0]
    # else, count number of bookings for the selected day and court
    else:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE date = :date AND court = :court", {"date": selected_date_str, "court": court})
        day_count = cur.fetchone()[0]

    con.close()

    return day_count

def getAllBookingsCount(input_range, court, current_time_str):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()
    
    isRangeValid = True
    # count number of all bookings based on input
    if input_range == "upcoming": # only count bookings for today and the future
        current_date_str = getCurrDate()
        if court == "All courts":
            cur.execute("SELECT COUNT(*) FROM bookings WHERE date >= :current_date AND time > :current_time",
                        {"current_date": current_date_str, "current_time": current_time_str})
        else:
            cur.execute("SELECT COUNT(*) FROM bookings WHERE date >= :current_date AND court = :court AND time > :current_time",
                        {"current_date": current_date_str, "court": court, "current_time": current_time_str})
    elif input_range == "total": # count all bookings regardless of date
        if court == "All courts":
            cur.execute("SELECT COUNT(*) FROM bookings")
        else:
            cur.execute("SELECT COUNT(*) FROM bookings WHERE court = :court", {"court": court})
    else:
        isRangeValid = False

    total_count = cur.fetchone()[0]
    return_data = [isRangeValid, total_count]

    con.close()

    return return_data


def getUserEmail(user_id):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    cur.execute("SELECT email FROM users WHERE id = :id", {"id": user_id})
    email = cur.fetchone()[0]

    con.close()

    return email


def getBookingInfo(booking_id):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    cur.execute("SELECT court, date, time FROM bookings WHERE booking_id = :booking_id", {"booking_id": booking_id})
    booking_info = cur.fetchall()

    con.close()

    return booking_info


def getUserId(booking_id):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    cur.execute("SELECT id FROM users JOIN bookings ON id = user_id WHERE booking_id = :booking_id", {"booking_id": booking_id})
    id = cur.fetchone()[0]

    con.close()

    return id
