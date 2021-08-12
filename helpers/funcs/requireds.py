from flask import flash, redirect, session, request, url_for
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Login required", "danger")
            return redirect((url_for("login", next=request.url)))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("isAdmin"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def not_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id"):
            flash("Log out to access this page", "danger")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function