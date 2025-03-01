"""Cards DB maintenance functions and CardsManager class"""


import json
import os
import requests
from datetime import datetime, timezone
from flask import current_app
from requests.exceptions import HTTPError, JSONDecodeError, Timeout


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
            print(e)

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
        except Timeout:
            print(f"Error: Connection to {bulkdata_api} timed out")
        except HTTPError as e:
            print(e)
        else:
            with open(self.__bulk_data_path, "wb") as f:
                f.write(response.content)

    def _bulk_data_up_to_date(self) -> bool:
        """Ensures bulk data is up to date.

        Scryfall updates bulk data every 12 hours. So check to see if the
        updated_at time of the bulk_data.json file is within 12 hours of the
        current time.

        Returns
        -------
        bool
            False if data needs to be updated, else True
        """
        # Bulk data is only updated every 12 hours.
        bulk_data = None
        with open(self.__bulk_data_path, "rb") as f:
            bulk_data = json.load(f)

        if bulk_data is not None:
            last_update = datetime.fromisoformat(bulk_data["updated_at"])
            current_time = datetime.now(timezone.utc)
            difference = current_time - last_update
            twelve_hours = 43200  # seconds
            return difference.seconds > twelve_hours
        else:
            raise RuntimeError("Error: Something went wrong reading "
                               f"{self.__bulk_data_path}.")

    def _download_default_cards(self):
        """Downloads default_cards.json"""
        # If the bulk_data.json isn't up to date, update it.
        if not self._bulk_data_up_to_date():
            self._download_bulk_data()
