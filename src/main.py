from dynaconf import settings
import logging
import os
import pytz
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults

import init


def main() -> None:
    """Main program to run."""
    # Create directory tree structure.
    for path in [settings.LOG_PATH]:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

    # Set up logging and debugging.
    logging_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(filename=settings.LOG_PATH, level=logging_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Setup the bot.
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN, tzinfo=pytz.timezone(settings.TIMEZONE))
    app = Application.builder().token(settings.TOKEN).defaults(defaults)\
        .arbitrary_callback_data(True).build()
    # Add handlers.
    init.add_handlers(app)
    # Start the bot.
    app.run_polling()


if __name__ == "__main__":
    main()