# coding=UTF-8

from datetime import datetime, time, timedelta
from dynaconf import settings
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

import utils
from model import event


NOTIFICATION_JOB_NAME = 'game_night_notification'
NOTIFICATION_UPDATE_JOB_NAME = 'game_night_notification_update'
MR_EVENTS_URL = 'https://mafiaratings.com/api/get/events.php'
MR_EVENTS_HEADERS = {
    "User-Agent": "NotificationBot/0.0.1",
}
MR_EVENTS_PARAMS = {
    'club_id': settings.CLUB_ID,
    'started_after': 'now',
    'canceled': 1,
    'lod': 1
}


def create_handlers() -> list:
    """Creates handlers that process piece/war modes."""
    notifications_on_handler = CommandHandler(
        'notifications_on', notifications_on,
        filters.User(username=settings.ADMINS))
    notifications_off_handler = CommandHandler(
        'notifications_off', notifications_off,
        filters.User(username=settings.ADMINS))
    return [notifications_on_handler, notifications_off_handler]


def notifications_on(_: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch notifications on."""
    notifications_on(context.application)


def notifications_on(app: Application) -> None:
    """Switch notifications on."""
    utils.log('notifications_on')
    notification_time = time.fromisoformat(settings.NOTIFICATION_TIME)
    if not app.job_queue.get_jobs_by_name(NOTIFICATION_JOB_NAME):
        app.job_queue.run_daily(
            notify,
            time=notification_time,
            name=NOTIFICATION_JOB_NAME)
        utils.log('notification_job_added')
    notification_update_interval = timedelta(seconds=settings.NOTIFICATION_UPDATE_INTERVAL)
    notification_update_datetime = datetime.combine(datetime.today(), notification_time) + notification_update_interval
    if not app.job_queue.get_jobs_by_name(NOTIFICATION_UPDATE_JOB_NAME):
        app.job_queue.run_repeating(
            notification_update,
            interval=notification_update_interval,
            first=notification_update_datetime.time(),
            name=NOTIFICATION_UPDATE_JOB_NAME)
        utils.log('notification_update_job_added')   


def notifications_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch notifications off."""
    utils.log('notifications_off')
    utils.clear_jobs(context.application, NOTIFICATION_JOB_NAME)
    utils.clear_jobs(context.application, NOTIFICATION_UPDATE_JOB_NAME)


async def notify(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send notification about the game event."""
    utils.log('notify')
    event = process_nearest_event(fetch_events())
    if not event or event.event_id in context.bot_data[settings.CLUB_CHANNEL] or event.canceled:
        return
    utils.log('send_notification_message')
    bot_message = await context.bot.send_photo(
        chat_id=settings.CLUB_CHANNEL,
        photo=settings.NOTIFICATION_IMAGE,
        caption=event.get_notification_message())
    context.bot_data[settings.CLUB_CHANNEL][event.event_id] = event.__dict__
    context.bot_data[settings.CLUB_CHANNEL][event.event_id]['message_id'] = bot_message.message_id


async def notification_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update notification about the game event."""
    utils.log('notification_update')
    event = process_nearest_event(fetch_events())
    if not event or event.event_id not in context.bot_data[settings.CLUB_CHANNEL]:
        return
    changed = [key for key in event.__dict__ if event.__dict__[key] != context.bot_data[settings.CLUB_CHANNEL][event.event_id][key]]
    utils.log('changed fields: ' + ', '.join(changed))
    if not changed:
        return
    utils.log('update_notification_message')
    await context.bot.edit_message_caption(
        chat_id=settings.CLUB_CHANNEL,
        message_id=context.bot_data[settings.CLUB_CHANNEL][event.event_id]['message_id'],
        caption=event.get_notification_message())
    context.bot_data[settings.CLUB_CHANNEL][event.event_id].update(event.__dict__)


def fetch_events() -> list:
    """Fetches events from mafiaratings.com."""
    utils.log('fetch_events')
    mr_events_params = MR_EVENTS_PARAMS.copy()
    mr_events_params['started_before'] = (datetime.now() + timedelta(weeks=2)).strftime('%Y-%m-%d')
    response = requests.get(MR_EVENTS_URL,
                            headers=MR_EVENTS_HEADERS,
                            params=mr_events_params)
    # Check if the request was successful
    if response.status_code == 200:
        # Return the JSON response as a Python list/dict
        return response.json()
    else:
        # Return an empty list if the request was not successful
        return []
    
def process_nearest_event(events: list) -> event.Event:
    """Processes JSON events."""
    utils.log('process_nearest_event')
    if events['count'] == 0:
        return None
    return event.Event(events['events'][-1])
