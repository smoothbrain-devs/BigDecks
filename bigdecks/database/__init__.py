import sqlite3
from datetime import datetime
import click
from flask import current_app, g
import os


def get_db(db_name=None):
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

#def init_db():
#    db = get_db()

#    path = os.path.join(os.curdir, 'database')
#    path = os.path.join(path, 'users_schema.sql')
#    with current_app.open_resource(path) as f:
#        db.executescript(f.read().decode('utf8'))

def init_db(db_name=None):
    db_name = db_name if db_name else current_app.config['DATABASE']

    # Check if database file exists
    if not os.path.exists(db_name):
        db = get_db(db_name)
        path = os.path.join(os.curdir, 'database', 'users_schema.sql')

        with current_app.open_resource(path) as f:
            db.executescript(f.read().decode('utf8'))

        click.echo(f'Initialized database: {db_name}')
    else:
        click.echo(f'Database {db_name} already exists. Skipping initialization.')

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    with app.app_context():
        init_db()