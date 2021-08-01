import os

from flask import Flask, flash, redirect, render_template, session, request
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import SelectField
from datetime import datetime
from flask_mail import Mail, Message
# Own helper funcs
from helpers.funcs.actions.creates import createIndex, createBooking, createUser, createAccount, bookAllDay
from helpers.funcs.actions.deletes import deleteBookings
from helpers.funcs.actions.gets import getDayBookingsCount, getUserType, getAllUsernames, getCurrDate, getCurrTime, getUpcomingUserBookings, getUserBookingsData, \
    getBookingsData, getDayBookingsCount, getAllBookingsCount, getUserEmail, getBookingInfo, getUserId
from helpers.funcs.others import isDatePast
from helpers.funcs.validations import validateBooking, validateLogin, validateEmail, validateRegistration, validateIndex, validateDate
from helpers.funcs.requireds import login_required, admin_required
# Own helper lists
from helpers.variables.lists import numofpeople, courts, courts_all, possibletimes, possibletimesweekend

# Initialize app
app = Flask(__name__)

# Configure for flask_wtf
app.config["SECRET_KEY"] = "secret"

# Get environment variables
ADMIN_SECRET_PASSWORD = os.environ.get('ADMIN_SECRET_PASSWORD')

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
    time = SelectField('Time (open from 09:00 to 22:00)', choices=possibletimes, default="Choose a time")

# Check bookings form
class CheckBookingsForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())

# Admin book a court for a day form
class CourtDateForm(FlaskForm):
    court = SelectField('Court', choices=courts_all)
    date = DateField('Date', format='%Y-%m-%d', default=datetime.now())

# Function to send an email
def sendEmail(title, text, email):
    msg = Message(title, recipients=[email])
    msg.html = text
    mail.send(msg)
    return


#  ----------------------------------------------------------------------------------ROUTES--------------------------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")


@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():

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
        
            return redirect("/booking")


    return render_template("booking.html", form=form)



