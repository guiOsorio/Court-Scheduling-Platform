# AWS Lambda
# send admins an email with all the bookings for the day
# execute this function every day at 8 am
# https://www.youtube.com/watch?v=aqnJvXOIr6

import os
import psycopg2
import smtplib
import datetime as dt

from datetime import datetime
from email.message import EmailMessage

# Store program's name
appname = "Scheduling"
path_to_site = "#"

# Store links to show at the end of emails
link_to_site = f'<p>Visit us at <a href="{path_to_site}">{appname}.com</a></p>'
link_to_this_page = f'<p>Visit this page at <a href="{path_to_site}/today">{appname}.com</a></p>'

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

    con = psycopg2.connect(os.environ.get('POSTGRE_URI')) # make a system variable on AWS Lambda
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

# From today.html, form a string to mark the html to be sent on msg
def getAdminEmailHTML(court, current_date, thirdlengthpt, courts_dict):
    court_msg = f"""<div class='court-times' style='border: 1px solid #777; text-align: center; margin-bottom: 20px; overflow-x: auto;'>
                        <h1>Court {court}</h1>
                        
                        <table style='font-size: 18px; margin: 0 auto;'>
                            <thead>
                                <tr style='padding: 7px 15px;'>
                                    """
    if isWeekend(current_date):
        for time in possibletimesweekend[1:thirdlengthpt]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 20px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 7px 15px;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[1:thirdlengthpt]:
                if courts_dict[court][time]["username"]:
                    if len(courts_dict[court][time]["username"]) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 18px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 7px 15px;'>"""
        for time in possibletimesweekend[thirdlengthpt:thirdlengthpt*2-1]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 20px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 7px 15px;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[thirdlengthpt:thirdlengthpt*2-1]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """<table style='font-size: 18px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 7px 15px;'>"""
        for time in possibletimesweekend[thirdlengthpt*2-1:thirdlengthpt*3]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 20px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 7px 15px;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[thirdlengthpt*2-1:thirdlengthpt*3]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
            </div>"""
    else:
        for time in possibletimes[1:thirdlengthpt]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 20px;'>{time}</th>"
        court_msg += "</tr><tr>"
        for time in courts_dict[court]:
            if time in possibletimes[1:thirdlengthpt]:
                if courts_dict[court][time]["username"]:
                    if len(courts_dict[court][time]["username"]) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 18px; margin: 0 auto;'>
                    <thead>
                        <tr>"""
        for time in possibletimes[thirdlengthpt:thirdlengthpt*2-1]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 20px;'>{time}</th>"
        court_msg += "</tr><tr>"
        for time in courts_dict[court]:
            if time in possibletimes[thirdlengthpt:thirdlengthpt*2-1]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}..</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """<table style='font-size: 18px; margin: 0 auto;'>
                    <thead>
                        <tr>"""
        for time in possibletimes[thirdlengthpt*2-1:thirdlengthpt*3]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 20px;'>{time}</th>"
        court_msg += "</tr><tr>"
        for time in courts_dict[court]:
            if time in possibletimes[thirdlengthpt*2-1:thirdlengthpt*3]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}..</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
            </div>"""
    return court_msg


def getResponsiveAdminEmailHTML(court, current_date, fifthlengthpt, courts_dict):
    court_msg = f"""<div class='court-times' style='border: 1px solid #777; text-align: center; margin-bottom: 20px; overflow-x: auto;'>
                        <h1>Court {court}</h1>
                        
                        <table style='font-size: 10px; margin: 0 auto;'>
                            <thead>
                                <tr style='padding: 4px 10px;'>
                                    """
    if isWeekend(current_date):
        for time in possibletimesweekend[1:fifthlengthpt]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[1:fifthlengthpt+1]:
                if courts_dict[court][time]["username"]:
                    if len(courts_dict[court][time]["username"]) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimesweekend[fifthlengthpt+1:fifthlengthpt*2]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[fifthlengthpt+1:fifthlengthpt*2]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimesweekend[fifthlengthpt*2:fifthlengthpt*3-1]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[fifthlengthpt*2:fifthlengthpt*3-1]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimesweekend[fifthlengthpt*3-1:fifthlengthpt*4-2]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[fifthlengthpt*3-1:fifthlengthpt*4-2]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimesweekend[fifthlengthpt*4-2:fifthlengthpt*5]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimesweekend[fifthlengthpt*4-2:fifthlengthpt*5]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
            </div>"""
    else:
        for time in possibletimes[1:fifthlengthpt+1]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimes[1:fifthlengthpt+1]:
                if courts_dict[court][time]["username"]:
                    if len(courts_dict[court][time]["username"]) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimes[fifthlengthpt+1:fifthlengthpt*2]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimes[fifthlengthpt+1:fifthlengthpt*2]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}..</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimes[fifthlengthpt*2:fifthlengthpt*3-1]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimes[fifthlengthpt*2:fifthlengthpt*3-1]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}..</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimes[fifthlengthpt*3-1:fifthlengthpt*4-2]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimes[fifthlengthpt*3-1:fifthlengthpt*4-2]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}..</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>"""
        court_msg += """</tr>
                    </thead>
                </table>
                <table style='font-size: 10px; margin: 0 auto;'>
                    <thead>
                        <tr style='padding: 4px 10px;'>"""
        for time in possibletimes[fifthlengthpt*4-2:fifthlengthpt*5]:
            if time != 'Choose a time':
                court_msg += f"<th style='padding: 0 10px;'>{time}</th>"
        court_msg += "</tr><tr style='padding: 4px 10px; text-align: center;'>"
        for time in courts_dict[court]:
            if time in possibletimes[fifthlengthpt*4-2:fifthlengthpt*5]:
                if courts_dict[court][time]['username']:
                    if len(courts_dict[court][time]['username']) > 6:
                        court_msg += f"<td>{courts_dict[court][time]['username'][:5]}..</td>"
                    else:
                        court_msg += f"<td>{courts_dict[court][time]['username']}..</td>"
                else:
                    court_msg += "<td> - </td>"
        court_msg += """</tr>
                    </thead>
                </table>
            </div>"""
    return court_msg

def getAllAdminsEmails():
    con = psycopg2.connect(os.environ.get('POSTGRE_URI')) # make a system variable on AWS Lambda
    cur = con.cursor()

    cur.execute("SELECT email FROM users WHERE type = 'admin'")
    admins = cur.fetchall()

    return admins

def lambda_handler(event, context):
    # Get data to send to admin
    # get current date as string ("%Y"-"%m"-"%-d")
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")
    thirdlengthpt = 0
    fifthlengthpt = 0
    if isWeekend(current_date):
        courts_dict = getTableData(current_date_str, courts, possibletimes, possibletimesweekend, True)
        thirdlengthpt = int(len(possibletimesweekend) / 3) + 1
        fifthlengthpt = int(len(possibletimesweekend) / 4) + 1
    else: # today is not a weekend day
        courts_dict = getTableData(current_date_str, courts, possibletimes, possibletimesweekend, False) 
        thirdlengthpt = int(len(possibletimes) / 3) + 1
        fifthlengthpt = int(len(possibletimes) / 5) + 1

    courts_msg_list = []

    # Get HTML to be on the email
    for court in courts_dict:
        court_msg = getAdminEmailHTML(court, current_date, thirdlengthpt, courts_dict)
        courts_msg_list.append(court_msg)
    courts_msg = ""
    for message in courts_msg_list:
        courts_msg += message
    courts_msg += link_to_site + link_to_this_page

    
    # Get info for email

    # get the email for all admins
    admins_emails = getAllAdminsEmails()

    MAIL_ADDRESS = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_TO = []
    for admin in admins_emails:
        MAIL_TO.append(admin[0])

    msg = EmailMessage()
    current_date_str_tosend = current_date.strftime("%m-%d-%Y")
    msg['Subject'] = f'{appname} - Bookings for {current_date_str_tosend}'
    msg['From'] = MAIL_ADDRESS
    msg['To'] = MAIL_TO

    msg.add_header('Content-Type','text/html')
    msg.set_payload(courts_msg)
    

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)
        smtp.send_message(msg) 

    courts_msg_list_responsive = []

    for court in courts_dict:
        court_msg_responsive = getResponsiveAdminEmailHTML(court, current_date, fifthlengthpt, courts_dict)
        courts_msg_list_responsive.append(court_msg_responsive)
    courts_msg_responsive = ""
    for message in courts_msg_list_responsive:
        courts_msg_responsive += message
    courts_msg_responsive += link_to_site + link_to_this_page
    

    msg_responsive = EmailMessage()
    msg_responsive['Subject'] = f'{appname} - Bookings for {current_date_str_tosend} (MOBILE)'
    msg_responsive['From'] = MAIL_ADDRESS
    msg_responsive['To'] = MAIL_TO

    msg_responsive.add_header('Content-Type','text/html')
    msg_responsive.set_payload(courts_msg_responsive)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)
        smtp.send_message(msg_responsive) 


# {% for court in cd %}

# <div class="court-times">
#     <h3>Court {{ court }}</h3>
    
#     <table>
#         <thead>
#             <tr>
#                 {% for time in pt[1:hlenpt] %}
#                     {% if time != 'Choose a time' %}
#                         <th>{{ time }}</th>
#                     {% endif %}
#                 {% endfor %}
#             </tr>
#             <tr>
#                 {% for time in cd[court] %}
#                     {% if time in pt[1:hlenpt] %}
#                         {% if cd[court][time]["username"] %}
#                             {% if cd[court][time]["username"]|length > 8 %}
#                                 <td>{{ cd[court][time]["username"][:7] }}..</td>
#                             {% else %}
#                                 <td>{{ cd[court][time]["username"] }}</td>
#                             {% endif %}
#                         {% else %}
#                             <td> - </td>
#                         {% endif %}
#                     {% endif %}
#                 {% endfor %}
#             </tr>
#         </thead>
#     </table>
    
#     <table>
#         <thead>
#             <tr>
#                 {% for time in pt[hlenpt:] %}
#                     {% if time != 'Choose a time' %}
#                         <th>{{ time }}</th>
#                     {% endif %}
#                 {% endfor %}
#             </tr>
#             <tr>
#                 {% for time in cd[court] %}
#                     {% if time in pt[hlenpt:] %}
#                         {% if cd[court][time]["username"] %}
#                             {% if cd[court][time]["username"]|length > 8 %}
#                                 <td>{{ cd[court][time]["username"][:7] }}..</td>
#                             {% else %}
#                                 <td>{{ cd[court][time]["username"] }}</td>
#                             {% endif %}
#                         {% else %}
#                             <td> - </td>
#                         {% endif %}
#                     {% endif %}
#                 {% endfor %}
#             </tr>
#         </thead>
#     </table>
# </div>

# {% endfor %}

# <style>
#     .court-times {
#         border: 1px solid #777;
#         text-align: center;
#         margin-bottom: 20px;
#         overflow-x: auto;
#     }
#     table {
#         font-size: 18px;
#         margin: 0 auto;
#     }
#     tr * {
#         padding: 7px 15px;
#     }

#     @media (max-width: 600px) {
#         table {
#             font-size: 10px;
#         }
#         tr * {
#             padding: 4px 10px;
#         }
#     }
# </style>


