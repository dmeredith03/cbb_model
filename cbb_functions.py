import pandas as pd
import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup
import os
import time
from datetime import date, datetime
import pandas as pd
import numpy as np
import pybettor as pb
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from selenium import webdriver
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import re
import statistics

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# import kenpompy
# from kenpompy import team, misc
# from kenpompy.utils import login


# must have chromedriver installed
#chromedriver = '/usr/local/bin/chromedriver'


def get_mgm_df(webpage, tab):
    browser = webdriver.Chrome()
    browser.get(webpage)
    time.sleep(10)

    click = browser.find_element("xpath", '//*[@id="main-view"]/ms-widget-layout/ms-widget-slot/ms-composable-widget/ms-widget-tab-bar/ms-tab-bar/ms-scroll-adapter/div/div/ul/li[' + str(tab) + ']')
    click.click()

    time.sleep(1)
    for i in range(30):
        try:
            element = browser.find_element('class name', 'grid-footer')
            browser.execute_script("arguments[0].scrollIntoView({behavior: \"auto\", block: \"center\", inline: \"center\"})", element)
            element.click()
            time.sleep(1)
        except:
            time.sleep(1)
    time.sleep(1)
    home_teams = []
    away_teams = []
    spread_home = []
    ou = []
    times = []
    elements = ["grid-six-pack-event"]
    for element in elements:
            parents = browser.find_elements('class name', element)
            for parent in parents:
                time_start_el = parent.find_elements('class name', 'starting-time')
                for time_start in time_start_el:
                    try:
                        times.append(time_start.text.split("Today • ")[1])
                    except:
                        times.append(time_start.text)
                teams = parent.find_elements("class name", "participant")
                i = 1
                for team in teams:
                    if i % 2 == 1:
                        away_teams.append(team.text.replace("State", "St."))
                    else:
                        home_teams.append(team.text.replace("State", "St."))
                    i += 1
                options = parent.find_elements("class name", "option-attribute")
                i = 1
                for option in options:
                    if i % 4 == 1:
                        try:
                            spread = option.text
                            if spread[0] == '-':
                                spread_home.append(-1 * float(spread.split('-')[1]))
                            else:
                                spread_home.append(float(spread.split('+')[1]))
                        except:
                            spread_home.append(np.nan)
                    elif i % 4 == 3:
                        try:
                            ou.append(float(option.text.split('O ')[1]))
                        except:
                            ou.append(np.nan)
                    i += 1

    browser.close()

    df = [list(row) for row in zip(times, away_teams, home_teams, spread_home, ou)]
    df = pd.DataFrame(df, columns=['time', 'away_team', 'home_team', 'spread', 'ou'])
    df = df.drop_duplicates()
    df = df.dropna()
    return df

def tableDataText(table):
    """Parses a html segment started with tag <table> followed
    by multiple <tr> (table rows) and inner <td> (table data) tags.
    It returns a list of rows with inner columns.
    Accepts only one <th> (table header/data) in the first row.
    """
    def rowgetDataText(tr, coltag='td'): # td (data) or th (header)
        return [td.get_text(strip=True) for td in tr.find_all(coltag)]
    rows = []
    trs = table.find_all('tr')
    headerow = rowgetDataText(trs[0], 'th')
    if headerow: # if there is a header row include first
        rows.append(headerow)
        trs = trs[1:]
    for tr in trs: # for every table row
        rows.append(rowgetDataText(tr, 'td') ) # data row
    return rows

def get_player_table(master, html, column_list):
    soup = BeautifulSoup(html,'html.parser')
    tables = soup.find_all( "table", {"id":"ratings-table"})
    table = tables[len(tables) - 1]
    table = tableDataText(table)
    table = pd.DataFrame(table, columns=column_list)
    table = table[table[column_list[1]].notna()]
    master = pd.concat([master, table])
    return master

def get_schedule_table(master, html, column_list, team):
    soup = BeautifulSoup(html,'html.parser')
    tables = soup.find_all( "table", {"id": "schedule-table"})
    table = tables[len(tables) - 1]
    table = tableDataText(table)
    table = pd.DataFrame(table, columns=column_list)
    table = table[table[column_list[5]].notna()]
    table = table[table[column_list[0]] != 'Date']
    table['Team'] = [team] * (len(table))
    master = pd.concat([master, table])
    return master

