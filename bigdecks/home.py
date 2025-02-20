"""Home

This module contains the logic for the home page.
"""


from flask import (
    Blueprint, render_template
)


# Create the blueprint for the index page at /index
bp = Blueprint(name="home", import_name="__name__")


# Set up the route to home.
@bp.route("/")
def home():
    return render_template("home.html")
