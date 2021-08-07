# AWS Lambda
# send admins an email with all the bookings for the day
# execute this function every day at 8 am
import os
import psycopg2
import smtplib
import datetime as dt

from datetime import datetime
from email.message import EmailMessage


# Function to return a list of strings to represent the time options for a certain club
def getRegPossibleTimes(opening, close):
    possibletimes = ["Choose a time"]

    for i in range(opening, close):
        if i < 10:
            t = dt.time(i, 0)
            possibletimes.append("0{}:{}0".format(t.hour, t.minute))
            t2 = dt.time(i, 30)
            possibletimes.append("0{}:{}".format(t2.hour, t2.minute))
        else:
            t = dt.time(i, 0)
            possibletimes.append("{}:{}0".format(t.hour, t.minute))
            t2 = dt.time(i, 30)
            possibletimes.append("{}:{}".format(t2.hour, t2.minute))
    return possibletimes

# Function which returns a list of all the courts from a club, all options set to true adds "All courts" entry to the list
def getRegCourts(numofcourts, all = False):
    courts = []
    for i in range(1, numofcourts + 1):
        courts.append(str(i))
    if all:
        courts.append("All courts")
    return courts

courts = getRegCourts(3)
possibletimes = getRegPossibleTimes(9, 22)
possibletimesweekend = getRegPossibleTimes(9, 20)



def isWeekend(day): # accepts a datetime argument
    current_week_day = day.strftime("%A")
    weekend_days = ['Saturday', 'Sunday']

    if current_week_day in weekend_days:
        return True
    else:
        return False

def getTableData(current_date_str, courts, possibletimes, possibletimesweekend, weekend):
    courts_dict = dict.fromkeys(courts)
    fields = ["username"]

    con = psycopg2.connect(POSTGRE_URI) # make a system variable on AWS Lambda
    cur = con.cursor()

    if weekend:
        i = 0
        for court in courts_dict:
            courts_dict[courts[i]] = dict.fromkeys(possibletimesweekend)
            for time in possibletimesweekend:
                courts_dict[courts[i]][time] = dict.fromkeys(fields)
            i += 1

        # get bookings where date = current_date
        cur.execute("SELECT booking_id FROM bookings WHERE date = %(current_date_str)s", {"current_date_str": current_date_str})
        day_bookings_queryresult = cur.fetchall()
        day_bookings = ()
        for booking in day_bookings_queryresult:
            day_bookings = day_bookings + (booking[0],)
        # get info from bookings for the day
        daytime_dict = dict.fromkeys(possibletimesweekend[1:]) # day_dict is a dict of dicts (dict[time]['username', 'time', 'court']) with all times in possibletimesweekend
        i = 0
        for time in possibletimesweekend:
            daytime_dict[possibletimesweekend[i]] = dict.fromkeys(["username"])
            i += 1

        if day_bookings:
            # get the relevant data from the day's bookings
            cur.execute("SELECT username, time, court FROM bookings JOIN users ON user_id = id WHERE booking_id IN %(day_bookings)s ORDER BY time, court", {"day_bookings": day_bookings})
            day_info = cur.fetchall()

            for info in day_info:
                info_court = str(info[2])
                time = info[1]
                courts_dict[info_court][time]["username"] = info[0]
        con.close()
    
    else: # not a weekend day
        i = 0
        for court in courts_dict:
            courts_dict[courts[i]] = dict.fromkeys(possibletimes)
            for time in possibletimes:
                courts_dict[courts[i]][time] = dict.fromkeys(fields)
            i += 1

        # get bookings where date = current_date
        cur.execute("SELECT booking_id FROM bookings WHERE date = %(current_date_str)s", {"current_date_str": current_date_str})
        day_bookings_queryresult = cur.fetchall()
        day_bookings = ()
        for booking in day_bookings_queryresult:
            day_bookings = day_bookings + (booking[0],)
        # get info from bookings for the day
        daytime_dict = dict.fromkeys(possibletimes[1:]) # day_dict is a dict of dicts (dict[time]['username', 'time', 'court']) with all times in possibletimes
        i = 0
        for time in possibletimes:
            daytime_dict[possibletimes[i]] = dict.fromkeys(["username"])
            i += 1

        if day_bookings:
            # get the relevant data from the day's bookings
            cur.execute("SELECT username, time, court FROM bookings JOIN users ON user_id = id WHERE booking_id IN %(day_bookings)s ORDER BY time, court", {"day_bookings": day_bookings})
            day_info = cur.fetchall()

            for info in day_info:
                info_court = str(info[2])
                time = info[1]
                courts_dict[info_court][time]["username"] = info[0]
        con.close()
    
    return courts_dict

def lambda_handler(event, context):
    # get current date as string ("%Y"-"%m"-"%-d")
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")

    if isWeekend(current_date):
        courts_dict = getTableData(current_date_str, courts, possibletimes, possibletimesweekend, True)
        halflengthpt = int(len(possibletimesweekend) / 2) + 1
    else: # today is not a weekend day
        courts_dict = getTableData(current_date_str, courts, possibletimes, possibletimesweekend, False) 
        halflengthpt = int(len(possibletimes) / 2) + 1
    
    # From today.html, form a string to mark the html to be sent on msg

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

