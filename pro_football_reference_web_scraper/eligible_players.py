from bs4 import BeautifulSoup
import requests
import pandas as pd

VALID_STATS = ['passing', 'scrimmage', 'kicking']
VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K']

'''
A function that takes statistic type and year as arguments and returns a pandas dataframe of player fantasy stats

    GOAL: get all eligible QBs, FLEXs (RB/WR/TE), and Ks for a given year. After finding these, we will be able to
    use these names to find game-by-game statistics using the game log

    Args:
        stat_type (str): passing, rushing, receiving, kicking
        year (int): year in which the statistics were accumulated

    Returns:
        pandas.Dataframe with the following attributes:
        playerID (str), name (str), position (str), age (int)

'''
def get_eligible_players(stat_type: str, season: int) -> pd.DataFrame:
    # statistic type must be formatted properly
    if stat_type not in VALID_STATS:
        raise Exception('Invalid statistic type: "stat_type" arg must be passing, scrimmage, or kicking')

    # find appropriate url for request
    request_url = 'https://www.pro-football-reference.com/years/%s/%s.%s' % (str(season), stat_type, 'htm')
    
    # store response from request
    response = requests.get(request_url)
    
    # get beautiful soup text object and find the table element
    soup = BeautifulSoup(response.text, 'html.parser')
    table_rows = soup.find('tbody').find_all('tr')

    # get the list of elements in the table to ignore
    ignore_list = get_ignore_list(stat_type, table_rows)

    # set the structure for the return data frame
    data = {
        'playerID': [],
        'name': [],
        'position': [],
        'age': [],
        'season': []
    }

    # add data to the data dictionary
    for i in range(len(table_rows)):
        if i not in ignore_list:
            # calculate unique player ID (FirstLastPositionYear)
            # Includes caveat for Baker Mayfield 2022 as well as string cleansing for player name
            name = (table_rows[i].find('td', {'data-stat': 'player'}).text).replace('*', '')
            name = name.replace('+', '')
            position = table_rows[i].find('td', {'data-stat': 'pos'}).text
            if len(position) == 0:
                position = 'QB'
            playerID = get_player_id(name, position, season)

            #assign values to data dict
            data['playerID'].append(playerID)
            data['name'].append(name)
            data['position'].append(position)
            data['age'].append(int(table_rows[i].find('td', {'data-stat': 'age'}).text))
            data['season'].append(season)
    
    '''
    # adding data to data dictionary
    for i in range(len(table_rows)):
        if i not in to_ignore:
            data['date'].append(table_rows[i].find('td', {'data-stat': 'game_date'}).text)
            data['week'].append(int(table_rows[i].find('td', {'data-stat': 'week_num'}).text))
            data['team'].append(table_rows[i].find('td', {'data-stat': 'team'}).text)
            data['game_location'].append(table_rows[i].find('td', {'data-stat': 'game_location'}).text)
            data['opp'].append(table_rows[i].find('td', {'data-stat': 'opp'}).text)
            data['result'].append(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[0])
            data['team_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[0])
            )
            data['opp_pts'].append(
                int(table_rows[i].find('td', {'data-stat': 'game_result'}).text.split(' ')[1].split('-')[1])
            )
            data['cmp'].append(int(table_rows[i].find('td', {'data-stat': 'pass_cmp'}).text)) if table_rows[i].find(
                'td', {'data-stat': 'pass_cmp'}
            ).text != '' else data['cmp'].append(0)
            data['att'].append(int(table_rows[i].find('td', {'data-stat': 'pass_att'}).text)) if table_rows[i].find(
                'td', {'data-stat': 'pass_att'}
            ).text != '' else data['att'].append(0)
            data['pass_yds'].append(int(table_rows[i].find('td', {'data-stat': 'pass_yds'}).text)) if table_rows[
                i
            ].find('td', {'data-stat': 'pass_yds'}).text != '' else data['pass_yds'].append(0)
            data['pass_td'].append(int(table_rows[i].find('td', {'data-stat': 'pass_td'}).text)) if table_rows[i].find(
                'td', {'data-stat': 'pass_td'}
            ).text != '' else data['pass_td'].append(0)
            data['int'].append(int(table_rows[i].find('td', {'data-stat': 'pass_int'}).text)) if table_rows[i].find(
                'td', {'data-stat': 'pass_int'}
            ).text != '' else data['int'].append(0)
            data['rating'].append(float(table_rows[i].find('td', {'data-stat': 'pass_rating'}).text)) if table_rows[
                i
            ].find('td', {'data-stat': 'pass_rating'}).text != '' else data['rating'].append(0)
            data['sacked'].append(int(table_rows[i].find('td', {'data-stat': 'pass_sacked'}).text)) if table_rows[
                i
            ].find('td', {'data-stat': 'pass_sacked'}).text != '' else data['sacked'].append(0)
            data['rush_att'].append(int(table_rows[i].find('td', {'data-stat': 'rush_att'}).text)) if table_rows[
                i
            ].find('td', {'data-stat': 'rush_att'}).text != '' else data['rush_att'].append(0)
            data['rush_yds'].append(int(table_rows[i].find('td', {'data-stat': 'rush_yds'}).text)) if table_rows[
                i
            ].find('td', {'data-stat': 'rush_yds'}).text != '' else data['rush_yds'].append(0)
            data['rush_td'].append(int(table_rows[i].find('td', {'data-stat': 'rush_td'}).text)) if table_rows[i].find(
                'td', {'data-stat': 'rush_td'}
            ).text != '' else data['rush_td'].append(0)
    '''

    return pd.DataFrame(data=data)


