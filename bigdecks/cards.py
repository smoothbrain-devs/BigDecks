"""Cards DB maintenance functions and CardsManager class"""

import click
import json
import os
import re
import requests
import sqlite3
from datetime import datetime, timezone, timedelta
from flask import current_app, Blueprint, render_template
from flask.cli import with_appcontext
from requests.exceptions import HTTPError, Timeout
from .database import get_db_connection

bp = Blueprint(name="cards", import_name=__name__)


@bp.route("/cards")
def home():
    conn = get_db_connection("cards")
    card = dict(conn.execute(
        """
        SELECT * FROM core
        ORDER BY RANDOM()
        LIMIT 1
        """).fetchone())
    return render_template("cards.html", card=card)


@bp.cli.command("populate")
@click.option("-r", "--rebuild", is_flag=True,
              help="Rebuild the database from scratch")
@click.option("-f", "--force", is_flag=True,
              help="Force repopulation of database")
@with_appcontext
def populate_cards_command(rebuild=False, force=False):
    """Populate the cards db from the Scryfall JSON file."""
    updated = False
    with CardsManager() as manager:
        if rebuild:
            click.echo("Rebuilding the cards database.")
            return

        if not manager._bulk_data_up_to_date() or \
           not os.path.exists(manager._get_default_cards_path()):
            click.echo("Donloading the latest card data.")
            success = manager._download_default_cards()
            if not success:
                click.echo("Failed to download card data.", err=True)
                return
            updated = True

        if updated or force:
            click.echo("Populating database...")
            success = manager.populate_card_database()

        success = True
        if success:
            click.echo("Database populated successfully.")
        else:
           click.echo("Failed to populate the database.", err=True)


