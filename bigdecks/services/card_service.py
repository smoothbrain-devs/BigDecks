"""Service layer for retrieving card information and instantiating Cards."""

import sqlite3
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bigdecks.models.card import Card
from bigdecks.database import get_db_connection


class CardService:
    _SELECT_CARD_C = """
        SELECT c.id, c.scryfall_id, c.layout, c.all_parts, c.card_faces, c.cmc,
        c.color_identity, c.keywords, c.standard, c.future, c.historic, c.timeless,
        c.gladiator, c.pioneer, c.explorer, c.modern, c.legacy, c.pauper, c.vintage,
        c.penny, c.commander, c.oathbreaker, c.standardbrawl, c.brawl, c.alchemy,
        c.paupercommander, c.duel, c.oldschool, c.premodern, c.predh, c.mana_cost, c.name,
        c.oracle_text, c.power, c.toughness, c.type_line, c.supertype, c.cardtype,
        c.subtype, c.collector_number, c.flavor_text, c.paper, c.arena, c.mtgo, c.png,
        c.border_crop, c.art_crop, c.large, c.normal, c.small, c.price_usd, c.price_usd_foil,
        c.price_usd_etched, c.price_eur, c.price_eur_foil, c.price_eur_etched,
        c.price_tix, c.rarity, c.reprint, c.set_name, c.set_code
        """
    _SELECT_CARD_FACES = """
        SELECT id, cmc, color_indicator, colors, defense, flavor_text,
        png, border_crop, art_crop, large, normal, small, layout, loyalty,
        mana_cost, name, oracle_text, power, toughness, type_line, supertype,
        cardtype, subtype
        """
    _SELECT_PRINTS_BY_NAME = """
        SELECT id, set_name, set_code, collector_number, price_usd,
        price_usd_foil, price_usd_etched, price_eur, price_eur_foil,
        price_eur_etched, price_tix, png, border_crop, art_crop, large,
        normal, small
        FROM core
        WHERE name = ?;
        """
    _SELECT_SEARCH = """
        SELECT c.name, c.scryfall_id, c.set_code, c.collector_number, c.small, c.card_faces
        """

    _SELECT_ARENA_ID = "SELECT arena_id"
    _SELECT_DEFENSE = "SELECT defense"
    _SELECT_GAME_CHANGER = "SELECT game_changer"
    _SELECT_LOYALTY = "SELECT loyalty"
    _SELECT_FLAVOR_NAME = "SELECT flavor_name"
    _SELECT_PRODUCED_MANA = "SELECT produced_mana"

    _FROM_CORE = " FROM core c"
    _FROM_ALL_PARTS = " FROM all_parts"
    _FROM_CARD_FACES = " FROM card_faces"

    _BY_ID = " WHERE id = ?;"
    _BY_SCRYFALL_ID = " WHERE scryfall_id = ?;"
    _BY_NAME = " WHERE name = ?;"
    _BY_CORE_ID = " WHERE core_id = ?;"
    _BY_SET_COLLECTOR = " WHERE set_code = ? AND collector_number = ?;"

    _RANDOM_CARD = """
        ORDER BY RANDOM()
        LIMIT 1;
        """

    @classmethod
    def get_random_card(cls, conn: sqlite3.Connection | None = None) -> "Card":
        """Get a random card from the core table.

        Parameters
        ----------
        conn: sqlite3.Connection | None (default None)
            Connection to 'cards' database.

        Returns
        -------
        Card
        """
        assert isinstance(conn, (sqlite3.Connection | None))
        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_CARD_C + cls._FROM_CORE + cls._RANDOM_CARD
        row = conn.execute(query).fetchone()

        from bigdecks.models.card import Card
        return Card(row, conn)

    @classmethod
    def get_card_by_scryfall_id(cls, scryfall_id: str,
                                conn: sqlite3.Connection | None = None
                                ) -> "Card":
        """Get a card by it's scryfall id.

        Parameters
        ----------
        conn: sqlite3.Connection | None
            Connection to the 'cards' database.
        scryfall_id: str
            Scryfall ID of the card to retrieve.

        Returns
        -------
        Card
        """
        assert isinstance(scryfall_id, str)
        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_CARD_C + cls._FROM_CORE + cls._BY_SCRYFALL_ID
        params = (scryfall_id,)
        row = conn.execute(query, params).fetchone()

        from bigdecks.models.card import Card
        return Card(row, conn)

    @classmethod
    def get_card_by_set_collector(cls, set_code: str, collector_number: str,
                                  conn: sqlite3.Connection | None = None
                                  ) -> "Card":
        """Get a card using it's set code and collector number.

        Parameters
        ----------
        set_code: str
            Set code for the card.
        collector_number: str
            Collector number for the card.
        conn: sqlite3.Connection | None
            Connection to the 'cards' database.
        """
        assert isinstance(set_code, str)
        assert isinstance(collector_number, str)
        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_CARD_C + cls._FROM_CORE + cls._BY_SET_COLLECTOR
        params = (set_code, collector_number,)
        row = conn.execute(query, params).fetchone()

        from bigdecks.models.card import Card
        return Card(row, conn)

    @classmethod
    def get_card_faces(cls, scryfall_id: str,
                       conn: sqlite3.Connection | None = None
                       ) -> list[sqlite3.Row]:
        """Get the card faces for a Card.

        Parameters
        ----------
        scryfall_id: str
            Scryfall ID of the card to select card faces for.
        conn: sqlite3.Connction | None
            Connection to 'cards' database.

        Returns
        -------
        list[sqlite3.Row]
            Rows for found card faces.
        """
        assert isinstance(scryfall_id, str)

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_CARD_FACES + cls._FROM_CARD_FACES + cls._BY_CORE_ID
        params = (scryfall_id,)
        rows = conn.execute(query, params).fetchall()
        assert isinstance(rows, list)

        return rows

    @classmethod
    def get_arena_id(cls, id: int,
                     conn: sqlite3.Connection | None = None) -> int:
        """Get arena id for a given card.

        Parameters
        ----------
        id: int
            The id for the card.
        conn: sqlite3.Connection | None
            Connection to the 'cards' database

        Returns
        -------
        int
            Arena ID
        """
        assert isinstance(id, int)
        assert isinstance(conn, (sqlite3.Connection | None))

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_ARENA_ID + cls._FROM_CORE + cls._BY_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()
        arena_id = int(row["arena_id"])

        assert isinstance(arena_id, int)
        return arena_id

    @classmethod
    def get_defense(cls, id: int, table: str,
                    conn: sqlite3.Connection | None = None) -> str | None:
        """Get defense for a given card

        Parameters
        ----------
        id: int
            The id for the card.
        table: str
            'card', select from core table
            'card_face', select from card_faces table
        conn: sqlite3.Connection | None
            Connection to the 'cards' database

        Returns
        -------
        str
        """
        assert isinstance(id, int)
        assert isinstance(table, str)

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_DEFENSE
        if table == "card":
            query += cls._FROM_CORE
        elif table == "card_face":
            query += cls._FROM_CARD_FACES
        query += cls._BY_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()

        try:
            defense = row["defense"]
        except KeyError:
            defense = None

        return defense

    @classmethod
    def get_game_changer(cls, id: int,
                         conn: sqlite3.Connection | None = None) -> bool:
        """Get whether a card is a game changer or not.

        Parameters
        ----------
        id: int
            The id for the card.
        conn: sqlite3.Connection | None
            Connection to 'cards' database.

        Returns
        -------
        bool
            True if card is game changer.
            False otherwise.
        """
        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_GAME_CHANGER + cls._FROM_CORE + cls._BY_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()

        return bool(row["game_changer"])

    @classmethod
    def get_loyalty(cls, id: int, table: str,
                    conn: sqlite3.Connection | None = None) -> str | None:
        """Get the loyalty for a card/card_face.

        Parameters
        ----------
        id: int
            Id for the card/card face
        table: str
            'card', select from core table
            'card_face', select from card_faces table
        conn: sqlite3.Connection | None
            Connection to 'cards' database.

        Returns
        -------
        str | None
        """
        assert isinstance(id, int)
        assert isinstance(table, str)

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_LOYALTY
        if table == "card":
            query += cls._FROM_CORE
        elif table == "card_face":
            query += cls._FROM_CARD_FACES
        query += cls._BY_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()

        try:
            loyalty = row["loyalty"]
        except KeyError:
            loyalty = None

        return loyalty

    @classmethod
    def get_flavor_name(cls, id: int, table: str,
                        conn: sqlite3.Connection | None = None) -> str | None:
        """Get the flavor name for a card/card face.

        Parameters
        ----------
        id: int
            Id for the card/card face.
        table: str
            'card', select from core table
            'card_face', select from card_faces table
        conn: sqlite3.Connection | None
            Connection to 'cards' database.

        Returns
        -------
        str | None
            str, if card/card face has a flavor name.
            None, otherwise.
        """
        assert isinstance(id, int)
        assert isinstance(table, str)

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_FLAVOR_NAME
        if table == "card":
            query += cls._FROM_CORE
        elif table == "card_face":
            query += cls._FROM_CARD_FACES
        query += cls._BY_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()

        try:
            flavor_name = row["flavor_name"]
        except KeyError:
            flavor_name = None

        return flavor_name

    @classmethod
    def get_produced_mana(cls, id: int, conn: sqlite3.Connection | None = None
                          ) -> str | None:
        """Get the produced mana for a card.

        Parameters
        ----------
        id: int
            Id for the card.
        conn: sqlite3.Connection | None
            Connection to 'cards' database.

        Returns
        -------
        str | None
            str, json array if card produces mana.
            None, otherwise.
        """
        assert isinstance(id, int)

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_PRODUCED_MANA + cls._FROM_CORE + cls._BY_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()

        try:
            produced_mana = row["produced_mana"]
        except KeyError:
            produced_mana = None

        return produced_mana

    @classmethod
    def get_prints(cls, name: str,
                   conn: sqlite3.Connection | None = None
                   ) -> list[sqlite3.Row] | None:
        """Get a list of other printings of this card.

        Parameters
        ----------
        id: int
            The card's id.
        conn: sqlite3.Connection | None
            Connection to the 'cards' database.

        Returns
        -------
        list[sqlite3.Row] | None
        """
        assert isinstance(name, str)
        assert isinstance(conn, (sqlite3.Connection | None))

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_PRINTS_BY_NAME
        params = (name,)
        rows = conn.execute(query, params).fetchall()

        return rows

    @classmethod
    def search_for(cls, name: str | None = None,
                   colors: list[str] | None = None,
                   page: int = 1, per_page: int = 25,
                   conn: sqlite3.Connection | None = None
                   ) -> dict[str, object]:
        """Search for cards with pagination.

        Parameters
        ----------
        name: str, optional
            Partial or full name to search for.
        colors: list[str], optional
            list of color strings (e.g. "W", "U").
        page: int, default 1
            The page number (1-indexed).
        per_page: int, default 25
            Number of results to show per page.

        Returns
        -------
        dict
        {
            - "cards": list[Card], List of Card objects for the current page.
            - "total": int,        Total number of matching cards.
            - "pages": int,        Total number of pages.
            - "current_page": int, The current page number.
        }
        """
        if not conn:
            conn = get_db_connection("cards")

        # Build the base query
        base_query = cls._SELECT_SEARCH +\
            """
            FROM core c
            JOIN (
                SELECT name, MIN(id) as min_id
                FROM core
                WHERE name LIKE ?
                GROUP BY name
            ) as distinct_names
            ON c.id = distinct_names.min_id
            """

        params = [f"%{name}%"]

        # Get total count for pagination
        count_query = base_query.replace(cls._SELECT_SEARCH, "SELECT COUNT(*)")
        total = conn.execute(count_query, params).fetchone()[0]

        # Add pagination
        query = base_query + " LIMIT ? OFFSET ?"
        offset = (page - 1) * per_page
        params.extend([str(per_page), str(offset)])

        # Calculate total pages
        pages = (total + per_page - 1) // per_page

        # Execute and return dict
        rows = conn.execute(query, params).fetchall()
        dicts = [dict(row) for row in rows]
        for card in dicts:
            if card["card_faces"] and not card["small"]:
                card["small"] = conn.execute("SELECT small FROM card_faces WHERE ? = core_id", (card["scryfall_id"],)).fetchone()["small"]

        return {
            "cards": dicts,
            "total": total,
            "pages": pages,
            "current_page": page
        }