def get_ratings(year):
    browser = webdriver.Chrome()
    if year == 2023:
        webpage = 'https://kenpom.com/'
    else:
        webpage = f'https://kenpom.com/index.php?y={year}'
    browser.get(webpage)
    time.sleep(2)

    html = browser.page_source
    soup = BeautifulSoup(html,'html.parser')
    table = soup.find("table", {"id":"ratings-table"})
    ratings_table = tableDataText(table)

    ratings_table = pd.DataFrame(ratings_table)

    ratings_table = ratings_table[ratings_table[0].notna()]
    ratings_table.columns = ['Ranking','Team','Conf','Record', 'AdjEM', 'AdjO', 'Del', 'AdjD', 'Del', 'AdjT', 'Del', 'Luck', 'Del', 'OppAdjEM', 'Del', 'OppO', 'Del','OppD', 'Del','NCOppEM','Del']
    ratings_table['Team'] = ratings_table['Team'].str.replace('\d+', '')
    ratings_table = ratings_table[ratings_table['Ranking'] != '']
    ratings_table = ratings_table[['Team', 'Conf', 'AdjEM', 'AdjO', 'AdjD','AdjT']]
    ratings_table[['AdjEM', 'AdjO', 'AdjD','AdjT']] = ratings_table[['AdjEM', 'AdjO', 'AdjD','AdjT']].apply(pd.to_numeric, errors='coerce')

    browser.close()
    return ratings_table

def get_hca():
    browser = webdriver.Chrome()
    webpage = "https://kenpom.com/hca.php?s=RankHCA"
    browser.get(webpage)
    time.sleep(2)
    username = browser.find_element("name", "email")
    password = browser.find_element("name", "password")

    username.send_keys("drew.c.meredith@gmail.com")
    password.send_keys("EdeysNuts")

    login = browser.find_element("name", "submit")
    login.click()

    html = browser.page_source
    soup = BeautifulSoup(html,'html.parser')
    table = soup.find("table", {"id":"ratings-table"})
    hca_table = tableDataText(table)

    hca_table = pd.DataFrame(hca_table)
    hca_table = hca_table[[0,2]]
    column_list = ['Team', 'hca']
    hca_table = pd.DataFrame(hca_table)
    hca_table.columns = column_list
    hca_table = hca_table[hca_table['Team'] != '']
    hca_table = hca_table[hca_table['Team'].notna()]
    browser.close()
    return hca_table

def get_players():
    browser = webdriver.Chrome()
    webpage = 'https://kenpom.com/playerstats.php?s=ORtg&y=2023'
    browser.get(webpage)
    time.sleep(2)
    username = browser.find_element("name", "email")
    password = browser.find_element("name", "password")

    username.send_keys("drew.c.meredith@gmail.com")
    password.send_keys("EdeysNuts")

    login = browser.find_element("name", "submit")
    login.click()

    elems = browser.find_elements("xpath", "//a[@href]")

    conferences = []
    for elem in elems:
        text = elem.get_attribute("href")
        if text.startswith('https://kenpom.com/playerstats.php?s=ORtg&y=2023&f='):
            conferences.append(text.split("f=")[1])
    column_list = ['Rk', 'Player', 'Team','ORtg', 'Ht', 'Wt', 'Yr']
    player_table = pd.DataFrame(columns=column_list)
    for conference in conferences:
        element = browser.find_element("link text", str(conference))
        element.click()
        time.sleep(1)
        html = browser.page_source
        player_table = get_player_table(player_table, html, column_list).reset_index(drop=True)

    player_table[['ORtg', 'Use']] = player_table['ORtg'].str.split('(', 1, expand=True)
    player_table[['Use','del']] = player_table['Use'].str.split(')', 1, expand=True)
    player_table = player_table[['Player','Team','ORtg','Use']]
    player_table['ORtg'] = pd.to_numeric(player_table['ORtg'])
    player_table['Use'] = pd.to_numeric(player_table['Use'])
    player_table['Value'] = player_table['ORtg'] * player_table['Use']/100
    player_table = player_table.sort_values(by='Value',ascending=False)
    return player_table

