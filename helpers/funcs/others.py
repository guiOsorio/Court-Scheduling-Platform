import sqlite3

from helpers.funcs.actions.gets import getCurrDate
from flask import flash
from werkzeug.security import check_password_hash


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
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Find user's hash
    cur.execute("SELECT hash FROM users WHERE id = :user_id", {"user_id": user_id})
    hash = cur.fetchone()[0]

    if not check_password_hash(hash, password):
        flash("Incorrect password", "danger")
        return False

    con.close()

    return True