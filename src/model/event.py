from datetime import datetime, time, timedelta
from dynaconf import settings
from format import clock

class Event:
    def __init__(self, event: dict):
        self.event_id = event['id']
        self.title = event['name']
        self.datetime = datetime.fromtimestamp(event['timestamp'])
        self.duration = event['duration'] / 3600
        self.canceled = 'canceled' in event

    def get_notification_message(self) -> str:
        return settings.NOTIFICATION_MESSAGE.format(
            month=self.datetime.strftime('%B')[:3],
            day=self.datetime.strftime('%d'),
            day_of_week=self.datetime.strftime('%A')[:3],
            clock_emoji=clock.get_clock_emoji(self.datetime.time()),
            hours=self.datetime.strftime('%H'),
            minutes=self.datetime.strftime('%M'),
            club_admin=settings.ADMINS[0],
            event_id=self.event_id)