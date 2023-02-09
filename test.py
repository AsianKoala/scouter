import os
import json
from requests import Session
from datetime import date, datetime

class Alliance:
    def __init__(self, color, team1, team2, auto, score):
        self.color = color
        self.team1 = team1
        self.team2 = team2
        self.auto = auto
        self.score = score

    def __str__(self):
        return self.color + " Alliance: " + str(self.team1) + ", " + (self.team2)

class Match:
    def __init__(self, num, red, blue):
        self.num = num
        self.red = red
        self.blue = blue

    def __str__(self):
        return "Match # " + str(self.num) + ": (" + str(self.red.team1) + " & " + str(self.red.team2) + ") " + str(self.red.score) + " - " + str(self.blue.score) + " (" + str(self.blue.team1) + " & " +  str(self.blue.team2) + ")"

def get_api_key():
    file = os.path.join("api_key")
    with open(file, 'r') as f:
        api_key = f.read().strip()
        return api_key

def scrape_event(event_code):
    api_key = get_api_key()
    session = Session()
    session.headers.update({"Authorization": "Basic {}".format(api_key), "content-type": "application/json"})
    event_url = 'https://ftc-api.firstinspires.org/v2.0/2022/matches/{}'.format(event_code)
    with open('{}-event.json'.format(event_code), 'w') as f:
        response = session.get(event_url)
        f.write(json.dumps(response.json()))

def scrape_team_list(event_code):
    api_key = get_api_key()
    session = Session()
    session.headers.update({"Authorization": "Basic {}".format(api_key), "content-type": "application/json"})
    event_url = 'https://ftc-api.firstinspires.org/v2.0/2022/teams?eventCode={}'.format(event_code)
    response = session.get(event_url)
    teams = list(map(lambda x: x['teamNumber'], response.json()['teams']))
    with open('{}-teams.json'.format(event_code), 'w') as f:
        for team in teams:
            f.write(str(team) + '\n')

def load_matches(event_code):
    with open('{}-event.json'.format(event_code), 'r') as f:
        s = f.read()
        data = json.loads(s)
        matches = []
        for match_num, loaded_match in enumerate(data['matches']):
            teams = list(map(lambda x: x['teamNumber'], loaded_match['teams']))
            red1, red2 = teams[0], teams[1]
            blue1, blue2 = teams[2], teams[3]
            red_score = loaded_match['scoreRedFinal']
            red_auto = loaded_match['scoreRedAuto']
            blue_score = loaded_match['scoreBlueFinal']
            blue_auto = loaded_match['scoreBlueAuto']
            red = Alliance('red', red1, red2, red_auto, red_score)
            blue = Alliance('blue', blue1, blue2, blue_auto, blue_score)
            final_match = Match(match_num+1, red, blue)
            matches.append(final_match)
        return matches

def load_teams(event_code):
    with open('{}-teams.json'.format(event_code), 'r') as f:
        teams = []
        for team in f.readlines():
            teams.append(int(team.strip()))
        return teams


def main():
    event = 'USCHSHAQ2'
    # scrape_event(event)
    # scrape_team_list(event)
    matches = load_matches(event)
    for m in matches: print(m)
    # load_teams(event)

if __name__ == "__main__":
    main()
