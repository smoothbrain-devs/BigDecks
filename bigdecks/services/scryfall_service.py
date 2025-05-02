import click
import json
import os
import requests
from datetime import datetime, timezone, timedelta
from requests.exceptions import HTTPError, Timeout
from flask import current_app


def _ensure_resources_exists() -> None:
    """Ensures the resources directory exists in the instance directory."""
    try:
        os.makedirs(os.path.join(current_app.instance_path, "resources"),
                    exist_ok=True)
    except OSError as e:
        click.echo(f"Error: {e}", err=True)


def _get_resources_path() -> str:
    """Returns the path to the resources directory"""
    _ensure_resources_exists()
    return os.path.join(current_app.instance_path, "resources")


def _get_bulk_data_path() -> str:
    """Returns a path to the bulkdata.json"""
    return os.path.join(_get_resources_path(), "bulk_data.json")


def _get_default_cards_path() -> str:
    """Returns a path to the default_cards.json"""
    return os.path.join(_get_resources_path(), "default_cards.json")


def _get_headers() -> dict[str, str]:
    """Return session headers required for accessing the Scryfall api."""
    headers = {
        "User-Agent": "BigDecksApp/1.1",
        "Accept": "*/*"
    }
    return headers


def _download_bulk_data():
    """Downloads bulk_data.json"""
    bulkdata_api = "https://api.scryfall.com/bulk-data/default-cards"
    try:
        with requests.Session() as s:
            s.headers.update(_get_headers())
            response = s.get(url=bulkdata_api, timeout=35.0)
            response.raise_for_status()

            with open(_get_bulk_data_path(), "wb") as f:
                f.write(response.content)

    except (HTTPError, Timeout, ConnectionError) as e:
        click.echo(f"Newtork error while downloading bulk data: {e}")

    except RuntimeError as e:
        click.echo(f"Unexcpected error while downloading bulk data: {e}")


def _bulk_data_up_to_date() -> bool:
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
    bulk_path = _get_bulk_data_path()
    try:
        with open(bulk_path, "r") as f:
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
                   f"{bulk_path}", err=True)
        return False

    except (json.JSONDecodeError, KeyError) as e:
        click.echo(f"Error parsing bulk data: {e}", err=True)
        return False


def _download_default_cards() -> bool:
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
    default_cards = _get_default_cards_path()
    try:
        # Check if bulk data is up to date (within last 24 hours)
        if not _bulk_data_up_to_date():
            _download_bulk_data()

        # Read bulk data to get the download URI
        try:
            with open(_get_bulk_data_path(), "r") as f:
                bulk_data = json.load(f)
                download_uri = bulk_data.get("download_uri")

                if not download_uri:
                    click.echo("Error: No download URI found in bulk data",
                               err=True)
                    return False

                click.echo(f"Downloading card data from {download_uri}...")
                with requests.Session() as s:
                    s.headers.update(_get_headers())
                    response = s.get(url=download_uri, stream=True,
                                     timeout=35.0)
                    response.raise_for_status()

                    # Read the default_cards.json file 8Kb at a time to avoid
                    # loading the 400+Mb file into memory.
                    with open(default_cards, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    if os.path.exists(default_cards):
                        click.echo("Card data successfully downloaded to "
                                   f"{default_cards}")
                        return True
                    click.echo("Card data not found at "
                               f"{default_cards}", err=True)
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


def update_default_cards() -> bool:
    """Update the default cards.json

    Returns
    -------
        True if successful, False otherwise.
    """
    if _bulk_data_up_to_date():
        return False
    return _download_default_cards()
