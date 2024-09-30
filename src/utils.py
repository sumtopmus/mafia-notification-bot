# coding=UTF-8

from datetime import datetime
from dynaconf import settings
import logging


def log(message: str, level=logging.DEBUG) -> None:
    """Logging/debugging helper."""
    logging.getLogger(__name__).log(level, message)
    if settings.DEBUG:
        print(f"⌚️ {datetime.now().strftime(settings.DATETIME_FORMAT)}: {message}")


def escape_markdown(text: str) -> str:
    # List of special characters that need to be escaped in Markdown
    markdown_chars = [
        "*",
        "_",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]

    for char in markdown_chars:
        text = text.replace(char, "\\" + char)

    return text