def get_injured_players(player_table):
    browser = webdriver.Chrome()
    webpage = 'https://www.rotowire.com/cbasketball/injury-report.php'
    browser.get(webpage)
    time.sleep(5)
    csv_click = browser.find_elements("class name", "export-button")[1]
    csv_click.click()
    time.sleep(5)
    injury_report = pd.read_csv("/Users/dmeredith/Downloads/college-basketball-injury-report.csv")

    os.remove("/Users/dmeredith/Downloads/college-basketball-injury-report.csv")

    def fuzzy_merge_inj(dframe1, dframe2, thresh):
        merged_df = dframe1.copy()

        mat1 = []
        mat2 = []

        threshold = 80
        list1 = merged_df['Player'].tolist()
        list2 = dframe2['Player'].tolist()

        for i in list1:
            match = process.extract(i, list2, limit=1)[0]
            if match[1] >= threshold:
                mat1.append(match[0])
            else:
                mat1.append(i)
        merged_df['ply_matches'] = mat1

        list1 = merged_df['Team'].tolist()
        list2 = dframe2['Team'].tolist()

        for i in list1:
            match = process.extract(i, list2, limit=1)[0]
            if match[1] >= threshold:
                mat2.append(match[0])
            else:
                mat2.append(i)
        merged_df['tm_matches'] = mat2

        merged_df = merged_df.merge(dframe2, how='outer', left_on=['ply_matches', 'tm_matches'],
                                right_on=['Player', 'Team'])
        return merged_df

    player_table_merged = fuzzy_merge_inj(player_table, injury_report, 80)
    player_table_merged['Injured'] = np.where(player_table_merged['Player_y'].isnull(), 0, 1)
    injured_players = player_table_merged[player_table_merged['Injured'] == 1][['Player_x','Team_x','ORtg','Use', 'Value','Injury','Status']].dropna().reset_index(drop=True)
    injured_players.columns = ['Player','Team','ORtg','Use','Value', 'Injury','Status']
    return injured_players

def get_injured_team_report(injured_players, teams):
    team_injury_report = pd.DataFrame(columns=['Team', 'Injuries','IV'])
    for i in range(len(teams)):
        team = teams.iloc[i]['Team']
        team_injuries = injured_players[injured_players['Team'] == team]
        injured_players_num = len(team_injuries)
        injured_players_value = np.sum(team_injuries['Value'])
        team_report = [[team, injured_players_num, injured_players_value]]
        team_report = pd.DataFrame(team_report, columns=['Team', 'Injuries','IV'])
        team_injury_report = pd.concat([team_injury_report, team_report])
    return(team_injury_report)

