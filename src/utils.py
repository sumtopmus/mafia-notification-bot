from datetime import datetime
from dynaconf import settings
import logging


def log(message: str, level=logging.DEBUG) -> None:
    """Logging/debugging helper."""
    logging.getLogger(__name__).log(level, message)
    if settings.DEBUG:
        print(f"⌚️ {datetime.now().strftime(settings.DATETIME_FORMAT)}: {message}")
