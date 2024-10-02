from datetime import date, datetime, time, timedelta
from os import close
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from config import settings
from utils import log, clear_jobs


POLL_JOB_NAME_PREFIX = "poll"
PUBLIC_POLL_JOB_NAME = POLL_JOB_NAME_PREFIX + "_public_chat"
PRIVATE_POLL_JOB_NAME = POLL_JOB_NAME_PREFIX + "_private_chat"


def create_handlers() -> list:
    """Creates handlers that process /poll command."""
    return [
        CommandHandler(
            "polling_on", polling_on, filters.User(username=settings.ADMINS)
        ),
        CommandHandler(
            "polling_off", polling_off, filters.User(username=settings.ADMINS)
        ),
        CommandHandler(
            "poll_public", on_poll_public, filters.User(username=settings.ADMINS)
        ),
        CommandHandler(
            "poll_private", on_poll_private, filters.User(username=settings.ADMINS)
        ),
    ]


def polling_on(_: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch polling on."""
    polling_on(context.application)


def polling_on(app: Application) -> None:
    """Switch polling on."""
    log("polling_on")
    today = date.today()
    poll_date = today + timedelta(days=7 - today.weekday())
    poll_time = time.fromisoformat(settings.POLL_TIME)
    poll_datetime = datetime.combine(poll_date, poll_time)
    if not app.job_queue.get_jobs_by_name(PUBLIC_POLL_JOB_NAME):
        app.job_queue.run_repeating(
            poll_public,
            interval=timedelta(days=7),
            first=poll_datetime,
            name=PUBLIC_POLL_JOB_NAME,
        )
        log("public chat poll job added")
    if not app.job_queue.get_jobs_by_name(PRIVATE_POLL_JOB_NAME):
        app.job_queue.run_repeating(
            poll_private,
            interval=timedelta(days=7),
            first=poll_datetime,
            name=PRIVATE_POLL_JOB_NAME,
        )
        log("private chat poll job added")


def polling_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch polling off."""
    log("polling_off")
    clear_jobs(context.application, POLL_JOB_NAME_PREFIX)


async def on_poll_public(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a poll to the club chat."""
    log("poll_public")
    await poll_public(context)


async def on_poll_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a poll to the private club chat."""
    log("poll_private")
    await poll_private(context)


async def poll_public(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Creates a poll for public game nights."""
    log("poll_public")
    text = "Game Night"
    today = date.today()
    this_week = today - timedelta(days=today.weekday())
    options = [
        (this_week + timedelta(days=i)).strftime("%a, %m/%d") for i in range(4, 7)
    ]
    options += ["🐳"]
    poll = await context.bot.send_poll(
        chat_id=settings.CLUB_CHAT_ID,
        question=text,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    if "poll_public" in context.bot_data:
        await context.bot.unpin_chat_message(
            settings.CLUB_CHAT_ID, context.bot_data["poll_public"]
        )
    await context.bot.pin_chat_message(settings.CLUB_CHAT_ID, poll.id)
    context.bot_data["poll_public"] = poll.id


async def poll_private(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Creates a poll for private game nights."""
    log("poll_private")
    text = "Game Night"
    today = date.today()
    this_week = today - timedelta(days=today.weekday())
    options = [(this_week + timedelta(days=i)).strftime("%a, %m/%d") for i in range(7)]
    options += ["🐳"]
    poll = await context.bot.send_poll(
        chat_id=settings.PRIVATE_CLUB_CHAT_ID,
        question=text,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    if "poll_private" in context.bot_data:
        await context.bot.unpin_chat_message(
            settings.PRIVATE_CLUB_CHAT_ID, context.bot_data["poll_private"]
        )
    await context.bot.pin_chat_message(settings.PRIVATE_CLUB_CHAT_ID, poll.id)
    context.bot_data["poll_private"] = poll.id
