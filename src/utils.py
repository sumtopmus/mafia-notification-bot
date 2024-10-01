from datetime import datetime
from dynaconf import settings
import logging
from telegram.ext import Application


def log(message: str, level=logging.DEBUG) -> None:
    """Logging/debugging helper."""
    logging.getLogger(__name__).log(level, message)
    if settings.DEBUG:
        print(f"⌚️ {datetime.now().strftime(settings.DATETIME_FORMAT)}: {message}")


def clear_jobs(app: Application, job_family: str, job_data=None) -> None:
    """Clears the existing jobs."""
    job_name = job_family
    if job_data:
        job_name += f":{job_data}"
    log(f"clear_jobs: {job_name}")
    current_jobs = app.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
