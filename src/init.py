from dynaconf import settings
from telegram.ext import Application

from handlers import debug, error, info, upload
from handlers import notify
import utils


async def post_init(app: Application) -> None:
    """Initializes bot with data and its tasks."""
    utils.log("post_init")
    app.bot_data.setdefault(settings.CLUB_CHANNEL, {})
    # TODO: Start the routines.
    utils.log("post_init_notifications_on")
    notify.notifications_on(app)


def add_handlers(app: Application) -> None:
    # Error handler.
    app.add_error_handler(error.handler)
    # Debug commands.
    for module in [debug, info, upload]:
        app.add_handlers(module.create_handlers())
    # Chat handling.
    for module in [notify]:
        app.add_handlers(module.create_handlers())
