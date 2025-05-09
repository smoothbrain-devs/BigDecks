"""Cards enpoint management"""


from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
)
from urllib.parse import quote
from .services.card_service import CardService


bp = Blueprint(name="cards", import_name=__name__,
               template_folder="templates/cards", url_prefix="/card")


@bp.route("/")
def random():
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


@bp.route("/search", methods=["GET"])
def search():
    name = request.args.get("name")
    colors = request.args.getlist("colors")
    
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
        
    if name or colors:
        search_results = CardService.search_for(
            name=name,
            colors=colors,
            page=page,
            per_page=25
            )
        
        return render_template(
            "search_result.html",
            results=search_results["cards"],
            total=search_results["total"],
            pages=search_results["pages"],
            current_page=search_results["current_page"],
            name=name,
            colors=colors
        )

    return render_template("card_search.html")