class CardsManager:
    """Manages card data operations with an internal session.

    This class handles fetching, downloading, and updating card data within the
    cards.db using the Scryfall API while managing it's own session lifecycle.

    Use this class as a context manager for interacting with the cards db.
    """

    def __init__(self):
        """Initializes a new CardsManager with it's own session."""
        self.__session: requests.Session | None = requests.Session()
        # The Scryfall API requires this header.
        self.__session.headers.update({
            "User-Agent": "BigDecksApp/1.1",
            "Accept": "*/*"
        })
        self.__instance_path = current_app.instance_path
        self.__resources_path = self._get_resources_path()
        self.__bulk_data_path = self._get_bulk_data_path()
        self.__default_cards_path = self._get_default_cards_path()

        # Get bulk data if it doesn't already exist.
        if not os.path.exists(self.__bulk_data_path):
            self._download_bulk_data()

        if not os.path.exists(self.__default_cards_path):
            # Get default cards
            self._download_default_cards()

    def close(self) -> None:
        """Close the session when operations are complete."""
        if self.__session is not None:
            self.__session.close()
            self.__session = None

    def __enter__(self) -> "CardsManager":
        """Support for 'with' statement - returns self as the context manager."""
        return self

    # Bubbles up any exceptions that causet the context manager to exit.
    # Alternatively, we could handle exceptions here.
    def __exit__(self, exception_type, exception_value,
                 exception_traceback) -> None:
        """Automatically close the session when exiting a 'with' block."""
        self.close()

    @property
    def session(self) -> requests.Session:
        """Get the requests session with the proper type information."""
        if self.__session is None:
            self.__session = requests.Session()
            self.__session.headers.update({
                "User-Agent": "BigDecksApp/1.1",
                "Accept": "*/*"
            })
        return self.__session

    def _ensure_resources_exists(self) -> None:
        """Ensures the resources directory exists in the instance directory."""
        try:
            os.makedirs(os.path.join(self.__instance_path, "resources"),
                        exist_ok=True)
        except OSError as e:
            click.echo(e)

    def _get_resources_path(self) -> str:
        """Returns the path to the resources directory"""
        self._ensure_resources_exists()
        return os.path.join(self.__instance_path, "resources")

    def _get_bulk_data_path(self) -> str:
        """Returns a path to the bulkdata.json"""
        return os.path.join(self.__resources_path, "bulk_data.json")

    def _get_default_cards_path(self) -> str:
        """Returns a path to the default_cards.json"""
        return os.path.join(self.__resources_path, "default_cards.json")

    def _download_bulk_data(self):
        """Downloads bulk_data.json"""
        bulkdata_api = "https://api.scryfall.com/bulk-data/default-cards"
        try:
            response = self.session.get(url=bulkdata_api, timeout=35.0)
            response.raise_for_status()

        except (HTTPError, Timeout, ConnectionError) as e:
           click.echo(f"Network error while downloading bulk data: {e}",
                      err=True)
        else:
            with open(self.__bulk_data_path, "wb") as f:
                f.write(response.content)

    def _bulk_data_up_to_date(self) -> bool:
        """Ensures bulk data is up to date.

        Scryfall updates bulk data every 24 hours. So check to see if the
        updated_at time of the bulk_data.json file is within 24 hours of the
        current time.

        Returns
        -------
        bool
            True if the data is up to date, False if it needs to be updated
            or if there was an error accessing/parsing the file.
        """
        try:
            with open(self.__bulk_data_path, "r") as f:
                bulk_data = json.load(f)

            # Extract the timestamp and compare to current time
            last_update = datetime.fromisoformat(bulk_data["updated_at"])
            current_time = datetime.now(timezone.utc)
            difference = current_time - last_update
            one_day = timedelta(days=1)

            # Return True if data is less than 24 hours old
            return difference < one_day

        except FileNotFoundError:
            click.echo("Warning: Bulk data file not found at "
                       f"{self.__bulk_data_path}", err=True)
            return False

        except (json.JSONDecodeError, KeyError) as e:
            click.echo(f"Error parsing bulk data: {e}", err=True)
            return False

    def _download_default_cards(self) -> bool:
        """Downloads default_cards.json from Scryfall's API

        This method:
        1. Checks if bulk data info is up to date.
        2. Downloads new bulk data info if needed.
        3. Uses the download_uri from bulk data to get the actual card data.

        Returns
        -------
        bool
            True if download was successful, False otherwise.
        """
        try:
            # Check if bulk data is up to date (within last 24 hours)
            if not self._bulk_data_up_to_date():
                self._download_bulk_data()

            # Read bulk data to get the download URI
            try:
                with open(self.__bulk_data_path, "r") as f:
                    bulk_data = json.load(f)
                    download_uri = bulk_data.get("download_uri")

                    if not download_uri:
                        click.echo("Error: No download URI found in bulk data",
                                   err=True)
                        return False

                    click.echo(f"Downloading card data from {download_uri}...")
                    response = self.session.get(url=download_uri,
                                                stream=True, timeout=35.0)
                    response.raise_for_status()

                    # Read the default_cards.json file 8Kb at a time to avoid
                    # loading the 400+Mb file into memory.
                    with open(self.__default_cards_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    if os.path.exists(self.__default_cards_path):
                        click.echo("Card data successfully downloaded to "
                              f"{self.__default_cards_path}")
                        return True
                    click.echo("Card data not found at "
                               f"{self.__default_cards_path}", err=True)
                    return False

            except FileNotFoundError:
                click.echo("Error: Bulk data file not found", err=True)
                return False
            except json.JSONDecodeError as e:
                click.echo(f"Error parsing bulk data JSON: {e}", err=True)
                return False
        except (HTTPError, Timeout, ConnectionError) as e:
            click.echo(f"Network error while downloading card data: {e}",
                       err=True)
            return False
        except RuntimeError as e:
            click.echo(f"Unexpected error downloading card data: {e}",
                       err=True)
            return False


    def _insert_core_data(self, cursor: sqlite3.Cursor,
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
        assert(isinstance(legalities, dict))
        
        # Extract games
        games = card.get('games', [])
        assert(isinstance(games, list))
        in_paper = 'paper' in games
        in_arena = 'arena' in games
        in_mtgo = 'mtgo' in games
        
        # Extract finishes
        finishes = card.get('finishes', [])
        assert(isinstance(finishes, list))
        has_foil = 'foil' in finishes
        has_nonfoil = 'nonfoil' in finishes
        has_etched = 'etched' in finishes
        
        # Extract image URIs
        image_uris = card.get('image_uris', {})
        assert(isinstance(image_uris, dict))
        
        # Extract prices
        prices = card.get('prices', {})
        assert(isinstance(prices, dict))
        
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
<<<<<<< HEAD
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
            toughness, type_line, artist, artist_ids, attraction_lights, 
            booster, border_color, card_back_id, collector_number, content_warning, 
            digital, foil, nonfoil, etched, flavor_name, 
            flavor_text, frame_effects, frame, full_art, paper, 
            arena, mtgo, highres_image, illustration_id, image_status, 
            png, border_crop, art_crop, large, normal, 
            small, oversized, price_usd, price_usd_foil, price_usd_etched, 
            price_eur, price_eur_foil, price_eur_etched, price_tix, printed_name, 
            printed_text, printed_type_line, promo, promo_types, rarity, 
            released_at, reprint, scryfall_set_uri, set_name, set_search_uri, 
            set_type, set_uri, set_code, set_id, story_spotlight, 
            textless, variation, variation_of, security_stamp, watermark
=======
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
>>>>>>> b305ead (feat(database.cards): update cards cli and init database on flask start)
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


    def _insert_all_parts(self, cursor: sqlite3.Cursor, core_id: str,
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
        params = None
        for part in all_parts:
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

        query = """
        INSERT OR REPLACE INTO all_parts (
            core_id, scryfall_id, component, name, type_line, supertype,
            cardtype, subtype, uri
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        if params is not None:
            cursor.execute(query, params)


    def _insert_card_face(self, cursor: sqlite3.Cursor, core_id: str,
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
            assert(isinstance(image_uris, dict))

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

            cursor.execute(query, params)


    def populate_card_database(self) -> bool:
        """Populates the cards database from default_cards.json

        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            try:
                import ijson
            except ImportError:
                click.echo("Error: ijson is not installed. Please run "
                           "'pip install ijson'", err=True)
                return False

            conn = get_db_connection("cards")
            cursor = conn.cursor()

            conn.execute("BEGIN TRANSACTION")

            # Stats about the transaction
            start_time = datetime.now()
            cards_processed = 0
            cards_inserted = 0

            click.echo("Starting database population from "
                       f"{self.__default_cards_path}")
            click.echo(f"Started at {start_time}")

            # Use ijson to incrementally process the JSON
            with open(self.__default_cards_path, "rb") as f:
                # Go through all the cards
                for card in ijson.items(f, "item", use_float=True):
                    cards_processed += 1

                    # The core data for a reversible_card doesn't contain the
                    # type_line, but since both faces are the same card,
                    # just grab the type_line from one and put it as the core
                    # type_line
                    if card.get("layout") == "reversible_card":
                        face = card.get("card_faces")
                        card["type_line"] = face[0].get("type_line")

                    types = ["supertype", "cardtype", "subtype"]
                    card_types = _get_card_types(card.get("type_line"))
                    for t in types:
                        if t in card_types:
                            card[t] = card_types.get(t)

                    try:
                        # Insert core data
                        self._insert_core_data(cursor, card)

                        if "all_parts" in card and card["all_parts"]:
                            self._insert_all_parts(cursor, card["id"],
                                                   card["all_parts"])

                        if "card_faces" in card and card["card_faces"]:
                            self._insert_card_face(cursor, card["id"],
                                                   card["card_faces"])

                        cards_inserted += 1

                        # Commit every 1000 cards
                        if cards_inserted % 1000 == 0:
                            conn.commit()
                            conn.execute("BEGIN TRANSACTION")
                            elapsed = datetime.now() - start_time
                            click.echo(f"Processed {cards_processed} cards, "
                                       f"inserted {cards_inserted} in "
                                       f"{elapsed}")
                    except Exception as e:
                        click.echo("Error processing card "
                                   f"{card.get("name", "unknown")}: {e}",
                                   err=True)
                        continue

                # Commit anything leftover
                conn.commit()

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
            if "conn" in locals():
                conn.rollback()
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


def update_default_cards_json() -> bool:
    """Update the default_cards.json from Scryfall.

    This function creates a CardsManager, uses it to update the
    default_cards.json, and properly closes the session when done.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    with CardsManager() as manager:
        if manager._bulk_data_up_to_date():
            return False
        return manager._download_default_cards()
