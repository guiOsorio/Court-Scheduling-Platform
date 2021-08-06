# TODO (check testing.py, stack overflow own question, app.py /test, copy() and deepcopy() and retry this function)








# AWS Lambda
# send admins an email with all the bookings for the day
# execute this function every day at 8 am
import os
import psycopg2
import smtplib

from datetime import datetime
from email.message import EmailMessage

def lambda_handler(event, context):
    # Connect to database
    con = psycopg2.connect(os.environ.get('POSTGRE_URI'))
    cur = con.cursor()

    # get current date as string ("%Y"-"%m"-"%-d")
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")

    # get bookings where date = current_date
    cur.execute("SELECT booking_id FROM bookings WHERE date = %(current_date_str)s", {"current_date_str": current_date_str})
    day_bookings = cur.fetchall()
    # get info from bookings for the day
    day_bookings_info = dict.fromkeys(["username", "time", "court"])
    cur.execute("SELECT username, time, court FROM bookings JOIN users ON user_id = id WHERE booking_id IN %(day_bookings)s", {"day_bookings": day_bookings})

    # get accounts where type = 'admin'
    cur.execute("SELECT id FROM users WHERE type = 'admin'")
    admins = cur.fetchall()
    # send email with booking_info on a table of all bookings for the day

    MAIL_ADDRESS = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_TO = os.environ.get('MAIL_TO')

    msg = EmailMessage()
    msg['Subject'] = 'Your dog of the day!'
    msg['From'] = MAIL_ADDRESS
    msg['To'] = [MAIL_TO]

    msg.set_content(f"Have a great day :)!\n{dog_image_url}")
    msg.add_alternative(f'Here is a dog image to cheer you up<br><br><img src="{dog_image_url}" width="300px"><br><br>Have a great day :)', subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)
        smtp.send_message(msg)
