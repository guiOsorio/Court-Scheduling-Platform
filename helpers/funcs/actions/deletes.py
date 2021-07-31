import sqlite3

from flask import flash
from helpers.funcs.actions.gets import getCurrDate



def deleteBookings(booking_id, user_id = None, selected_date = None, court = None):
    # Connect to database
    con = sqlite3.connect("scheduling.db", check_same_thread=False)
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
