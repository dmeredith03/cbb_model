from cbb_functions import *

# Get Odds
#mgm_df = get_mgm_df('https://sports.co.betmgm.com/en/sports/basketball-7/betting/usa-9/ncaa-264', 2)
#Get KP Rankings and Teams list
kp_ratings = get_ratings(2024).reset_index(drop=True)
teams = kp_ratings[['Team', 'Conf']]

#Get Data for DNN

games_list_1 = pd.read_csv('~/games_list_2022.csv')
games_list_2 = pd.read_csv('~/games_list_2023.csv')
games_list_3 = pd.read_csv('~/games_list_2024.csv')
home_score_1, away_score_1 = get_features_past(games_list_1,get_ratings(2022))
home_score_2, away_score_2 = get_features_past(games_list_2,get_ratings(2023))
future_games_home, future_games_away, future_home,future_away, future_dates, future_loc = get_features_future(games_list_3, get_ratings(2024))
future_games_home.pop('score')
home_score = pd.DataFrame(columns=future_games_home.columns)
away_score = pd.DataFrame(columns=future_games_away.columns)
home_score = pd.concat([home_score, home_score_1, home_score_2]).fillna(int(0))
away_score = pd.concat([away_score,away_score_1, away_score_2]).fillna(int(0))


predictions = get_pred(home_score, away_score, future_games_home, future_home, future_away, future_dates, future_loc)
predictions['Date'] = pd.to_datetime(predictions['Date'].str[4:], format='%b %d')

predictions['Date'].loc[predictions['Date'].dt.month > 10] = \
    predictions[predictions['Date'].dt.month > 10]['Date'].apply(lambda dt: dt.replace(year=2023))
predictions['Date'].loc[predictions['Date'].dt.month < 10] = \
    predictions[predictions['Date'].dt.month < 10]['Date'].apply(lambda dt: dt.replace(year=2024))

predictions = predictions.sort_values(by='Date').reset_index(drop=True)
predictions['Date'] = predictions['Date'].dt.date

#Find todays spreads
d1 = date(2023, 11, 6)
d2 = date(2023, 11, 6)
week_predictions = predictions[(d1 <= predictions['Date']) & (predictions['Date'] <= d2)]

# Commented until mgm puts up odds
# week_games = fuzzy_merge(mgm_df, week_predictions, 80)
# week_games['spread_diff'] = abs(week_games['Spread'] - week_games['spread'])
# week_games['ou_diff'] = abs(week_games['OU'] - week_games['ou'])

#Get Injured_Players
# player_table = pd.read_csv('/Users/dmeredith/Desktop/player_table.csv')
# player_table = player_table.iloc[: , 1:]
# injured_players = get_injured_players(player_table)
# ipr = get_injured_team_report(injured_players, teams)
# ipr_home = ipr.copy()
# ipr_away = ipr.copy()
# ipr_home.columns = ['Team', 'HInj', 'HValInj']
# ipr_away.columns = ['Opponent', 'AInj', 'AValInj']
# week_games = week_games.merge(ipr_home, on='Team')
# week_games = week_games.merge(ipr_away, on='Opponent')
# best_spreads = week_games.sort_values(by='spread_diff', ascending=False)
# best_ous = week_games.sort_values(by='ou_diff', ascending=False)


records = get_records(predictions)
bigten = records[records['Conf'] == 'B10'].sort_values(by='Conf Wins',ascending=False).reset_index(drop=True)
bigtwelve = records[records['Conf'] == 'B12'].sort_values(by='Conf Wins',ascending=False).reset_index(drop=True)
sec = records[records['Conf'] == 'SEC'].sort_values(by='Conf Wins',ascending=False).reset_index(drop=True)
acc = records[records['Conf'] == 'ACC'].sort_values(by='Conf Wins',ascending=False).reset_index(drop=True)
pactwelve = records[records['Conf'] == 'P12'].sort_values(by='Conf Wins',ascending=False).reset_index(drop=True)
bigeast = records[records['Conf'] == 'BE'].sort_values(by='Conf Wins',ascending=False).reset_index(drop=True)





