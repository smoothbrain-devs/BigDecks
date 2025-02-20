"""Database initialization and connection functions"""


import os
import sqlite3
from flask import Flask, g, current_app


def init_app(app: Flask):
    """Initialize database handling for the Flask application.

    This should be called when setting up the app.

    Parameters
    ----------
    app: Flask
    """
    # Ensure the directory for user databases exists.
    with app.app_context():
        os.makedirs(os.path.join(app.instance_path, "user_data"), exist_ok=True)

    # Register the teardown function to close database connections
    app.teardown_appcontext(close_connections)


def get_db_connection(db_name: str):
    """Get a database connection, creating it if it doesn"t exist already.

    Parameters
    ----------
    db_name: str
        The name of the database.

    Returns
    -------
    Database connection
    """
    if not hasattr(g, "db_connections"):
        g.db_connections = {}

    if db_name not in g.db_connections:
        db_path = _get_db_path(db_name)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        g.db_connections[db_name] = conn

    return g.db_connections[db_name]


def close_connections(exception):
    """Close all database connections for the current request

    Parameters
    ----------
    exception
        Exception based on the error that occurred.
        We currently have no error logger so this goes ignored.
    """
    db_connections = getattr(g, "db_connections", {})
    for conn in db_connections.values():
        conn.close()


def _get_db_path(db_name: str) -> str:
    """Internal function to get database file paths.

    Parameters
    ----------
    db_name: str
        The name of the database

    Returns
    -------
    str
        Path to the requested database.
    """
    instance_path = current_app.instance_path
    if db_name in ["cards", "users"]:
        db_path = os.path.join(instance_path, f"{db_name}.db")
    else:
        db_path = os.path.join(instance_path, "user_data", f"{db_name}.db")
    return db_path
