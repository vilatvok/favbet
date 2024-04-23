import json
import stripe

from celery import shared_task, Task

from datetime import datetime, date, timedelta

from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.db.models import F
from django_celery_beat.schedulers import (
    PeriodicTask,
    IntervalSchedule,
)

from users.models import DemoWallet
from users.schedulers import schedule_demo_wallet
from bets.schedulers import schedule_match, schedule_odds
from bets.models import Match, Bet
from bets.decorators import Timer
from bets.utils import get_matches_data, get_match_data, get_odds_data
from teams.models import Competition, Team


football_api_key = settings.FOOTBALL_SECRET_KEY


class BaseTaskRetry(Task):
    autoretry_for = (Exception,)
    retry_backoff = True
    max_retries = 3


@shared_task(queue='first')
def start_match():
    tasks = {
        task.name: task
        for task in PeriodicTask.objects.filter(name__contains='update-odds')
    }
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.MINUTES,
    )
    tasks_list = []
    created_tasks = []
    updated_statuses = []
    matches = Match.objects.filter(
        date=timezone.now().replace(second=0, microsecond=0),
    )
    for match in matches:
        response = get_match_data(match.uid, football_api_key)
        if response['match_status'] == 'Live':
            match.status = 'Live'
            updated_statuses.append(match)
            created_tasks.append(
                PeriodicTask(
                    interval=schedule,
                    name=f'end-match-{match.uid}',
                    task='bets.tasks.end_match',
                    args=json.dumps([match.uid]),
                )
            )
            task = tasks.get(f'update-odds-{match.uid}', None)
            task.enabled = False
            tasks_list.append(task)

    PeriodicTask.objects.bulk_create(created_tasks)
    PeriodicTask.objects.bulk_update(tasks_list, ['enabled'])
    Match.objects.bulk_update(updated_statuses, ['status'])


@shared_task(queue='first', bind=True, base=BaseTaskRetry)
def end_match(self, match_uid):
    try:
        response = get_match_data(match_uid, football_api_key)
    except KeyError:
        return 'Your plan has been expired. Please, renew it.'

    match_status = response['match_status']
    stripe.api_key = settings.STRIPE_SECRET_KEY

    bets_to_update = []
    wallets_to_update = []
    emails = []
    with Timer(logger=True):
        with transaction.atomic():
            match = Match.objects.get(uid=match_uid)
            if match_status == 'Finished':
                home_score = response['match_hometeam_score']
                away_score = response['match_awayteam_score']
                match.score = f'{home_score} - {away_score}'
                bets = match.bets.select_related('user')
                for bet in bets:
                    user = bet.user
                    if home_score > away_score:
                        if bet.prediction == 'H':
                            income = bet.amount * match.home_team_odds
                            increase_balance = F('balance') + income
                            if bet.demo:
                                user.demo_wallet.balance = increase_balance
                                wallets_to_update.append(user.demo_wallet)
                            bet.status = 'Success'
                            bet.income = income
                        else:
                            bet.status = 'Failure'
                    elif home_score < away_score:
                        if bet.prediction == 'A':
                            income = bet.amount * match.away_team_odds
                            increase_balance = F('balance') + income
                            if bet.demo:
                                user.demo_wallet.balance = increase_balance
                                wallets_to_update.append(user.demo_wallet)
                            bet.status = 'Success'
                            bet.income = income
                        else:
                            bet.status = 'Failure'
                    else:
                        if bet.prediction == 'D':
                            income = bet.amount * match.draw_odds
                            increase_balance = F('balance') + income
                            if bet.demo:
                                user.demo_wallet.balance = increase_balance
                                wallets_to_update.append(user.demo_wallet)
                            bet.status = 'Success'
                            bet.income = income
                        else:
                            bet.status = 'Failure'

                    bets_to_update.append(bet)

                    min_dep = (
                        Bet._meta.get_field('amount').validators[0].limit_value
                    )
                    lack = user.demo_wallet.balance < min_dep
                    bets = (
                        Bet.objects.filter(user=user).
                        exclude(status='Pending').exists()
                    )
                    if lack or not bets:
                        schedule_demo_wallet(user.demo_wallet.id)
                    if bet.status == 'Success':
                        message = (
                            f'Congratulations! You won! +{income}$\n'
                            f'Match result: {home_score} - {away_score}'
                        )
                    else:
                        message = (
                            'You lost! :(\n'
                            f'Match result: {home_score} - {away_score}'
                        )
                    emails.append((
                        'Bet results',
                        message,
                        settings.EMAIL_HOST_USER,
                        [user.email],
                    ))

                Bet.objects.bulk_update(bets_to_update, ['status', 'income'])

            elif match_status == 'Cancelled':
                bets = match.bets.all()
                for bet in bets:
                    if bet.demo:
                        bet.user.demo_wallet.balance = (
                            F('balance') + bet.amount
                        )
                        wallets_to_update.append(bet.user.demo_wallet)
                    else:
                        stripe.Refund.create(
                            payment_intent=bet.payment_id,
                        )
                    bet.status = match_status
                    bets_to_update.append(bet)

                Bet.objects.bulk_update(bets_to_update, ['status'])

            DemoWallet.objects.bulk_update(wallets_to_update, ['balance'])

            send_mass_mail(emails)
            task = PeriodicTask.objects.get(name=f'end-match-{match_uid}')
            task.enabled = False
            task.save()
            match.status = match_status
            match.save()


