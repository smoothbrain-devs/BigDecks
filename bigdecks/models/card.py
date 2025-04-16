"""Card datamodel / Active Record"""


from __future__ import annotations
from bigdecks.database import get_db_connection
from .card_components.enums import (
    Colors,
    GameAvailability,
    Rarity
)
from .card_components.wrappers import (
    CardLegalities,
    ImageUris,
    Prices
)
from .card_components.card_faces import CardFace
from .card_components.related_parts import RelatedParts
import sqlite3
import json


class Card:
    """Represents card information from the cards database, also handles
    simple card retrieval.

    Available Properties
    --------------------
    - id
    - scryfall_id
    - arena_id
    - layout
    - has_related_parts
    - related_parts
    - has_card_faces
    - front_face
    - back_face
    - cmc
    - color_identity
    - colors
    - defense
    - game_changer
    - keywords
    - legality
    - loyalty
    - mana_cost
    - name
    - oracle text
    - power
    - produced_mana
    - toughness
    - type_line
    - super_type
    - card_type
    - sub_type
    - collector_number
    - flavor_name
    - flavor_text
    - game_availability
    - image_uris
    - prices
    - rarity
    - prints
    - set_name
    - set_code
    """

    def __init__(self, row: dict[str, object],
                 conn: sqlite3.Connection | None = None):
        """
        Parameters
        ----------
        row: dict[str, object]
            A row from the cards database core table converted to a dict.
        """
        assert isinstance(row, dict)
        self.__id = row["id"]
        assert isinstance(self.__id, int)
        self.__scryfall_id = row["scryfall_id"]
        assert isinstance(self.__scryfall_id, str)
        self.__layout = row["layout"]
        assert isinstance(self.__layout, str)
        self.__has_related_parts = bool(row["all_parts"])
        assert isinstance(self.__has_related_parts, bool)
        self.__has_card_faces = bool(row["card_faces"])
        assert isinstance(self.__has_card_faces, bool)
        self.__cmc = row["cmc"]
        assert isinstance(self.__cmc, float)
        self.__color_identity = self._get_colors(row["color_identity"])
        assert isinstance(self.__color_identity, Colors)
        self.__colors = self._get_colors(row.get("colors"))
        assert isinstance(self.__colors, (Colors | None))
        self.__keywords = self._parse_json_array(row["keywords"])
        assert isinstance(self.__keywords, (list | None))
        self.__legality = CardLegalities(row)
        assert isinstance(self.__legality, CardLegalities)
        self.__mana_cost = row.get("mana_cost")
        assert isinstance(self.__mana_cost, str | None)
        self.__name = row["name"]
        assert isinstance(self.__name, str)
        self.__oracle_text = row.get("oracle_text")
        assert isinstance(self.__oracle_text, (str | None))
        self.__power = row.get("power")
        assert isinstance(self.__power, (str | None))
        self.__toughness = row.get("toughness")
        assert isinstance(self.__toughness, (str | None))
        self.__type_line = row["type_line"]
        assert isinstance(self.__type_line, str)
        self.__supertype = self._parse_json_array(row["supertype"])
        assert isinstance(self.__supertype, (list | None))
        self.__cardtype = self._parse_json_array(row["cardtype"])
        assert isinstance(self.__cardtype, (list | None))
        self.__subtype = self._parse_json_array(row["subtype"])
        assert isinstance(self.__subtype, (list | None))
        self.__collector_number = row["collector_number"]
        assert isinstance(self.__collector_number, str)
        self.__flavor_text = row.get("flavor_text")
        assert isinstance(self.__flavor_text, (str | None))
        self.__game_availability = self.__get_game_availability(row)
        assert isinstance(self.__game_availability, GameAvailability)
        self.__image_uris = ImageUris(row)
        assert isinstance(self.__image_uris, ImageUris)
        self.__prices = Prices(row)
        assert isinstance(self.__prices, Prices)
        self.__rarity = self.__get_rarity(row)
        assert isinstance(self.__rarity, (Rarity | None))
        self.__prints = self.__get_other_prints(conn)
        self.__set_name = row["set_name"]
        assert isinstance(self.__set_name, str)
        self.__set_code = row["set_code"]
        assert isinstance(self.__set_code, str)

        # Doing these at the bottom since it relies on some of the other
        # card information being available.
        if self.__has_related_parts:
            self.__related_parts = RelatedParts.get_related_parts(
                self.__scryfall_id, self.__name, conn)
            assert isinstance(self.__related_parts, list)
            assert isinstance(self.__related_parts[0], RelatedParts)

        if self.__has_card_faces:
            front, back = CardFace.get_card_faces(self, conn)
            assert isinstance(front, CardFace)
            assert isinstance(back, CardFace)
            self.__card_front = front
            self.__card_back = back

    def __str__(self):
        """String representation of core data for this Card."""
        rep = \
            f"Internal ID: {self.id}\n"\
            f"Scryfall ID: {self.scryfall_id}\n"\
            f"Layout: {self.layout}\n"\
            f"Has all parts: {self.has_related_parts}\n"\
            f"Has card faces: {self.has_card_faces}\n"\
            f"CMC: {self.cmc}\n"\
            f"Color Identity: {self.color_identity}\n"\
            f"Colors: {self.colors}\n"\
            f"Keywords: {self.keywords}\n"\
            f"Legality: {self.legality.as_dict()}\n"\
            f"Name: {self.name}\n"\
            f"Oracle Text: {self.oracle_text}\n"\
            f"Power: {self.power}\n"\
            f"Toughness: {self.toughness}\n"\
            f"Type line: {self.type_line}\n"\
            f"Super types: {self.super_type}\n"\
            f"Card types: {self.card_type}\n"\
            f"Sub types: {self.sub_type}\n"\
            f"Collector number: {self.collector_number}\n"\
            f"Flavor text: {self.flavor_text}\n"\
            f"Game availability: {self.game_availability.as_dict()}\n"\
            f"Image uris: {self.image_uris.as_dict()}\n"\
            f"Prices: {self.prices.as_dict()}\n"\
            f"Set Name: {self.set_name}\n"\
            f"Set Code: {self.set_code}\n"
        return rep

    @property
    def id(self) -> int:
        """The id of this card.

        Use this for faster lookup in the core table.

        Returns
        -------
        int
            The id of the card in the table it originates from.
        """
        assert isinstance(self.__id, int)
        return self.__id

    @property
    def scryfall_id(self) -> str:
        """The scryfall id of this card.

        Returns
        -------
        str
            UUID used by scryfall to identify objects.
        """
        assert isinstance(self.__scryfall_id, str)
        return self.__scryfall_id

    @property
    def arena_id(self, conn: sqlite3.Connection | None = None) -> int | None:
        """The arena id of this card, if it exists.

        Returns
        -------
        int | None
            int if the card has an arena id.
            None otherwise.
        """
        if not (bool(self.__game_availability & GameAvailability.arena)):
            arena_id = None
        else:
            from bigdecks.services.card_service import CardService
            arena_id = CardService.get_arena_id(self.id, conn)
            assert isinstance(arena_id, int)
        return arena_id

    @property
    def layout(self) -> str:
        """The layout of this card.

        Check https://scryfall.com/docs/api/layouts for the available options.
        """
        assert isinstance(self.__layout, str)
        return self.__layout

    @property
    def has_related_parts(self) -> bool:
        """Get whether or not this card has related card parts.

        Returns
        -------
            True, if has related parts.
            False, otherwise.
        """
        assert isinstance(self.__has_related_parts, bool)
        return self.__has_related_parts

    @property
    def related_parts(self) -> list[RelatedParts] | None:
        """Get the list of related parts for this card.

        Only exists if this card has related parts.

        Returns
        -------
        list[RelatedParts]
        """
        if self.__has_related_parts:
            assert isinstance(self.__related_parts, list)
            assert isinstance(self.__related_parts[0], RelatedParts)
            return self.__related_parts
        else:
            return None

    @property
    def has_card_faces(self) -> bool:
        """Get whether or not this card has card faces associated to it.

        Returns
        -------
            True, if the card has more than one face.
            False, if the card has only one face.
        """
        assert isinstance(self.__has_card_faces, bool)
        return self.__has_card_faces

    @property
    def front_face(self) -> CardFace | None:
        """Get the front face for this card.

        Use only when a card has more than one face.

        Returns
        -------
        CardFace
        """
        if self.has_card_faces:
            assert isinstance(self.__card_front, CardFace)
            return self.__card_front
        else:
            return None

    @property
    def back_face(self) -> CardFace | None:
        """Get the back face for this card.

        Use only when a card has more than one face.

        Returns
        -------
        CardFace
        """
        if self.has_card_faces:
            assert isinstance(self.__card_back, CardFace)
            return self.__card_back
        else:
            return None

    @property
    def cmc(self) -> float:
        """The converted mana cost of this card, may be a fractional value.

        Returns
        -------
        float
        """
        assert isinstance(self.__cmc, float)
        return self.__cmc

    @property
    def color_identity(self) -> Colors | None:
        """The color identity of this card.

        Check https://mtg.fandom.com/wiki/Color_identity for the rules of
        color identity.
        The tldr is that if a card has a color in it's cost or rules text
        (minus reminder text), that color is a part of it's identity.

        Returns
        -------
        Colors | None
            Colors enum, if the card has a color identity.
            None, if the card doesn't have a color identity. (Idk if this can
            happen)
        """
        return self.__color_identity

    @property
    def colors(self) -> Colors | None:
        """The colors of this card.

        Returns
        -------
        Colors | None
            Colors enum, if this card has colors (including colorless).
            None, if this card doesn't have colors associated to it.
        """
        return self.__colors

    @property
    def defense(self, conn: sqlite3.Connection | None = None) -> str:
        """Get the defense for this card.

        Parameters
        ----------
        conn: sqlite3.Connection | None (default = None)
            Connection to cards database.

        Returns
        -------
        str
        """
        from bigdecks.services.card_service import CardService
        defense = CardService.get_defense(self.id, "card", conn)
        assert isinstance(defense, str)
        return defense

    @property
    def game_changer(self, conn: sqlite3.Connection | None = None) -> bool:
        """Get whether this card is a 'game changer.'

        Parameters
        ----------
        conn: sqlite3.Connection | None (default = None)
            Connection to cards database.

        Returns
        -------
        bool
        """
        from bigdecks.services.card_service import CardService
        game_changer = CardService.get_game_changer(self.id, conn)
        assert isinstance(game_changer, bool)
        return game_changer

    @property
    def loyalty(self, conn: sqlite3.Connection | None = None) -> str | None:
        """Get the loyalty for this card.

        Parameters
        ----------
        conn: sqlite3.Connection | None (default = None)
            Connection to cards database.

        Returns
        -------
        str | None
            str, if this card has a loyalty value.
            None otherwise.
        """
        from bigdecks.services.card_service import CardService
        loyalty = CardService.get_loyalty(self.id, "card", conn)
        assert isinstance(loyalty, (str | None))
        return loyalty

    @property
    def mana_cost(self) -> str | None:
        """Get the mana cost for this card.

        Parameters
        ----------
        conn: sqlite3.Connection | None (default = None)
            Connection to cards database.

        Returns
        -------
        str | None
            str, if this card has a mana cost.
            None otherwise.
        """
        assert isinstance(self.__mana_cost, (str | None))
        return self.__mana_cost

    @property
    def keywords(self) -> list[str] | None:
        """List of the keywords of this card if any. Otherwise None.

        Returns
        -------
        list[str] | None
            list[str] if card has keywords.
            None otherwise.
        """
        return self.__keywords

    @property
    def legality(self) -> CardLegalities:
        """Get the format legalities for this card.

        This wrapper class allows for dot notation for accessing format
        legalities. e.g. card.legality.standard (this would return a
        Legality enum). There's also card.legality.as_dict() which returns
        a dict of all the legalities (as Legality enums).
        """
        return self.__legality

    @property
    def name(self) -> str:
        """Get the name of this card.

        Returns
        -------
        str
        """
        assert isinstance(self.__name, str)
        return self.__name

    @property
    def oracle_text(self) -> str | None:
        """Get the oracle text for this card, if it exists.

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
    def produced_mana(self,
                      conn: sqlite3.Connection | None = None) -> Colors | None:
        """Get the colors of the mana produced by this card.

        Parameters
        ----------
        conn: sqlite3.Connection | None
            Connection to 'cards' database.

        Returns
        -------
        Colors | None
            Colors, if card produces mana.
            None, otherwise.
        """
        from bigdecks.services.card_service import CardService
        produced_mana = CardService.get_produced_mana(self.id, conn)
        if produced_mana is not None:
            produced_mana = self._get_colors(produced_mana)

        return produced_mana

    @property
    def toughness(self) -> str | None:
        """Get the toughness for this card.

        Returns
        -------
        str | None
        """
        assert isinstance(self.__toughness, (str | None))
        return self.__toughness

    @property
    def type_line(self) -> str:
        """Get the type_line of this card.

        Returns
        -------
        str
        """
        assert isinstance(self.__type_line, str)
        return self.__type_line

    @property
    def super_type(self) -> list[str] | None:
        """Get the super types for this card.

        Returns
        -------
        list[str] | None
            list[str] if this card has at least 1 super type.
            None otherwise.
        """
        assert isinstance(self.__supertype, (list | None))
        return self.__supertype

    @property
    def card_type(self) -> list[str] | None:
        """Get the card types for this card.

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
        """Get the sub types for this card.

        Returns
        -------
        list[str] | None
            list[str] if this card has at least 1 sub type.
            None otherwise.
        """
        assert isinstance(self.__subtype, (list | None))
        return self.__subtype

    @property
    def collector_number(self) -> str:
        """Get the collector number for this card. Note, a collector 'number'
        is not an integer.

        Returns
        -------
        str
        """
        assert isinstance(self.__collector_number, str)
        return self.__collector_number

    @property
    def flavor_name(self,
                    conn: sqlite3.Connection | None = None) -> str | None:
        """Get the flavor name for this card.

        Returns
        -------
        str | None
        """
        from bigdecks.services.card_service import CardService
        flavor_name = CardService.get_flavor_name(self.id, "card", conn)
        return flavor_name

    @property
    def flavor_text(self) -> str | None:
        """Get the flavor text for this card. Note, a card may not have flavor
        text.

        Returns
        -------
        str | None
            str if the card has flavor text.
            None otherwise.
        """
        assert isinstance(self.__flavor_text, (str | None))
        return self.__flavor_text

    @property
    def game_availability(self) -> GameAvailability:
        """Get the game availability for this card.

        Access the data members through dot notation:
            .paper
            .arena
            .mtgo
        or get a dict[str, bool] where the key is 'paper', 'arena', or 'mtgo'
        using .game_availability.as_dict().

        Returns
        -------
        GameAvailability
            enum(Flag) of game availabilities.
        """
        return self.__game_availability

    @property
    def image_uris(self) -> ImageUris:
        """Get the image uris for this card.

        You can access the uris using dot notation (e.g. card.png)

        Returns
        -------
        ImageUris
            Access data members using dot notation, or retrieve all uris as a
            dict using .image_uris.as_dict()
        """
        assert isinstance(self.__image_uris, ImageUris)
        return self.__image_uris

    @property
    def prices(self) -> Prices:
        """Get the prices for this card.

        Returns
        -------
        Prices
            Access data members using dot notation or retrieve all prices as a
            dict using .as_dict()
        """
        assert isinstance(self.__prices, Prices)
        return self.__prices

    @property
    def rarity(self) -> Rarity:
        """Get the rarity for this card.

        Returns
        -------
        Rarity
        """
        assert isinstance(self.__rarity, Rarity)
        return self.__rarity

    @property
    def prints(self) -> list[dict[str, str | ImageUris]] | None:
        """Get the list of prints for this card.

        Returns
        -------
        list[dict[str, str | ImageUris]
        """
        return self.__prints

    @property
    def set_name(self) -> str:
        """Get the name of the set this card belongs to.

        Returns
        -------
        str
        """
        assert isinstance(self.__set_name, str)
        return self.__set_name

    @property
    def set_code(self) -> str:
        """Get the set code for the set this card belongs to.

        Return
        ------
        str
        """
        assert isinstance(self.__set_code, str)
        return self.__set_code

    def _get_colors(self, field: object) -> Colors | None:
        """Converts list of color strings to a Colors object.

        Parameters
        ----------
        field: str
            json array

        Returns
        -------
        Colors
            Enum containing color information.
        """
        assert isinstance(field, (str | None))
        color_list = self._parse_json_array(field)
        if color_list is None:
            return None

        colors = Colors(0)
        if len(color_list) == 0:
            colors |= Colors.colorless

        else:
            for element in color_list:
                match (element):
                    case "W":
                        colors |= Colors.white
                    case "U":
                        colors |= Colors.blue
                    case "B":
                        colors |= Colors.black
                    case "R":
                        colors |= Colors.red
                    case "G":
                        colors |= Colors.green

        return colors

    def __get_game_availability(self,
                                row: dict[str, object]) -> GameAvailability:
        """Returns a GameAvailabilty enum based on where the card is
        available.
        """
        availability = GameAvailability(0)

        if bool(row["paper"]):
            availability |= GameAvailability.paper
        if bool(row["arena"]):
            availability |= GameAvailability.arena
        if bool(row["mtgo"]):
            availability |= GameAvailability.mtgo

        return availability

    def __get_rarity(self, row: dict[str, object]) -> Rarity | None:
        """Returns rarity enum or None based on the card rarity."""
        match row.get("rarity"):
            case "common":
                rarity = Rarity.common

            case "uncommon":
                rarity = Rarity.uncommon

            case "rare":
                rarity = Rarity.rare

            case "mythic":
                rarity = Rarity.mythic

            case "special":
                rarity = Rarity.special

            case "bonus":
                rarity = Rarity.bonus

            case _:
                rarity = None

        return rarity

    def __get_other_prints(self, conn: sqlite3.Connection | None = None
                           ) -> list[dict[str, str | ImageUris]] | None:
        """Get a list of other printings of this card.

        Parameters
        ----------
        conn: sqlite3.Connection
            Connection to 'cards' database

        Returns
        -------
        list[dict[str, str | ImageUris]] | None
        """
        from bigdecks.services.card_service import CardService

        rows = CardService.get_prints(self.name, conn=conn)

        if rows is None:
            prints = None

        else:
            prints = []
            for row in rows:
                prints.append({"id": row["id"],
                               "set_name": row["set_name"],
                               "set_code": row["set_code"],
                               "collector_number": row["collector_number"],
                               "images": ImageUris(dict(row))})

        return prints

    def _parse_json_array(self, field: object | None) -> list[str] | None:
        """Parses a json array, returns a list[str] of the items, an empty
        list if no items are present, or None if the field is null.

        Parameters
        ----------
        field: str
            json array

        Returns
        -------
        list[str] | None
        """
        assert isinstance(field, (str | None))

        if field is None:
            return None

        array = json.loads(field)
        return [str(element) for element in array] if array else []
