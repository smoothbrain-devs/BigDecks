"""Wrapper classes for card information."""


from .enums import (Legality)


class CardLegalities:
    """Wrapper for dict containing format legality for a card."""
    def __init__(self, row: dict[str, object]):
        self.__format_legality = {
            "standard": self.__get_legality(str(row["standard"])),
            "future": self.__get_legality(str(row["future"])),
            "historic": self.__get_legality(str(row["historic"])),
            "timeless": self.__get_legality(str(row["timeless"])),
            "gladiator": self.__get_legality(str(row["gladiator"])),
            "pioneer": self.__get_legality(str(row["pioneer"])),
            "explorer": self.__get_legality(str(row["explorer"])),
            "modern": self.__get_legality(str(row["modern"])),
            "legacy": self.__get_legality(str(row["legacy"])),
            "pauper": self.__get_legality(str(row["pauper"])),
            "vintage": self.__get_legality(str(row["vintage"])),
            "penny": self.__get_legality(str(row["penny"])),
            "commander": self.__get_legality(str(row["commander"])),
            "oathbreaker": self.__get_legality(str(row["oathbreaker"])),
            "standardbrawl": self.__get_legality(str(row["standardbrawl"])),
            "brawl": self.__get_legality(str(row["brawl"])),
            "alchemy": self.__get_legality(str(row["alchemy"])),
            "paupercommander": self.__get_legality(str(row["paupercommander"])),
            "duel": self.__get_legality(str(row["duel"])),
            "oldschool": self.__get_legality(str(row["oldschool"])),
            "premodern": self.__get_legality(str(row["premodern"])),
            "predh": self.__get_legality(str(row["predh"]))
        }

    def __get_legality(self, status: str) -> Legality:
        """Converts string representation to Legality enum.

        Returns
        -------
        Legality
            Enum member based on string legality.
        """
        legalities = ["legal", "not_legal", "restricted", "banned"]
        assert status in legalities, "Invalid legality string"
        match (status):
            case "legal":
                legality = Legality.legal
            case "not_legal":
                legality = Legality.not_legal
            case "restricted":
                legality = Legality.restricted
            case "banned":
                legality = Legality.banned
            case _:
                # This should never be reached
                raise RuntimeError(f"Missing/incorrect legality for {status}")
        return legality

    @property
    def standard(self) -> Legality:
        """Get legality status for the standard format."""
        return self.__format_legality["standard"]

    @property
    def future(self) -> Legality:
        """Get legality status for the future format."""
        return self.__format_legality["future"]

    @property
    def historic(self) -> Legality:
        """Get legality status for the historic format."""
        return self.__format_legality["historic"]

    @property
    def timeless(self) -> Legality:
        """Get legality status for the timeless format."""
        return self.__format_legality["timeless"]

    @property
    def gladiator(self) -> Legality:
        """Get legality status for the gladiator format."""
        return self.__format_legality["gladiator"]

    @property
    def pioneer(self) -> Legality:
        """Get legality status for the pioneer format."""
        return self.__format_legality["pioneer"]

    @property
    def explorer(self) -> Legality:
        """Get legality status for the explorer format."""
        return self.__format_legality["explorer"]

    @property
    def modern(self) -> Legality:
        """Get legality status for the modern format."""
        return self.__format_legality["modern"]

    @property
    def legacy(self) -> Legality:
        """Get legality status for the legacy format."""
        return self.__format_legality["legacy"]

    @property
    def pauper(self) -> Legality:
        """Get legality status for the pauper format."""
        return self.__format_legality["pauper"]

    @property
    def vintage(self) -> Legality:
        """Get legality status for the vintage format."""
        return self.__format_legality["vintage"]

    @property
    def penny(self) -> Legality:
        """Get legality status for the penny format."""
        return self.__format_legality["penny"]

    @property
    def commander(self) -> Legality:
        """Get legality status for the commander format."""
        return self.__format_legality["commander"]

    @property
    def oathbreaker(self) -> Legality:
        """Get legality status for the oathbreaker format."""
        return self.__format_legality["oathbreaker"]

    @property
    def standardbrawl(self) -> Legality:
        """Get legality status for the standardbrawl format."""
        return self.__format_legality["standardbrawl"]

    @property
    def brawl(self) -> Legality:
        """Get legality status for the brawl format."""
        return self.__format_legality["brawl"]

    @property
    def alchemy(self) -> Legality:
        """Get legality status for the alchemy format."""
        return self.__format_legality["alchemy"]

    @property
    def paupercommander(self) -> Legality:
        """Get legality status for the paupercommander format."""
        return self.__format_legality["paupercommander"]

    @property
    def duel(self) -> Legality:
        """Get legality status for the duel format."""
        return self.__format_legality["duel"]

    @property
    def oldschool(self) -> Legality:
        """Get legality status for the oldschool format."""
        return self.__format_legality["oldschool"]

    @property
    def premodern(self) -> Legality:
        """Get legality status for the premodern format."""
        return self.__format_legality["premodern"]

    @property
    def predh(self) -> Legality:
        """Get legality status for the predh format."""
        return self.__format_legality["predh"]

    def as_dict(self) -> dict[str, Legality]:
        """Get all format legalities as a dictionary."""
        return self.__format_legality.copy()


class ImageUris():
    """Wrapper class for dict containing image uris."""
    def __init__(self, row: dict[str, object]):
        self.__data: dict[str, str | None] = {
            "png": self.__get_uri("png", row),
            "border_crop": self.__get_uri("border_crop", row),
            "art_crop": self.__get_uri("art_crop", row),
            "large": self.__get_uri("large", row),
            "normal": self.__get_uri("normal", row),
            "small": self.__get_uri("small", row)
        }

    def __get_uri(self, key: str, row: dict[str, object]) -> str | None:
        """Ensure some type safety."""
        val = row.get(key)
        assert isinstance(val, (str | None))
        return val

    @property
    def png(self) -> str | None:
        """Uri to the png image for this card if it exists.

        Returns
        -------
        str | None
            str if the uri exists.
            None otherwise.
        """
        return self.__data["png"]

    @property
    def border_crop(self) -> str | None:
        """Uri to the border crop image for this card if it exists.

        Returns
        -------
        str | None
            str if the uri exists.
            None otherwise.
        """
        return self.__data["border_crop"]

    @property
    def art_crop(self) -> str | None:
        """Uri to the art crop image for this card if it exists.

        Returns
        -------
        str | None
            str if the uri exists.
            None otherwise.
        """
        return self.__data["art_crop"]

    @property
    def large(self) -> str | None:
        """Uri to the large image for this card if it exists.

        Returns
        -------
        str | None
            str if the uri exists.
            None otherwise.
        """
        return self.__data["large"]

    @property
    def normal(self) -> str | None:
        """Uri to the normal image for this card if it exists.

        Returns
        -------
        str | None
            str if the uri exists.
            None otherwise.
        """
        return self.__data["normal"]

    @property
    def small(self) -> str | None:
        """Uri to the small image for this card if it exists.

        Returns
        -------
        str | None
            str if the uri exists.
            None otherwise.
        """
        return self.__data["small"]

    @property
    def highest_resolution(self) -> str | None:
        """Returns the uri for the highest resolution image available.

        Returns
        -------
        str | None
            str, if the card has images.
            None, if the card has no images.
        """
        highest_resolution_uri = None
        for _, uri in self.__data.items():
            if uri is not None and highest_resolution_uri is None:
                highest_resolution_uri = uri
                break

        return highest_resolution_uri

    def as_dict(self) -> dict[str, str | None]:
        """Returns a copy of the underlying dict containing the image uris."""
        return self.__data.copy()
