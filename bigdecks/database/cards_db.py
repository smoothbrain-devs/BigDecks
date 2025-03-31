"""Cards database management and maintenance."""


import os
import click
import json
import re
import sqlite3
from contextlib import closing
from . import get_db_connection
from datetime import datetime
from flask import current_app, Flask
from flask.cli import with_appcontext


@click.group()
def cards():
    pass


def init_app(app: Flask):
    """Register the cli commands with the flask app."""
    app.cli.add_command(cards)


@cards.command("populate")
@with_appcontext
def populate_command():
    """Populates the cards database."""
    success = _populate()
    if success:
        click.echo("Database populated successfully")
    else:
        click.echo("Database population failed", err=True)


@cards.command("rebuild")
@with_appcontext
def rebuild_command():
    """Rebuild the database"""
    success = _rebuild()
    if success:
        click.echo("Rebuild successful")
    else:
        click.echo("Rebuild failed", err=True)


def _rebuild() -> bool:
    """Remove and repopulate the cards database from scratch.

    Returns
    ------
    bool
        True if successful, False otherwise.
    """
    from . import init_db
    db_path = os.path.join(current_app.instance_path, "cards.db")
    click.echo("Rebuilding the cards database")
    try:
        # Delete the DB
        if os.path.exists(db_path):
            os.remove(db_path)
            click.echo(f"Database file at {db_path} removed successfully")
    except Exception as e:
        click.echo(f"Error deleting database: {e}", err=True)
        return False

    try:
        init_db("cards")
    except FileNotFoundError as e:
        click.echo(f"{e}")

    return _populate()


