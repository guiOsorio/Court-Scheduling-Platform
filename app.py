import os
import psycopg2

from flask import Flask, flash, redirect, render_template, session, request
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import SelectField
from datetime import datetime
from flask_mail import Mail, Message
# Own helper funcs
from helpers.funcs.actions.creates import createSchema, createIndex, createBooking, createUser, createAccount, bookAllDay
from helpers.funcs.actions.deletes import deleteBooking, deleteUserDayBookings, deleteAllUserBookings, deleteAllDayBookings, deleteUserAccount
from helpers.funcs.actions.gets import getDayBookingsCount, getUserType, getAllUsernames, getCurrDate, getCurrTime, getUpcomingUserBookings, getUserBookingsData, \
    getBookingsData, getDayBookingsCount, getAllBookingsCount, getUserEmail, getBookingInfo, getUserId, getBookingId, getUsername, getUserAccountData, \
    getTableData, getAllBookedHoursInfo
from helpers.funcs.actions.updates import updateUserPassword, updateUserEmail
from helpers.funcs.others import isDatePast, isWeekend, passwordEqualsHash, doesBookingIdExist, showDateToUserFormat
from helpers.funcs.validations import validateBooking, validateLogin, validateEmail, validateRegistration, validateIndex, validateDate, validatePassword
from helpers.funcs.requireds import login_required, admin_required, not_logged_in
# Own helper variables
from helpers.variables.lists import numofpeople, courts, courts_all, possibletimes, possibletimesweekend
from helpers.variables.others import ADMIN_SECRET_PASSWORD, appname, link_to_site

# Initialize app
app = Flask(__name__)

# Configure for flask_wtf
app.config["SECRET_KEY"] = "secret"

# If schema already exists, move on with the program
# try:
#     createSchema()
# except psycopg2.errors.DuplicateTable:
#     pass

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure flask_mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
mail = Mail(app)

# FLASK-WTF FORMS
# Booking form
class BookingForm(FlaskForm):
    people = SelectField('Number of people', choices=numofpeople)
    court = SelectField('Court', choices=courts)
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())
    time = SelectField('Time', choices=possibletimes, default="Choose a time")

# Check bookings form
class CheckBookingsForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())

# Admin book a court for a day form
class CourtDateForm(FlaskForm):
    court = SelectField('Court', choices=courts_all)
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())

# Function to send an email
def sendEmail(title, text, recipient):
    msg = Message(title, recipients=[recipient])
    msg.html = text + link_to_site
    mail.send(msg)
    return


#  ----------------------------------------------------------------------------------ROUTES--------------------------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")


@app.route("/makebooking", methods=["GET", "POST"])
@login_required
def makebooking():

    # Initialize form
    form = BookingForm()

    # if request is POST and form fields are validated
    if form.validate_on_submit():
        user_id = session["user_id"] # store current user's id
        people = form.people.data # string
        court = form.court.data # string
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string
        time = form.time.data # string

        if validateBooking(people, court, date, time, numofpeople, courts, possibletimesweekend, possibletimes, user_id):

            createBooking(date, user_id, selected_date, time, court, people)

            selected_date_showuser = showDateToUserFormat(selected_date)
            title = f"{appname} - Booking created"
            text = f"<p>A booking for court {court} at {time} on {selected_date_showuser} was created for you.</p>"
            recipient = getUserEmail(user_id)
            sendEmail(title, text, recipient)

            return redirect("/makebooking")
    
    booked_hours_info = getAllBookedHoursInfo()

    return render_template("makebooking.html", form=form, pts=possibletimes, ptsw=possibletimesweekend, bhs=booked_hours_info)



@app.route("/login", methods=["GET", "POST"])
@not_logged_in
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        next_url = request.form.get("next")

        if not validateLogin(username, password):
            return redirect(request.referrer)
        
        id = createUser(username)

        # Remember which user has logged in
        session["user_id"] = id

        type = getUserType(id)

        # if user is of admin type, set isAdmin to true, else set it to false
        if type == "admin":
            session["isAdmin"] = True
        else:
            session["isAdmin"] = False

        if next_url:
            return redirect(next_url)
        return redirect("/")

    return render_template("login.html")



