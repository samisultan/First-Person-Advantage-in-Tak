import sqlite3  # Get the SQlite package
import string   # For ABC...XYZ list
from math import *
#from numpy import transpose

import os
import subprocess
from shutil import copyfile
import datetime
import time
import calendar

# At some point, I need to use .upper() on the move string to make sure 
##=============================================================================
##=============== ----------------- Constants ---------------- ================
##=============================================================================
whiteELOadvantage = 45 # White win rate is 56.48% (for "good players" on a 5x5) TO DO: At some point I should not have this hard coded, but calculated base on win rates. See http://www.3dkingdoms.com/chess/elo.htm

letters = list(string.ascii_uppercase) # Returns the list of tiles that belong to that orthant.

botlist = ['AlphaTakBot_5x5', 'BeginnerBot', 'IntuitionBot', 'ShlktBot', 'TakkerBot', 'TakkerusBot', 'TakticBot', 'TakticianBot', 'TakticianBotDev', 'alphabot', 'alphatak_bot', 'alphatak_bot1', 'antakonistbot', 'cutak_bot', 'cutak_bot', 'takkybot', 'FPAbot', 'AaaarghBot']

##=============================================================================
##=============== ----------------- File Names --------------- ================
##=============================================================================

folder = os.getcwd()
games_db = 'games_anon.db'
trfolder = "takrating-master"
trjs   = "takrating.js"
node = "\"c:\\Program Files\\nodejs\\node.exe\""
mydb= "openingsdb.db"
ratingsfile = "takrating-master/ratings.txt"


games_db_temp_loc = trfolder +"\\" + games_db[:-3]+ "_temp.db"

debugging = False

# If getting a 'database locked' error in one of the get_ELO functions, try changing i=500 down to i=100 or i=50 in add_ELO_and_games_played_to_games(,,,)
##=============================================================================
##=============================================================================
##=============== ---------------- Player ELOs --------------- ================
##=============================================================================
##=============================================================================


##------------------------- + Run takrating.js + ------------------------------
def runtakratingjs(message):
    # 1. Navigate to folder the the javascript is in
    os.chdir(folder + "\\" + trfolder)

    # 2. Run node + <name.js>
    result = subprocess.check_output(node + " " + trjs, shell=True)

    # 3. Navigate back
    os.chdir(folder)
    if len(message) != 0 and not debugging:        
        print(message, end='\r')

##------------- + Take the output and add it to the database + ----------------

def make_table_from_txt(file, tablename):
    # 1. Make a table that will become the database:
    inFile = open(file, 'r')
    filestring = inFile.read().strip() # Removes extra \n newline at end.
    inFile.close()
    
    linelist = filestring.split("\n")
    #print(linelist)
    for i in range(len(linelist)):
        line = linelist[i].split("|")
        #print(line)
        linelist[i] = [ line[1].strip() ,                # "Name". The actual entry includes quotation marks. CHANGED so that it does not.
                       int(  line[2] ),                    # ELO
                       int(  line[4])]                     # Number of Games
        #print(linelist[i])
    #print(linelist[:10],'...', len(linelist),'total.')
    
    #2. Make the Database
    conn = sqlite3.connect(mydb) # Open/create a database
    c = conn.cursor() # Create a cursor/pointer for navigating through the file.
    
    # 3. Remove any previous table, if one exists
    c.execute('DROP TABLE IF EXISTS'+ tablename)
    c.execute('CREATE TABLE IF NOT EXISTS ' + tablename + '(name TEXT, elo INTEGER, gamesplayed INTEGER)')

        
    for line in linelist:
        c.execute('INSERT INTO ' + tablename + ' VALUES (?,?,?)', line)
        #print(line)
    
    conn.commit() # Anytime you make a change, you need to commit.
    c.close()
    conn.close()

##------------------ + Make a Datebase to Store Data and ELOs + ---------------
def makegamesdbbackup():
    # 1. Make a backup copy of Playtak games database
    copyfile(trfolder +"\\" + games_db, games_db_temp_loc)
    print("Created backup of", games_db, 'at', games_db_temp_loc)


def makeopeningsdb():
    # 2. Make a new database to store ELOs, games, and normalized games.
    copyfile(trfolder +"\\" + games_db, mydb)
    print("Created working database called", mydb, 'at', trfolder +"\\" + games_db)
    
def revertgamesdb():
    # 4a. Revert the backup of Playtak_games database
    os.remove(trfolder + "\\" + games_db)
    copyfile(games_db_temp_loc, trfolder + "\\" + games_db)
    os.remove(folder + "\\" + games_db_temp_loc)
    print('Backup deleted and', games_db, 'restored.')

# 0a. Move all of this code into openings.py into a function called setup()
# 0b. Everything else should be in another function functionname() that runs... actually, no. Yes. There should only be ONE function that runs. main() main() is always called in the script, and asks whether or not to run setup (It should be able to check whether setup NEEDs to be run i.e. whether or not openings.db exists). After asking about setup() (and running it if necessary), main() will ask the parameters for openings analysis and run the analysis()


##--------------------- + Compute ELOs and Add to Database + ------------------
# 3. Find the UNIX timestamp when the most recent game was played
def findmostrecentgamedate():
    conn = sqlite3.connect(mydb) # Open/create a database
    c = conn.cursor() # Create a cursor/pointer for navigating through the file.
    
    c.execute('SELECT MAX(date) FROM games;')
    maxunixdate = c.fetchall()[0][0]  # c.fetchall returns [(1466141169186,)] 
    
    # Remove the ms digits  
    maxunixdate = maxunixdate // 10**3
    print('Unix timestamp for the most recent game is', maxunixdate)
    
    # 3.0 Find the date from the timestamp
    maxdate = datetime.datetime.utcfromtimestamp(maxunixdate).strftime('%Y-%m-%d')
    
    #conn.commit() # Do not need to commit since no changes were made.
    c.close()
    conn.close()
    return maxdate
    

def add_ELOs_all_dates():
    # 3.0.1 Make a list of all the dates that the ELO needs to be calculated for.
    maxdate = findmostrecentgamedate()
    datelist=[maxdate]
    while maxdate > '2016-04-23':
        maxdate = datetime.date(int(maxdate[0:4]), int(maxdate[5:7]), int(maxdate[8:10]) )
        maxdate = maxdate - datetime.timedelta(days=1)
        maxdate = maxdate.strftime('%Y-%m-%d')
        datelist.append(maxdate)
    print('About to calculate ELOS for',datelist)
    
    # 3.1 Run takrating.js on games_anon.db
    for datestr in datelist:
        # IF the table doesn't exist THEN do the following: TO DO
        runtakratingjs("\rRan takratingjs for " + datestr)
        
        # 3.2 Use make_table_from_txt to add a table "2016-06-18" with the ELOs generated
        
        make_table_from_txt(ratingsfile, '[ELOs_for_' + datestr+']')
        
        # 3.3 Delete all games AFTER datestr
        conn = sqlite3.connect(trfolder +"\\" + games_db) 
        c = conn.cursor() 
        
        #unixdate = calendar.timegm(datetime.date(int(datestr[0:4]), int(datestr[5:7]), int(datestr[8:10])).timetuple())
        unixdate = datetime.datetime(int(datestr[0:4]), int(datestr[5:7]), int(datestr[8:10]) ).timestamp()*10**3
        unixdate = str(int(unixdate))
        #print(datestr, unixdate)
        c.execute('DELETE FROM games WHERE date>' + unixdate)
        
        conn.commit()
        c.close()
        conn.close()        
        

def add_ply_counts(database, table, createColumn=True):
    conn = sqlite3.connect(database) 
    c = conn.cursor()
    
    # Add a column to store the number of plies in the game
    if createColumn:
        c.execute('ALTER TABLE '+ table +' ADD COLUMN plycount   INTEGER;')
        
    c.execute('SELECT id, notation from games')
    games_table = c.fetchall() # Looks like (7983, 'opticus', 'Glitches')
    
    i=0
    while len( games_table) > 0:
        game_entry = games_table.pop()
        #print(game_entry)
        
        game_id      = str(  game_entry[0]  )
        notation     = game_entry[1]
        #print('Game:', game_id, 'looked like', notation)
        
        plycount = notation.count(',') + 1

        c.execute('UPDATE ' + table + ' SET plycount =' + str(plycount) + ' WHERE id=' + game_id)        
        
        #This commit make the program ungodly slow. But it seems like if you make ~5000 changes before a commit, the _journal gets too big, and it locks the database. Best bet is probably to commit every 1000 or so games.
        i = i+1
        if i==500:
            conn.commit()
            i=0
            print( "\rAdded plycounts till game", game_id +'.', "Commit sent.")
        
    
    print('Done. Finished adding plycounts to', table, 'in', database)
    
    conn.commit()
    c.close()
    conn.close()    

