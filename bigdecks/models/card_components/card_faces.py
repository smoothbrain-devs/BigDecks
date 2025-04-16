"""Card faces"""


from __future__ import annotations
from .enums import Colors
from .wrappers import ImageUris
from bigdecks.database import get_db_connection
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bigdecks.models.card import Card
import sqlite3


class CardFace():
    """Represents card faces for cards with more than one face.

    Available properties
    --------------------
    - id
    - cmc
    - color_indicator
    - colors
    - defense
    - flavor_text
    - image_uris
    - layout
    - loyalty
    - mana_cost
    - name
    - oracle_text
    - power
    - printed_name
    - printed_text
    - printed_type_line
    - toughness
    - type_line
    - super_type
    - card_type
    - sub_type
    """
    def __init__(self, row: dict[str, object], parent: Card):
        self.__id = row["id"]
        assert isinstance(self.__id, int)
        self.__cmc = row.get("cmc")
        assert isinstance(self.__cmc, (float | None))
        self.__color_indicator = parent._get_colors(row.get("color_indicator"))
        assert isinstance(self.__color_indicator, (Colors | None))
        self.__colors = parent._get_colors(row.get("colors"))
        assert isinstance(self.__colors, (Colors | None))
        self.__flavor_text = row.get("flavor_text")
        assert isinstance(self.__flavor_text, (str | None))
        self.__image_uris = ImageUris(row)
        assert isinstance(self.__image_uris, ImageUris)
        self.__layout = row.get("layout")
        assert isinstance(self.__layout, (str | None))
        self.__mana_cost = row["mana_cost"]
        assert isinstance(self.__mana_cost, str)
        self.__name = row["name"]
        assert isinstance(self.__name, str)
        self.__oracle_text = row.get("oracle_text")
        assert isinstance(self.__oracle_text, (str | None))
        self.__power = row.get("power")
        assert isinstance(self.__power, (str | None))
        self.__toughness = row.get("toughness")
        assert isinstance(self.__toughness, (str | None))
        self.__type_line = row.get("type_line")
        assert isinstance(self.__type_line, (str | None))
        self.__supertype = parent._parse_json_array(row["supertype"])
        assert isinstance(self.__supertype, (list | None))
        self.__cardtype = parent._parse_json_array(row["cardtype"])
        assert isinstance(self.__cardtype, (list | None))
        self.__subtype = parent._parse_json_array(row["subtype"])
        assert isinstance(self.__subtype, (list | None))

    @property
    def id(self) -> int:
        """Get the internal database id for this card face.

        Useful to speed up lookups in the database for this card face.

        Returns
        -------
        int
        """
        assert isinstance(self.__id, int)
        return self.__id

    @property
    def cmc(self) -> float | None:
        """Get the cmc for this card face.

        Returns
        -------
        float | None
        """
        assert isinstance(self.__cmc, (float | None))
        return self.__cmc

    @property
    def color_indicator(self) -> Colors | None:
        """Get the color indicator(s) for this card face.

        Returns
        -------
        list[Colors] | None
        """
        assert isinstance(self.__color_indicator, (Colors | None))
        return self.__color_indicator

    @property
    def colors(self) -> Colors | None:
        """Get the colors for this card face.

        Returns
        -------
        Colors | None
        """
        assert isinstance(self.__colors, (Colors | None))
        return self.__colors

    @property
    def defense(self, conn: sqlite3.Connection | None = None) -> str | None:
        """Get the defense of this card face.

        Parameters
        ----------
        conn: sqlite3.Connection | None (default None)
            Connection to the database

        Returns
        -------
        str | None
            str, if this card face has defense.
            None, otherwise.
        """
        from bigdecks.services.card_service import CardService
        defense = CardService.get_defense(self.id, "card_face", conn)
        return defense

    @property
    def flavor_text(self) -> str | None:
        """Get the flavor text for this card face.

        Returns
        -------
        str | None
            str, if the card has flavor text
            None, otherwise
        """
        assert isinstance(self.__flavor_text, (str | None))
        return self.__flavor_text

    @property
    def image_uris(self) -> ImageUris:
        """Get the image uris for this card face.

        Returns
        -------
        ImageUris
        """
        assert isinstance(self.__image_uris, ImageUris)
        return self.__image_uris

    @property
    def layout(self) -> str:
        """Get the layout for this card face.

        Returns
        -------
        str
        """
        assert isinstance(self.__layout, str)
        return self.__layout

    @property
    def loyalty(self, conn: sqlite3.Connection | None = None) -> str | None:
        """Get the loyalty for this card face.

        Returns
        -------
        str | None
        """
        from bigdecks.services.card_service import CardService
        loyalty = CardService.get_loyalty(self.id, "card_face", conn)
        return loyalty

    @property
    def mana_cost(self) -> str:
        """Get the mana cost for this card.

        Returns
        -------
        str
        """
        assert isinstance(self.__mana_cost, str)
        return self.__mana_cost

    @property
    def name(self) -> str:
        """Get the name of this card face.

        Returns
        -------
        str
        """
        assert isinstance(self.__name, str)
        return self.__name

    @property
    def oracle_text(self) -> str | None:
        """Get the oracle text for this card.

        Returns
        -------
        str | None
        """
        assert isinstance(self.__oracle_text, (str | None))
        return self.__oracle_text

    @property
    def power(self) -> str | None:
        """Get the power for this card.

        Returns
        -------
        str | None
        """
        assert isinstance(self.__power, (str | None))
        return self.__power

    @property
    def toughness(self) -> str | None:
        """Get the toughness for this card face.

        Returns
        -------
        str | None
        """
        assert isinstance(self.__toughness, (str | None))
        return self.__toughness

    @property
    def type_line(self) -> str | None:
        """Get the type line for this card

        Returns
        -------
        str
        """
        assert isinstance(self.__type_line, (str | None))
        return self.__type_line

    @property
    def super_type(self) -> list[str] | None:
        """Get the super types for this card face.

        Returns
        -------
        list[str] | None
            list[str], if this card has at least 1 super type
            None, otherwise
        """
        assert isinstance(self.__supertype, (list | None))
        return self.__supertype

    @property
    def card_type(self) -> list[str] | None:
        """Get the card types for this card face.

        Returns
        -------
        list[str] | None
            list[str] if this card has at least 1 card type.
            None otherwise.
        """
        assert isinstance(self.__cardtype, (list | None))
        return self.__cardtype

    @property
    def sub_type(self) -> list[str] | None:
        """Get the sub types for this card face.

        Returns
        -------
        list[str] | None
            list[str] if this card has at least 1 sub type.
            None otherwise.
        """
        assert isinstance(self.__subtype, (list | None))
        return self.__subtype

    @classmethod
    def get_card_faces(cls, parent: Card,
                       conn: sqlite3.Connection | None = None
                       ) -> list[CardFace]:
        """Instantiates CardFace objects"""
        from bigdecks.services.card_service import CardService
        rows = CardService.get_card_faces(parent.scryfall_id, conn)
        return [CardFace(dict(row), parent) for row in rows]
