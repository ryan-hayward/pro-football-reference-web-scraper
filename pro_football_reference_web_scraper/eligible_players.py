from bs4 import BeautifulSoup
import requests
import pandas as pd
import time

VALID_STATS = ['passing', 'scrimmage', 'kicking'] # valid statistics to request for
VALID_POSITIONS = ['QB', 'RB', 'FB' 'WR', 'TE', 'K'] # valid positions in databasee
REQUEST_COUNTER = 0 # count requests

'''
A function that takes statistic type and year as arguments and returns a pandas dataframe of player fantasy stats

    GOAL: get all eligible QBs, FLEXs (RB/WR/TE), and Ks for a given year. After finding these, we will be able to
    use these names to find game-by-game statistics using the game log

    Args:
        stat_type (str): passing, rushing, receiving, kicking
        year (int): year in which the statistics were accumulated

    Returns:
        pandas.Dataframe with the following attributes: playerID (str), name (str), position (str), 
        age (int), season (int)
        counter (int): number of times that PFR has been scraped within the minute. Will reset and pause
        for the next 60 seconds after 20 requests have been made

'''
def get_eligible_players(stat_type: str, season: int) -> pd.DataFrame:
    # statistic type must be formatted properly
    if stat_type not in VALID_STATS:
        raise Exception('Invalid statistic type: "stat_type" arg must be passing, scrimmage, or kicking')

    # find appropriate url for request
    request_url = 'https://www.pro-football-reference.com/years/%s/%s.%s' % (str(season), stat_type, 'htm')
    
    # get BS object from the target URL
    soup = get_soup(request_url)
    # find the desired HTML component
    table_rows = soup.find('tbody').find_all('tr')

    # set the base structure for the return data frame
    data = {
        'playerID': [],
        'name': [],
        'position': [],
        'age': [],
        'season': []
    }

    # determine the eligible positions given the stat type
    eligible_positions = get_eligible_positions(stat_type)

    # loop through each row in the table
    for i in range(len(table_rows)):
        # store position object from the row attribute for position
        position_object = table_rows[i].find('td', {'data-stat': "pos"})

        # skip over table breaks that have no position attribute at all
        # store position's content as text
        if position_object is None:
            continue
        else:
            position = position_object.text

        # if position value is blank, call helper method to populate
        if len(position) == 0:
            href = table_rows[i].find('a').get('href')
            position = get_player_position(href)

        # if the player is not in an eligible position, ignore. Else, add line to the dataframe
        if position not in eligible_positions:
            continue
        else:
            # get player name and strip irrelevant characters
            name = (table_rows[i].find('td', {'data-stat': 'player'}).text).replace('*', '').replace('+', '')
            # use player name, position, and season to get player id
            playerID = get_player_id(name, position, season)
            #assign values to data dict
            data['playerID'].append(playerID)
            data['name'].append(name)
            data['position'].append(position)
            data['age'].append(int(table_rows[i].find('td', {'data-stat': 'age'}).text))
            data['season'].append(season)
    # return data frame
    return [pd.DataFrame(data=data), REQUEST_COUNTER]



'''
A helper method to make requests to a webpage for HTML and convert the HTML to a Beautiful Soup object.
A counter has been included to track the # of requests made in a given run

    Args:
        request_url (str): address of page we would like to scrape
    
    Returns:
        BeautifulSoup object representing parsed html
    
    @NOTE I have added sleep() in order to prevent session locking from PFR. These limitations are put in
    to maintain site performance.
'''
def get_soup(request_url: str) -> BeautifulSoup:
    global REQUEST_COUNTER
    # if request counter is already at 20, sleep program for sixty seconds
    if REQUEST_COUNTER >= 20:
        time.sleep(60)
        REQUEST_COUNTER = 0
    # store response from request
    response = requests.get(request_url)
    # update the request counter
    REQUEST_COUNTER += 1
    # return soup
    return BeautifulSoup(response.text, 'html.parser')



'''
Function to create a player's unique id for a given season. Will allow us to store multiple seasons from the
same player

    Args:
        name: player's first and last name
        position: player's position
        season: season of the player's stats
    
    Returns:
        playerid (str): player-season unique identifier

    @TODO come back and create a better unique ID
'''
def get_player_id(name: str, position: str, season: int):
    return (name + position + str(season)).replace(' ', '')

      

'''
For cases in which player position is not listed in the table, we must inspect the player's page to find
their position

    Args:
        href: the player's page url. Can be found in the table itself

    Returns:
        position: two character player position
'''
def get_player_position(href: str) -> str:
    #get the PFR root url to attach to player name
    root_url = 'https://www.pro-football-reference.com/'
    # get BS object from the target URL
    soup = get_soup(root_url + href)
    # get player metadata
    meta = soup.find('div', {'id': 'meta'})
    # find player position
    position_strong = meta.find(string="Position")
    # find parent element of player position and extract text
    parent = position_strong.find_parent('p').text
    # split string on "position: " and return the next two characters and strip whitespace (for kickers)
    return parent.split("Position: ", 1)[1][:2].strip()



'''
A helper function to get the eligible positions for a given stat type. Since this script is about determining
all the players in a given year that accumulated fantasy stats WITHOUT repeating players, we want to restrict
QBs to passing stats, RBs/WRs/TEs to scrimmage stats, and Ks to kicking stats. We can then use these lists of
player names alongside player_game_log.py to find all player game logs for a given season and position

    Args:
        stat_type (str): type of statistic (passing, scrimmage, kicking)
    
    Returns:
        positions (list): list of eligible positions
'''
def get_eligible_positions(stat_type: str) -> list:
    # declare array to store positions
    positions = []
    # assign valid positions based on stat type
    if stat_type == "passing":
        positions.append('QB')
    elif stat_type == "scrimmage":
        positions.extend(('RB', 'FB', 'WR', 'TE', 'FB'))
    elif stat_type == "kicking":
        positions.append('K')
    # return eligible positions
    return positions



def main():
    print(get_eligible_players('scrimmage', 2014)[0].to_string())



if __name__ == '__main__':
    main()