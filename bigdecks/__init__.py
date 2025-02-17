"""Flask application factory.

This module contains the application factory function create_app() that
initializes and configures the Flask application. It handles configuration
loading.

The create_app function accepts an optional test_config parameter that can
override the default configuration for testing purposes.
"""


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
        SECRET_KEY='dev', # TODO(Cthuloops): obviously we should change this for production.
        # TODO(Cthuloops): We need to put the actual DB path here.
        DATABASE=os.path.join(app.instance_path, 'bigdecks.sqlite')
    )

    if test_configuration is None:
        # Load the instance configuration if it exists, when not testing.
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test configuration if it was passed in.
        app.config.from_mapping(test_configuration)

    # Ensure the instance folder exists.
    try:
        os.makedirs(app.instance_path)
    except FileExistsError:
        # We don't care if the file already exists because we want it to exist.
        pass
    except OSError as e:
        print(f"{e}")

    @app.route("/")
    def index():
        return "Hello, World!"


    # TODO(Cthuloops): We need to add the app.routes here as blueprints
    # https://flask.palletsprojects.com/en/stable/tutorial/views/


    return app