@shared_task(queue='second', bind=True, base=BaseTaskRetry)
def update_odds(self, match_uid):
    odds = get_odds_data(match_uid, football_api_key)

    match = Match.objects.get(uid=match_uid)
    match.home_team_odds = odds['odd_1']
    match.draw_odds = odds['odd_x']
    match.away_team_odds = odds['odd_2']
    match.save()


@shared_task(queue='first', bind=True, base=BaseTaskRetry)
def set_matches(self):
    """Updates matches daily."""
    day = date.today() + timedelta(days=3)
    leagues = [3, 152, 175, 302, 168, 207]

    competitions = {comp.uid: comp for comp in Competition.objects.all()}
    teams = {team.uid: team for team in Team.objects.all()}
    matches = []
    for league in leagues:
        response = get_matches_data(league, football_api_key, day)
        try:
            if response['error'] == 404:
                continue
        except TypeError:
            for match in response:
                match_id = match['match_id']

                odds = get_odds_data(match_id, football_api_key)

                date_ = datetime.strptime(match['match_date'], '%Y-%m-%d')
                time = datetime.strptime(match['match_time'], '%H:%M').time()
                datetime_ = datetime.combine(date_, time)

                competition = competitions.get(match['league_id'])
                home_team = teams.get(match['match_hometeam_id'])
                away_team = teams.get(match['match_awayteam_id'])

                matches.append(
                    Match(
                        uid=match_id,
                        competition=competition,
                        home_team=home_team,
                        away_team=away_team,
                        home_team_odds=odds['odd_1'],
                        draw_odds=odds['odd_x'],
                        away_team_odds=odds['odd_2'],
                        status='Pending',
                        date=datetime_,
                    )
                )
    matches = Match.objects.bulk_create(matches, ignore_conflicts=True)
    matches_time = Match.objects.only('uid', 'date').distinct('date')
    schedule_match(matches_time, matches)
    schedule_odds(matches)


@shared_task(queue='second')
def send_bet_letter(bet_id):
    """Sends a letter to the user after the bet is made."""
    bet = Bet.objects.get(id=bet_id)
    if bet.prediction == 'H':
        team = bet.match.home_team.name
    elif bet.prediction == 'A':
        team = bet.match.away_team.name
    else:
        team = 'Draw'
    letter = (
        f'Amount: {bet.amount}$\n'
        f'Match: {bet.match.match_name}\n'
        f'Prediction: {team}\n'
        f'Status: {bet.status}\n'
        f'Time: {bet.match.date}\n'
        'You can cancel a bet on this link: '
        f'http://127.0.0.1:8000/bets/{bet_id}/'
    )
    send_mail(
        subject=f'You bet on {team}',
        message=letter,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[bet.user.email],
        fail_silently=False,
    )


@shared_task(queue='second')
def remind_about_match(match_id):
    match = Match.objects.get(uid=match_id)
    bets = match.bets.all()
    emails = []
    for bet in bets:
        user_email = bet.user.email
        emails.append(
            'Match starting',
            f'Match {match.match_name} has been already started.',
            settings.EMAIL_HOST_USER,
            [user_email],
        )

    if len(emails):
        send_mass_mail(emails)
