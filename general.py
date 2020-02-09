import praw
import os
import discord
from colorama import init, Fore, Back, Style
import json
import git
from git import Repo
from datetime import datetime

server_id = 617021917622173747
awoo_id = 640862189288423425
gen_id = 617021918071226369

roles = ['Prostitute', 'Rookie', 'Adventurer', 'Player', 'Hero']

status = ["Saksham's Son", 'Is Mayank', 'Who Is Gay']

subreddits = ["memes", "dankmemes", "cursedcomments", "animemes"]

cog_colours = {"exp":"cyan", "music":"green"}

epic = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


admin_role_id = 632906375839744001
MEE6_disc = 4876


level_Rookie = 5
level_Adventurer = 10
level_Player = 25
level_Hero = 50
level_CON = 85

reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    username=os.environ.get("REDDIT_USERNAME"),
    password=os.environ.get("REDDIT_PASSWORD"),
    user_agent="FuqU"
)


def commit(sp_msg: str()):
   
    os.rename("./Database/gothy", "./Database/.git")

    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y %H:%M:%S")
    commit_msg = f"Database updated - {date_time} -> {sp_msg} "
    g = git.Git("./Database")
    try:
        g.execute(f'git add --all')
        g.execute(f'git commit -m "{commit_msg}" ')
        g.execute("git push --force")
    except:
        print("Commit upto the point. Can't commit.")
        done = False
    else:
        done = True
            
    os.rename("./Database/.git", "./Database/gothy")
    return done


def reset():
    os.rename("./Database/gothy", "./Database/.git")

    g = git.Git("./Database")
    

    try:
        g.execute("git stash")
        g.execute("git stash drop")
    except:
        pass
 
    repo = Repo("./Database/.git")
    origin = repo.remote(name="origin")
    origin.pull()

 
    print("Pulled Database Successfully")
    os.rename("./Database/.git", "./Database/gothy")
 

def permu(strs):
    if len(strs) == 1:
        if strs.isalnum():
            return [strs.lower(), strs.upper()]
        else:
            return[strs]
    else:
        output = []
        f = strs[0]
        l = strs[1:]
        for st in permu(l):
            if f.isalnum():
                output.append(f.lower() + st)
                output.append(f.upper() + st)
            else:
                output.append(f+st)
        return output


def error_message(error, color="white"):
    color: str()

    init(convert=True)
    cmd = f"print(Fore.BLACK + Back.{color.upper()} + str(error))"
    exec(cmd)
    print(Fore.WHITE+Back.BLACK)


def db_receive(name):
    with open(f'./Database/{name}.json', 'r') as f:
        return json.load(f)


def db_update(name, db):
    with open(f'./Database/{name}.json', 'w') as f:
        json.dump(db, f, indent=4)


def new_entry(name, disc):
    mem_info = db_receive("inf")
    mem_info[disc] = {"name": name, "messages": 0,
                      "level": "Prostitute", "coins": 500}
    db_update("inf", mem_info)
