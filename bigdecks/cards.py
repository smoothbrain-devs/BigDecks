"""Cards enpoint management"""


from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
)
from urllib.parse import quote
from .services.card_service import CardService


bp = Blueprint(name="cards", import_name=__name__,
               template_folder="templates/cards", url_prefix="/card")


@bp.route("/")
def home():
    card = CardService.get_random_card()
    return redirect(
        url_for("cards.card_by_set_collector",
                set_code=card.set_code,
                collector_number=card.collector_number,
                card_name=quote(card.name))
    )


@bp.route("/<scry_id>")
def card_by_scry_id(scry_id: str):
    card = CardService.get_card_by_scryfall_id(scry_id)
    print(card)
    return render_template("cards.html", card=card)


@bp.route("/<set_code>/<collector_number>/<path:card_name>")
def card_by_set_collector(set_code: str, collector_number: str,
                          card_name: str) -> str:
    """Get a card using set code and collector number.

    Parameters
    ----------
    set_code
        Set code for the card to display.
    collector_number
       Collector number for the card to display.
    """
    card = CardService.get_card_by_set_collector(set_code, collector_number)
    return render_template("cards.html", card=card)


@bp.route("/search")
def search():
    return render_template("card_search.html")
