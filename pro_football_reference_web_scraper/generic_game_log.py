import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
import requests
import time

VALID_POSITIONS = ['QB', 'RB', 'FB', 'WR', 'TE', 'K']
REQUEST_COUNTER = 0
ELEMENT_TABLE = pd.read_csv('./data/field_player_mapping.csv')

'''
@NOTE: ENHANCEMENT of player_game_log.py, written by Michael Kim

A function to return a player's game log regardless of position. This is to account for players accumulating
stats that are atypical for their listed position (i.e. Ladainian Tomlinson throwing touchdown passes). Position
will still be passed as an argument, but since this method will only be called by eligible_players, there is no
need to check twice for valid positions. We will route QBs, RBs, WRs, and TEs to field player, and Ks to kicker.

    Args:
        player (str): Player's full Name (firstname lastname)
        position (str): Player's position (will be associated 1:1 with player name from eligible players)
        season (int): Desired season to obtain game logs for
    Returns:
        pd.DataFrame of a NFL player's game log in a given season. These dataframes will come in three types:
        Quarterback (QB), FLEX (RB, FB, WR, TE), and Kicker (K)
'''
def get_player_game_log(player: str, position: str, season: int) -> pd.DataFrame:

    # position arg must be formatted properly
    if position not in VALID_POSITIONS:
        raise Exception('Invalid position: "position" must be "QB", "RB", "FB", "WR", "TE", or "K"')

    # find appropriate URL for request
    player_list_url = get_player_list_url(player)
    # make HTTP request to URL for BS4 player list object
    player_list = get_soup(player_list_url)

    # find href of player
    href = get_href(player, position, season, player_list)

    # using href and season, find the appropriate url for the player's game log
    game_log_url = get_player_url(href, season)
    # make HTTP request to URL for BS4 player game log object
    game_log = get_soup(game_log_url)

    # generating the appropriate game log format according to position
    if position == 'QB' or 'RB' or 'FB' or 'WR' or 'TE':
        return field_player_game_log(game_log)
    else:
        return kicker_game_log(game_log)



# helper function that gets the player's href
def get_href(player: str, position: str, season: int, player_list: BeautifulSoup) -> str:
    players = player_list.find('div', id='div_players').find_all('p')
    for p in players:
        seasons = p.text.split(' ')
        seasons = seasons[len(seasons) - 1].split('-')
        if season >= int(seasons[0]) and season <= int(seasons[1]) and player in p.text and position in p.text:
            return p.find('a').get('href').replace('.htm', '')
    raise Exception('Cannot find a ' + position + ' named ' + player + ' from ' + str(season))


# helper function that makes a HTTP request over a list of players with a given last initial
def get_player_list_url(player: str):
    name_split = player.split(' ')
    last_initial = name_split[1][0]
    url = 'https://www.pro-football-reference.com/players/%s/' % (last_initial)
    return url


# helper function that makes a HTTP request for a given player's game log
def get_player_url(href: str, season: int):
    url = 'https://www.pro-football-reference.com%s/gamelog/%s/' % (href, season)
    return url



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
Gets the complete season game log for a field player 
'''
def field_player_game_log(soup: BeautifulSoup) -> pd.DataFrame:

    data = {
        # General Game Log Information
        'date': [],
        'game': [],
        'week': [],
        'team': [],
        'game_location': [],
        'opp': [],
        'result': [],
        'team_pts': [],
        'opp_pts': [],
        'start': [], 
        # Passing Information
        'cmp': [],
        'att': [],
        'pass_yds': [],
        'pass_td': [],
        'int': [],
        'qbr': [],
        'sacked_qty': [],
        'sacked_yds': [], 
        # Rushing Information
        'rush_att': [],
        'rush_yds': [],
        'rush_td': [],
        # Receiving Information 
        'targets': [], 
        'receptions': [], 
        'rec_yds': [], 
        'rec_td': [], 
        # Kicking Stats
        'xp_made': [], 
        'xp_att': [], 
        'fg_made': [], 
        'fg_att': [], 
        # General Scrimmage Stats
        'fumbles': [], 
        'fumbles_lost': [], 
        'snap_count': [], 
        'snap_pct': [], 
        'total_td': [], 
        'two_pcs': []
    }  # type: dict

    # find the table within the BS object
    table_rows = soup.find('tbody').find_all('tr')

    # ignore inactive or DNP games
    to_ignore = []
    for i in range(len(table_rows)):
        elements = table_rows[i].find_all('td')
        x = elements[len(elements) - 1].text
        if x == 'Inactive' or x == 'Did Not Play' or x == 'Injured Reserve':
            to_ignore.append(i)

    # first, iterate over the rows in the data table
    for i in range(len(table_rows)):

        # if the row is not empty, add its data
        if i not in to_ignore:

            # iterate over the columns in each row 
            for j in range(len(ELEMENT_TABLE.index)):          

                # get data from specific col & row
                cell_data = table_rows[i].find('td', {'data-stat': ELEMENT_TABLE['pfr'][j]})

                # if data is non-existant, overwrite with zero and continue to the next element
                if cell_data is None:
                    data[ELEMENT_TABLE['app'][j]].append(0)
                
                # else, convert cell data to text and continue
                else:
                    cell_data_text = cell_data.text

                    # if cell data text is blank, append zero and continue. Else, typecast appropriately and enter
                    if len(cell_data_text) == 0:
                        data[ELEMENT_TABLE['app'][j]].append(0)
                                             
                    else:
                            # special cleansing for team pts, opp pts, snap %, and starts
                        if ELEMENT_TABLE['app'][j] == 'team_pts':
                            data['team_pts'].append(cell_data_text.split(' ')[1].split('-')[0])

                        elif ELEMENT_TABLE['app'][j] == 'opp_pts':
                            data['opp_pts'].append(cell_data_text.split(' ')[1].split('-')[1])

                        elif ELEMENT_TABLE['app'][j] == 'snap_pct':
                            data['snap_pct'].append(float(cell_data_text.replace('%', '')) / 100)

                        elif ELEMENT_TABLE['app'][j] == 'start':
                            data['start'].append(1)

                        # for integers
                        elif ELEMENT_TABLE['data_type'][j] == 'int':
                            data[ELEMENT_TABLE['app'][j]].append(int(cell_data_text))

                        # for floats
                        elif ELEMENT_TABLE['data_type'][j] == 'float':
                            data[ELEMENT_TABLE['app'][j]].append(float(cell_data_text))

                        # for everything else
                        else:
                            data[ELEMENT_TABLE['app'][j]].append(cell_data_text)

    return pd.DataFrame(data=data)


'''
@TODO come back and add for kickers
'''
def kicker_game_log(soup: BeautifulSoup):
    return 0


def main():
    df = get_player_game_log('Anthony Fasano', 'TE', 2010)
    df.to_csv('./data/test_data.csv', sep='\t', index=False)

if __name__ == '__main__':
    main()