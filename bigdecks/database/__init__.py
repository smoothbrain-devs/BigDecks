"""Database initialization and connection functions"""


import click
import os
import sqlite3
from datetime import datetime
from flask import Flask, g, current_app
from flask.cli import with_appcontext


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)


def init_app(app: Flask):
    """Initialize database handling for the Flask application.

    This function:
    1. Creates the necessary directories.
    2. Sets up the cards and users databases.
    3. Registers connnection cleanup.

    Parameters
    ----------
    app: Flask
        The Flask app instance.
    """

    os.makedirs(app.instance_path, exist_ok=True)

    # Create the users and cards databases
    with app.app_context():
        for db in ["users", "cards"]:
            try:
                init_db(db)
            except Exception as e:
                click.echo(f"Error initializing {db} database: {e}")

    # Create the users and cards databases
    #with app.app_context():
    #    for db in ["users", "cards"]:
    #        init_db(db)

    # Register CLI command
    app.cli.add_command(init_db_command)

    # Register the teardown function to close database connections
    app.teardown_appcontext(close_connections)


def init_db(db_name: str) -> None:
    """Create and initialize the named database.

    Parameters
    ----------
    db_name: str
        Name of the database to initialize.

    Exceptions
    ----------
    FileNotFoundError
        Raises if the db or the db schema do not exist.
    """
    db_path = _get_db_path(db_name)
    db_exists = os.path.exists(db_path)
    schema_path = None

    if not db_exists:
        click.echo(f"Creating the {db_name} database")
        if db_name in ["users", "cards"]:
            schema_path = os.path.join("database", f"{db_name}_schema.sql")
        conn = get_db_connection(db_name)

        if schema_path is not None:
            conn = get_db_connection(db_name)
            full_schema_path = os.path.join(current_app.root_path, schema_path)
            if os.path.exists(full_schema_path):
                with current_app.open_resource(schema_path) as f:
                    try:
                        conn.executescript(f.read().decode("utf8"))
                        conn.commit()
                    except Exception as e:
                        print(f"Error occurred in {db_name}_schema.sql:")
                        print("\t", e)
            else:
                raise FileNotFoundError(f"{schema_path} does not exist")
        else:
            raise FileNotFoundError(f"{db_name} does not exist.")
    else:
        pass

    if db_name == "users":
        conn = get_db_connection(db_name)

        tournament_schema_path = os.path.join("database", "tournament_schema.sql")
        full_tournament_schema_path = os.path.join(current_app.root_path, tournament_schema_path)
        
        if os.path.exists(full_tournament_schema_path):
            with current_app.open_resource(tournament_schema_path) as f:
                try:
                    conn.executescript(f.read().decode("utf8"))
                    conn.commit()
                    click.echo("Tournament schema applied to users database.")
                except Exception as e:
                    print(f"Error occurred in tournament_schema.sql:")
                    print("\t", e)
        else:
            click.echo(f"Warning: {tournament_schema_path} does not exist. Tournament functionality may be limited.")

        post_schema_path = os.path.join("database", "post_schema.sql")
        full_post_schema_path = os.path.join(current_app.root_path, post_schema_path)
        
        if os.path.exists(full_post_schema_path):
            with current_app.open_resource(post_schema_path) as f:
                try:
                    conn.executescript(f.read().decode("utf8"))
                    conn.commit()
                    click.echo("Post schema applied to users database.")
                except Exception as e:
                    print(f"Error occurred in post_schema.sql:")
                    print("\t", e)
        else:
            click.echo(f"Warning: {post_schema_path} does not exist. Blog functionality may be limited.")



@click.command("init-db")
@click.argument("db_name", required=True)
@with_appcontext
def init_db_command(db_name):
    """Command to initialize a database via Flask CLI."""
    init_db(db_name)

def get_db_connection(db_name: str) -> sqlite3.Connection:
    """Get a database connection, creating it if it doesn't exist already.

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
    db_path = os.path.join(instance_path, f"{db_name}.db")
    os.makedirs(instance_path, exist_ok=True)
    return db_path
