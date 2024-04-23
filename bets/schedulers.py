import json

from datetime import datetime, date, timedelta

from django_celery_beat.schedulers import (
    PeriodicTask,
    CrontabSchedule,
    IntervalSchedule,
)


def schedule_match(time_matches, matches):
    day = date.today() + timedelta(days=3)
    crontabs = []
    for match in time_matches:
        match_date = match.date
        crontab = CrontabSchedule(
            minute=match_date.minute,
            hour=match_date.hour,
            day_of_month=match_date.day,
            month_of_year=match_date.month,
        )
        crontabs.append(crontab)

    CrontabSchedule.objects.bulk_create(crontabs, ignore_conflicts=True)
    crontabs = CrontabSchedule.objects.filter(
        day_of_month=day.day,
        month_of_year=day.month,
    )
    crontabs_dict = {}
    for crontab in crontabs:
        __date = datetime(
            year=2024,
            month=int(crontab.month_of_year),
            day=int(crontab.day_of_month),
            hour=int(crontab.hour),
            minute=int(crontab.minute),
        )
        __date = __date.strftime('%m/%d/%H:%M')
        crontabs_dict[__date] = crontab

    matches_for_schedule = []
    for match in time_matches:
        match_date = match.date
        day_ = match_date.strftime('%m/%d/%H:%M')
        cron = crontabs_dict.get(day_)
        matches_for_schedule.append(
            PeriodicTask(
                crontab=cron,
                name=f'start-{day_}',
                task='bets.tasks.start_match',
            )
        )

    for match in matches:
        match_date = match.date
        day_ = match_date.strftime('%m/%d/%H:%M')
        cron = crontabs_dict.get(day_)
        matches_for_schedule.append(
            PeriodicTask(
                crontab=cron,
                name=f'remind-about-match-{match.uid}',
                task='bets.tasks.remind_about_match',
                args=json.dumps([match.uid]),
            )
        )

    PeriodicTask.objects.bulk_create(matches_for_schedule)


def schedule_odds(matches):
    """Update odds every 6 hours."""
    interval, _ = IntervalSchedule.objects.get_or_create(
        every=6,
        period=IntervalSchedule.HOURS
    )

    odds_for_schedule = []
    for match in matches:
        odds_for_schedule.append(
            PeriodicTask(
                interval=interval,
                name=f'update-odds-{match.uid}',
                task='bets.tasks.update_odds',
                args=json.dumps([match.uid]),
            )
        )

    PeriodicTask.objects.bulk_create(odds_for_schedule)
