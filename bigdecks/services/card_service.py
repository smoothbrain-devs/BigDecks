"""Service layer for retrieving card information and instantiating Cards."""

import sqlite3
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bigdecks.models.card import Card
from bigdecks.database import get_db_connection


class CardService:
    _SELECT_CARD = """
        SELECT id, scryfall_id, layout, all_parts, card_faces, cmc,
        color_identity, keywords, standard, future, historic, timeless,
        gladiator, pioneer, explorer, modern, legacy, pauper, vintage,
        penny, commander, oathbreaker, standardbrawl, brawl, alchemy,
        paupercommander, duel, oldschool, premodern, predh, mana_cost, name,
        oracle_text, power, toughness, type_line, supertype, cardtype,
        subtype, collector_number, flavor_text, paper, arena, mtgo, png,
        border_crop, art_crop, large, normal, small, price_usd, price_usd_foil,
        price_usd_etched, price_eur, price_eur_foil, price_eur_etched,
        price_tix, rarity, reprint, set_name, set_code
        """
    _SELECT_CARD_FACES = """
        SELECT id, cmc, color_indicator, colors, defense, flavor_text,
        image_uris, layout, loyalty, mana_cost, name, oracle_text, power,
        toughness, type_line, supertype, cardtype, subtype
        """

    _SELECT_ARENA_ID = "SELECT arena_id"
    _SELECT_DEFENSE = "SELECT defense"
    _SELECT_GAME_CHANGER = "SELECT game_changer"
    _SELECT_LOYALTY = "SELECT loyalty"
    _SELECT_FLAVOR_NAME = "SELECT flavor_name"
    _SELECT_PRODUCED_MANA = "SELECT produced_mana"

    _FROM_CORE = " FROM core"
    _FROM_ALL_PARTS = " FROM all_parts"
    _FROM_CARD_FACES = " FROM card_faces"

    _BY_ID = " WHERE id = ?;"
    _BY_SCRYFALL_ID = " WHERE scryfall_id = ?;"
    _BY_NAME = " WHERE name = ?;"
    _BY_CORE_ID = " WHERE core_id = ?;"

    _RANDOM_CARD = """
        ORDER BY RANDOM()
        LIMIT 1;
        """

    _SELECT_PRINTS_BY_NAME = """
        SELECT id, set_name, set_code, collector_number, png,
        border_crop, art_crop, large, normal, small
        FROM core
        WHERE name = ?;
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

        query = cls._SELECT_CARD + cls._FROM_CORE + cls._RANDOM_CARD
        row = conn.execute(query).fetchone()

        from bigdecks.models.card import Card
        return Card(dict(row), conn)

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
        assert isinstance(conn, (sqlite3.Connection | None))
        assert isinstance(scryfall_id, str)

        if not conn:
            conn = get_db_connection("cards")

        query = cls._SELECT_CARD + cls._FROM_CORE + cls._BY_SCRYFALL_ID
        params = (scryfall_id,)
        row = conn.execute(query, params).fetchone()

        from bigdecks.models.card import Card
        return Card(dict(row), conn)

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
