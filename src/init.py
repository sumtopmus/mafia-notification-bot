import logging
from telegram.ext import Application
from telegram.warnings import PTBUserWarning
from warnings import filterwarnings

from config import settings
import handlers
import utils


def setup_logging() -> None:
    # Logging
    logging_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        filename=settings.LOG_PATH,
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Debugging
    filterwarnings(
        action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
    )


async def post_init(app: Application) -> None:
    """Initializes bot with data and its tasks."""
    app.bot_data.setdefault(settings.CLUB_CHANNEL, {})
    # TODO: Start the routines.
    utils.log("post_init_notifications_on")
    handlers.notify.notifications_on(app)


def add_handlers(app: Application) -> None:
    # Error handler
    app.add_error_handler(handlers.error)
    # Debug & business logic handlers
    app.add_handlers(handlers.all)
