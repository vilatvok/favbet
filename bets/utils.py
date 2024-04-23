import requests


def get_matches_data(league_id, api_key, day):
    response = (
        'https://apiv3.apifootball.com/'
        f'?action=get_events&from={day}&to={day}'
        f'&league_id={league_id}&APIkey={api_key}'
    )
    return response.json()[0]


def get_match_data(match_id, api_key):
    response = requests.get(
        'https://apiv3.apifootball.com/'
        f'?action=get_events&match_id={match_id}'
        f'&APIkey={api_key}'
    )
    return response.json()[0]


def get_odds_data(match_id, api_key):
    response = (
        'https://apiv3.apifootball.com/'
        f'?action=get_odds&match_id={match_id}'
        f'&APIkey={api_key}'
    )
    return response.json()[0]
