import os
import json
from requests import Session
import numpy as np
import sys
import argparse
from datetime import datetime

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
            tele_ground,
            tele_low,
            tele_med,
            tele_high,
            beacons,
            owned_junctions,
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
        self.tele_ground = tele_ground
        self.tele_low = tele_low
        self.tele_med = tele_med
        self.tele_high = tele_high
        self.beacons = beacons
        self.owned_junctions = owned_junctions
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

def scrape_matches(event_code):
    api_key = get_api_key()
    session = Session()
    session.headers.update({"Authorization": "Basic {}".format(api_key), "content-type": "application/json"})
    event_url = 'https://ftc-api.firstinspires.org/v2.0/2022/scores/{}/qual'.format(event_code)
    response = session.get(event_url)
    with open('data/{}-matches.json'.format(event_code), 'w') as f:
        f.write(json.dumps(response.json()))

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

def build_alliance(color, team1, team2, match_data):
    return Alliance(
            color,
            team1,
            team2,
            match_data['autoPoints'],
            match_data['dcPoints'],
            match_data['endgamePoints'],
            match_data['prePenaltyTotal'],
            match_data['autoJunctionConePoints'],
            match_data['autoJunctionCones'][1],
            match_data['autoJunctionCones'][2],
            match_data['autoJunctionCones'][3],
            match_data['signalBonusPoints'],
            match_data['dcJunctionConePoints'],
            match_data['dcJunctionCones'][0],
            match_data['dcJunctionCones'][1],
            match_data['dcJunctionCones'][2],
            match_data['dcJunctionCones'][3],
            match_data['beacons'],
            match_data['ownedJunctions'],
            match_data['circuitPoints']
            )

def load_matches_new(event_code):
    with open('data/{}-matches.json'.format(event_code), 'r') as a, open('data/{}-event.json'.format(event_code), 'r') as b:
        s = a.read()
        t = b.read()
        match_data = json.loads(s)
        event_data = json.loads(t)
        matches = []
        if len(match_data['MatchScores']) == 0: 
            print('skipping', event_code)
            return None
        for i, m in enumerate(match_data['MatchScores']):
            teams = list(map(lambda x: x['teamNumber'], event_data['matches'][i]['teams']))
            red1, red2 = int(teams[0]), int(teams[1])
            blue1, blue2 = int(teams[2]), int(teams[3])
            blue = build_alliance('blue', blue1, blue2, m['alliances'][0])
            red = build_alliance('red', red1, red2, m['alliances'][1])
            built_match = Match(i+1, red, blue)
            matches.append(built_match)
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
            if m.red.team1 == team or m.red.team2 == team: r.append(1)
            else: r.append(0)
        M.append(r)
        b = []
        for team in teams:
            if m.blue.team1 == team or m.blue.team2 == team: b.append(1)
            else: b.append(0)
        M.append(b)
    return M

def build_new_data(matches):
    auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
    for m in matches:
        auto.append([m.red.auto])
        tele.append([m.red.tele])
        endgame.append([m.red.endgame])
        score.append([m.red.score])
        auto_cone_pts.append([m.red.auto_cone_pts])
        auto_low.append([m.red.auto_low])
        auto_med.append([m.red.auto_med])
        auto_high.append([m.red.auto_high])
        signal_park.append([m.red.signal_park])
        tele_cone_pts.append([m.red.tele_cone_pts])
        tele_ground.append([m.red.tele_ground])
        tele_low.append([m.red.tele_low])
        tele_med.append([m.red.tele_med])
        tele_high.append([m.red.tele_high])
        beacons.append([m.red.beacons])
        owned_junctions.append([m.red.owned_junctions])
        circuit_pts.append([m.red.circuit_pts])

        auto.append([m.blue.auto])
        tele.append([m.blue.tele])
        endgame.append([m.blue.endgame])
        score.append([m.blue.score])
        auto_cone_pts.append([m.blue.auto_cone_pts])
        auto_low.append([m.blue.auto_low])
        auto_med.append([m.blue.auto_med])
        auto_high.append([m.blue.auto_high])
        signal_park.append([m.blue.signal_park])
        tele_cone_pts.append([m.blue.tele_cone_pts])
        tele_ground.append([m.blue.tele_ground])
        tele_low.append([m.blue.tele_low])
        tele_med.append([m.blue.tele_med])
        tele_high.append([m.blue.tele_high])
        beacons.append([m.blue.beacons])
        owned_junctions.append([m.blue.owned_junctions])
        circuit_pts.append([m.blue.circuit_pts])

    return auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts

