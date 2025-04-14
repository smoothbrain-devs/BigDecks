"""Service layer for retrieving card information and instantiating Cards."""

import sqlite3
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bigdecks.models.card import Card
from bigdecks.database import get_db_connection


class CardService:
    # SQL Stuff
    _SQL_SELECT_CARD = """
        SELECT id, scryfall_id, layout, all_parts, card_faces, cmc,
        color_identity, keywords, standard, future, historic, timeless,
        gladiator, pioneer, explorer, modern, legacy, pauper, vintage,
        penny, commander, oathbreaker, standardbrawl, brawl, alchemy,
        paupercommander, duel, oldschool, premodern, predh, name,
        oracle_text, power, toughness, type_line, supertype, cardtype,
        subtype, collector_number, flavor_text, paper, arena, mtgo, png,
        border_crop, art_crop, large, normal, small, price_usd, price_usd_foil,
        price_usd_etched, price_eur, price_eur_foil, price_eur_etched,
        price_tix, rarity, reprint, set_name, set_code
        FROM core
        """

    _SQL_RANDOM_CARD = """
        ORDER BY RANDOM()
        LIMIT 1;
        """

    _SQL_BY_SCRYFALL_ID = "WHERE scryfall_id = ?;"

    _SQL_SELECT_ARENA_ID = """
        SELECT arena_id
        FROM core
        WHERE id = ?;
        """

    _SQL_SELECT_PRINTS_BY_NAME = """
        SELECT scryfall_id, set_name, png, border_crop, art_crop, large, normal, small
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

        query = cls._SQL_SELECT_CARD + cls._SQL_RANDOM_CARD
        row = conn.execute(query).fetchone()

        from bigdecks.models.card import Card
        return Card(dict(row), conn)

    @classmethod
    def get_card_by_scryfall_id(cls, scryfall_id: str,
                                conn: sqlite3.Connection | None = None
                                ) -> "Card":
        """Get a card by it"s scryfall id.

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

        query = cls._SQL_SELECT_CARD + cls._SQL_BY_SCRYFALL_ID
        params = (scryfall_id,)
        row = conn.execute(query, params).fetchone()

        from bigdecks.models.card import Card
        return Card(dict(row), conn)

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

        query = cls._SQL_SELECT_ARENA_ID
        params = (id,)
        row = conn.execute(query, params).fetchone()
        arena_id = int(row["arena_id"])

        assert isinstance(arena_id, int)
        return arena_id

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

        query = cls._SQL_SELECT_PRINTS_BY_NAME
        params = (name,)
        rows = conn.execute(query, params).fetchall()

        return rows
