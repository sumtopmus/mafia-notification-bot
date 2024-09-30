from dynaconf import settings
import logging
from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

import utils


def create_handlers() -> list:
    """Creates handlers that process admin's photo upload."""
    return [
        MessageHandler(
            filters.User(username=settings.ADMINS) & filters.PHOTO, photo_upload
        )
    ]


async def photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Photo upload"""
    utils.log("photo_upload")
    utils.log(f"file_id: {update.message.photo[0].file_id}", logging.INFO)
