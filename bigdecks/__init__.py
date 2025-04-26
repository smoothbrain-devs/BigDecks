"""Flask application factory.

This module contains the application factory function create_app() that
initializes and configures the Flask application. It handles configuration
loading.

The create_app function accepts an optional test_config parameter that can
override the default configuration for testing purposes.
"""


from datetime import datetime
import os
from flask import Flask


def create_app(test_configuration=None):
    """Create and configure the Flask application

    Parameters
    ---------
    test_configuration: Dict (Default = None, optional)
        Configuration dictionary to override the default configuration.
        This is primarily used for testing.

    Returns
    -------
    Flask
        A configured Flask application instance.
    """
    # Here __name__ is the current python module, bigdecks, and sets up some
    # paths. The instance_relative_config tells the app that config files are
    # in the instance folder, which shouldn't be committed to github.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',  # TODO(Cthuloops): obviously we should change this for production.
    )

    if test_configuration is None:
        # Load the instance configuration if it exists, when not testing.
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test configuration if it was passed in.
        app.config.from_mapping(test_configuration)

    # Ensure the instance directory
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        print(f"{e}")

    # Create a context for the app
    @app.context_processor
    def inject_year():
        """Make the current year available to all templates"""
        return {'year': datetime.now().year}

    # Create a template filter to encode strings
    @app.template_filter('urlencode')
    def urlencode_filter(string: str):
        """Url encode a string to make it safe for urls

        Parameters
        ----------
        string: str
            The string to encode

        Returns
        -------
        quote(string)
            url encoded version of the string.
        """
        from urllib.parse import quote

        if isinstance(string, str):
            return quote(string)
        return quote(str(string))

    # TODO(Cthuloops): We need to add the app.routes here as blueprints
    # https://flask.palletsprojects.com/en/stable/tutorial/views/

    # Initialize database first
    from .database import init_app
    try:
        init_app(app)
    except Exception as e:
        print(f"{e}")

    # Add the index to the app.
    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule("/", endpoint="index")

    # Register cards cli commands
    from .database.cards_db import init_app as init_cards_db_app
    init_cards_db_app(app)

    # Register the blueprints
    from . import auth, cards, home
    app.register_blueprint(auth.bp)
    app.register_blueprint(cards.bp)

    # Import blog bp
    from . import blog
    app.register_blueprint(blog.bp)

    # Import tournament bp
    from . import tournament
    app.register_blueprint(tournament.bp)
    app.add_url_rule('/tournament', endpoint='tournament.index',
                     view_func=tournament.index)

    # Import shop bp
    from . import shop
    app.register_blueprint(shop.bp)

    return app