def get_games_list(year):
    browser = webdriver.Chrome()
    webpage = 'https://kenpom.com/'
    browser.get(webpage)
    time.sleep(2)
    username = browser.find_element("name", "email")
    password = browser.find_element("name", "password")

    username.send_keys("drew.c.meredith@gmail.com")
    password.send_keys("EdeysNuts")

    login = browser.find_element("name", "submit")
    login.click()
    if year != 2024:
        browser.get(f"https://kenpom.com/index.php?y={year}")

    column_list = ['Date', 'Del', 'OppRank', 'Opponent','Result', 'Rank', 'OT', 'Location', 'Record', 'Conf','del']
    team_elements = browser.find_elements("class name", "next_left")
    master_sched = pd.DataFrame(columns=['Date', 'Del', 'OppRank', 'Opponent','Result', 'Rank', 'Team', 'OT', 'Location', 'Record', 'Conf','del'])
    i = 0
    teams = []
    for team in team_elements:
        team_name = "".join(re.split("\s+\d+", team.text))
        if (team_name != "") & (team_name != "Team"):
            teams.append(team_name)

    for team in teams:
        try:
            element = browser.find_element("link text", team)
            element.click()
            html = browser.page_source
            master_sched = get_schedule_table(master_sched, html, column_list, team).reset_index(drop=True)
            browser.back()
        except:
            browser.get(f"https://kenpom.com/index.php?y={year}")

    master_sched[['Win Score', 'Loss Score']] = master_sched['Result'].str.split(', ', 1, expand=True)[1].str.split('-',1,expand=True)
    master_sched['Result'] = master_sched['Result'].str.split(', ', 1, expand=True)[0]

    scores = master_sched[['Date', 'Team', 'Opponent', 'Win Score', 'Loss Score', 'Result', 'OT', 'Location', 'Conf']]
    home_winners = scores[(scores['Result'] == 'W') & ((scores['Location'] == 'Home') | (scores['Location'] == 'Semi-Home'))][['Date', 'Team', 'Opponent', 'Win Score', 'Loss Score', 'OT', 'Conf']]
    home_winners.columns = ['Date', 'Home', 'Away', 'Home Score', 'Away Score', 'OT', 'Conf']
    home_winners['Result'] = [1] * len(home_winners)
    home_winners['Nuetral'] = [0] * len(home_winners)
    home_winners['Conf'] = np.array((home_winners['Conf'] != ''), dtype=bool).astype(int)

    home_losers = scores[(scores['Result'] == 'L') & ((scores['Location'] == 'Home') | (scores['Location'] == 'Semi-Home'))][['Date', 'Team', 'Opponent', 'Win Score', 'Loss Score', 'OT', 'Conf']]
    home_losers.columns = ['Date', 'Home', 'Away', 'Away Score', 'Home Score', 'OT', 'Conf']
    home_losers['Result'] = [0] * len(home_losers)
    home_losers['Nuetral'] = [0] * len(home_losers)
    home_losers['Conf'] = np.array((home_losers['Conf'] != ''), dtype=bool).astype(int)

    neutral_winners = scores[(scores['Result'] == 'W') & (scores['Location'] == 'Neutral')][['Date', 'Team', 'Opponent', 'Win Score', 'Loss Score', 'OT', 'Conf']]
    neutral_winners_first = neutral_winners.sample(frac=0.5)
    neutral_winners_first.columns = ['Date', 'Home', 'Away', 'Home Score', 'Away Score', 'OT', 'Conf']
    neutral_winners_first['Result'] = [1] * len(neutral_winners_first)
    neutral_winners_first['Nuetral'] = [1] * len(neutral_winners_first)
    neutral_winners_first['Conf'] = np.array((neutral_winners_first['Conf'] != ''), dtype=bool).astype(int)

    neutral_winners_second = neutral_winners.drop(neutral_winners_first.index)
    neutral_winners_second.columns = ['Date', 'Away', 'Home', 'Away Score', 'Home Score', 'OT', 'Conf']
    neutral_winners_second['Result'] = [0] * len(neutral_winners_second)
    neutral_winners_second['Nuetral'] = [1] * len(neutral_winners_second)
    neutral_winners_second['Conf'] = np.array((neutral_winners_second['Conf'] != ''), dtype=bool).astype(int)

    games_list = pd.concat([home_winners, home_losers, neutral_winners_first, neutral_winners_second])
    games_list[['Home Score', 'Away Score']] = games_list[['Home Score', 'Away Score']].apply(pd.to_numeric, errors='coerce')

    games_list['Date'] = pd.to_datetime((str(year) + ' ' + games_list['Date'].str[4:]), format='%Y %b %d')

    games_list['Date'].loc[games_list['Date'].dt.month > 10] = \
        games_list[games_list['Date'].dt.month > 10]['Date'].apply(lambda dt: dt.replace(year=year-1))
    games_list['Date'].loc[games_list['Date'].dt.month < 10] = \
        games_list[games_list['Date'].dt.month < 10]['Date'].apply(lambda dt: dt.replace(year=year))

    games_list = games_list.sort_values(by='Date').reset_index(drop=True)
    games_list['Date'] = games_list['Date'].dt.date

    if year != 2024:
        games_list = games_list[~games_list["OT"].str.contains("%")]

    return games_list

def get_features_past(games_list, ratings):
    kp_games = games_list.merge(ratings, left_on='Home', right_on='Team')
    kp_games = kp_games.merge(ratings, left_on='Away', right_on='Team')

    home_teams = kp_games['Home']
    home_score = kp_games[
        ['AdjEM_x', 'AdjO_x', 'AdjD_x', 'AdjT_x', 'AdjEM_y', 'AdjO_y', 'AdjD_y', 'AdjT_y', 'Conf_x',
         'Nuetral', 'Home Score']]
    home_score.columns = ['hAdjEM', 'hAdjO', 'hAdjD', 'hAdjT', 'aAdjEM', 'aAdjO', 'aAdjD', 'aAdjT',
                          'Conf', 'Nuetral', 'score']

    away_teams = kp_games['Away']
    away_score = kp_games[
        ['AdjEM_x', 'AdjO_x', 'AdjD_x', 'AdjT_x', 'AdjEM_y', 'AdjO_y', 'AdjD_y', 'AdjT_y', 'Conf_x',
         'Nuetral', 'Away Score']]
    away_score.columns = ['hAdjEM', 'hAdjO', 'hAdjD', 'hAdjT', 'aAdjEM', 'aAdjO', 'aAdjD', 'aAdjT',
                          'Conf', 'Nuetral', 'score']

    return home_score, away_score
def get_features_past_result(games_list, ratings):
    kp_games = games_list.merge(ratings, left_on='Home', right_on='Team')
    kp_games = kp_games.merge(ratings, left_on='Away', right_on='Team')

    home_teams = kp_games['Home']
    games = kp_games[
        ['AdjEM_x', 'AdjO_x', 'AdjD_x', 'AdjT_x', 'AdjEM_y', 'AdjO_y', 'AdjD_y', 'AdjT_y', 'Conf_x',
         'Nuetral', 'Result']]
    games.columns = ['hAdjEM', 'hAdjO', 'hAdjD', 'hAdjT', 'aAdjEM', 'aAdjO', 'aAdjD', 'aAdjT',
                          'Conf', 'Nuetral', 'result']

    return games