def solve_new(M, auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts):
    M = np.matrix(M)
    auto = np.matrix(auto)
    tele = np.matrix(tele)
    endgame = np.matrix(endgame)
    score = np.matrix(score)
    auto_cone_pts = np.matrix(auto_cone_pts)
    auto_low = np.matrix(auto_low)
    auto_med = np.matrix(auto_med)
    auto_high = np.matrix(auto_high)
    signal_park = np.matrix(signal_park)
    tele_cone_pts = np.matrix(tele_cone_pts)
    tele_ground = np.matrix(tele_ground)
    tele_low = np.matrix(tele_low)
    tele_med = np.matrix(tele_med)
    tele_high = np.matrix(tele_high)
    beacons = np.matrix(beacons)
    owned_junctions = np.matrix(owned_junctions)
    circuit_pts = np.matrix(circuit_pts)
    
    psuedoinverse = np.linalg.pinv(M)

    auto = np.matmul(psuedoinverse, auto)
    tele = np.matmul(psuedoinverse, tele)
    endgame = np.matmul(psuedoinverse, endgame)
    score = np.matmul(psuedoinverse, score)
    auto_cone_pts = np.matmul(psuedoinverse, auto_cone_pts)
    auto_low = np.matmul(psuedoinverse, auto_low)
    auto_med = np.matmul(psuedoinverse, auto_med)
    auto_high = np.matmul(psuedoinverse, auto_high)
    signal_park = np.matmul(psuedoinverse, signal_park)
    tele_cone_pts = np.matmul(psuedoinverse, tele_cone_pts)
    tele_ground = np.matmul(psuedoinverse, tele_ground)
    tele_low = np.matmul(psuedoinverse, tele_low)
    tele_med = np.matmul(psuedoinverse, tele_med)
    tele_high = np.matmul(psuedoinverse, tele_high)
    beacons = np.matmul(psuedoinverse, beacons)
    owned_junctions = np.matmul(psuedoinverse, owned_junctions)
    circuit_pts = np.matmul(psuedoinverse, circuit_pts)

    return auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts

def matrix_to_list(m):
    res = []
    for x in m: res.append(round(float(x), 2))
    return res

def format_team(num, name, score, auto, tele, endgame, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts):
    return f'{num : ^10}{name[:min(len(name), 20)] : ^30}{score : ^15}{auto: ^15}{tele: ^15}{endgame: ^15}{auto_cone_pts: ^15}{auto_low: ^15}{auto_med: ^15}{auto_high: ^15}{signal_park: ^15}{tele_cone_pts: ^15}{tele_ground: ^15}{tele_low: ^15}{tele_med: ^15}{tele_high: ^15}{beacons: ^15}{owned_junctions: ^15}{circuit_pts: ^15}'

def print_header():
    print(format_team('TEAM', 'NAME', 'OPR', 'AUTO', 'TELE', 'END', 'A_CONE_PTS', 'A_L', 'A_M', 'A_H', 'PARK', 'T_CONE_PTS', 'T_G', 'T_L', 'T_M', 'T_H', 'BEACON', 'OWNED', 'CIRCUIT'))

def print_team(num, name, auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts):
    print(format_team(num, name, score, auto, tele, endgame, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts))

def print_all_teams(teams, teams_list, sorted_teams, sorted_auto, sorted_tele, sorted_endgame, sorted_score, sorted_auto_cone_pts, sorted_auto_low, sorted_auto_med, sorted_auto_high, sorted_signal_park, sorted_tele_cone_pts, sorted_tele_ground, sorted_tele_low, sorted_tele_med, sorted_tele_high, sorted_beacons, sorted_owned_junctions, sorted_circuit_pts):
        for i in range(len(teams_list)):
            team_num = sorted_teams[i]
            print_team(team_num, teams[team_num],sorted_auto[i], sorted_tele[i], sorted_endgame[i], sorted_score[i], sorted_auto_cone_pts[i], sorted_auto_low[i], sorted_auto_med[i], sorted_auto_high[i], sorted_signal_park[i], sorted_tele_cone_pts[i], sorted_tele_ground[i], sorted_tele_low[i], sorted_tele_med[i], sorted_tele_high[i], sorted_beacons[i], sorted_owned_junctions[i], sorted_circuit_pts[i])

