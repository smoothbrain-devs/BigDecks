"""Related parts"""

from __future__ import annotations
from .wrappers import ImageUris
from bigdecks.database import get_db_connection
import sqlite3


class RelatedParts():
    """Represents the cards related to a card.

    Available Properties
    --------------------
    - scryfall_id
    - component_type
    - name
    - type_line
    - image_uris
    """
    def __init__(self, row: sqlite3.Row,
                 conn: sqlite3.Connection | None = None):
        """Fetch the related parts data from the related parts table.

        Parameters
        ----------
        row: sqlite3.Row
            A row from the all_parts table.
        """
        if conn is None:
            conn = get_db_connection("cards")
        # We can get away with using a row here since all the fields being
        # accessed are guaranteed by the database schema.
        self.__scryfall_id = row["scryfall_id"]
        self.__component_type = row["component"]
        self.__name = row["name"]
        self.__type_line = row["type_line"]
        self.__image_uris = self.__get_image_uris(conn)

        def __str__(self):
            rep = \
                f"Scryfall ID: {self.scryfall_id}\n"\
                f"Component type: {self.component_type}\n"\
                f"Name: {self.name}\n"\
                f"Type line: {self.type_line}\n"\
                f"Image uris: {self.image_uris.as_dict()}\n"
            return rep

    def __get_image_uris(self, conn: sqlite3.Connection | None = None):
        """Fetch the image uris from the core table."""
        if conn is None:
            conn = get_db_connection("cards")
        row = conn.execute(
                """
                SELECT png, border_crop, art_crop, large, normal, small
                FROM core
                WHERE scryfall_id = ?;
                """,
                (self.__scryfall_id,)).fetchone()
        print(self.name, self.scryfall_id)
        return ImageUris(dict(row))

    @property
    def scryfall_id(self) -> str:
        """Get the scryfall id for the card related to this part.

        Returns
        -------
        str
            Scryfall UUID
        """
        assert isinstance(self.__scryfall_id, str)
        return self.__scryfall_id

    @property
    def component_type(self) -> str:
        """Get the type of component this related part is.

        4 types:
        - 'combo_piece'
        - 'token'
        - 'meld_part'
        - 'meld_result'

        Returns
        -------
        str
        """
        assert isinstance(self.__component_type, str)
        return self.__component_type

    @property
    def name(self) -> str:
        """Name of this related part.

        Returns
        -------
        str
        """
        assert isinstance(self.__name, str)
        return self.__name

    @property
    def type_line(self) -> str:
        """Get the type line of this related part.

        Returns
        -------
        str
        """
        assert isinstance(self.__type_line, str)
        return self.__type_line

    @property
    def image_uris(self) -> ImageUris:
        """Get the ImageUris object associated to this related part.

        Returns
        -------
        ImageUris
        """
        assert isinstance(self.__image_uris, ImageUris)
        return self.__image_uris

    @classmethod
    def get_related_parts(cls, parent_scryfall_id: str, parent_name: str,
                          conn: sqlite3.Connection | None = None,
                          ) -> list[RelatedParts]:
        """Instantiates the RelatedParts object(s) to a card."""
        if conn is None:
            conn = get_db_connection("cards")
        rows = conn.execute(
            """
            SELECT *
            FROM all_parts
            WHERE core_id = ?;
            """,
            (parent_scryfall_id,)).fetchall()
        return [RelatedParts(row, conn) for row in rows
                if row["name"] != parent_name]