def get_features_future(games_list, ratings):
    kp_games = games_list.merge(ratings, left_on='Home', right_on='Team')
    kp_games = kp_games.merge(ratings, left_on='Away', right_on='Team')

    dates = kp_games['Date']
    loc = kp_games['Nuetral']
    home_teams = kp_games['Home']
    home_score = kp_games[
        ['AdjEM_x', 'AdjO_x', 'AdjD_x', 'AdjT_x', 'AdjEM_y', 'AdjO_y', 'AdjD_y', 'AdjT_y', 'Conf_x',
         'Nuetral', 'Home Score']]
    home_score.columns = ['hAdjEM', 'hAdjO', 'hAdjD', 'hAdjT', 'aAdjEM', 'aAdjO', 'aAdjD', 'aAdjT',
                          'Conf', 'Nuetral', 'score']

    away_teams = kp_games['Away']
    away_score = kp_games[
        ['AdjEM_x', 'AdjO_x', 'AdjD_x', 'AdjT_x', 'AdjEM_y', 'AdjO_y', 'AdjD_y', 'AdjT_y', 'Conf_x',
         'Nuetral', 'Away Score']]
    away_score.columns = ['hAdjEM', 'hAdjO', 'hAdjD', 'hAdjT', 'aAdjEM', 'aAdjO', 'aAdjD', 'aAdjT',
                          'Conf', 'Nuetral', 'score']

    return home_score, away_score, home_teams, away_teams, dates, loc
def get_features_future_result(games_list, ratings):
    kp_games = games_list.merge(ratings, left_on='Home', right_on='Team')
    kp_games = kp_games.merge(ratings, left_on='Away', right_on='Team')

    dates = kp_games['Date']
    loc = kp_games['Nuetral']
    home_teams = kp_games['Home']
    away_teams = kp_games['Away']
    games = kp_games[
        ['AdjEM_x', 'AdjO_x', 'AdjD_x', 'AdjT_x', 'AdjEM_y', 'AdjO_y', 'AdjD_y', 'AdjT_y', 'Conf_x',
         'Nuetral', 'Result']]
    games.columns = ['hAdjEM', 'hAdjO', 'hAdjD', 'hAdjT', 'aAdjEM', 'aAdjO', 'aAdjD', 'aAdjT',
                          'Conf', 'Nuetral', 'Result']



    return games, home_teams, away_teams, dates, loc

