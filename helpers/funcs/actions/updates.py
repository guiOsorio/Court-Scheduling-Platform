import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash


def updateUserPassword(newpassword, user_id):
    # Connect to database
    con = sqlite3.connect("scheduling.db")
    cur = con.cursor()

    # Generate a hash corresponding to the new password and update the users table to match it
    newhash = generate_password_hash(newpassword)
    cur.execute("UPDATE users SET hash = :new_hash WHERE id = :user_id", {"new_hash": newhash, "user_id": user_id})
    con.commit()

    con.close()

    return