@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/api/createaccount", methods=["POST"])
def create_account():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("pswdconf")
        email = request.form.get("email")
        usernames = getAllUsernames()

        if not validateRegistration(usernames, username, password, confirmation, email):
            return redirect("/register")

        # Successful registering
        else:
            id = createAccount(password, username, email)

            # Remember which user has logged in
            session["user_id"] = id

            # get email and send registration confirmation
            title = f"Welcome to {appname}"
            msg = f"""<h2>Your account was successfully created</h2>
                       <p><strong>Username</strong>: {username}.</p>"""
            recipient = getUserEmail(id)
            sendEmail(title, msg, recipient)
            return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/mybookings", methods=["GET", "POST"])
@login_required
def mybookings():

    # Initialize form
    form = CheckBookingsForm()

    user_id = session["user_id"] # store current user's id

    # Shows the user's bookings for a selected day
    if "show_day" in request.form and form.validate_on_submit():
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        # Get data for all of the user's bookings in the selected day 
        bookings_data = getUserBookingsData(user_id, selected_date)

        selected_date_showuser = showDateToUserFormat(selected_date)
        if not bookings_data:
            msg = f"You have no bookings for {selected_date_showuser}"
            return render_template("mybookings.html", form=form, msg=msg)
        else:
            return render_template("mybookings.html", form=form, bd=bookings_data)

    # Shows all of the user's upcoming bookings
    if "show_upcoming" in request.form and form.validate_on_submit():
        # Get user data for all of the user's upcoming bookings
        showAll = True
        bookings_data = getUserBookingsData(user_id, None, showAll)

        if not bookings_data:
            msg = "You have no upcoming bookings"
            return render_template("mybookings.html", form=form, msg=msg)
        else:
            return render_template("mybookings.html", form=form, bd=bookings_data)
    
    current_date_str = getCurrDate()
    upcoming_user_bookings = getUpcomingUserBookings(user_id, current_date_str)

    # check if there are any upcoming bookings, if not, return no upcoming bookings for {user}
    if upcoming_user_bookings == 0:
        msg = "You have no upcoming bookings"
        return render_template("mybookings.html", form=form, msg=msg)
    
    return render_template("mybookings.html", form=form)

@app.route("/api/deletebooking", methods=["POST"])
@login_required
def delete_booking():
    user_id = session["user_id"] # store current user's id

    # Request to delete a single booking coming from /mybookings
    if "delete_booking" in request.form and request.method == "POST":
        booking_id = request.form.get("id")

        # Check if booking id is valid
        if not doesBookingIdExist(booking_id):
            return redirect("/mybookings")
        
        booking_info = getBookingInfo(booking_id)
        deleteBooking(booking_id)

        court = booking_info[0][0]
        date = booking_info[0][1].strftime("%Y-%m-%d")
        date_showuser = showDateToUserFormat(date)
        time = booking_info[0][2]                                                                        
        title = f"{appname} - Booking Deleted"
        msg = f"<p>Your booking for court {court} on {date_showuser} at {time} was deleted.</p>"
        recipient = getUserEmail(user_id)
        sendEmail(title, msg, recipient)

        return redirect("/mybookings")

    # Request to delete a single booking coming from /admin
    if "admin_delete_booking" in request.form and request.method == "POST":
        booking_id = request.form.get("id")
        # Check if booking id is valid
        if not doesBookingIdExist(booking_id):
            return redirect("/admin")
        booking_info = getBookingInfo(booking_id) # get court, date, time
        # Check if deletion is valid
        deleteBooking(booking_id)                                                           
        court = booking_info[0][0]
        date = booking_info[0][1].strftime("%Y-%m-%d")
        time = booking_info[0][2]
        # get id of user who had made the booking
        id = getUserId(booking_id)

        date_showuser = showDateToUserFormat(date)
        title = f"{appname} - Booking Deleted"
        msg = f"<p>Your booking for court {court} on {date_showuser} at {time} was deleted by an admin.</p>"
        recipient = getUserEmail(id)
        sendEmail(title, msg, recipient)

        deletedBookingUsername = getUsername(id)
        admin_title = f"{appname} - Booking Deleted"
        admin_msg = f"<p>You deleted a booking made by {deletedBookingUsername} using your admin power.</p>"
        admin_email = getUserEmail(user_id)
        sendEmail(admin_title, admin_msg, admin_email)

        return redirect("/admin")