def fuzzy_merge(dframe1, dframe2, thresh):
    team_dict = {"IPFW" : 'Purdue Fort Wayne', "VA Commonwealth" : 'VCU', "Florida Intl.": 'FIU',
                 'Queens Charlotte': 'Queens', 'Texas A and M Corpus': 'Texas A&M Corpus Chris', 'Central Florida': 'UCF'
                 ,'NC St.': 'N.C. State', 'SE Missouri St.': 'Southeast Missouri St.', 'So Illinois': 'Southern Illinois'
                 ,'Ole Miss': 'Mississippi', 'California San Diego': 'UC San Diego', 'FGCU': 'Florida Gulf Coast',
                 'FAMU Rattlers': 'Florida A&M','UCSB': 'UC Santa Barbara', 'St. Joseph\'s': 'Saint Joseph\'s',
                 'South Carolina Upstate':'USC Upstate','N. Carolina A and T':'North Carolina A&T','UIC':'Illinois Chicago',
                 'Texas San Antonio': 'UTSA','SE Louisiana':'Southeastern Louisiana', 'California Baptist': 'Cal Baptist',
                 'Cal Irvine': 'UC Irvine','Miss Valley St.': 'Mississippi Valley St.','Long Island':'LIU',
                 'Middle Tenn St.': 'Middle Tennessee'}
    merged_df = dframe1.copy()
    merged_df.replace({"home_team": team_dict}, inplace=True)
    merged_df.replace({"away_team": team_dict}, inplace=True)
    cols = len(merged_df.columns)
    row_list = []
    for i in range(0, cols+2):
        if i < cols:
            row_list.append(i)
        if i >= cols:
            row_list.append(i+4)

    mat1 = []
    mat2 = []

    threshold = thresh
    list1 = merged_df['home_team'].tolist()

    list2 = dframe2['Team'].tolist()

    for i in list1:
        if process.extract(i, list2, limit=1)[0][1] >= threshold:
            mat1.append(process.extract(i, list2, limit=1)[0][0])
        else:
            mat1.append(i)
    merged_df['ht_matches'] = mat1

    list1 = merged_df['away_team'].tolist()
    list2 = dframe2['Opponent'].tolist()

    for i in list1:
        if process.extract(i, list2, limit=1)[0][1] >= threshold:
            mat2.append(process.extract(i, list2, limit=1)[0][0])
        else:
            mat2.append(i)
    merged_df['at_matches'] = mat2
    teams = pd.concat([merged_df['home_team'],merged_df['away_team']])
    merged_df_2 = merged_df.copy()
    merged_df_3 = merged_df.copy()
    merged_df_4 =merged_df.copy()
    merged_df = merged_df.merge(dframe2, how='outer', left_on=['ht_matches', 'at_matches'],
                            right_on=['Team', 'Opponent'])
    merged_df_2 = merged_df_2.merge(dframe2, how='outer', left_on=['home_team', 'away_team'],
                            right_on=['Team', 'Opponent'])
    merged_df_3 = merged_df_3.merge(dframe2, how='outer', left_on=['at_matches', 'ht_matches'],
                                    right_on=['Team', 'Opponent'])
    merged_df_3['Spread'] = merged_df['Spread'] * -1
    merged_df_4 = merged_df_4.merge(dframe2, how='outer', left_on=['away_team', 'home_team'],
                                    right_on=['Team', 'Opponent'])
    merged_df_4['Spread']= merged_df_4['Spread'] * -1

    merged_df = pd.concat([merged_df, merged_df_2, merged_df_3, merged_df_4])
    merged_df = merged_df.dropna()
    merged_df = merged_df.drop_duplicates()
    final_teams = pd.concat([merged_df['home_team'], merged_df['away_team']])
    print('Missing Teams:')
    for team in teams:
        if sum(final_teams.str.contains(team)) == 0:
            print(team)
    # merged_df = merged_df.merge(dframe2, how='outer', left_on=['at_matches', 'ht_matches'],
    #                             right_on=['Team', 'Opponent'])
    merged_df = merged_df[['time', 'Team', 'Score', 'Opponent', 'Opponent Score', 'Spread', 'OU', 'spread', 'ou']]
    return merged_df

