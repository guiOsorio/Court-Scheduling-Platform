# AWS Lambda
# if a user has a booking in the next hour, send him an email
# execute this function every hour of every day from 8 am to 8 pm (hour 20)
import os
import psycopg2
import smtplib

from datetime import datetime
from email.message import EmailMessage

# Store program's name
appname = "Scheduling"
path_to_site = "#"

# Store links to show at the end of emails
link_to_site = f'<p>Visit us at <a href="{path_to_site}">{appname}.com</a></p>'

def lambda_handler(event, context):
    # Connect to database
    con = psycopg2.connect('postgres://sdekffai:EQWNHQ8WqiTemvmwSEfhewB9Gq6ACsfE@kashin.db.elephantsql.com/sdekffai')
    cur = con.cursor()

    # Get current date as string ("%Y"-"%m"-"%-d")
    curr_date = datetime.now()
    curr_date_str = curr_date.strftime("%Y-%m-%d")
    # Get current hour of the day as string (if hour is < 10, add a zero in the beginning, else just get the hour)
    curr_hour = curr_date.strftime("%H")
    next_hour = int(curr_hour) + 1
    next_hour_str = str(next_hour)
    if len(next_hour_str) == 1:
        next_hour_str = "0" + next_hour_str
    # Get bookings where date = current_date and time like current_hour
    cur.execute("SELECT booking_id FROM bookings WHERE date = %(curr_date)s AND time LIKE %(curr_hour)s", {"curr_date": curr_date_str, "curr_hour": f'{next_hour_str}%'})
    bookings_qresult = cur.fetchall()
    bookings = []
    # Populate bookings list to have the booking ids of all bookings in the next hour
    for booking in bookings_qresult:
        bookings.append(booking[0])
    # Get users associated with the bookings
    cur.execute("SELECT id FROM users JOIN bookings ON id = user_id WHERE booking_id IN %(bookings)s", {"bookings": tuple(bookings)})
    ids_qresult = cur.fetchall()
    ids = [] # store the unique identifier for the user
    for id in ids_qresult:
        if id[0] not in ids:
            ids.append(id[0]) # populate ids list with the id for each user with a booking in the next hour
    # For every user associated with a booking, send its specific info (only send the user the info for their own booking - get email, time, court)
    info_qresult = []
    # Populate list to have an email, time, and court for each booking in the next hour
    for id in ids:
        cur.execute("SELECT email, time, court, username FROM users JOIN bookings ON id = user_id WHERE id = %(id)s AND booking_id IN %(bookings)s", {"id": id, "bookings": tuple(bookings)})
        info_qresult.append(cur.fetchall()[0])
    # Write HTML to send in email
    for info in info_qresult:
        msg_html = f"""<div class='notify-user'>
                        <p>Dear {info[3]}, we are sending you this email as a reminder of your booking for <strong>court {info[2]} at {info[1]} today.</strong></p>
                        <p>We are excited to welcome you to our facilities and hope you have a great time!</p>
                    </div>"""
        msg_html += link_to_site
        # Get email address to send to
        email = info[0]
        # Configure email settings
        MAIL_ADDRESS = os.environ.get('MAIL_USERNAME')
        MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
        MAIL_TO = [email]

        msg = EmailMessage()
        msg['Subject'] = f'{appname} - A Quick Reminder'
        msg['From'] = MAIL_ADDRESS
        msg['To'] = MAIL_TO

        msg.add_header('Content-Type','text/html')
        msg.set_payload(msg_html)

        # Send email 
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)
            smtp.send_message(msg) 