@app.route("/api/deletedaybookings", methods=["POST"])
@login_required
def delete_day_bookings():
    user_id = session["user_id"] # store current user's id
    form = CheckBookingsForm()

    # Deletes all of the user's bookings for a selected day
    if "delete_day" in request.form and form.validate_on_submit():
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        if isDatePast(selected_date):
            return redirect("/mybookings")
        
        deleteUserDayBookings(user_id, selected_date)

        selected_date_showuser = showDateToUserFormat(selected_date)
        title = f"All {selected_date_showuser} Bookings Deleted"
        msg = f"<p>All of your bookings for {selected_date_showuser} were deleted.</p>"
        recipient = getUserEmail(user_id)
        sendEmail(title, msg, recipient)

        return redirect("/mybookings")

@app.route("/api/deleteallbookings", methods=["POST"])
@login_required
def delete_all_bookings():
    user_id = session["user_id"] # store current user's id

    # Request to delete all bookings for the user, coming from /mybookings
    if "delete_all" in request.form and request.method == "POST":
        deleteAllUserBookings(user_id)

        title = "All Bookings Deleted"
        msg = "<p>All of your bookings were deleted.</p>"
        recipient = getUserEmail(user_id)
        sendEmail(title, msg, recipient)

        return redirect("/mybookings")
       

@app.route("/admin", methods=["GET", "POST"])
@login_required
@admin_required
def admin():

    # Initialize forms
    form_court_date = CourtDateForm()

    user_id = session["user_id"] # store current user's id
    
    # POST request for searching bookings for a certain day (default for today)
    if "show_day" in request.form and form_court_date.validate_on_submit():
        court = form_court_date.court.data
        date = form_court_date.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        bookings_data = getBookingsData(court, selected_date)
        if not bookings_data:
            if court == "All courts":
                msg = "No bookings for the selected day"
                return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, msg=msg)
            else:
                msg = "No bookings for this court on the selected day"
                return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, msg=msg)
        else:
            return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, bd=bookings_data)

    # count the number of bookings for a selected court on a selected day
    if "count_day_bookings" in request.form and form_court_date.validate_on_submit():
        court = form_court_date.court.data # pass this into query
        selected_date = form_court_date.date.data
        selected_date_str = selected_date.strftime("%Y-%m-%d") # pass this into query
        selected_date_str_showuser = showDateToUserFormat(selected_date_str)

        day_count = getDayBookingsCount(court, selected_date_str)

        if court == "All courts":
            return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, day_count=day_count, selected_date_str=selected_date_str_showuser)
        else:
            return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, day_count=day_count, selected_date_str=selected_date_str_showuser, court=court)

    # counts all the bookings for the selected court
    if "count_all_bookings" and request.method == "POST":
        
        input_range = request.form.get("range")
        court = request.form.get("court")
        current_time_str = getCurrTime()

        return_data = getAllBookingsCount(input_range, court, current_time_str)
        isRangeValid = return_data[0]
        total_count = return_data[1]

        if not isRangeValid:
            flash("Invalid range input")
            return redirect("/admin")
        
        return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, court=court, total_count=total_count, input_range=input_range)

    # page load with GET
    return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all)