def get_pred(home_score, away_score, future, future_home, future_away, future_dates, future_loc):
    train_dataset = home_score.sample(frac=0.8, random_state=0)
    test_dataset = home_score.drop(train_dataset.index)

    train_datasetOpp = away_score.sample(frac=0.8, random_state=0)
    test_datasetOpp = away_score.drop(train_dataset.index)

    train_features = train_dataset.copy()
    test_features = test_dataset.copy()

    train_labels = train_features.pop('score')
    test_labels = test_features.pop('score')

    train_featuresOpp = train_datasetOpp.copy()
    test_featuresOpp = test_datasetOpp.copy()

    train_labelsOpp = train_featuresOpp.pop('score')
    test_labelsOpp = test_featuresOpp.pop('score')

    normalizer = tf.keras.layers.Normalization(axis=-1)
    normalizer.adapt(np.array(train_features).astype(np.float32))

    normalizerOpp = tf.keras.layers.Normalization(axis=-1)
    normalizerOpp.adapt(np.array(train_featuresOpp).astype(np.float32))

    def build_and_compile_model(norm):
      model = keras.Sequential([
          norm,
          layers.Dense(128, activation='relu'),
          layers.Dense(128, activation='relu'),
          layers.Dense(128, activation='relu'),
          layers.Dense(128, activation='relu'),
          layers.Dense(1)
      ])

      model.compile(loss='mean_absolute_error',
                    optimizer=tf.keras.optimizers.Adam(0.001))
      return model

    team_model = build_and_compile_model(normalizer)
    team_model2 = build_and_compile_model(normalizer)
    team_model3 = build_and_compile_model(normalizer)
    opp_model = build_and_compile_model(normalizerOpp)
    opp_model2 = build_and_compile_model(normalizerOpp)
    opp_model3 = build_and_compile_model(normalizerOpp)

    test_results = {}

    history = team_model.fit(
        train_features,
        train_labels,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['team_model'] = team_model.evaluate(test_features, test_labels, verbose=0)

    history = team_model2.fit(
        train_features,
        train_labels,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['team_model2'] = team_model2.evaluate(test_features, test_labels, verbose=0)

    history = team_model3.fit(
        train_features,
        train_labels,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['team_model3'] = team_model3.evaluate(test_features, test_labels, verbose=0)

    history = opp_model.fit(
        train_featuresOpp,
        train_labelsOpp,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['opp_model'] = opp_model.evaluate(test_features, test_labels, verbose=0)

    history = opp_model2.fit(
        train_featuresOpp,
        train_labelsOpp,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['opp_model2'] = opp_model2.evaluate(test_features, test_labels, verbose=0)

    history = opp_model3.fit(
        train_featuresOpp,
        train_labelsOpp,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['opp_model3'] = opp_model3.evaluate(test_features, test_labels, verbose=0)
    print(test_results)

    import statistics
    teamPredictions = team_model.predict(future).flatten()
    teamPredictions2 = team_model2.predict(future).flatten()
    teamPredictions3 = team_model3.predict(future).flatten()
    oppPredictions = opp_model.predict(future).flatten()
    oppPredictions2 = opp_model2.predict(future).flatten()
    oppPredictions3 = opp_model3.predict(future).flatten()

    d = {'Date': future_dates, 'Team': future_home, 'Score': (teamPredictions+teamPredictions2+teamPredictions3)/3, 'Opponent': future_away, 'Opponent Score': (oppPredictions+oppPredictions2+oppPredictions3)/3, 'Location': future_loc}
    preds = pd.DataFrame(d)
    preds['Spread'] = preds['Score'] - preds["Opponent Score"]
    preds['OU'] = preds['Score'] + preds["Opponent Score"]
    preds = preds.sort_values(by="Date")
    pd.set_option('display.max_columns', 10)
    return preds

def get_predrf(home_score, away_score, future, future_home, future_away, future_dates, future_loc):
    train_dataset = home_score.sample(frac=0.8, random_state=0)
    test_dataset = home_score.drop(train_dataset.index)

    train_datasetOpp = away_score.sample(frac=0.8, random_state=0)
    test_datasetOpp = away_score.drop(train_dataset.index)

    train_features = train_dataset.copy()
    test_features = test_dataset.copy()

    train_labels = train_features.pop('score')
    test_labels = test_features.pop('score')

    train_featuresOpp = train_datasetOpp.copy()
    test_featuresOpp = test_datasetOpp.copy()

    train_labelsOpp = train_featuresOpp.pop('score')
    test_labelsOpp = test_featuresOpp.pop('score')

    # Initialize and train the Random Forest model for the home team
    home_rf_model = RandomForestRegressor(n_estimators=100, random_state=0)
    home_rf_model.fit(train_features, train_labels)

    # Initialize and train the Random Forest model for the away team
    away_rf_model = RandomForestRegressor(n_estimators=100, random_state=0)
    away_rf_model.fit(train_featuresOpp, train_labelsOpp)

    # Make predictions for future matches
    future_predictions_home = home_rf_model.predict(future_home)
    future_predictions_away = away_rf_model.predict(future_away)

    teamPredictions = team_model.predict(future).flatten()
    oppPredictions = opp_model.predict(future).flatten()

    d = {'Date': future_dates, 'Team': future_home, 'Score': (teamPredictions+teamPredictions2+teamPredictions3)/3, 'Opponent': future_away, 'Opponent Score': (oppPredictions+oppPredictions2+oppPredictions3)/3, 'Location': future_loc}
    preds = pd.DataFrame(d)
    preds['Spread'] = preds['Score'] - preds["Opponent Score"]
    preds['OU'] = preds['Score'] + preds["Opponent Score"]
    preds = preds.sort_values(by="Date")
    pd.set_option('display.max_columns', 10)
    return preds


def get_records(predictions):
    teams = get_ratings(2024)
    predictions = predictions.merge(teams, on='Team')
    predictions = predictions.merge(teams, left_on='Opponent', right_on='Team')
    records = pd.DataFrame(columns=['Team','Conf','Wins','Losses','Conf Wins','Conf Losses'])
    for index, row in teams.iterrows():
        ws = 0
        ls = 0
        cws = 0
        cls = 0
        team_name = row[0]
        team_conf = row[1]
        team_sched = predictions[(predictions['Team_x'] == team_name) | (predictions['Team_y'] == team_name)]
        for index1, row1 in team_sched.iterrows():
            if ((row1['Team_x'] == team_name) & (row1['Spread'] >= 0)) | (
                    (row1['Team_y'] == team_name) & (row1['Spread'] < 0)):
                ws += 1
                if (row1['Conf_x'] == team_conf) & (row1['Conf_y'] == team_conf):
                    cws += 1
            else:
                ls += 1
                if (row1['Conf_x'] == team_conf) & (row1['Conf_y'] == team_conf):
                    cls += 1
        d = [[team_name, team_conf, ws, ls, cws, cls]]
        team_record = pd.DataFrame(d, columns=['Team','Conf','Wins','Losses','Conf Wins','Conf Losses'])
        records = pd.concat([records,team_record])
        return records

def get_pred_results(games, future, future_home, future_away, future_dates, future_loc):
    train_dataset = games.sample(frac=0.8, random_state=0)
    test_dataset = games.drop(train_dataset.index)

    train_features = train_dataset.copy()
    test_features = test_dataset.copy()

    train_labels = train_features.pop('result')
    test_labels = test_features.pop('result')

    scalar = MinMaxScaler()
    scalar.fit(train_features)
    train_features = scalar.transform(train_features)

    def build_and_compile_model(norm):
        model = Sequential()
        model.add(Dense(64, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(1, activation='sigmoid'))
        model.compile(loss='mean_squared_error', optimizer='adam')
        return model

    team_model = build_and_compile_model(normalizer)
    team_model2 = build_and_compile_model(normalizer)
    team_model3 = build_and_compile_model(normalizer)

    test_results = {}

    history = team_model.fit(
        train_features,
        train_labels,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['team_model'] = team_model.evaluate(test_features, test_labels, verbose=0)

    history = team_model2.fit(
        train_features,
        train_labels,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['team_model2'] = team_model2.evaluate(test_features, test_labels, verbose=0)

    history = team_model3.fit(
        train_features,
        train_labels,
        validation_split=0.2,
        verbose=0, epochs=100)
    #plot_loss(history)
    test_results['team_model3'] = team_model3.evaluate(test_features, test_labels, verbose=0)

    teamPredictions = team_model.predict(scalar.transform(future)).flatten()
    teamPredictions2 = team_model2.predict(scalar.transform(future)).flatten()
    teamPredictions3 = team_model3.predict(scalar.transform(future)).flatten()

    d = {'Date': future_dates, 'Team': future_home, 'Opponent': future_away, 'Odds':
        (teamPredictions+teamPredictions2+teamPredictions3)/3, 'Location': future_loc}
    preds = pd.DataFrame(d)
    preds = preds.sort_values(by="Date")
    return preds

def get_records_results(predictions, teams):
    predictions = predictions.merge(teams, on='Team')
    predictions = predictions.merge(teams, left_on='Opponent', right_on='Team')
    records = pd.DataFrame(columns=['Team','Conf','Wins','Losses','Conf Wins','Conf Losses'])
    for index, row in teams.iterrows():
        print(row[0])
        ws = 0
        ls = 0
        cws = 0
        cls = 0
        team_name = row[0]
        team_conf = row[1]
        team_sched = predictions[(predictions['Team_x'] == team_name) | (predictions['Team_y'] == team_name)]
        for index1, row1 in team_sched.iterrows():
            if (row1['Team_x'] == team_name):
                ws += row1['Odds']
                ls += 1 - row1['Odds']
                if (row1['Conf_x'] == team_conf) & (row1['Conf_y'] == team_conf):
                    cws += row1['Odds']
                    cls += 1 - row1['Odds']
            else:
                ws += 1 - row1['Odds']
                ls += row1['Odds']
                if (row1['Conf_x'] == team_conf) & (row1['Conf_y'] == team_conf):
                    cws += 1- row1['Odds']
                    cls += row1['Odds']
        d = [[team_name, team_conf, ws, ls, cws, cls]]
        team_record = pd.DataFrame(d, columns=['Team','Conf','Wins','Losses','Conf Wins','Conf Losses'])
        records = pd.concat([records,team_record])
        return records

def get_best_bets(d1, d2, predictions):
    probs_table = pd.DataFrame(columns=['Team', 'Conf', 'Prob'])
    week_predictions = predictions[(d1 <= predictions['Date']) & (predictions['Date'] <= d2)]
    for i in range(len(teams)):
        probs = []
        team = teams.iloc[i]['Team']
        conf = teams.iloc[i]['Conf']
        team_sched = week_predictions[(week_predictions['Team'] == team) | (week_predictions['Opponent'] == team)]
        for i in range(len(team_sched)):
            if team_sched.iloc[i]['Team'] == team:
                probs.append(team_sched.iloc[i]['Odds'])
            else:
                probs.append(1 - team_sched.iloc[i]['Odds'])
        d = [[team, conf, np.prod(probs)]]
        team_prob = pd.DataFrame(d, columns=['Team','Conf','Prob'])
        probs_table = pd.concat([probs_table, team_prob])
    return probs_table
