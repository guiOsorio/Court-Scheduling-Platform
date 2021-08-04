import psycopg2

from helpers.funcs.actions.gets import getCurrDate
from flask import flash
from werkzeug.security import check_password_hash
from helpers.variables.others import POSTGRE_URI


def isDatePast(selected_date_str):
    # check if date is not in the past
    current_date_str = getCurrDate()

    if selected_date_str < current_date_str:
        flash("Invalid date", "danger")
        return True
    else:
        return False

def passwordEqualsHash(user_id, password):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # Find user's hash
    cur.execute("SELECT hash FROM users WHERE id = %(user_id)s", {"user_id": user_id})
    hash = cur.fetchone()[0]

    if not check_password_hash(hash, password):
        flash("Incorrect password", "danger")
        return False

    con.close()

    return True


def doesBookingIdExist(booking_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    booking_id = int(booking_id)
    # Check if booking id exists
    cur.execute("SELECT booking_id FROM bookings")
    allbookings = cur.fetchall()
    tracker = False # if corresponding booking_id is found, set tracker to True
    for booking in allbookings:
        if booking[0] == booking_id:
            tracker = True
            break
        else:
            continue
    if not tracker:
        flash(f"Invalid booking id", "danger")
        return False
    else:
        return True