
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable
from loguru import logger

class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def schedule_once(self, job_id: int, run_date, func: Callable, *args, **kwargs):
        logger.info(f"Scheduling once job_id={job_id} at {run_date}")
        self.scheduler.add_job(func, DateTrigger(run_date=run_date), args=args, kwargs=kwargs, id=f"job_{job_id}", replace_existing=True)

    def schedule_interval(self, job_id: int, seconds: int, func: Callable, *args, **kwargs):
        logger.info(f"Scheduling interval job_id={job_id} every {seconds}s")
        self.scheduler.add_job(func, IntervalTrigger(seconds=seconds), args=args, kwargs=kwargs, id=f"job_{job_id}", replace_existing=True)

    def cancel(self, job_id: int):
        try:
            self.scheduler.remove_job(f"job_{job_id}")
        except Exception:
            pass
