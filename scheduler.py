from apscheduler.schedulers.blocking import BlockingScheduler
from update_data import update_data


def start_scheduler():
    scheduler = BlockingScheduler()

    scheduler.add_job(
        update_data,
        "cron",
        day_of_week="mon",
        hour=3,
        minute=0
    )

    print(
        "Scheduler pornit. "
        "Actualizarea se executa in fiecare luni la 03:00."
    )

    scheduler.start()


if __name__ == "__main__":
    start_scheduler()