@app.route("/api/bookalday", methods=["POST"])
@login_required
@admin_required
def book_all_day():
    form_court_date = CourtDateForm()
    user_id = session["user_id"] # store current user's id

    # admin has the ability to delete bookings for the selected day (if any exists) and disable bookings for that day
    if "book_day" in request.form and form_court_date.validate_on_submit() and validateDate(form_court_date.date): 
        court = form_court_date.court.data # pass this into query
        selected_date = form_court_date.date.data
        selected_date_str = selected_date.strftime("%Y-%m-%d") # pass this into query
        selected_weekday = selected_date.strftime("%a") # pass this into query
        people = numofpeople[0] # default when admin makes a booking

        if isDatePast(selected_date_str):
            return redirect("/admin")

        # Delete existing bookings and book for all possible day times
        deleteAllDayBookings(selected_date_str, court)
        bookAllDay(selected_weekday, possibletimesweekend, user_id, selected_date_str, court, people, possibletimes)

        selected_date_str_showuser = showDateToUserFormat(selected_date_str)
        title = "Day Booked"
        msg = f"<p>All times for {court} on {selected_date_str_showuser} are now booked.</p>"
        recipient = getUserEmail(user_id)
        sendEmail(title, msg, recipient)

        return redirect("/admin")


@app.route("/api/createindex", methods=["POST"])
@login_required
def create_index():
    if "create_index" in request.form and request.method == "POST":
        name = request.form.get("name")
        table = request.form.get("table")
        columns_input = request.form.get("columns")

        # transform columns into a list
        columns = columns_input.split(",")
        # remove whitespaces from each element of the list
        i = 0
        for column in columns:
            columns[i] = column.strip()
            i += 1

        # turn invalid SQL character into _
        k = 0
        for n in name:
            if n == " " or n == ";" or n == ">" or n == "<" or n == ">":
                name[k] = "_"
            k += 1

        if not validateIndex(name, table, columns_input, columns):
            return redirect("/admin")
        
        createIndex(columns, name, table)

        return redirect("/admin")


@app.route("/createadmin", methods=["GET"])
@login_required
def createadmin():
    return render_template("createadmin.html")

@app.route("/api/createadmin", methods=["POST"])
@login_required
def create_admin():
    user_id = session["user_id"]

    if "create_admin" in request.form and request.method == "POST":
        secret_password = request.form.get("secretpassword")
        # if the secret password is correct, proceed to create new admin account
        if secret_password == ADMIN_SECRET_PASSWORD:
            admin_username = request.form.get("username")
            admin_password = request.form.get("password")
            confirmation = request.form.get("confirmation")
            email = request.form.get("email")

            usernames = getAllUsernames()

            if not validateEmail(email) or not validateRegistration(usernames, admin_username, admin_password, confirmation, email):
                return redirect("/createadmin")
            else:
                isAdmin = True
                createAccount(admin_password, admin_username, email, isAdmin)
                # Email new admin
                title = "Admin Created"
                msg = f"<p>Admin {admin_username} created.</p>"
                sendEmail(title, msg, email)
                # Email user who created new admin
                second_title = "Admin Created"
                second_msg = f"<p>Admin {admin_username} created.</p>"
                user_email = getUserEmail(user_id)
                sendEmail(second_title, second_msg, user_email)
                return redirect("/createadmin")
        else:
            flash("Invalid secret password", "danger")
            return redirect("/")


@app.route("/account", methods=["GET"])
@login_required
def account():
    user_id = session["user_id"]

    data = getUserAccountData(user_id)
    username = data[0]
    email_address = data[1]
    type = data[2]
    userInfo = {"uname": username, "eaddress": email_address, "type": type}

    return render_template("account.html", userInfo=userInfo)