@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not validateLogin(username, password):
            return render_template("login.html")
        
        id = createUser(username)

        # Remember which user has logged in
        session["user_id"] = id

        type = getUserType(id)

        # if user is of admin type, set isAdmin to true, else set it to false
        if type == "admin":
            session["isAdmin"] = True
        else:
            session["isAdmin"] = False

        return redirect("/")

    return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("pswdconf")
        email = request.form.get("email")

        usernames = getAllUsernames()

        if not validateRegistration(usernames, username, password, confirmation, email):
            return render_template("register.html")

        # Successful registering
        else:
            id = createAccount(password, username, email)

            # Remember which user has logged in
            session["user_id"] = id

            # get email and send registration confirmation
            email = getUserEmail(id)
            msg = Message("Welcome to Scheduling", recipients=[email])
            msg.html = "<p>Your account was successfully created</p>"
            mail.send(msg)

            return redirect("/")

    return render_template("register.html")


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

    current_date_str = getCurrDate()

    upcoming_user_bookings = getUpcomingUserBookings(user_id, current_date_str)

    # check if there are any upcoming bookings, if not, return no upcoming bookings for {user}
    if upcoming_user_bookings == 0:
        msg = "You have no upcoming bookings"
        return render_template("mybookings.html", form=form, msg=msg)

    if "show_day" in request.form and form.validate_on_submit():
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        # Get data for all of the user's bookings in the selected day 
        bookings_data = getUserBookingsData(user_id, selected_date)

        if not bookings_data:
            msg = f"You have no bookings for {date}"
            return render_template("mybookings.html", form=form, msg=msg)
        else:
            return render_template("mybookings.html", form=form, bd=bookings_data)

    if "show_upcoming" in request.form:
        # Get user data for all of the user's upcoming bookings
        showAll = True
        selected_date = None
        bookings_data = getUserBookingsData(user_id, selected_date, showAll)

        if not bookings_data:
            msg = "You have no upcoming bookings"
            return render_template("mybookings.html", form=form, msg=msg)
        else:
            return render_template("mybookings.html", form=form, bd=bookings_data)
    
    if "delete_booking" in request.form and request.method == "POST":
        booking_id = request.form.get("id")
        deleteBookings(booking_id)

        email = getUserEmail(user_id)
        title = "Booking Deleted"
        msg = "<p>One of your bookings was deleted</p>"
        sendEmail(title, msg, email)

        type = getUserType(user_id)

        if type == "admin":
            return redirect("/admin")
        else:
            return redirect("/mybookings")
    
    if "delete_day" in request.form and form.validate_on_submit:
        date = form.date.data # datetime.date
        selected_date = date.strftime("%Y-%m-%d") # string

        deleteBookings(None, user_id, selected_date)

        email = getUserEmail(user_id)
        title = f"All {selected_date} Bookings Deleted"
        msg = f"<p>All of your bookings for {selected_date} were deleted</p>"
        sendEmail(title, msg, email)

        return render_template("mybookings.html", form=form)
    
    if "delete_all" in request.form:
        deleteBookings(None, user_id)

        email = getUserEmail(user_id)
        title = "All Bookings Deleted"
        msg = "<p>All of your bookings were deleted</p>"
        sendEmail(title, msg, email)

        return render_template("mybookings.html", form=form)
    
    return render_template("mybookings.html", form=form)


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

    if "delete_booking" in request.form and request.method == "POST":
        booking_id = request.form.get("id")
        booking_info = getBookingInfo(booking_id) # get court, date, time

        # get id of user who had made the booking
        id = getUserId(booking_id)
        deleteBookings(booking_id)
        
        court = booking_info[0][0]
        date = booking_info[0][1]
        time = booking_info[0][2]
        email = getUserEmail(id)
        title = "Booking Deleted"
        msg = f"<p>Your booking for court {court} on {date} at {time} was deleted by an admin</p>"
        sendEmail(title, msg, email)

        admin_email = getUserEmail(user_id)
        admin_title = "Booking Deleted"
        admin_msg = "<p>One booking was deleted</p>"
        sendEmail(admin_title, admin_msg, admin_email)

        # get type - if type is admin, redirect to admin, if not, redirect to homepage
        type = getUserType(user_id)
        if type == "admin":
            return redirect("/admin")
        else:
            return redirect("/mybookings")

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
    
    # admin has the ability to delete bookings for the selected day (if any exists) and disable bookings for that day
    if "book_day" in request.form and form_court_date.validate_on_submit() and validateDate(form_court_date.date): 
        court = form_court_date.court.data # pass this into query
        selected_date = form_court_date.date.data
        selected_date_str = selected_date.strftime("%Y-%m-%d") # pass this into query
        selected_weekday = selected_date.strftime("%a") # pass this into query
        people = 4 # default when admin makes a booking

        if isDatePast(selected_date_str):
            return redirect("/admin")

        # Delete existing bookings and book for all possible day times
        deleteBookings(None, None, selected_date_str, court)
        bookAllDay(selected_weekday, possibletimesweekend, user_id, selected_date_str, court, people, possibletimes)

        email = getUserEmail(user_id)
        title = "Day Booked"
        msg = f"<p>All times for {court} on {selected_date_str} are now booked</p>"
        sendEmail(title, msg, email)

        return redirect("/admin")

    # count the number of bookings in a selected day
    if "count_day_bookings" in request.form and form_court_date.validate_on_submit():
        court = form_court_date.court.data # pass this into query
        selected_date = form_court_date.date.data
        selected_date_str = selected_date.strftime("%Y-%m-%d") # pass this into query

        day_count = getDayBookingsCount(court, selected_date_str)

        if court == "All courts":
            return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, day_count=day_count, selected_date_str=selected_date_str)
        else:
            return render_template("admin.html", form_court_date=form_court_date, courts_all=courts_all, day_count=day_count, selected_date_str=selected_date_str, court=court)


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


@app.route("/makeadmin", methods=["GET", "POST"])
@login_required
def makeadmin():

    if "make_admin" in request.form and request.method == "POST":
        secret_password = request.form.get("secretpassword")
        # if the secret password is correct, proceed to create new admin account
        if secret_password == ADMIN_SECRET_PASSWORD:
            admin_username = request.form.get("username")
            admin_password = request.form.get("password")
            confirmation = request.form.get("confirmation")
            email = request.form.get("email")

            usernames = getAllUsernames()

            if not validateEmail(email) or not validateRegistration(usernames, admin_username, admin_password, confirmation, email):
                return redirect("/makeadmin")
            else:
                isAdmin = True
                createAccount(admin_password, admin_username, email, isAdmin)
                # Email new admin
                title = "Admin Created"
                msg = f"<p>Admin {admin_username} created</p>"
                sendEmail(title, msg, email)
                # Email user who created new admin
                user_email = getUserEmail(id)
                second_title = "Admin Created"
                second_msg = f"<p>Admin {admin_username} created</p>"
                sendEmail(second_title, second_msg, user_email)
        else:
            flash("Invalid secret password", "danger")
            return redirect("/")

    return render_template("makeadmin.html")



if __name__ == '__main__':
    app.run(debug=True)


# NEXT TODOS
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# send me an email when an booking or cancellation is made, with the action's info
# send email to user after a booking is made
# send email to user if one of its bookings are cancelled (both by the user himself or an admin)
# if there are bookings in the next hour, send admin an email with all the bookings
# if a user has a booking in the next hour, send him an email
# allow users to delete their account (delete all bookings for the account when the account is deleted and send a confirmation email)
# allow users to change their passwords on the app (need current password confirmation) or by email

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------