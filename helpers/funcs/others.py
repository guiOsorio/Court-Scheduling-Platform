from helpers.funcs.actions.gets import getCurrDate
from flask import flash


def isDatePast(selected_date_str):
    # check if date is not in the past
    current_date_str = getCurrDate()

    if selected_date_str < current_date_str:
        flash("Invalid date", "danger")
        return True
    else:
        return False