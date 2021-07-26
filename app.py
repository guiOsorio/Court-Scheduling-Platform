import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request


# Configure application
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")