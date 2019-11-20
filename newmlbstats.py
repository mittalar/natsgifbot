import urllib.parse
import json
import utils
from datetime import datetime

def _new_player_search(name):
    url = "https://suggest.mlb.com/svc/suggest/v1/min_all/%s/99999" % urllib.parse.quote(name)
    players = utils.get_json(url)['suggestions']
    if len(players) > 0:
        for player in players:
            data = player.split('|')
            playerid = data[1]
            url = "https://statsapi.mlb.com/api/v1/people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league)),leagueListId=mlb_hist)" % playerid
            return utils.get_json(url)['people'][0]

def _get_player_info_line(player):
    pos = player['primaryPosition']['abbreviation']
    bats = player['batSide']['code']
    throws = player['pitchHand']['code']
    height = player['height']
    weight = player['weight']
    return "%s | B/T: %s/%s | %s | %s" % (pos, bats, throws, height, weight)

def get_player_season_stats(name, type=None, year=None, career=None, reddit=None):
    player = _new_player_search(name)
    if player is None:
        return "No matching player found"
    teamid = player['currentTeam']['id']
    teamabv = player['currentTeam']['abbreviation']
    pid = player['id']
    disp_name = player['fullName']
    pos = player['primaryPosition']['abbreviation']
    infoline = _get_player_info_line(player)
    now = datetime.now()
    # birthdate = player['birth_date']
    birthdate = player['birthDate']
    birthdate = birthdate[:birthdate.find('T')]
    birth = birthdate.split('-')

    if year is None:
        year = str(now.year)
        year2 = year
    elif '-' in year:
        years = year.split('-')
        year = years[0]
        year2 = years[1]
    else:
        year2 = year

    d = None
    if year == None:
        d = now.year - int(birth[0]) - ((now.month, now.day) < (int(birth[1]), int(birth[2])))
    elif year is not None:
        d = int(year) - int(birth[0]) - ((7,1) < (int(birth[1]), int(birth[2])))
    if d is not None:
        infoline = "%s | Age: %d" % (infoline, d)
    if now.month == int(birth[1]) and now.day == int(birth[2]):
        infoline = infoline + "  **HAPPY BIRTHDAY**"

    if type is None and pos == 'P':
        type = "pitching"
    elif type is None and pos != 'P':
        type = "hitting"

    stattype = 'yearByYear'
    if career:
        stattype = "career"

    seasons = []
    for stat in player['stats']:
        if stat['type']['displayName'] == stattype and 'displayName' in stat['group'] and stat['group']['displayName'] == type:
            if career:
                for cstat in player['stats']:
                    if cstat['type']['displayName'] == 'yearByYear' and 'displayName' in cstat['group'] and cstat['group']['displayName'] == type:
                        years = "%s-%s" % (cstat['splits'][0]['season'], cstat['splits'][-1]['season'])
            for split in stat['splits']:
                if stattype == 'yearByYear':
                    if int(split['season']) < int(year) or int(split['season']) > int(year2):
                        continue
                season = split['stat']
                if 'season' in split:
                    season['season'] = split['season']
                if 'team' in split:
                    season['team'] = split['team']['abbreviation']
                else:
                    season['team'] = split['sport']['abbreviation']
                seasons.append(split['stat'])
    if type == "hitting":
        stats = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg' ,'ops']
    elif type == "pitching":
        stats = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched', 'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']
    if len(seasons) > 1:
        stats = ['season', 'team'] + stats
    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr','baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip'}

    if year == year2:
        output = "%s season stats for %s (%s):" % (year, disp_name, teamabv)
    else:
        output = "%s-%s seasons stats for %s:" % (year, year2, disp_name)
    if career:
        output = "Career stats for %s (%s):" % (disp_name, years)
    output = "%s\n\t%s\n\n" % (output, infoline)
    output = output + utils.format_table(stats, seasons, repl_map=repl, reddit=reddit)
    return output

if __name__ == "__main__":
    # print(get_player_season_stats("rendon", year="2016-2019"))
    # print(get_player_season_stats("rendon", career=True))
    print(get_player_season_stats('max scherzer'))
