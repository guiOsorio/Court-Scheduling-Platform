# AWS Lambda
# if a user has a booking in the next hour, send him an email
# execute this function every hour of every day from 8 am to 8 pm (hour 20)
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
    curr_date = datetime.now()
    curr_date_str = curr_date.strftime("%Y-%m-%d")
    # get current hour of the day as string (if hour is < 10, add a zero in the beginning, else just get the hour)
    curr_hour = curr_date.strftime("%H")
    # get bookings where date = current_date and time like current_hour
    cur.execute("SELECT booking_id FROM bookings WHERE date = %(curr_date)s AND time = %(curr_hour)s", {"curr_date": curr_date_str, "curr_hour": curr_hour})
    bookings = cur.fetchall()
    # get users associated with the bookings
    # for every user associated with a booking, send its specific info (only send the user the info for their own booking) 

    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    MAIL_TO = os.environ.get('MAIL_TO')

    msg = EmailMessage()
    msg['Subject'] = 'Your dog of the day!'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = [MAIL_TO]

    msg.set_content(f"Have a great day :)!\n{dog_image_url}")
    msg.add_alternative(f'Here is a dog image to cheer you up<br><br><img src="{dog_image_url}" width="300px"><br><br>Have a great day :)', subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)