'''
A helper function that removes non-target positions from consideration

    i.e. for throwing stats, only consider QBs, for scrimmage yards, only consider RB, WR, TE

    Args:
        stat_type (str): type of statistic (passing, scrimmage, kicking)
        table_rows (str): a "stringified" version of the table that appears on the web page (from bs4)

    Returns:
        ignore_list (list): list of 'rows' from table_rows that we can ignore in our final parse

    Note: we are omitting positions from their secondary stat tpes because the point of this meethod is NOT 
    to accumulate stats, but to find players that we will search game logs for
'''
def get_ignore_list(stat_type: str, table_rows: str) -> list:
    # store list of indices to ignore here
    ignore_list = []

    # limit list of passers to QBs ONLY
    if stat_type == 'passing':

        # loop through each row in the table
        for i in range(len(table_rows)):

            # store position from the row attribute for position
            position_object = table_rows[i].find('td', {'data-stat': "pos"})
            
            # if position object is None, add to the ignore list and restart loop
            if position_object is None:
                ignore_list.append(i)
                continue
            
            # else grab text from position object
            else:
                position = position_object.text

            # outlier, but if position is empty then convert to QB (observed with 2022 Baker Mayfield)
            if len(position) == 0:
                position = 'QB'

            # if the player is not a QB, add the row to the ignore list
            if position != 'QB':
                ignore_list.append(i)
    
    # limit list of scrimmage stat accumulators to RBs, WRs, and TEs only
    # @TODO
    elif stat_type == 'scrimmage':
        pass
    
    # limit list of kickers to Ks only
    # @TODO
    elif stat_type == 'kicking':
        pass

    # return the list of indices to ignore
    return ignore_list


'''
Function to create a player's unique id for a given season. Will allow us to store multiple seasons from the
same player

    Args:
        name: player's first and last name
        position: player's position
        season: season of the player's stats
    
    Returns:
        playerid (str): player-season unique identifier
'''
def get_player_id(name: str, position: str, season: int):
    # @TODO come back and make a better ID
    return (name + position + str(season)).replace(' ', '')

      
def main():
    print(get_eligible_players('passing', 2022))



if __name__ == '__main__':
    main()