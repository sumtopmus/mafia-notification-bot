from collections import defaultdict
from datetime import time


clock_emoji = defaultdict(lambda: '🕕')
clock_emoji.update({
    '16:00': '🕓',
    '16:30': '🕟',
    '17:00': '🕔',
    '17:30': '🕠',
    '18:00': '🕕',
    '18:30': '🕡',
    '19:00': '🕖',
    '19:30': '🕢',
    '20:00': '🕗'
})


def get_clock_emoji(time: time) -> str:
    return clock_emoji[time.strftime('%H:%M')]