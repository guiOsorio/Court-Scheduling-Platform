import psycopg2

from werkzeug.security import check_password_hash, generate_password_hash
from helpers.variables.others import POSTGRE_URI


def updateUserPassword(newpassword, user_id):
    # Connect to database
    con = psycopg2.connect(POSTGRE_URI)
    cur = con.cursor()

    # Generate a hash corresponding to the new password and update the users table to match it
    newhash = generate_password_hash(newpassword)
    cur.execute("UPDATE users SET hash = %(new_hash)s WHERE id = %(user_id)s", {"new_hash": newhash, "user_id": user_id})
    con.commit()

    con.close()

    return