import discord
from discord.ext import commands,tasks

import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen
from state import GuildState
class Meme(commands.Cog):
    ''':clap: Memes are a part of our culture.'''

    def __init__(self, client):
        self.client = client
       
        self.a_meme.start()

    def log(self, msg):  # ! funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    def cog_unload(self):
        self.a_meme.cancel()

    @commands.command()
    async def meme(self,ctx,subreddit = "memes", amount = 1,types = "hot"):
        '''Get some fresh memes, you insolent prick.'''
        
        reddit = gen.reddit
        subr = reddit.subreddit(subreddit)
        if types.lower() == "hot":                  #* Checks no stickied
            memes=[]
            i=1
            while len(memes) < amount:
                x=[]
                for j in subr.hot(limit=i):
                    x+=[j]
                x=x[-1]
                if not x.stickied:
                    memes += [x]
                i+=1

                        
        elif types.lower() == "top":
            memes=[]
            i=1
            while len(memes) < amount:
                x=[]
                for j in subr.top(limit=i):
                    x+=[j]
                x=x[-1]
                if not x.stickied:
                    memes += [x]
                i+=1
        elif types.lower() == "new":
            memes=[]
            i=1
            while len(memes) < amount:
                x=[]
                for j in subr.new(limit=i):
                    x+=[j]
                x=x[-1]
                if not x.stickied:
                    memes += [x]
                i+=1
        elif types.lower() == "controversial":
            memes=[]
            i=1
            while len(memes) < amount:
                x=[]
                for j in subr.controversial(limit=i):
                    x+=[j]
                x=x[-1]
                if not x.stickied:
                    memes += [x]
                i+=1
        elif types.lower() == "rising":
            memes=[]
            i=1
            while len(memes) < amount:
                x=[]
                for j in subr.rising(limit=i):
                    x+=[j]
                x=x[-1]
                if not x.stickied:
                    memes += [x]
                i+=1
        else:
            await ctx.send("No Boi, I only see 'Hot','Top','New'.'Controversial','Rising'.")
            return

        for submissions in memes:
            meh = discord.Embed(
                    title = submissions.title, url = submissions.shortlink,
                    colour = discord.Colour.orange()
                )
            meh.set_image(url=submissions.url)
            meh.set_author(name = f"u/{submissions.author}" , icon_url=submissions.author.icon_img)
            meh.add_field(name = '~~Spanks~~ Updoots', value = f"{round(submissions.ups/1000,1)}k" , inline = True)
            meh.add_field(name = 'Subreddit', value = f"r/{subreddit}" , inline = True)
            
            meh.set_thumbnail(url = subr.icon_img)


            
            await ctx.send(embed = meh)


    #* AUTOMEME
    @tasks.loop(minutes = 30)
    async def a_meme(self):
        limit = 5       
        reddit = gen.reddit
        for sr in gen.subreddits:
            #! GETS MEMES AND CHECK IF SHOWN
            
            subreddit = reddit.subreddit(sr)
            hot_memes = subreddit.hot(limit=limit)
            meme_info = gen.db_receive("meme")
            
            if sr in meme_info:
                sub_info = meme_info[sr]
            else:
                meme_info[sr]={"total":[] , "unshowed":[] }
                sub_info = meme_info[sr]   
    
            for submission in hot_memes:
                if not submission.stickied:
                    
                    if str(submission) not in sub_info["total"]:
                        
                        sub_info["total"].append(str(submission))
                        sub_info["unshowed"].append(str(submission))
            
            gen.db_update("meme",meme_info)
       
        #! MAKE SUBMISSION EMBED
        meme_info = gen.db_receive("meme")

        for sub_name in meme_info:
            sub_info = meme_info[sub_name]
            for submissions in sub_info["unshowed"]:
                subr = reddit.subreddit(sub_name)
                submissions = reddit.submission(submissions)
                meh = discord.Embed(
                    title = submissions.title, url = submissions.shortlink,
                    colour = discord.Colour.orange()
                )
                meh.set_image(url=submissions.url)
                meh.set_author(name = f"u/{submissions.author}" , icon_url=submissions.author.icon_img)
                meh.add_field(name = '~~Spanks~~ Updoots', value = f"{round(submissions.ups/1000,1)}k" , inline = True)
                meh.add_field(name = 'Subreddit', value = f"r/{sub_name}" , inline = True)
                
                meh.set_thumbnail(url = subr.icon_img)

                for guild in self.client.guilds:       
                    channel = GuildState(guild).auto_meme_channel
                    if channel is None:
                        continue        
                    await channel.send(embed = meh)

        #! CLEARING UNSHOWED
       

        for sub_info in meme_info:
            sub_info = meme_info[sub_info] 
            sub_info["unshowed"].clear()
        
        gen.db_update("meme",meme_info)
        #! CLEANING MEMES
        for sub_info in meme_info:
            sub_info = meme_info[sub_info]
            tot=len(sub_info["total"])
            req=limit*10
            if tot>req:
                for i in range(req,tot):
                    sub_info["total"].pop(0)
                gen.db_update("meme",meme_info)

  
def setup(client):
    client.add_cog(Meme(client))
    
