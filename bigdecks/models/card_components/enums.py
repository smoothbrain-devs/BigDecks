"""Enums for card information."""


from enum import (Flag, auto)


class Colors(Flag):
    """Enum containing the possible colors for a card."""
    white = auto()
    blue = auto()
    black = auto()
    red = auto()
    green = auto()
    colorless = auto()

    def as_dict(self):
        """Get the colors as a dict.

        Returns
        -------
        dict[str, bool]
            Where the key is the color and the value True/False indicates the
            color.
        """
        return {"white": bool(self & Colors.white),
                "blue": bool(self & Colors.blue),
                "black": bool(self & Colors.black),
                "red": bool(self & Colors.red),
                "green": bool(self & Colors.green),
                "colorless": bool(self & Colors.colorless)}


class GameAvailability(Flag):
    """Enum containing which games a card is available in."""
    paper = auto()
    arena = auto()
    mtgo = auto()

    def __str__(self):
        assert self.name is not None
        return self.name

    def as_dict(self):
        """Get the game availability as a dict.

        Returns
        -------
        dict[str, bool]
            Where the key is the game and the value True/False indicates if
            card is present in the game.
        """
        return {"paper": bool(self & GameAvailability.paper),
                "arena": bool(self & GameAvailability.arena),
                "mtgo": bool(self & GameAvailability.mtgo)}


class Legality(Flag):
    """Enum containing the possible legalities.

    Possible legalities:
    legal
    not_legal
    restricted
    banned
    """
    legal = auto()
    not_legal = auto()
    restricted = auto()
    banned = auto()

    def __str__(self):
        assert self.name is not None
        return self.name


class Rarity(Flag):
    """Enum containing the possible rarities of a card."""
    common = auto()
    uncommon = auto()
    rare = auto()
    mythic = auto()

    def __str__(self):
        assert self.name is not None
        return self.name
