import sys
from pro_football_reference_web_scraper import player_game_log as p

'''
The second argument (sys.argv[1]) is designed to contain the indicator for which method we would like to call
KEY BELOW
"gameLog" == Get Player Game Log
'''

if sys.argv[1] == "gameLog":
    name = sys.argv[2]
    position = sys.argv[3]
    year = int(sys.argv[4])  #MUST typecast year
    print(p.get_player_game_log(name, position, year).to_html)
    
sys.stdout.flush()
