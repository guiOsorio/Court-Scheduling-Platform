import sqlite3

from flask import flash
from helpers.funcs.actions.gets import getCurrDate
from werkzeug.security import check_password_hash




def deleteBookings(booking_id, user_id = None, selected_date = None, court = None):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Delete booking
    if booking_id:
        cur.execute("DELETE FROM bookings WHERE booking_id = :booking_id", {"booking_id": booking_id})
        con.commit()
        flash("Booking succesfully deleted", "success")
    elif user_id: 
        if not selected_date:
            cur.execute("DELETE FROM bookings WHERE user_id = :user_id", {"user_id": user_id})
            con.commit()
            flash("No more bookings for you", "success")
        else:
            current_date = getCurrDate()
            cur.execute("DELETE FROM bookings WHERE user_id = :user_id AND date = :selected_date AND date >= :current_date",
                        {"user_id": user_id, "selected_date": selected_date, "current_date": current_date})
            con.commit()
            flash(f"No more bookings for {selected_date}", "success")
    elif court:
        # delete every booking for the selected_date and court
        cur.execute("DELETE FROM bookings WHERE date = :date AND court = :court", {"date": selected_date, "court": court})
        con.commit()
    
    con.close()

    return

def deleteUserAccount(user_id, password):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Ensure password was submitted
    if not password:
        flash("Must have a password", "danger")
        return False

    # Check if password is valid
    cur.execute("SELECT hash FROM users WHERE id = :user_id", {"user_id": user_id})
    hash = cur.fetchone()[0]
    if not check_password_hash(hash, password):
        flash("Invalid password", "danger")
        return False
    
    # Delete all bookings for the account
    cur.execute("DELETE FROM bookings WHERE user_id = :user_id", {"user_id": user_id})
    con.commit()

    # Delete account
    cur.execute("DELETE FROM users WHERE id = :user_id", {"user_id": user_id})
    con.commit()

    con.close()

    return True
