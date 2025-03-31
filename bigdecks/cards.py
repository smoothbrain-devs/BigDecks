"""Cards enpoint management"""


from .database import get_db_connection
from flask import Blueprint, render_template


bp = Blueprint(name="cards", import_name=__name__)


@bp.route("/cards")
def home():
    conn = get_db_connection("cards")
    card = dict(conn.execute(
        """
        SELECT *
        FROM core
        ORDER BY RANDOM()
        LIMIT 1
        """).fetchone())
    return render_template("cards.html", card=card)