# THIS BLOCK IS DONE. See add_ELOs_all_dates()
# 4. While the UNIX timestamp is greater than the UNIX timestamp for 2016-04-25 (It looks like the database did not store usernames until April 23rd)
    # 4.0 Set the Unix time stamp to that of the previous date
    # 4.1 Remove all games from games_anon with a greater timestamp
    # 4.2 Run takrating.js again
    # 4.3 Use make_table_from_txt to add a table named for that date with the ELOs generated


def delete_bad_games(database, table):
    print('Creating a copy of all games in ', table, ' called games_all')
    conn = sqlite3.connect(database) 
    c = conn.cursor()

    c.execute('CREATE TABLE games_all AS SELECT id, date, size, player_white, player_black, notation, result, plycount FROM games')
    
    print("\nDeleting games that can't be analyzed from the table  ", table, '  in  ', database + ':')
    # 4b. Delete all games before April 24th (before db logged usernames)  
    #c.execute('DELETE FROM '+ table +' WHERE date<' + unixdate)
    c.execute('DELETE FROM '+ table +' WHERE player_white="Anon" OR player_black="Anon"')
    print('\tDeleted', c.rowcount, 'games with username Anon')
    
    # 4c. Delete all games with Guests
    c.execute('DELETE FROM '+ table +' WHERE player_white LIKE "Guest%" OR player_black LIKE "Guest%" ')
    print('\tDeleted', c.rowcount, 'games with Guests')
    
    # I should make a list of non-ranked players that need to be removed, and remove all of them in a for loop. Right now FriendlyBot is the only one, but there may be more later. I think the <botname>_dev accounts might need to be removed, but idk.
    # 4c2. Delete all games with FriendlyBot, since it has no ELO
    c.execute('DELETE FROM '+ table +' WHERE player_white = "FriendlyBot" OR player_black = "FriendlyBot" ')
    print('\tDeleted', c.rowcount, 'games with FriendlyBot')    
    
    ## 4d. Delete all games with less than 6-ish plies
    #minlength=10*3
    #c.execute('DELETE FROM '+ table + ' WHERE LENGTH(notation) <' + #str(minlength))
    #print('\tDeleted', c.rowcount, 'games with fewer than', minlength, 'characters in the notation. (Approx',minlength//5,'plies)')
    
    # 4d. Properly deleting games with less than 10 plies
    minplies = 14
    c.execute('DELETE FROM '+ table + ' WHERE plycount <' + str(minplies))
    print('\tDeleted', c.rowcount, 'games with fewer than', minplies, 'plies)')
    
    # 4d. Delete games that were inconclusive
    minplies = 14
    c.execute('DELETE FROM '+ table + ' WHERE result ="0-0"')
    print('\tDeleted', c.rowcount, 'games with result 0-0')    
    
    # 4d2. Delete all games that are size 3 and 4, since they do not count in NoHatCoder's ELO script. (If a player has ONLY played size 4, then they will not have an ELO)
    minsize=5
    c.execute('DELETE FROM '+ table + ' WHERE size <' + str(minsize))
    print('\tDeleted', c.rowcount, 'games played on boards smaller than', minsize)
    
    conn.commit()
    c.close()
    conn.close()    

def get_player_elo_and_games_at_date(player, datestr): # Datestr in "YYYY-MM-DD" format
    #print('Getting ELO for', player, 'on', datestr + ':')
    conn = sqlite3.connect(mydb) 
    c = conn.cursor() 

    table="[ELOs_for_" + datestr +']'
    player = '"' + player + '"'
    c.execute('SELECT elo, gamesplayed FROM '+ table +' WHERE name=' + player)
    #c.execute('SELECT elo FROM [ELOs_for_2016-05-10] WHERE name="KingSultan"')
    mylist = c.fetchone()
    
    #conn.commit() # Do not need to commit since no changes were made.
    c.close()
    conn.close()
    
    return mylist

def unixms_to_datestr(unixtimems):
    unixtime = unixtimems  // 10**3
    datestr = datetime.datetime.utcfromtimestamp(unixtime).strftime('%Y-%m-%d')
    return datestr

def datestr_to_unixms(datestr):
    unixtime = calendar.timegm(datetime.date(int(datestr[0:4]), int(datestr[5:7]), int(datestr[8:10])).timetuple())
    unixtime = unixtimems  * 10**3
    return datestr
    