def sort_teams(teams, auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts):
    teams_list, sorted_teams = [], []
    sorted_auto, sorted_tele, sorted_endgame, sorted_score, sorted_auto_cone_pts, sorted_auto_low, sorted_auto_med, sorted_auto_high, sorted_signal_park, sorted_tele_cone_pts, sorted_tele_ground, sorted_tele_low, sorted_tele_med, sorted_tele_high, sorted_beacons, sorted_owned_junctions, sorted_circuit_pts = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
    for team in teams: teams_list.append(team)
    while len(sorted_teams) < len(teams_list):
        auto_list = matrix_to_list(auto)
        tele_list = matrix_to_list(tele)
        endgame_list = matrix_to_list(endgame)
        score_list = matrix_to_list(score)
        auto_cone_pts_list = matrix_to_list(auto_cone_pts)
        auto_low_list = matrix_to_list(auto_low)
        auto_med_list = matrix_to_list(auto_med)
        auto_high_list = matrix_to_list(auto_high)
        signal_park_list = matrix_to_list(signal_park)
        tele_cone_pts_list = matrix_to_list(tele_cone_pts)
        tele_ground_list = matrix_to_list(tele_ground)
        tele_low_list = matrix_to_list(tele_low)
        tele_med_list = matrix_to_list(tele_med)
        tele_high_list = matrix_to_list(tele_high)
        beacons_list = matrix_to_list(beacons)
        owned_junctions_list = matrix_to_list(owned_junctions)
        circuit_pts_list = matrix_to_list(circuit_pts)

        for i in range(len(teams_list)):
            if teams_list[i] not in sorted_teams:
                best_team = teams_list[i]
                best_auto = auto_list[i] 
                best_tele = tele_list[i]
                best_endgame = endgame_list[i]
                best_score = score_list[i]
                best_auto_cone_pts = auto_cone_pts_list[i]
                best_auto_low = auto_low_list[i]
                best_auto_med = auto_med_list[i]
                best_auto_high = auto_high_list[i]
                best_signal_park = signal_park_list[i]
                best_tele_cone_pts = tele_cone_pts_list[i]
                best_tele_ground = tele_ground_list[i]
                best_tele_low = tele_low_list[i]
                best_tele_med = tele_med_list[i]
                best_tele_high = tele_high_list[i]
                best_beacons = beacons_list[i]
                best_owned_junctions = owned_junctions_list[i]
                best_circuit_pts = circuit_pts_list[i]

        for i in range(len(teams_list)):
            if score_list[i] > best_score and teams_list[i] not in sorted_teams:
                best_team = teams_list[i]
                best_auto = auto_list[i] 
                best_tele = tele_list[i]
                best_endgame = endgame_list[i]
                best_score = score_list[i]
                best_auto_cone_pts = auto_cone_pts_list[i]
                best_auto_low = auto_low_list[i]
                best_auto_med = auto_med_list[i]
                best_auto_high = auto_high_list[i]
                best_signal_park = signal_park_list[i]
                best_tele_cone_pts = tele_cone_pts_list[i]
                best_tele_ground = tele_ground_list[i]
                best_tele_low = tele_low_list[i]
                best_tele_med = tele_med_list[i]
                best_tele_high = tele_high_list[i]
                best_beacons = beacons_list[i]
                best_owned_junctions = owned_junctions_list[i]
                best_circuit_pts = circuit_pts_list[i]

        sorted_teams.append(best_team)
        sorted_auto.append(best_auto)
        sorted_tele.append(best_tele)
        sorted_endgame.append(best_endgame)
        sorted_score.append(best_score)
        sorted_auto_cone_pts.append(best_auto_cone_pts)
        sorted_auto_low.append(best_auto_low)
        sorted_auto_med.append(best_auto_med)
        sorted_auto_high.append(best_auto_high)
        sorted_signal_park.append(best_signal_park)
        sorted_tele_cone_pts.append(best_tele_cone_pts)
        sorted_tele_ground.append(best_tele_ground)
        sorted_tele_low.append(best_tele_low)
        sorted_tele_med.append(best_tele_med)
        sorted_tele_high.append(best_tele_high)
        sorted_beacons.append(best_beacons)
        sorted_owned_junctions.append(best_owned_junctions)
        sorted_circuit_pts.append(best_circuit_pts)

    return [teams, teams_list, sorted_teams, sorted_auto, sorted_tele, sorted_endgame, sorted_score, sorted_auto_cone_pts, sorted_auto_low, sorted_auto_med, sorted_auto_high, sorted_signal_park, sorted_tele_cone_pts, sorted_tele_ground, sorted_tele_low, sorted_tele_med, sorted_tele_high, sorted_beacons, sorted_owned_junctions, sorted_circuit_pts]

def get_orange_api_key():
    file = os.path.join('orange_api_key')
    with open(file, 'r') as f:
        api_key = f.read().strip()
        return api_key

def strip_timestamp(t):
    return datetime.fromisoformat(t[:t.index('T')])