def _populate() -> bool:
    """Populates the cards database form default_cards.json.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    try:
        import ijson
    except ImportError:
        click.echo("Error: ijson is not installed. Please run 'pip install "
                   "ijson'", err=True)
        return False

    default_cards = os.path.join(current_app.instance_path, "resources",
                                 "default_cards.json")

    # Stats about the transaction
    start_time = datetime.now()
    cards_processed = 0
    cards_inserted = 0

    try:
        # Using the connection as a context manager will automagically
        # rollback on any exception and autocommit at the end of the block,
        # the connection will be closed by the closing()
        with closing(get_db_connection("cards")) as conn:
            cursor = conn.cursor()

            try:
                with open(file=default_cards,
                          mode="rb") as f:
                    click.echo("Starting database population")
                    conn.execute("BEGIN TRANSACTION")
                    for card in ijson.items(f, "item", use_float=True):
                        cards_processed += 1

                        # Core data for a reversible card doesn't contain a
                        # typeline, so grab it from one of the card faces
                        if card.get("layout") == "reversible_card":
                            face = card.get("card_faces")
                            card["type_line"] = face[0].get("type_line")

                        # Merge the card types into the card dict.
                        card |= _get_card_types(card.get("type_line"))

                        # Insert the data
                        try:
                            _insert_core_data(cursor, card)

                            if "all_parts" in card and card["all_parts"]:
                                _insert_all_parts(cursor, card["id"],
                                                  card["all_parts"])

                            if "card_faces" in card and card["card_faces"]:
                                _insert_card_face(cursor, card["id"],
                                                  card["card_faces"])

                            cards_inserted += 1

                            # Commit every 1000 cards
                            if cards_inserted % 1000 == 0:
                                conn.commit()
                                conn.execute("BEGIN TRANSACTION")
                                elapsed = datetime.now() - start_time
                                click.echo(f"Processed {cards_processed} "
                                           f"cards, inserted {cards_inserted} "
                                           f"in {elapsed}")

                        except Exception as e:
                            click.echo("Error processing card "
                                       f"{card.get("name", "unknown")}: {e}",
                                       err=True)
                            continue

            except FileNotFoundError:
                click.echo("Error: Default cards.json not found. Run download "
                           "command first.", err=True)

        end_time = datetime.now()
        elapsed = end_time - start_time
        click.echo("Database population complete")
        click.echo(f"Started at: {start_time}")
        click.echo(f"Ended at: {end_time}")
        click.echo(f"Total time: {elapsed}")
        click.echo(f"Processed {cards_processed} and inserted "
                   f"{cards_inserted}")

        return True

    except Exception as e:
        click.echo(f"Error populating database: {e}", err=True)
        return False


def _get_card_types(typeline: str) -> dict[str, str]:
    """Split the typeline and return the super/main/sub types for a card.

    Parameters
    ----------
    type_line: str
        Type line for a card

    Returns
    -------
    dict[str, str]
        If a key is present in the dictionary, the value will be a stringified
        json array with 1 or more values.
        Possible keys: "supertype", "subtype"
        Guaranteed key: "cardtype"
    """
    supertypes = ["Basic", "Elite", "Legendary", "Ongoing", "Snow",
                  "Token", "World"]
    cardtypes = ["Artifact", "Battle", "Conspiracy", "Creature", "Dungeon",
                 "Emblem", "Enchantment", "Hero", "Instant", "Kindred",
                 "Tribal", "Land", "Phenomenom", "Plane", "Planeswalker",
                 "Scheme", "Sorcery", "Vanguard"]

    card_types: dict[str, str] = {}
    types: set[str] = set()
    # Split the typeline, use a set to remove potential duplicates.
    types = set(re.split(r" — | \/\/ | ", typeline))
    card_types["supertype"] = json.dumps([st for st in types
                                          if st in supertypes])
    card_types["cardtype"] = json.dumps([mt for mt in types
                                         if mt in cardtypes])
    card_types["subtype"] = json.dumps([t for t in types if
                                        t not in supertypes and
                                        t not in cardtypes])
    return card_types


def _insert_core_data(cursor: sqlite3.Cursor,
                      card: dict[str, object]) -> None:
    """Insert a card's core data into the core table.

    Parameters
    ----------
    cursor: sqlite3.Cursor
        Database cursor
    card: dict
        Card data from Scryfall
    """
    # Prepare multiverse_ids if present
    if 'multiverse_ids' in card:
        multiverse_ids = json.dumps(card.get('multiverse_ids', []))
    else:
        multiverse_ids = None

    # Check for card_faces and all_parts
    has_card_faces = 'card_faces' in card and bool(card['card_faces'])
    has_all_parts = 'all_parts' in card and bool(card['all_parts'])

    # Arrays that need to be converted to JSON
    #####################################################################
    color_identity = json.dumps(card.get('color_identity', []))
    if 'color_indicator' in card:
        color_indicator = json.dumps(card.get('color_indicator', []))
    else:
        color_indicator = None

    if 'colors' in card:
        colors = json.dumps(card.get('colors', []))
    else:
        colors = None

    keywords = json.dumps(card.get('keywords', []))

    if 'produced_mana' in card:
        produced_mana = json.dumps(card.get('produced_mana', []))
    else:
        produced_mana = None

    if 'artist_ids' in card:
        artist_ids = json.dumps(card.get('artist_ids', []))
    else:
        artist_ids = None

    if 'attraction_lights' in card:
        attraction_lights = json.dumps(card.get('attraction_lights', []))
    else:
        attraction_lights = None

    if 'frame_effects' in card:
        frame_effects = json.dumps(card.get('frame_effects', []))
    else:
        frame_effects = None

    if 'promo_types' in card:
        promo_types = json.dumps(card.get('promo_types', []))
    else:
        promo_types = None
    ######################################################################

    # Extract legalities
    legalities = card.get('legalities', {})
    assert (isinstance(legalities, dict))

    # Extract games
    games = card.get('games', [])
    assert (isinstance(games, list))
    in_paper = 'paper' in games
    in_arena = 'arena' in games
    in_mtgo = 'mtgo' in games

    # Extract finishes
    finishes = card.get('finishes', [])
    assert (isinstance(finishes, list))
    has_foil = 'foil' in finishes
    has_nonfoil = 'nonfoil' in finishes
    has_etched = 'etched' in finishes

    # Extract image URIs
    image_uris = card.get('image_uris', {})
    assert (isinstance(image_uris, dict))

    # Extract prices
    prices = card.get('prices', {})
    assert (isinstance(prices, dict))

    # Create the parameter tuple
    params = (
        card.get("id"),
        card.get("arena_id"),
        card.get("mtgo_id"),
        card.get("mtgo_foil_id"),
        multiverse_ids,
        card.get("layout"),
        card.get("oracle_id"),
        card.get("rulings_uri"),
        card.get("scryfall_uri"),
        card.get("uri"),
        has_all_parts,
        has_card_faces,
        card.get("cmc", 0.0),
        color_identity,
        color_indicator,
        colors,
        card.get("defense"),
        card.get("game_changer", False),
        card.get("hand_modifier"),
        keywords,
        # Legalities
        legalities.get("standard", "not_legal"),
        legalities.get("future", "not_legal"),
        legalities.get("historic", "not_legal"),
        legalities.get("timeless", "not_legal"),
        legalities.get("gladiator", "not_legal"),
        legalities.get("pioneer", "not_legal"),
        legalities.get("explorer", "not_legal"),
        legalities.get("modern", "not_legal"),
        legalities.get("legacy", "not_legal"),
        legalities.get("pauper", "not_legal"),
        legalities.get("vintage", "not_legal"),
        legalities.get("penny", "not_legal"),
        legalities.get("commander", "not_legal"),
        legalities.get("oathbreaker", "not_legal"),
        legalities.get("standardbrawl", "not_legal"),
        legalities.get("brawl", "not_legal"),
        legalities.get("alchemy", "not_legal"),
        legalities.get("paupercommander", "not_legal"),
        legalities.get("duel", "not_legal"),
        legalities.get("oldschool", "not_legal"),
        legalities.get("premodern", "not_legal"),
        legalities.get("predh", "not_legal"),
        card.get("life_modifier"),
        card.get("loyalty"),
        card.get("mana_cost"),
        card.get("name"),
        card.get("oracle_text"),
        card.get("power"),
        produced_mana,
        card.get("reserved", False),
        card.get("toughness"),
        card.get("type_line"),
        card.get("supertype"),
        card.get("cardtype"),
        card.get("subtype"),
        card.get("artist"),
        artist_ids,
        attraction_lights,
        card.get("booster", False),
        card.get("border_color"),
        card.get("card_back_id", ""),
        card.get("collector_number"),
        card.get("content_warning", False),
        card.get("digital", False),
        # Finishes
        has_foil,
        has_nonfoil,
        has_etched,
        card.get("flavor_name"),
        card.get("flavor_text"),
        frame_effects,
        card.get("frame"),
        card.get("full_art", False),
        # Games availability
        in_paper,
        in_arena,
        in_mtgo,
        card.get("highres_image", False),
        card.get("illustration_id"),
        card.get("image_status"),
        # Image URIs
        image_uris.get("png"),
        image_uris.get("border_crop"),
        image_uris.get("art_crop"),
        image_uris.get("large"),
        image_uris.get("normal"),
        image_uris.get("small"),
        card.get("oversized", False),
        # Prices
        prices.get("usd"),
        prices.get("usd_foil"),
        prices.get("usd_etched"),
        prices.get("eur"),
        prices.get("eur_foil"),
        prices.get("eur_etched"),
        prices.get("tix"),
        card.get("printed_name"),
        card.get("printed_text"),
        card.get("printed_type_line"),
        card.get("promo", False),
        promo_types,
        card.get("rarity"),
        card.get("released_at"),
        card.get("reprint", False),
        card.get("scryfall_set_uri"),
        card.get("set_name"),
        card.get("set_search_uri"),
        card.get("set_type"),
        card.get("set_uri"),
        card.get("set"),
        card.get("set_id"),
        card.get("story_spotlight", False),
        card.get("textless", False),
        card.get("variation", False),
        card.get("variation_of"),
        card.get("security_stamp"),
        card.get("watermark")
    )

    # Create the SQL query
    query = """
    INSERT OR REPLACE INTO core (
        scryfall_id, arena_id, mtgo_id, mtgo_foil_id, multiverse_ids,
        layout, oracle_id, rulings_uri, scryfall_uri, uri,
        all_parts, card_faces, cmc, color_identity, color_indicator,
        colors, defense, game_changer, hand_modifier, keywords,
        standard, future, historic, timeless, gladiator,
        pioneer, explorer, modern, legacy, pauper,
        vintage, penny, commander, oathbreaker, standardbrawl,
        brawl, alchemy, paupercommander, duel, oldschool,
        premodern, predh, life_modifier, loyalty, mana_cost,
        name, oracle_text, power, produced_mana, reserved,
        toughness, type_line, supertype, cardtype, subtype, artist,
        artist_ids, attraction_lights, booster, border_color, card_back_id,
        collector_number, content_warning, digital, foil, nonfoil, etched,
        flavor_name, flavor_text, frame_effects, frame, full_art, paper,
        arena, mtgo, highres_image, illustration_id, image_status, png,
        border_crop, art_crop, large, normal, small, oversized, price_usd,
        price_usd_foil, price_usd_etched, price_eur, price_eur_foil,
        price_eur_etched, price_tix, printed_name, printed_text,
        printed_type_line, promo, promo_types, rarity, released_at,
        reprint, scryfall_set_uri, set_name, set_search_uri, set_type,
        set_uri, set_code, set_id, story_spotlight, textless, variation,
        variation_of, security_stamp, watermark
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """

    cursor.execute(query, params)


def _insert_all_parts(cursor: sqlite3.Cursor, core_id: str,
                      all_parts: list[dict[str, object]]) -> None:
    """Insert related card parts into the all_parts table.

    Parameters
    ----------
    cursor: sqlite3.Cursor
        Database cursor
    core_id: str
        Scryfall ID of the parent card
    all_parts: list[dict[str, object]]
        List of related card objects
    """
    all_params = []
    for part in all_parts:
        part |= _get_card_types(str(part.get("type_line")))
        params = (
            core_id,
            part.get("id"),
            part.get("component"),
            part.get("name"),
            part.get("type_line"),
            part.get("supertype"),
            part.get("cardtype"),
            part.get("subtype"),
            part.get("uri")
        )
        all_params.append(params)

    query = """
    INSERT OR REPLACE INTO all_parts (
        core_id, scryfall_id, component, name, type_line, supertype,
        cardtype, subtype, uri
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """

    cursor.executemany(query, all_params)


def _insert_card_face(cursor: sqlite3.Cursor, core_id: str,
                      card_faces: list[dict[str, object]]) -> None:
    """Insert card faces for multi-faced cards into the card_faces table.

    Parameters
    ----------
    cursor: sqlite3.Cursor
        Database cursor
    core_id: str
        Core Scryfall ID of the card
    card_faces: list[dict[str, object]]
        The card faces associated to the core id
    """
    all_params = []
    for face in card_faces:
        # Convert list to JSON array or None
        if "color_indicator" in face:
            color_indicator = json.dumps(face.get("color_indicator", []))
        else:
            color_indicator = None

        if "colors" in face:
            colors = json.dumps(face.get("colors", []))
        else:
            colors = None

        # Extract image uris
        image_uris = face.get("image_uris", {})
        assert (isinstance(image_uris, dict))

        face |= _get_card_types(str(face.get("type_line")))

        params = (
            core_id,
            face.get("artist_id"),
            face.get("cmc"),
            color_indicator,
            colors,
            face.get("defense"),
            face.get("flavor_text"),
            face.get("illustration_id"),
            image_uris.get("png"),
            image_uris.get("border_crop"),
            image_uris.get("art_crop"),
            image_uris.get("large"),
            image_uris.get("normal"),
            image_uris.get("small"),
            face.get("layout"),
            face.get("loyalty"),
            face.get("mana_cost", ""),
            face.get("name"),
            face.get("oracle_id"),
            face.get("oracle_text"),
            face.get("power"),
            face.get("printed_name"),
            face.get("printed_text"),
            face.get("printed_type_line"),
            face.get("toughness"),
            face.get("type_line"),
            face.get("supertype"),
            face.get("cardtype"),
            face.get("subtype"),
            face.get("watermark")
        )
        all_params.append(params)

    query = """
    INSERT OR REPLACE INTO card_faces (
        core_id, artist_id, cmc, color_indicator, colors, defense,
        flavor_text, illustration_id, png, border_crop, art_crop,
        large, normal, small, layout, loyalty, mana_cost, name,
        oracle_id, oracle_text, power, printed_name, printed_text,
        printed_type_line, toughness, type_line, supertype, cardtype,
        subtype, watermark
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """

    cursor.executemany(query, all_params)
