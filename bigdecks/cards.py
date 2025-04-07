"""Cards enpoint management"""


from .models.card import Card
from flask import (
    Blueprint,
    render_template,
)


bp = Blueprint(name="cards", import_name=__name__)


@bp.route("/card")
def home():
    card = Card.get_random_card()
    return render_template("cards.html", card=card)


@bp.route("/card/<scry_id>")
def card_by_scry_id(scry_id: str):
    card = Card.get_card_by_scryfall_id(scry_id)
    return render_template("cards.html", card=card)


@bp.route("/card/<set_name>/<collector_number>/<card_name>")
def card_by_set_num_name(set_name: str, collector_number: str, card_name: str):
    card = Card.get_card(set_name, collector_number, card_name)
    return render_template("cards.html", card=card)