def check_doesnt_exist(event, name):
    return not os.path.exists('data/{}-{}.json'.format(event, name))

def check_needs_scrape(event):
    names = ['matches', 'teams', 'event']
    needs_scrape = False
    for name in names:
        needs_scrape = needs_scrape or check_doesnt_exist(event, name)
    return needs_scrape

def scrape(event):
    scrape_event(event)
    scrape_team_list(event)
    scrape_matches(event)

def analyze(event, should_print):
    matches = load_matches_new(event)
    if matches == None: return None
    teams = load_teams(event)
    M = build_matrix(teams, matches)
    auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts = build_new_data(matches)
    auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts = solve_new(M, auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts)
    event_data = sort_teams(teams, auto, tele, endgame, score, auto_cone_pts, auto_low, auto_med, auto_high, signal_park, tele_cone_pts, tele_ground, tele_low, tele_med, tele_high, beacons, owned_junctions, circuit_pts)
    if should_print: print_all_teams(*event_data)
    return event_data

def get_team_event_response(team):
    api_key = get_api_key()
    session = Session()
    session.headers.update({"Authorization": "Basic {}".format(api_key), "content-type": "application/json"})
    event_url = 'https://ftc-api.firstinspires.org/v2.0/2022/events?teamNumber={}'.format(team)
    response = session.get(event_url).json()['events']
    event_codes = list(map(lambda x: x['code'], response))
    start_dates = list(map(lambda x: strip_timestamp(x['dateStart']), response))
    zipped = zip(event_codes, start_dates)
    res = list(map(lambda x: x[0], sorted(zipped, key=lambda x: x[1], reverse=True)))
    return res
    
def analyze_all_events(team):
    event_codes, start_dates = get_team_event_response(team)
    today = datetime.today()
    num_future_timestamps = sum([x > today for x in start_dates])
    prev_events = event_codes[num_future_timestamps + 1:]
    if len(prev_events) == 0: return []
    return prev_events

def analyze_recent_event(team):
    event_codes, start_dates = get_team_event_response(team)
    event_time_pairs = zip(event_codes, start_dates)
    event_time_pairs = sorted(event_time_pairs, key=lambda x: x[1], reverse=True)
    today = datetime.today()
    num_future_timestamps = sum([x > today for x in start_dates])
    print(num_future_timestamps)
    prev_events = list(map(lambda x: x[0], event_time_pairs))[num_future_timestamps:]
    return prev_events

def get_team_highest_opr(team):
    # events = get_team_event_response(team)
    # # best_opr = -100000 # surely no team will be below this opr
    # # best_event = []
    # # failed_event = True
    # for event in events:
    #     if check_needs_scrape(event):
    #         print('scraping', event)
    #         scrape(event)
    #     event_stats = analyze(event, False)
    #     if event_stats == None: continue
    #     idx = event_stats[2].index(team)
    #     team_stats = [team, event_stats[0][team]] + [x[idx] for x in event_stats[3:]]
    #     # team_opr = team_stats[5]
    #     return team_stats
    #    events = get_team_event_response(team)
    #  raise Exception('All events failed')
    events = get_team_event_response(team)
    # print(events)
    # best_opr = -100000 # surely no team will be below this opr
    best_event = []
    for event in events:
        if check_needs_scrape(event):
            print('scraping', event)
            scrape(event)
        event_stats = analyze(event, False)
        if event_stats == None: continue
        idx = event_stats[2].index(team)
        team_stats = [team, event_stats[0][team]] + [x[idx] for x in event_stats[3:]]
        # team_opr = team_stats[5]
        return team_stats
        # if team_opr > best_opr:
        #     best_opr = team_opr
        #     best_event = team_stats
    return best_event

def print_teams_best_events(best_events):
    print_header()
    best_events.sort(reverse=True, key=lambda x: x[5])
    for team in best_events:
        print_team(*team)

def scout_event(event_code):
    if not os.path.exists('{}-teams.json'.format(event_code)):
        scrape_team_list(event_code)
    teams = list(load_teams(event_code))
    best_events = list(filter(lambda x: len(x) > 0, map(lambda x: get_team_highest_opr(x), teams)))
    print_teams_best_events(best_events)

def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('event')
    # parser.add_argument('-t', '--teams', action='store_true')
    # args = parser.parse_args()
    # print(args.event, args.teams)
    # get_team_highest_opr(21232)
    # if len(sys.argv) > 1: event = str(sys.argv[1])
    # scrape(event)
    # analyze(event)
    # scout_event('USCHSCMPVIO')
    scout_event('USTXCECMPJHNS')
    # analyze_recent_event(21232)

if __name__ == "__main__":
    main()
