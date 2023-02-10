import os
import json
from requests import Session
import numpy as np
import sys

class Alliance:
    def __init__(self, 
            color,
            team1,
            team2,
            auto,
            tele,
            endgame,
            score,
            auto_cone_pts,
            auto_low,
            auto_med,
            auto_high,
            signal_park,
            tele_cone_pts,
            tele_low,
            tele_med,
            tele_high,
            owned_junctions,
            beacons,
            circuit_pts):
        self.color = color
        self.team1 = team1
        self.team2 = team2
        self.auto = auto
        self.tele = tele
        self.endgame = endgame
        self.score = score
        self.auto_cone_pts = auto_cone_pts
        self.auto_low = auto_low
        self.auto_med = auto_med
        self.auto_high = auto_high
        self.signal_park = signal_park
        self.tele_cone_pts = tele_cone_pts
        self.tele_low = tele_low
        self.tele_med = tele_med
        self.tele_high = tele_high
        self.owned_junctions = owned_junctions
        self.beacons = beacons
        self.circuit_pts = circuit_pts

class Match:
    def __init__(self, num, red, blue):
        self.num = num
        self.red = red
        self.blue = blue

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
    with open('data/{}-event.json'.format(event_code), 'w') as f:
        response = session.get(event_url)
        f.write(json.dumps(response.json()))

def scrape_team_list(event_code):
    api_key = get_api_key()
    session = Session()
    session.headers.update({"Authorization": "Basic {}".format(api_key), "content-type": "application/json"})
    event_url = 'https://ftc-api.firstinspires.org/v2.0/2022/teams?eventCode={}'.format(event_code)
    response = session.get(event_url)
    teams = list(map(lambda x: "{} {}".format(str(x['teamNumber']), x['nameShort']), response.json()['teams']))
    with open('data/{}-teams.json'.format(event_code), 'w') as f:
        for team in teams:
            f.write(str(team) + '\n')

def scrape_score(event_code):
    api_key = get_api_key()
    session = Session()
    session.headers.update({"Authorization": "Basic {}".format(api_key), "content-type": "application/json"})
    event_url = 'https://ftc-api.firstinspires.org/v2.0/2022/scores/{}/qual'.format(event_code)
    response = session.get(event_url)
    print(response.json()['MatchScores'][0]['alliances'][0])

def load_matches(event_code):
    with open('data/{}-event.json'.format(event_code), 'r') as f:
        s = f.read()
        data = json.loads(s)
        matches = []
        for match_num, loaded_match in enumerate(data['matches']):
            teams = list(map(lambda x: x['teamNumber'], loaded_match['teams']))
            red1, red2 = int(teams[0]), int(teams[1])
            blue1, blue2 = int(teams[2]), int(teams[3])
            red_score = int(loaded_match['scoreRedFinal'])
            red_auto = int(loaded_match['scoreRedAuto'])
            blue_score = int(loaded_match['scoreBlueFinal'])
            blue_auto = int(loaded_match['scoreBlueAuto'])
            red = Alliance('red', red1, red2, red_auto, red_score)
            blue = Alliance('blue', blue1, blue2, blue_auto, blue_score)
            final_match = Match(match_num+1, red, blue)
            matches.append(final_match)
        return matches

def load_teams(event_code):
    with open('data/{}-teams.json'.format(event_code), 'r') as f:
        teams = {}
        for l in f.readlines():
            cleaned = l.strip()
            i = cleaned.index(" ")
            num = int(cleaned[:i])
            name = str(cleaned[i+1:])
            teams[num] = name
        return teams

def build_matrix(teams, matches):
    M = []
    for m in matches:
        r = []
        for team in teams:
            if m.red.team1 == team or m.red.team2 == team:
                r.append(1)
            else:
                r.append(0)
        M.append(r)
        b = []
        for team in teams:
            if m.blue.team1 == team or m.blue.team2 == team:
                b.append(1)
            else:
                b.append(0)
        M.append(b)
    return M

def build_data(matches):
    scores, autos, margins = [], [], []
    for m in matches:
        scores.append([m.red.score])
        scores.append([m.blue.score])
        autos.append([m.red.auto])
        autos.append([m.blue.auto])
        margins.append([m.red.score - m.blue.score])
        margins.append([m.blue.score - m.red.score])
    return scores, autos, margins

def solve(M, scores, autos, margins):
    M = np.matrix(M)
    scores = np.matrix(scores)
    autos = np.matrix(autos)
    margins = np.matrix(margins)
    pseudoinverse = np.linalg.pinv(M)
    opr_matrix = np.matmul(pseudoinverse, scores)
    auto_matrix = np.matmul(pseudoinverse, autos)
    ccwm_matrix = np.matmul(pseudoinverse, margins)
    return opr_matrix, auto_matrix, ccwm_matrix

def matrix_to_list(m):
    res = []
    for x in m: res.append(round(float(x), 3))
    return res

def format_team(num, name, opr, auto, ccwm):
    return f'{num : ^5}{name : ^30}{opr : ^15}{auto: ^15}{ccwm: ^15}'

def sort_teams(teams, oprs, autos, ccwm):
    teams_list, sorted_teams = [], []
    sorted_oprs, sorted_autos, sorted_ccwm = [], [], []
    for team in teams: teams_list.append(team)
    while len(sorted_teams) < len(teams_list):
        oprs_list = matrix_to_list(oprs)
        autos_list = matrix_to_list(autos)
        ccwm_list = matrix_to_list(ccwm)

        for i in range(len(teams_list)):
            if teams_list[i] not in sorted_teams:
                best_team = teams_list[i]
                best_opr = oprs_list[i]
                best_auto = autos_list[i]
                best_ccwm = ccwm_list[i]
                break

        for i in range(len(teams_list)):
            if oprs_list[i] > best_opr and teams_list[i] not in sorted_teams:
                best_team = teams_list[i]
                best_opr = oprs_list[i]
                best_auto = autos_list[i]
                best_ccwm = ccwm_list[i]

        sorted_teams.append(best_team)
        sorted_oprs.append(best_opr)
        sorted_autos.append(best_auto)
        sorted_ccwm.append(best_ccwm)

    print(format_team('TEAM', 'NAME', 'OPR', 'AUTO', 'CCWM'))
    for i in range(len(teams_list)):
        team_num = sorted_teams[i]
        print(format_team(team_num, teams[team_num], sorted_oprs[i], sorted_autos[i], sorted_ccwm[i]))

def scrape(event):
    scrape_event(event)
    scrape_team_list(event)

def analyze(event):
    matches = load_matches(event)
    teams = load_teams(event)
    M = build_matrix(teams, matches)
    scores, autos, margins = build_data(matches)
    opr_matrix, auto_matrix, margin_matrix = solve(M, scores, autos, margins)
    sort_teams(teams, opr_matrix, auto_matrix, margin_matrix)

def main():
    event = 'USCHSHAQ2'
    # if len(sys.argv) > 1: event = str(sys.argv[1])
    # if os.path.exists('data/{}-event.json'.format(event)):
        # scrape(event)
    # analyze(event)
    scrape_score(event)

if __name__ == "__main__":
    main()