# 4e Add ELOs into openings.db/games entries
def add_ELO_and_games_played_to_games(database, table, createColumns): # This should only be run once.    
    # 4e.0 Add columns 'whiteELO' and 'blackELO' and gameswhite, gamesblack
    print('Adding columns to games in openings.py')
    conn = sqlite3.connect(database) 
    c = conn.cursor()
    
    if createColumns:
        c.execute('ALTER TABLE '+ table +' ADD COLUMN whiteELO   INTEGER;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN blackELO   INTEGER;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN whitegames INTEGER;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN blackgames INTEGER;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN isbotwhite INTEGER;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN isbotblack INTEGER;')        
    
    # 4e.1 for each, game get the ELO of each player on that day and enter them into 'whiteELO/blackELO'
    c.execute('SELECT id, date, player_white, player_black from games')
    #print(c.fetchall())
    games_table = c.fetchall() # Looks like (7983, 'opticus', 'Glitches')
    
    i=0
    while len( games_table) > 0:
        game_entry = games_table.pop()
        #print(game_entry)
        
        game_id      = str(  game_entry[0]  )
        unixdate     = game_entry[1]
        datestr      = unixms_to_datestr(unixdate)
        
        player_white = game_entry[2]
        player_black = game_entry[3]
        whiteval     = get_player_elo_and_games_at_date(player_white, datestr)
        blackval     = get_player_elo_and_games_at_date(player_black, datestr)

        whiteELO     = str(  whiteval[0]  )
        blackELO     = str(  blackval[0]  )
        whitegames   = str(  whiteval[1]  )
        blackgames   = str(  blackval[1]  )
        isbotwhite   = str(  int(player_white in botlist)  )
        isbotblack   = str(  int(player_black in botlist)  )
        #print('P1=', player_white,'has ELO', whiteELO, 'after', whitegames, 'games.    ', "P2=", player_black,'has ELO', blackELO, 'after', blackgames, 'games.')
        
        #txt = 'UPDATE ' + table + ' SET whiteELO =' + whiteELO + ' WHERE id=' + game_id
        #print(txt)
        c.execute('UPDATE ' + table + ' SET whiteELO ='   + whiteELO   + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET blackELO ='   + blackELO   + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET whitegames =' + whitegames + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET blackgames =' + blackgames + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET isbotwhite =' + isbotwhite + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET isbotblack =' + isbotblack + ' WHERE id=' + game_id)        
        
        #This commit make the program ungodly slow. But it seems like if you make ~5000 changes before a commit, the _journal gets too big, and it locks the database. Best bet is probably to commit every 1000 or so games.
        i = i+1
        if i==500:
            conn.commit()
            i=0
            print( "\rAdded ELO entries till game", game_id +'.', "Commit sent.")
        
    
    print('Done. Finished adding ELOs to', table, 'in', database)
    conn.commit()
    c.close()
    conn.close()
    
    
    # At this point, I could probably delete all the dated ELO tables, or at very close close them out. Actually, I should be closing them out after each use, even though that might be a bit slow.

##------------------- + Decide which games to keep + -----------------
# Make a function that prettily prints the board state

def is_int(string):
    try: 
        int(string)
        return True
    except ValueError:
        return False

def get_int(message, min_allowed = -10**20, max_allowed = 10**20): # Both min and max an inclusive
    #  Ask the user for an input
    print(message, end=': \t')
    string  = input("").strip() 
    
    string_is_int = is_int(string)
    while not string_is_int:
        print('\tPlease enter an integer', end=': \t')
        string  = input("")       
        string_is_int = is_int(string)        
    
    int_entered = int(string)
    while not(int_entered >= min_allowed and int_entered <=max_allowed    ):
        print('\tInput must be between', min_allowed, 'and', max_allowed)
        int_entered = get_int(message, min_allowed, max_allowed)
 
    return int_entered

def get_binary_choice(message, yes_list=['true', 't', 'y', 'yes', '1'], no_list = ['false', 'f' ,'n', 'no', '0']):
    #  Ask the user for an input
    print(message, end=': \t')
    choice  = input("").lower().strip()  
    
    valid_choice = (choice in yes_list) or (choice in no_list)
    while not valid_choice:
        print('\tPlease select from', yes_list, 'or', no_list, end=': \t')
        choice  = input("").lower()  
        valid_choice = (choice in yes_list) or (choice in no_list)

 
    return choice in yes_list


def get_date(message, mindate = '2016-04-23', maxdate = '2099-01-01'):
    #  Ask the user for an input
    print(message, end=': \t')
    string  = input("").strip()
    
    valid_date = len(string) == 10 and string[0:4].isnumeric() and string[5:7].isnumeric() and string[8:10].isnumeric()
    while not valid_date:
        print('\tPlease enter a date in YYYY-MM-DD format', end=': \t')
        string  = input("").strip()
        valid_date = len(string) == 10 and string[0:4].isnumeric() and string[5:7].isnumeric() and string[8:10].isnumeric()

    date = string[0:4] + '-' + string[5:7] + '-' + string[8:10]
    # Checking that the date is plausible. If won't catch things like 2016-03-31, but, I'm not about to figure out how to code in leap years.
    while not (date >= mindate and date <= maxdate and int(date[5:7])<=12 and int(date[8:10])<=31  ):
        print('\tDate must be between', mindate, 'and' , maxdate)
        date = get_date(message, mindate, maxdate)
    
    return date

# 5. Decide which games to keep
        # 5.0.0  Ask which size
        # 5.0.1  Ask min ELO
        # 5.0.1  Ask max ELO
        # 5.0.1b Ask if both players must meet ELO req, or just one
        # 5.0.2  Ask min games played
        # 5.0.2b Ask if both players must meet ELO req, or just one
        # 5.0.2c Ask whether to inclue bots
        # 5.0.3  Ask how many plies (1-999). If plies > 50, check how many games there are and warn the player that the average is likely to be low.
        # 5.0.4 Ask start date (YYYY MM DD). Must be after April 24th
        # 5.0.5 Ask end date (YYYY MM DD). Must be after start date. (Later I will need to take the min of this and the date of the most recent games)

def ask_settings():
    useDefaults = get_binary_choice("Use default settings?")
    if useDefaults:
        size   = 5
        plycount  = get_int('\nHow many plies?[1-999]', 1, 999)
        minELO = 1400
        maxELO = 9000
        bothmeetELO = True
        mingames    = 10
        includebots = True
        includetimeends = False
        startdate = '2016-04-23'
        enddate   = '2099-01-01'
    else:
        size   = get_int('\nBoard size [5-8]', 5, 8)
        plycount  = get_int('\nHow many plies?[1-999]', 1, 999)
        minELO = get_int('\nMinimum player ELO [+]', 1, 9000)
        maxELO = get_int('\nMaximum player ELO [+]', minELO, 9000)
        bothmeetELO = get_binary_choice('\nMust both players meet ELO minimum?')
        mingames    = get_int('\nMinimum number of games each player must have played', 1)
        includebots = get_binary_choice('\nInclude games with bots?')
        includetimeends = get_binary_choice('\nInclude games that ended on time or disconnect?')
        startdate = get_date('Include games after date  [YYYY-MM-DD]')
        enddate   = get_date('Include games before date [YYYY-MM-DD]', startdate)
    
    return [size, plycount, minELO, maxELO, bothmeetELO, includebots, startdate, enddate, mingames, includetimeends]

    # 5.0  Add all games of size desired to table 'good_games
    
    # There is definitely a faster way to do these variable assignments.

def make_table_name(settingslist):
    tablename = 'analyze'
    for item in settingslist:
        tablename = tablename + '_' + str(item)
    return tablename

def create_table_from_settings(settingslist, database):
    size      = settingslist[0]
    plycount  = settingslist[1]
    minELO    = settingslist[2]
    maxELO    = settingslist[3]
    bothmeetELO  = settingslist[4]
    includebots  = settingslist[5]
    startdate = settingslist[6]
    enddate   = settingslist[7]
    mingames  = settingslist[8]
    includetimeends = settingslist[9]
    
    if bothmeetELO: # The negation for deleting messes this up
        bothmeetELOstr = ' OR '
    else:
        bothmeetELOstr = ' AND '
    
    conn = sqlite3.connect(database)
    c = conn.cursor()
    
    newtablename = "[" + make_table_name(settingslist) +"]"
    
    print('Creating table', newtablename, 'to store normalized boards and openings scores.')
    
    c.execute("CREATE TABLE IF NOT EXISTS " + newtablename + " AS SELECT * FROM games")    
    
    c.execute('DELETE FROM '+newtablename+' WHERE size!=' + str(size))
    print('\tDeleted', c.rowcount, 'games that were not of size', size)
    
    
    c.execute('DELETE FROM '+newtablename+' WHERE whiteELO < ' + str(minELO) + bothmeetELOstr + ' blackELO < ' + str(minELO))
    print('\tDeleted', c.rowcount, 'games where ' + 'a'*(not bothmeetELO) + 'both'*bothmeetELO + ' player ELOs were less than', minELO)
    
    
    c.execute('DELETE FROM '+newtablename+' WHERE whiteELO > ' + str(maxELO) + bothmeetELOstr + ' blackELO > ' + str(maxELO))
    print('\tDeleted', c.rowcount, 'games where ' + 'a'*(not bothmeetELO) + 'both'*bothmeetELO + ' player ELOs were more than', maxELO)
    
    c.execute('DELETE FROM '+newtablename+' WHERE plycount < ' + str(plycount))
    print('\tDeleted', c.rowcount, 'games where plycount was less than', plycount)
    
    c.execute('DELETE FROM '+newtablename+' WHERE whitegames < ' + str(mingames) + ' OR blackgames < ' + str(mingames))
    print('\tDeleted', c.rowcount, 'games where one player had played less than', mingames, 'games')
    
    if not includetimeends:
        c.execute('DELETE FROM '+newtablename+' WHERE result = "1-0" or result = "0-1"')
        print('\tDeleted', c.rowcount, 'that ended on time or disconnection.')
        
    c.execute('SELECT count(*) FROM '+newtablename)
    gamecount = c.fetchone()
    print('\tThis table has', gamecount, 'games.')
    
    
    # Deal with bots
    bottotal=0
    if not includebots:
        for bot in botlist:
            bot = '"' + bot + '"'
            c.execute('DELETE FROM '+newtablename+' WHERE player_white = ' + bot + ' OR player_black = ' + bot)
            bottotal += c.rowcount
        print('\tDeleted', bottotal, 'games played by bots. (The bot list is hard coded.)')
            
    # Deal with startdate
    # Deal with enddate
    
    conn.commit()
    c.close()
    conn.close()    
    
    # 5.0b Add a column in good_games called score###,  ### for the number of plies
    # 5.1  Remove all games where either/both players' ELO is lower than min (Maybe define get_player_ELO(player,date) [Still need to do this, but earlier. By now the ELOs should be in the same row.]
    # 5.2 Remove all games where either/both player have played fewer than min games
    # 5.3 Remove games with too few plies.
    # 5.4 Remove games before start date.
    # 5.5 Remove games after end date.
    # 5.6 Print out how many games like this were found, and if fewer than 10, quit.

# At this point I have a database with the games I want to analyze, and daily player ELOs.
# 6. Make a function that scores each game given the player names:
    # 6.1 score(whiteELO, blackELO, result) = 1/ELO win-probability, where ELO-w-p is P(a)=1/(1+10^d) where d is elo_b - elo_a. The white player gets 110 added to their elo for first player advantange. + for white wins, - for black wins. If it is a tie, take the ?average? of a white and black win
def win_prob_white(whiteELO, blackELO):
    diff = blackELO - whiteELO
    return 1/(1+10**(  diff/400  ))

def score_win1(result, whiteELO, blackELO): # This is the inverse opponent win chance score # I probably want to subtract 1 from r-0 and 0-r these. Let's see what happens
    whiteELO += whiteELOadvantage
    if result in ['F-0', 'R-0', '1-0']:
        return 1/win_prob_white(whiteELO, blackELO)
    elif result in ['0-F', '0-R', '0-1']:
        return -1/(1-win_prob_white(whiteELO, blackELO))
    elif result in ['1/2-1/2']:
        return 0.5 /win_prob_white(whiteELO, blackELO) -0.5/(1-win_prob_white(whiteELO, blackELO))
    elif result in ['0-0']:
        print('Asked to calculate score1 for inconclusive game. Were the bad games not removed properly?')
        time.sleep(1)
        return 0
    else:
        print(result)
        raise ValueError('score_win1 not given a valid result ', result )
    
def score_win2(result, whiteELO, blackELO): # The is the opponent win chance score
    whiteELO += whiteELOadvantage
    if result in ['F-0', 'R-0', '1-0']:
        return 1-win_prob_white(whiteELO, blackELO)
    elif result in ['0-F', '0-R', '0-1']:
        return win_prob_white(whiteELO, blackELO)
    elif result in ['1/2-1/2']:
        return 0.5*(1-win_prob_white(whiteELO, blackELO)) +0.5*win_prob_white(whiteELO, blackELO)
    elif result in ['0-0']:
        print('Asked to calculate score2 for inconclusive game. Were the bad games not removed properly?')
        time.sleep(1)
        return 0
    else:
        print(result)
        raise ValueError('score_win2 not given a valid game result ', result )
        

# 7. Score each opening
    # 7.0 For each game, calculate the score and store it in score### column
    
def add_scores_to_table(database, table, createColumn = True):
    conn = sqlite3.connect(database) 
    c = conn.cursor()
    
    # Add a column to store the number of plies in the game
    if createColumn:
        c.execute('ALTER TABLE '+ table +' ADD COLUMN score1   REAL;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN score2   REAL;')
        #c.execute('ALTER TABLE '+ table +' ADD COLUMN score3   REAL;')
        
    c.execute('SELECT id, result, whiteELO, blackELO from games')
    games_table = c.fetchall() # Looks like (7983, 1430, 1590)
    
    i=0
    while len( games_table) > 0:
        game_entry = games_table.pop()
        #print(game_entry)
        
        game_id      = str(  game_entry[0]  )
        result       = game_entry[1]
        whiteELO     = game_entry[2]
        blackELO     = game_entry[3]
        #print('\rGame:', game_id)
        
        score1 = score_win1(result, whiteELO, blackELO)
        score2 = score_win2(result, whiteELO, blackELO)

        c.execute('UPDATE ' + table + ' SET score1 =' + str(score1) + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET score2 =' + str(score2) + ' WHERE id=' + game_id)
        #c.execute('UPDATE ' + table + ' SET score3 =' + str(score3) + ' WHERE id=' + game_id) 
        
        #This commit makes the program ungodly slow. But it seems like if you make ~5000 changes before a commit, the _journal gets too big, and it locks the database. Best bet is probably to commit every 1000 or so games.
        i = i+1
        if i==500:
            conn.commit()
            i=0
            print( "\rAdded scores till game", game_id +'.', "Commit sent.")
        
    
    print('Done. Finished adding scores to', table, 'in', database)
    
    conn.commit()
    c.close()
    conn.close()    
    # 7.1.0 Create a column 'normmoves###' 
    # 7.1.1 For each game, find the normalized moves to ### plies and store it in normmoves###
    # 7.2 Create a new table 'openings###' (moves, boardstate totalscore, num_games) (This is redundant, but worth having to veiw instantly)
    # 7.3 For each game, check if the normmoves### is in openings###
        # If it is, add it's score to the total score, and increase num_games by 1
        # If not, add a new row for it.
        
def add_norm_moves_and_board(database, table, plycount, createColumn=True):
    conn = sqlite3.connect(database) 
    c = conn.cursor()
    
    plycountstr = '0'*(3-len(  str(plycount)  )) + str(plycount)
    
    # Add a column to store the number of plies in the game
    if createColumn:
        table = '[' + table + ']'
        c.execute('ALTER TABLE '+ table +' ADD COLUMN  nmoves'+ plycountstr +'  INTEGER;')
        c.execute('ALTER TABLE '+ table +' ADD COLUMN  nboard'+ plycountstr +'  INTEGER;')
        
    c.execute('SELECT id, size, notation from games')
    games_table = c.fetchall() # Looks like (7983, 'opticus', 'Glitches')
    
    i=0
    while len( games_table) > 0:
        game_entry = games_table.pop()
        #print(game_entry)
        
        game_id      = str(  game_entry[0]  )
        board_size   = game_entry[1]
        move_string  = game_entry[2] # TO DO This needs to be chopped down to just the first plycount plies
        
        ##nmoves = '"' + normalize_moves(move_string, plycount, board_size) + '"'
        board_state = build_board_from_moves(move_string, plycount, board_size)
        nboard = '"' + str(normalize_board(board_state)) + '"'
        
        #print('Game:', game_id, 'looked like', move_string[:40])
        #print('Normalized moves:', nmoves)
        #print('Normalized board:', nboard)

        ##c.execute('UPDATE ' + table + ' SET nmoves'+plycountstr+' = ' + nmoves + ' WHERE id=' + game_id)
        c.execute('UPDATE ' + table + ' SET nboard'+plycountstr+' = ' + nboard + ' WHERE id=' + game_id) 
        
        #This commit make the program ungodly slow. But it seems like if you make ~5000 changes before a commit, the _journal gets too big, and it locks the database. Best bet is probably to commit every 1000 or so games.
        i = i+1
        if i==500:
            conn.commit()
            i=0
            print( "\rAdded normalized notation and boards till game", game_id +'.', "Commit sent.")
        
    
    print('Done. Finished adding normalized notation and boards to', table, 'in', database)
    
    conn.commit()
    c.close()
    conn.close()    



def aggregate_opening_boards(database, tablename, settingslist):
    conn = sqlite3.connect(database) 
    c = conn.cursor()
    
    plycount = str(  settingslist[1]  )
    boardcolumnname = 'nboard' +  '0'*(3-len(str( plycount )))  + str(plycount)
    newtablename = '[score_' + tablename + ']'
    # I should drop the table first, so I don't end up with duplicate entries
    # TO DO also include columns for how much higher the win rates are above the average win rates
    c.execute('CREATE TABLE IF NOT EXISTS ' + newtablename + '(board STRING, score1 REAL, score2 REAL, score3 REAL, avwhiteELO REAL, avblackELO REAL, gamecount INTEGER, white_wins INTEGER, black_wins INTEGER, ties INTEGER, white_rate REAL, black_rate REAL, tie_rate REAL)')
    
    c.execute(  "SELECT       `"+boardcolumnname+"`\
    FROM     `"+ tablename +"` \
    GROUP BY `"+boardcolumnname+"`    \
    ORDER BY COUNT(*) DESC  \
    LIMIT    20;  ")
    
    boardstr_list = c.fetchall()
    print(boardstr_list)
    # For each Board
    for boardstr in boardstr_list:
        boardstr = boardstr[0] #Each board is inside a 1-tuple.
        board = eval(boardstr)
        print_board(board)
        
        #print('tablename ',tablename, 'boardcolumn', boardcolumnname, 'boardstr', boardstr)
        c.execute('SELECT score1, score2, result, whiteELO, blackELO from ['+tablename+'] WHERE '+boardcolumnname+' = "'+ boardstr+ '"')
        games_table = c.fetchall()
        
        total_score1    = 0
        total_score2    = 0
        total_whiteELO  = 0
        total_blackELO  = 0
        white_win_count = 0
        black_win_count = 0
        tie_count = 0
        gamecount = 0 # This is redundant, since I can just do win + loss + ties
        
        while len( games_table) > 0: # There may be a better way to be these counts and sums using purely SQLite
            game_entry = games_table.pop()
            print(game_entry)
            
            gamecount += 1 # This is redundant, as before
            total_score1    += game_entry[0]
            total_score2    += game_entry[1]
            total_whiteELO  += game_entry[3]
            total_blackELO  += game_entry[4]
            
            result = game_entry[2]
            
            if   result  in ['R-0', 'F-0', '1-0']:
                white_win_count += 1
            elif result  in ['0-R', '0-F', '0-1']:
                black_win_count += 1
            elif result  in ['1/2-1/2']:
                tie_count += 1
            else:
                raise ValueError('Invalid result '+ result + 'in the row ' + str(game_entry) )
            
        
            
        c.execute('INSERT INTO ' + newtablename + '(board, score1, score2, avwhiteELO, avBlackELO, gamecount, white_wins, black_wins, ties, white_rate, black_rate, tie_rate) VALUES (?,?,?,?,?,   ?,?,?,?,?,  ?,?)', (boardstr, total_score1, total_score2, total_whiteELO/gamecount, total_blackELO/gamecount, gamecount, white_win_count, black_win_count, tie_count, white_win_count/gamecount, black_win_count/gamecount, tie_count/gamecount)) 
            
        
    
    print('Done. Finised aggregating scores from', tablename, 'in', database)

    conn.commit()
    c.close()
    conn.close() 
    
    
##------------------- + Make a Datebase to Store Daily ELOs + -----------------

# 0a. Move all of this code into openings.py into a function called setup()
# 0b. Everything else should be in another function functionname() that runs... actually, no. Yes. There should only be ONE function that runs. main() main() is always called in the script, and asks whether or not to run setup (It should be able to check whether setup NEEDs to be run i.e. whether or not openings.db exists). After asking about setup() (and running it if necessary), main() will ask the parameters for openings analysis and run the analysis()

# 3. Find the UNIX timestamp when the most recent game was played
    # 3.0 Find the date from the timestamp
    # 3.1 Run takrating.js on games_anon.db
    # 3.2 Use make_table_from_txt to add a table "2016-06-18" with the ELOs generated

# 4. While the UNIX timestamp is greater than the UNIX timestamp for 2016-04-25 (It looks like the database did not store usernames until April 23rd)
    # 4.0 Set the Unix time stamp to that of the previous date
    # 4.1 Remove all games from games_anon with a greater timestamp
    # 4.2 Run takrating.js again
    # 4.3 Use make_table_from_txt to add a table named for that date with the ELOs generated



# 4b. Delete all games before April 24th (before db logged usernames)
# 4c. Delete all games with Guests
# 4d. Delete all games with less than 4 moves

# 4e Add ELOs into openings.db/games entries
    # 4e.0 Add columns 'whiteELO' and 'blackELO'
    # 4e.1 for each, game get the ELO of each player on that day and enter them into 'whiteELO/blackELO'
    # At this point, I could probably delete all the dated ELO tables, or at very closet close them out. Actually, I should be closing them out after each use, even though that might be a bit slow.
    

##------------------- + Decide which games to keep + -----------------
# Do this in openings.py
# Make a function that prettily prints the board state
# 5. Decide which games to keep
        # 5.0.0  Ask which size
        # 5.0.1  Ask min ELO
        # 5.0.1b Ask if both players must meet ELO req, or just one
        # 5.0.2  Ask min games played
        # 5.0.2b Ask if both players must meet ELO req, or just one
        # 5.0.3  Ask how many plies (1-999). If plies > 50, check how many games there are and warn the player that the average is likely to be low.
    # 5.0  Add all games of size desired to table 'good_games'
    # 5.0b Add a column in good_games called score###,  ### for the number of plies
    # 5.1  Remove all games where either/both players' ELO is lower than min (Maybe define get_player_ELO(player,date) [Still need to do this, but earlier. By now the ELOs should be in the same row.]
    # 5.2 Remove all games where either/both player have played fewer than min games
    # 5.3 Remove games with too few plies.

# At this point I have a database with the games I want to analyze, and daily player ELOs.
# 6. Make a function that scores each game given the player names:
    # 6.1 score(whiteELO, blackELO, result) = 1/ELO win-probability, where ELO-w-p is P(a)=1/(1+10^d) where d is elo_b - elo_a. The white player gets 110 added to their elo for first player advantange. + for white wins, - for black wins. If it is a tie, take the ?average? of a white and black win

# 7. Score each opening
    # 7.0 For each game, calculate the score and store it in score### column
    # 7.1.0 Create a column 'normmoves###' 
    # 7.1.1 For each game, find the normalized moves to ### plies and store it in normmoves###
    # 7.2 Create a new table 'openings###' (moves, boardstate totalscore, num_games) (This is redundant, but worth having to veiw instantly)
    # 7.3 For each game, check if the normmoves### is in openings###
        # If it is, add it's score to the total score, and increase num_games by 1
        # If not, add a new row for it.

##=============================================================================
##=============================================================================
##=============== -------- Board/Tile Transformations -------- ================
##=============================================================================
##=============================================================================

def x_coord(tile): # This is from the usual perspective. The letter axis is the x axis.
    return letters.index(tile[0].upper()) # A1 corner is (0,0) a1 a2 a3 a4 a5
                                          # .upper(makes it no longer case sensitve)

def y_coord(tile):
    return int(tile[1])-1

##-----------------------------------------------------------------------------
def coord_to_tile(coord):      # Co-ord should be a list. Returns a string.
    return str(letters[coord[0]]) + str(  int(coord[1])+1  )
    
def tile_to_coord(tile):       # Takes the string tile and returns to corresponding co-ordinate as a LIST
    return [x_coord(tile), y_coord(tile)]

##--------------------------- + Rotations + ----------------------------------    
def rotate_coord(coord,size,number_of_rotations): # CLOCKWISE
    for i in range(number_of_rotations % 4):      # Working modulo 4 allows negative rotations.  
        coord=[  coord[1],  (size-1)-coord[0]]
    return coord

def rotate_tile(tile,size,number_of_rotations):
    coord = tile_to_coord(tile)
    newcoord = rotate_coord(coord, size, number_of_rotations)
    return coord_to_tile(newcoord)

def rotate_board(board_state): #, board_size, number_of_rotations):
    return list(zip(*board_state[::-1]))

def rotate_board_n(board_state, rotations):
    for i in range(rotations % 4 + 4): # Rotating changes the data type. Hopefully rotating 4 times instead of 0 fixes the problems that were showing up in the normalization stuff.
        board_state = list(zip(*board_state[::-1]))
    return board_state

##-----------------------------------------------------------------------------
def rotate_move(move, size, number_of_rotations):
    #1. Extract the tile from the string of the single move.
    tile = move[2:4]
    tile = rotate_tile(tile, size, number_of_rotations)
    
    # 2. Rotate the starting tiles
    new_move = move[0:2] + tile + move[4:]  #"P " + "A1" + "<the rest>"
    
    # 3. If the stack is being moved, rotate the destination tile.
    if move[0] == "M":
        end_tile = move[5:7]
        end_tile = rotate_tile(end_tile, size, number_of_rotations)
        new_move = new_move[0:5] + end_tile + new_move[7:]  #"M A1 " + "A3" + "2 1 1"
    
    return new_move

def rotate_move_string(move_string,size, number_of_rotations): # This could possibly done more simply by doing a mass simultanteous replacement of each tile by it's image under rotation.
    move_list = move_string.split(',')
    for i in range(len( move_list )):
        move = move_list[i].strip().upper()
        new_move = rotate_move(move, size, number_of_rotations)
        
        #4. Replace the old move with the rotated one
        move_list[i] = new_move
    
    #5. Reassemable the moves into a string:
    new_move_string = ','.join(move_list)
    return new_move_string

##----------------------------- + Flips + ------------------------------------    

def flipped_coord_let(coord,size):   
    coord=[ (size-1)- coord[0],  coord[1]]
    return coord

def flipped_coord_num(coord,size):   
    coord=[  coord[0],  (size-1)-coord[1]]
    return coord


def flipped_tile_let(tile,size): #This could also be done with a very simple replacement
    coord = tile_to_coord(tile)
    newcoord = flipped_coord_let(coord, size)
    return coord_to_tile(newcoord)

def flipped_tile_num(tile,size): #This could also be done with a very simple replacement
    coord = tile_to_coord(tile)
    newcoord = flipped_coord_num(coord, size)
    return coord_to_tile(newcoord)

##-----------------------------------------------------------------------------

def flipped_board_let(board): # The letters change, the numbers stay the same.
    new_board = board[:]
    new_board.reverse()
    return new_board

def flipped_board_num(board): # The numbers change, the letters stay the same.
    newboard = board[:]
    for i in range(len(newboard)):
        newboard[i]= newboard[i].reverse()
    return newboard


##-----------------------------------------------------------------------------

# The flipped_move_xxx and flipped_move_string_xxx are both the same as rotate_move, and rotate_move_string repectively, with the specific transformation functions changed appropriately. (rotate_yyyyy with flipped_yyyyy_xxx)

def flipped_move_num(move, size):
    #1. Extract the tile from the string of the single move.
    tile = move[2:4]
    tile = flipped_tile_num(tile, size)
    
    # 2. Rotate the starting tiles
    new_move = move[0:2] + tile + move[4:]  #"P " + "A1" + "<the rest>"
    
    # 3. If the stack is being moved, rotate the destination tile.
    if move[0] == "M":
        end_tile = move[5:7]
        end_tile = flipped_tile_num(end_tile, size)
        new_move = new_move[0:5] + end_tile + new_move[7:]  #"M A1 " + "A3" + "2 1 1"
    
    return new_move

def flipped_move_let(move, size):
    #1. Extract the tile from the string of the single move.
    tile = move[2:4]
    tile = flipped_tile_let(tile, size)
    
    # 2. Rotate the starting tiles
    new_move = move[0:2] + tile + move[4:]  #"P " + "A1" + "<the rest>"
    
    # 3. If the stack is being moved, rotate the destination tile.
    if move[0] == "M":
        end_tile = move[5:7]
        end_tile = flipped_tile_let(end_tile, size)
        new_move = new_move[0:5] + end_tile + new_move[7:]  #"M A1 " + "A3" + "2 1 1"
    
    return new_move

##-----------------------------------------------------------------------------
def flipped_move_string_num(move_string, size): # This could possibly done more simply by doing a mass simultanteous replacement of each tile by it's image under rotation.
    move_list = move_string.split(',')
    for i in range(len( move_list )):
        move = move_list[i].strip().upper()
        new_move = flipped_move_num(move, size)
        
        #4. Replace the old move with the rotated one
        move_list[i] = new_move
    
    #5. Reassemable the moves into a string:
    new_move_string = ','.join(move_list)
    return new_move_string

def flipped_move_string_let(move_string, size): # This could possibly done more simply by doing a mass simultanteous replacement of each tile by it's image under rotation.
    move_list = move_string.split(',')
    for i in range(len( move_list )):
        move = move_list[i].strip().upper()
        new_move = flipped_move_let(move, size)
        
        #4. Replace the old move with the rotated one
        move_list[i] = new_move
    
    #5. Reassemable the moves into a string:
    new_move_string = ','.join(move_list)
    return new_move_string


##=============================================================================
##=============================================================================
##=============== ------------- Building a Board ------------- ================
##=============================================================================
##=============================================================================


def tiles_inbetween(tile_start,tile_end): # Given A1, A5, would return ["A1", "A2", ..., "A5"], the straight path between them.
    tile_path=[tile_start, tile_end]
    need_to_reverse = False # 0. It is redundant to write code for both "M A1 A5 1" and  "M A5 A1 1" separately. This helps the script convert "A5 A1" to "A1 A5", and then convert back. 
    
    # 1a. The Letters are the same
    if tile_start[0]==tile_end[0]: 
        # 2. To avoid 4 cases, I will combine the cases where a1->a3 and a3->a1.
        if tile_start[1]>tile_end[1]:
            need_to_reverse = True
            tile_path.reverse()
            tile_start = tile_path[0]
            tile_end   = tile_path[1]
        
        # 3. At this point, the letters are the same, and the number is increasing.
        s = int(tile_start[1])
        e = int(tile_end[1])
        
        # 4. This is what actually builds the path
        s = s+1
        while s < e:
            tile_path.insert(-1, tile_start[0] + str(s))
            s = s+1
            # print(s,e,tile_path)
    
    # 1b. The Numbers are the same
    elif tile_start[1] == tile_end[1]:
        # 2. To avoid 4 cases, I will combine the cases where a1->c1 and c1->a1.
        if tile_start[0]>tile_end[0]:
            need_to_reverse = True
            tile_path.reverse()
            tile_start=tile_path[0]
            tile_end=tile_path[1]
        
        # 3. At this point, the numbers are the same, and the letter is increasing.
        s = tile_start[0]
        e = tile_end[0]
        #print(s,e,tile_path, "before")
        
        # 4. This is what actually builds the path
        s=chr(ord(s)+1) # This acts like 'A' + 1 ='B'
        while s < e:
            tile_path.insert(-1, s+ tile_start[1])
            s=chr(ord(s)+1)
            #print(s,e,tile_path)        
    else:
        raise ValueError('Start and End in tiles_inbetween not in same row or column. Start=', tile_start, "End=", tile_end)
    
    if need_to_reverse:
        tile_path.reverse()
    return tile_path
    
##-----------------------------------------------------------------------------
def print_board(board):  # TO DO make this a prettier type of output
    for row in board:
        print(row)    

def build_board_from_moves(move_string, plies,board_size):
    board = [['' for i in range(board_size)] for j in range(board_size)]
    move_list = move_string.split(',')
    
    # 0. If -1 plies are requested, that means build a board using all the moves in the string given.
    if plies == -1:
        plies = len(move_list)
    
    # 1. Go through each move in the list and place and move peices as specified.
    for i in range(  len(move_list[:plies])  ):
        move=move_list[i].strip()
        
        #2. Placing a peice
        if move[0]=="P":
            x = letters.index(move[2]) # A1 corner is (0,0) a1 a2 a3 a4 a5
            y = int(move[3])-1                            # b1 b2 b3 b4 b5 is the layout.
            #print(i,move,x,y,"move",move[5:]) # Error diagnostic prints
            #[print(row) for row in board]     # Error diagnostic prints
            
            #3. First two moves are weird (first a black tile is placed, then a white tile), thereafer even indices are white, odd are black (since indexing starts at 0)
            if i==0: board[x][y]= 'b'
            if i==1: board[x][y]= 'a'
            if i> 1 and i%2==0: board[x][y]= move[5:] + 'a' # move[i][5:6] looks like "P C1 W"[5:6], and get the wall if it is needed.
            if i> 1 and i%2==1: board[x][y]= move[5:] + 'b'
        
        # 3. Moving stacks
        if move[0]=="M":
            #print("About to make the move ", move, " on ply", i, ". The board looks like:")
            #for row in board:
            #    print(row)
            
            # 4. Figure out which line to move the tiles on.
            drop_counts = move[8:]             # The format of stack-moves is "M A1 A5 # # # # #", where the number of # is how many tiles are between A1 and A5
            drop_counts = drop_counts.split()
            for j in range(  len(drop_counts)  ):
                drop_counts[j]= int(drop_counts[j])
            tile_start = move[2:4]
            tile_end   = move[5:7]
            tile_path  = tiles_inbetween(tile_start, tile_end)
            
            
            # 6. Having a wall or a capstone will change how many characters (i.e stones) need to be placed at the ending tile
            hasCapstoneOrWall = board[x_coord(tile_start)][y_coord(tile_start)][0] in ["W","C"]
            
            #print("\n \t Drop counts:", drop_counts, "\n \t Tile path:", tile_path, "\n \t   -Tile start:", tile_start, "\n \t   -Tile end:", tile_end, "\n \t Has Capstone/Wall:", hasCapstoneOrWall)
            
            # 5. Add stones to each of the tiles on the line, based on the dropcounts (and remove them from the starting tile).
            for j in range( len(tile_path)-1 ):
                #9. Knock down walls if you move a capstone onto one.
                if board[x_coord(tile_start)][y_coord(tile_start)][0]=="C" and board[x_coord(tile_end)][y_coord(tile_end)][:1]=="W":
                    board[x_coord(tile_end)][y_coord(tile_end)]=board[x_coord(tile_end)][y_coord(tile_end)][1:]
                
                num_pick_up = drop_counts[-(j+1)] + hasCapstoneOrWall*(j==0) #Adds one to the total only if the first character in the pile you pick up from has a capstone or wall on top.
                pick_up = board[x_coord(tile_start)][y_coord(tile_start)][:num_pick_up]
                #print("\t Number picked up:", num_pick_up, "\n \t Peices picked up:", pick_up)
                
                # 7. Remove picked up stones from the starting tile
                board[x_coord(tile_start)][y_coord(tile_start)] = board[x_coord(tile_start)][y_coord(tile_start)][num_pick_up:]
                #print("\nAfter removing from ", letters[x_coord(tile_start)], y_coord(tile_start)+1 ," there remain", board[x_coord(tile_start)][y_coord(tile_start)], "also" )
                #[print(row) for row in board]

                # 8. And place them on the ending tile, and before (j).
                board[x_coord(tile_path[-(j+1)])][y_coord(tile_path[-(j+1)])]= pick_up + board[x_coord(tile_path[-(j+1)])][y_coord(tile_path[-(j+1)])]
                #print("\nAfter placing, there now are", board[x_coord(tile_path[-j])][y_coord(tile_path[-j])])
            
            
            
            
        
    #print("Complete. The board is:")     
    #[print(row) for row in board]
    #print("-"*4*board_size)
    return board


##=============================================================================
##=============================================================================
##=========== ------- Finding and Fixing Congruent Games ------- ==============
##=============================================================================
##=============================================================================
                         
##------------------------ + Most Populated Corner + --------------------------
# The new approach is to build all 8 orientations of the board and checking which one is the heaviest in the bottom left corner (The A1, or [0,0] corner). "Most populated" is not accurate, since the algorithim will rate a quadrant with 1 tile in the corner higher than any quadrant that does not have a tile in the corner. This can cause the normalization of a board to flip abruptly, but I don't think that there is any (computationally easy) normalization algorithim where some boards do not flip at some point.


# The order this generates is:
# 10
# 6 9
# 3 5 8
# 1 2 4 7
def build_diagonal_coord_list(board_size):
    coord_list=[]
    for xy_sum in range(2*board_size-1):
        for y in range(max(0, xy_sum-board_size+1)  ,min(board_size,xy_sum+1)):
            x = xy_sum-y
            coord_list.append( [x,y] )
    return coord_list
    

def coord_value(coord, board):
    value = 0
    pile = board[coord[0]][coord[1]].strip()
    
    # 1. Add value for Capstones, Walls, and flats
    # The values as assigned make it possible to read off the composition of the pile.
    # This could possible be done more efficiently.
    if "Ca" in pile:
        value += 60000
        pile = pile[2:]
    elif "Cb" in pile:
        value += 50000
        pile = pile[2:]
    elif "Wa" in pile:
        value += 40000
        pile = pile[2:]
    elif "Wb" in pile:
        value += 30000
        pile = pile[2:]
    
    # 2. Add value for Flats
    value += 100 * pile.count('a')
    value += 1 * pile.count('b')
    
    return value

def anyduplicates(thelist):
    seen = []
    for x in thelist:
        if x in seen: 
            return True
        seen.append(x)
    return False

# This is ugly, but I'm getting weird issues where new_board=board[:] isn't copying the board, it is just making new_board a pointer for board. I think it has to do with board[:] being thought of as [board[0], board[1]], but I don't know.
def remove_bottom_layer(board):
    size = len(board)
    new_board = ['']*size
    for i in range(size):
        new_board[i]=board[i][:]
    #print('new board', new_board)
    for x in range(size):
        for y in range(size):
            new_board[x][y] = new_board[x][y][:-1]
            #print('now is', new_board,board)
    return new_board


##-------------------------- + Normalizing Boards + ---------------------------

def find_normal_orientation(board_state):
    board_size = len(board_state)
    
    # 1. Make a list of all the possible orientations.
    board_list = ['']*8
    for i in range(8):
        # First flip on the letter axis first to obtain all the odd boards
        if i % 2 ==1:
            board_list[i] = rotate_board_n( flipped_board_let(board_state) , -(i//2))
        else:
            board_list[i] = rotate_board_n( board_state , -(i//2))
        #print("\n", "-"*40, '\n i=', i)
        #[print(row) for row in board_list[i]]
        
    # 2. Remove any duplicate boards, if there are any
    candidate_list = [0,1,2,3,4,5,6,7]
    if anyduplicates(board_list):
        for board_num in range(8-1, 0-1, -1):
            if board_list[:board_num].count(board_list[board_num])>0:
                #print('Found a duplicate', board_num)
                candidate_list.pop(board_num)
                #print('The candidate list is now', candidate_list)
    
    # 3. Keep only the boards that are the heaviest.
    coord_list = build_diagonal_coord_list(board_size)
    for coord in coord_list:
        #print('checking', coord_to_tile(coord))
        maxseen=0
        candidates_to_keep = []
        
        # 4. Go through each tile (following the diagonal path described above), and remove any boards which do not have as many stones as the other boards (Not the actual tile count, but value at that tile.)
        for i in range(len(  candidate_list)-1,0-1, -1  ):
            candidate = candidate_list[i]
            c_value = coord_value(coord, board_list[candidate])
            #print("\tBoard", candidate, "scored", c_value, end='\t')
            
            # 5. If bigger value is found, drop all previous candidates
            if c_value > maxseen:
                maxseen = c_value
                candidates_to_keep = [candidate]
                #print('\tnew max of', maxseen, end='\t')
            # 6. If an equally large value is found, keep it.
            elif c_value == maxseen:
                candidates_to_keep.append(candidate)
                #print('\tadded', candidate, end='\t')
            #print('\t',candidates_to_keep,'remain')
        
        # 7. When checking values at the next tile, only keep candidates which have had maximal values so far.
        candidate_list = candidates_to_keep[:]
        #print("\tAfter finishing tile", coord_to_tile(coord), "the candidate list is ", candidate_list)
        
        # 8. Once there is only one candidate left, that is the corrent orientation for the board.
        if len(candidate_list)==1:
            #print('about to return', candidate_list[0])
            return candidate_list[0]
    
    # 9. For any normal board, that should have yielded a unique board orientation. However, it is possible that that two orientations have the same value at every tile, but are not the same, since the stack ordering could be different. For example, the 2x2 board"
    # [-, ba]
    # [ab, -]
    # has 4 unique orientations, but two of them will satisfy the normalization so far.
    
    # In that case, to deal with the composition of the stacks, simply slice off the bottom layer and find the orientation for that. This procedure will always return a unique orientation.
    retval = find_normal_orientation(remove_bottom_layer(  board_state  ))
    #print(retval, '='*20)
    return retval
    
        
                            
def normalize_board(board_state):
    orientation = find_normal_orientation(board_state)
    normal_board = board_state[:]
    if orientation % 2 ==1:
        normal_board = rotate_board_n( flipped_board_let(board_state) , -(orientation//2))
    else:
        normal_board = rotate_board_n( board_state , -(orientation//2))    
    return normal_board
    

## And Finally
##-------------------------- + Normalizing Moves + ----------------------------

def normalize_moves(move_string, plies, board_size):
    board_state = build_board_from_moves(move_string, plies, board_size)
    orientation = find_normal_orientation(board_state)
    
    if orientation % 2 ==1:
        normal_move_string = rotate_move_string( flipped_move_string_let(move_string, board_size), board_size , -(orientation//2))
    else:
        normal_move_string = rotate_move_string( move_string, board_size, -(orientation//2))
        
    return normal_move_string
        
    




#make_database_from_reddit_ELO_file()

# Code for making server notation readable and comparable with PTN

# c = "<server code>"
# c = c.split(',')
# for i in range(0,len(c),2):
#     print(floor(i/2)+1,c[i],"\t",c[i+1])
#  
#  



#SELECT       `nboard003`
    #FROM     `analyze_5_3_1400_9000_True_True_2016-04-23_2099-01-01_10_False`
    #GROUP BY `nboard003`
    #ORDER BY COUNT(*) DESC
    #LIMIT    10;
# SELECT SUM(score) FROM `analyze_5_3_1400_9000_True_True_2016-04-23_2099-01-01_10_False` /*WHERE nboard003="[('a', '', '', '', ''), ('', '', '', '', ''), ('', '', 'a', '', ''), ('', '', '', '', ''), ('b', '', '', '', '')]"*/




#/*SELECT * FROM games WHERE notation LIKE 'P A5,P E5%' OR notation LIKE 'P E5,P A5%' OR notation LIKE 'P E1,P A1%' OR notation LIKE 'P A1,P E1%'; */ /*  < 4927 >This counts the SAME corner HORIZONTAL*/
#/*SELECT * FROM games WHERE notation LIKE 'P A5,P A1%' OR notation LIKE 'P A1,P A5%' OR notation LIKE 'P E1,P E5%' OR notation LIKE 'P E5,P E1%'; */    /* < 3909 >  This counts the SAME corner VERTICAL*/

# SELECT * FROM games WHERE notation LIKE 'P A1,P E5%' OR notation LIKE 'P E5,P A1%' OR notation LIKE 'P E1,P A5%' OR notation LIKE 'P A5,P E1%';  /*  < 7063 >This counts the OPPOSITE corners */


#/*SELECT MAX(date) FROM  games;*/
#/*SELECT MIN(date) FROM  games;*/
#SELECT * from games where date = 1457864605596

#Select * from games Where player_white NOT IN ('AlphaTakBot_5x5', 'BeginnerBot', 'IntuitionBot', 'ShlktBot', 'TakkerBot', 'TakkerusBot', 'TakticBot', 'TakticianBot', 'TakticianBotDev', 'alphabot', 'alphatak_bot', 'alphatak_bot1', 'antakonistbot', 'cutak_bot', 'cutak_bot', 'takkybot') and player_black NOT IN ('AlphaTakBot_5x5', 'BeginnerBot', 'IntuitionBot', 'ShlktBot', 'TakkerBot', 'TakkerusBot', 'TakticBot', 'TakticianBot', 'TakticianBotDev', 'alphabot', 'alphatak_bot', 'alphatak_bot1', 'antakonistbot', 'cutak_bot', 'cutak_bot', 'takkybot') and whiteELO>1600 and blackELO>1600 and size=6 and result like '%-0'


##=============================================================================
##=============================================================================
##=============== ------------- Driver functions ------------- ================
##=============================================================================
##=============================================================================

def calculate_FPA(database, table, sizelist = [5,6,7,8] , minELO=1600, maxELO=9000,  excludebots=True):
    conn = sqlite3.connect(database) 
    c = conn.cursor()
    

    if type(sizelist) is int:
        sizelist = '(' + str(sizelist) + ')'
    elif len(sizelist) == 1:
        sizelist = '(' + str(sizelist[0]) + ')'
    else:
        sizelist= str( tuple(sizelist) ) # Just making the [] in to ()
        
    
    bottuple = str(tuple(botlist))
    botstring = 'player_white NOT IN' + bottuple + ' and player_black NOT IN ' + bottuple
    
    
    
    query = 'SELECT * from ' + table + ' WHERE whiteELO > ' + str(minELO) + ' and blackELO > ' + str(minELO) + ' and blackELO < ' + str(maxELO) + ' and blackELO < ' + str(maxELO) + ' and size IN ' + sizelist +  (' and ' + botstring)*excludebots
    
    print(query + 'and result LIKE "%-0"')
    c.execute(query + 'and result LIKE "%-0"')
    whitewins = len(c.fetchall())
    print('Counted', whitewins, 'white wins')
    
    c.execute(query + 'and result LIKE "0-%"')
    blackwins = len(c.fetchall())
    print('Counted', blackwins, 'black wins')
    
    whitepercent = whitewins/(whitewins + blackwins)//.0001/100
    print('White: ' + str(whitepercent) + '   Black: ' + str(100-whitepercent))
    conn.commit()
    c.close()
    conn.close() 
    print("done")
    
    return FPA

##=============================================================================
##=============================================================================
##=========== ---------- Scripts that run the program ---------- ==============
##=============================================================================
##=============================================================================
                         
##----------------------- + Getting Everything Ready + ------------------------



def setup():
    makegamesdbbackup()
    makeopeningsdb()
    add_ELOs_all_dates()
    add_ply_counts(mydb, 'games')
    delete_bad_games(mydb, 'games')
    add_ELO_and_games_played_to_games(mydb, 'games', True) # This also adds whether or not each player is a bot
    #add_scores_to_table(mydb, 'games', True)
    #cornerizegames()   # This would just make the openings easier to sift through by hand.
    revertgamesdb()
    print(('='*60+'\n')*5, ' - - step up complete - - '*4)
    
    
def main():
    print("\n\n Welcome to SultanPepper's opening analyizer. This script will take the PlayTak.com games database and analyze which openings have been the most sucessful.\n")
    if not os.path.isfile('openingsdb.db'):
        print("Looks like this is the first time this script has been run in this location. It'll take a minute or two to set everything up.")
        setup()
        shouldresetup = False
    else:
        shouldresetup = get_binary_choice("Would you like to recompute ELOs and update the list of games? (Do this if you've just downloaded the new games_anon database from PlayTak.com)")
     
    if shouldresetup:
        setup()
    
    settingslist = ask_settings() # returns [size, plycount, minELO, maxELO, bothmeetELO, includebots, startdate, enddate]
    
    # There is definitely a faster way to do these variable assignments.
    size       = settingslist[0]
    plycount   = settingslist[1]
    minELO     = settingslist[2]
    maxELO     = settingslist[3]
    bothmeetELO  = settingslist[4]
    includebots  = settingslist[5]
    startdate  = settingslist[6]
    enddate    = settingslist[7]
    
    create_table_from_settings(settingslist, mydb)
    tablename = make_table_name(settingslist)
    
    print("The FPA for these settings is:", calculate_FPA(mydb, tablename, sizelist = [5,6,7,8] , minELO, maxELO,  !includebots) )
    add_norm_moves_and_board(mydb, tablename, plycount, True)
    aggregate_opening_boards(mydb, tablename, settingslist)
    
    




# game 48648
#m0 = "P A5"
#m1 = "P A1,P A2,P B2,P B1,M A1 A2 1,M B2 B1 1"
#m2 = "P E1,P E5,P D5,P C4,P C5,P B5,P D4,P D3,P E4,P C3,P B4 C,P A5,P A4,M B5 C5 1,M D5 C5 1,M C4 D4 1,P D5,M A5 A4 1,P A5,P B5 C,M C5 C3 1 2,P C5,M D5 D4 1,M D3 D4 1,M E4 D4 1,P D3 W,M D4 E4 4,M D3 D4 1,M E4 E2 2 2,P D3,P D5,P D2,P E4,M D2 E2 1,M C3 D3 3,M D4 D3 2,M A5 A4 1,M D3 D5 1 4,M E3 D3 2,M E2 E4 1 2,M B4 C4 1,M D4 D3 1,M E5 E4 1,M E3 E4 1,M C4 E4 1 1,M D5 D4 3,P E5,P E3 W,M E4 E5 5,M D3 B3 1 2,M E5 C5 1 4,P D2,M C5 C3 3 2,P B4,P A3,P B2,M C3 B3 3,P C5,M B3 D3 1 4,P B3,M A3 B3 1,P E2,P A3,M B2 B3 1,M A3 B3 1,M B4 A4 1,M D5 C5 2,M B5 C5 1,M C4 A4 1 2,M B4 A4 1,P B4,M A4 A1 2 1 2,M B3 A3 2,M A4 A3 2,M B3 A3 2,M A2 A3 1,P B3,M C5 C2 1 1 2,M D3 D2 5,P C1,M D5 C5 1,P B1,P D1 W,P B5,M C5 C4 1,P A2"

#b0 = build_board_from_moves(m0, -1,7)
#b1 = build_board_from_moves(m1, -1,2)
#b2 = build_board_from_moves(m2, -1,5)
#n0 = find_normal_orientation(b0)

