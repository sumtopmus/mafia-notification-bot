from dynaconf import settings
from telegram.ext import Application

from handlers import debug, error, info
import utils


async def post_init(app: Application) -> None:
    """Initializes bot with data and its tasks."""
    utils.log('post_init')
    # TODO: Start the routines.


def add_handlers(app: Application) -> None:
    # Error handler.
    app.add_error_handler(error.handler)
    # Debug commands.
    for module in [debug, info]:
        app.add_handlers(module.create_handlers())
    # Chat handling.
    for module in []:
        app.add_handlers(module.create_handlers())