@app.route("/api/changepassword", methods=["POST"])
@login_required
def change_password():
    user_id = session["user_id"]

    if "changepassword" in request.form and request.method == "POST":
        password = request.form.get("password")
        data = getUserAccountData(user_id)
        username = data[0]
        recipient = data[1]
        newpassword = request.form.get("newpassword")
        confirmation = request.form.get("confirmation")

        if newpassword.split() == "" or confirmation.split() == "":
            flash("New password cannot be null", "danger")
            return redirect("/account")
        elif newpassword != confirmation:
            flash("New password and confirmation don't match", "danger")
            return redirect("/account")
        else: # check if password hash matches current hash, if it does, change user's password
            if passwordEqualsHash(user_id, password):
                updateUserPassword(newpassword, user_id)
                flash("Password successfuly updated", "success")
                title = f"{appname} - Password modified"
                msg = f"<p>The password for {username} was modified.</p>"
                sendEmail(title, msg, recipient)
            return redirect("/account")

@app.route("/api/changeemail", methods=["POST"])
@login_required
def change_email():
    user_id = session["user_id"]

    if "changeemail" in request.form and request.method == "POST":
        password = request.form.get("password")
        newemail = request.form.get("newemail")
        username = getUsername(user_id)
        recipient = getUserEmail(user_id)

        # Check if password is correct
        if not validatePassword(password, user_id) or not validateEmail(newemail):
            return redirect("/account")
        updateUserEmail(newemail, user_id)
        flash("Email successfuly updated", "success")

        # Send email to original email account
        title = f"{appname} - Email modified"
        msg = f"""<p>The email for {username} was modified.</p>
                   <p>Your new email is {newemail}.</p>"""
        sendEmail(title, msg, recipient)

        # Send email to new email account
        title_newemail = f"{appname} - Email modified"
        msg_newemail = f"""<p>This email is now the email address for the account {username}.</p>"""
        sendEmail(title_newemail, msg_newemail, newemail)

        return redirect("/account")
        


@app.route("/api/deleteaccount", methods=["POST"])
@login_required
def delete_account():
    user_id = session["user_id"]

    if "deleteaccount" in request.form and request.method == "POST":
        password = request.form.get("password")
        data = getUserAccountData(user_id)
        username = data[0]
        recipient = data[1]
        if deleteUserAccount(user_id, password):
            # Email new admin
            title = f"Goodbye from {appname}"
            msg = f"<p>Your account {username} was deleted.</p>"
            sendEmail(title, msg, recipient)

            session.clear()

            return redirect("/login")
        else:
            return redirect("/account")


@app.route("/today", methods=["GET"])
@admin_required
def today():
    # get current date as string ("%Y"-"%m"-"%-d")
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")

    if isWeekend(current_date):
        courts_dict = getTableData(current_date_str, courts, possibletimes, possibletimesweekend, True)
        halflengthpt = int(len(possibletimesweekend) / 2) + 1
        return render_template("today.html", cd=courts_dict, pt=possibletimesweekend, hlenpt=halflengthpt) 
    else: # today is not a weekend day
        courts_dict = getTableData(current_date_str, courts, possibletimes, possibletimesweekend, False) 
        halflengthpt = int(len(possibletimes) / 2) + 1
        return render_template("today.html", cd=courts_dict, pt=possibletimes, hlenpt=halflengthpt)



if __name__ == '__main__':
    app.run(debug=True)


# NEXT TODOS
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Pre-Deployment
    # styling (with SASS and JS where necessary + Bootstrap) (simple but modern style - clean lines, have a nice login and homepage, simple design on other pages)
        # move today.html styles to sass
        # style all pages
        # make forms buttons and inputs look nice
        # style bookings result
        # add footer to the layout
        # make pages responsive
        # JS
            # on /today page, add styles to make long usernames clickable, and once clicked, show full username on a box (like a dialog box)
                # have each element have the class equal to the username, and using the .classList[classindex] selector, display the full selected username on the popup box
    # have a detailed Readme
    # delete Bootstrap locally
# Deployment
    # deploy and show to Luis

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------