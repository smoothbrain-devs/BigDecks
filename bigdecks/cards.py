"""Cards enpoint management"""


from flask import (
    Blueprint,
    render_template,
)
from .services.card_service import CardService


bp = Blueprint(name="cards", import_name=__name__)


@bp.route("/card")
def home():
    card = CardService.get_random_card()
    return render_template("cards.html", card=card)


@bp.route("/card/<scry_id>")
def card_by_scry_id(scry_id: str):
    card = CardService.get_card_by_scryfall_id(scry_id)
    return render_template("cards.html", card=card)
