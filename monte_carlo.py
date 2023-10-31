import random
import pandas as pd
from numpy import mean, std
from cbb_functions import *

kp_ratings = get_ratings(2024).reset_index(drop=True)
#mgm_df = get_mgm_df('https://sports.co.betmgm.com/en/sports/basketball-7/betting/usa-9/ncaa-264', 1)
teams = kp_ratings[['Team', 'Conf']]
games_list_full = pd.read_csv('~/Desktop/cbb_model/games_list_2024.csv')
games_list_full['Date'] = pd.to_datetime(games_list_full['Date'], format='%Y-%m-%d')
games_list = games_list_full
hca = get_hca()
avr_d = mean(kp_ratings['AdjD'])

todays_games = games_list_full[games_list_full['Date'] >= datetime.today()]
todays_games = todays_games.dropna()

def get_ot_adj(row):
    if (row['OT'] == '') | ('%' in row['OT']):
        ot_adj = 1
    elif (row['OT'] == 'OT'):
        ot_adj = 8/9
    else:
        denom = int(row['OT'][0]) + 8
        ot_adj = 8/denom
    return(ot_adj)

def get_score(team, games_list):
    team_home_scores = games_list[(games_list['Home'] == team)]
    team_away_scores = games_list[(games_list['Away'] == team)]
    team_ratings = kp_ratings[kp_ratings['Team'] == team]

    team_home_scores = team_home_scores.merge(kp_ratings, left_on = 'Away', right_on = 'Team')
    team_home_scores['OT Adj'] = team_home_scores.apply(get_ot_adj, axis=1)
    team_home_scores['AdjScore'] = team_home_scores['Home Score'] * (avr_d/team_home_scores['AdjD']) * \
                                   team_home_scores['OT Adj']

    team_away_scores = team_away_scores.merge(kp_ratings, left_on = 'Home', right_on = 'Team')
    team_away_scores['OT Adj'] = team_away_scores.apply(get_ot_adj, axis=1)
    team_away_scores['AdjScore'] = team_away_scores['Away Score'] * (avr_d / team_away_scores['AdjD']) * \
                                   team_away_scores['OT Adj']

    tempO = (mean(team_away_scores['AdjT']) + mean(team_home_scores['AdjT']) + 2 * team_ratings['AdjT'])/2

    mean_score = mean(pd.concat([team_home_scores['AdjScore'],team_away_scores['AdjScore']]))

    std_score = std(pd.concat([team_home_scores['AdjScore'],team_away_scores['AdjScore']]))

    return np.random.normal(mean_score, std_score, 1000), tempO

def get_spread(ht, at, nuet, games_list):

    home_d = float(kp_ratings[kp_ratings['Team'] == ht]['AdjD'].iloc[0])
    away_d = float(kp_ratings[kp_ratings['Team'] == at]['AdjD'].iloc[0])

    home_temp = float(kp_ratings[kp_ratings['Team'] == ht]['AdjT'].iloc[0])
    away_temp = float(kp_ratings[kp_ratings['Team'] == at]['AdjT'].iloc[0])

    if nuet == 0:
        try:
            hca_pm = float(hca[hca['Team'] == ht]['hca'].iloc[0])/2
        except:
            hca_pm = float(min(hca['hca']))/2
    else:
        hca_pm = 0

    home_sims = get_score(ht, games_list)
    home_tempO = float(home_sims[1].iloc[0])
    home_sims = np.array(home_sims[0])
    away_sims = get_score(at, games_list)
    away_tempO = float(away_sims[1].iloc[0])
    away_sims = np.array(away_sims[0])
    home_scores = (home_sims * (away_d/avr_d) * (home_temp + away_temp)/home_tempO) + hca_pm
    away_scores = (away_sims * (home_d/avr_d) * (home_temp + away_temp)/away_tempO) - hca_pm

    game_scores = pd.concat([pd.DataFrame(away_scores), pd.DataFrame(home_scores)], axis=1)
    game_scores.columns = ['Home Score', 'Away Score']
    game_scores['Result'] = (game_scores['Home Score'] > game_scores['Away Score']).astype(int)
    #odds = mean(game_scores['Result'])

    game_line = pd.DataFrame([['Date', ht, mean(home_scores), at, mean(away_scores), nuet,
                              mean(home_scores)-mean(away_scores),mean(home_scores) + mean(away_scores),mean(game_scores['Result'])]])
    game_line.columns = ['Date','Team','Score','Opponent','Opponent Score', 'Location', 'Spread', 'OU', 'Win Percent']
    game_line['Date'] = games_list['Date']

    return game_line

column_names = ['Date','Team','Score','Opponent','Opponent Score', 'Location', 'Spread', 'OU', 'Win Percent']
predictions = pd.DataFrame(columns=column_names)
for i in range(len(todays_games)):
    ht = todays_games.iloc[i]['Home']
    at = todays_games.iloc[i]['Away']
    nuet = todays_games.iloc[i]['Nuetral']
    if (ht in set(teams['Team'])) & (at in set(teams['Team'])):
        game_pred = get_spread(ht, at, nuet, games_list_full)
        game_pred.columns = column_names
        predictions = pd.concat([predictions, game_pred])


# line_analysis = fuzzy_merge(mgm_df, predictions, 80)
# line_analysis['spread_diff'] = abs(line_analysis['Spread'] - line_analysis['spread'])
# line_analysis['ou_diff'] = abs(line_analysis['OU'] - line_analysis['ou'])

#Get Injured_Players
# player_table = get_players()
# injured_players = get_injured_players(player_table)
# ipr = get_injured_team_report(injured_players, teams)
# ipr_home = ipr.copy()
# ipr_away = ipr.copy()
# ipr_home.columns = ['Team', 'HInj', 'HValInj']
# ipr_away.columns = ['Opponent', 'AInj', 'AValInj']
# line_analysis = line_analysis.merge(ipr_home, on='Team')
# line_analysis = line_analysis.merge(ipr_away, on='Opponent')
# best_spreads = line_analysis.sort_values(by='spread_diff', ascending=False)
# best_ous = line_analysis.sort_values(by='ou_diff', ascending=False)
#
# team_sort = predictions.sort_values(by='Team', ascending=False)
