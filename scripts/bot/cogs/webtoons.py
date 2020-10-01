import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands
from webtoon import Webtoon, Days, Genres
from random import choice

class Webtoons(commands.Cog):
    
    webtoon_logo = "https://upload.wikimedia.org/wikipedia/commons/0/09/Naver_Line_Webtoon_logo.png"
    site_url = "https://www.webtoons.com/en/"
    
    def __init__(self, client):
        self.client = client 
        self.client: commands.Bot
        
    def make_webtoon_embed(self, webtoon):
        embed = discord.Embed(title=webtoon.title, url=webtoon.url, color=discord.Colour.red())
        
        embed.set_author(name="Me!Me!Me!", icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=Webtoons.webtoon_logo)
        embed.description = webtoon.summary
        
        embed.add_field(name="Episodes", value=webtoon.length)
        embed.add_field(name="Genre", value=webtoon.genre)
        embed.add_field(name="Author", value=webtoon.author)
        embed.add_field(name="Likes", value=webtoon.likes)
        embed.add_field(name="Status", value=webtoon.status.replace("UP", "UP ")) if webtoon.status.startswith("UP") else embed.add_field(name="Status", value=webtoon.status)
        embed.add_field(name="Last Updated", value=webtoon.last_updated)
        
        return embed
    
    @commands.group()
    async def webtoon(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.webtoon)
     
    @webtoon.command(name="search")
    async def webtoon_search(self, ctx, *, query):
        webtoon = Webtoon.search(query)[0]
        
        embed = self.make_webtoon_embed(webtoon)
        
        await ctx.send(embed=embed)
        
    @webtoon.command()
    async def genre(self, ctx, query):
        result = list(Webtoon.get_webtoons_by_genre(query, limit=7))
        webtoon = choice(result)
        embed = self.make_webtoon_embed(webtoon)
        await ctx.send(embed)
        
    @webtoon.command()
    async def day(self, ctx, query):
        logic = {("mon", "monday"): Days.MONDAY, ("tues", "tuesday"): Days.TUESDAY, ("wed", "wednesday"): Days.WEDNESDAY, ("thurs", "thursday"): Days.THURSDAY, ("fri", "friday"): Days.FRIDAY, ("sat", "saturday"): Days.SATURDAY, ("sun", "sunday"): Days.SUNDAY}
        
        day = None
        for i, j in logic.items():
            if query in i:
                day = j
                query = i[-1]
        if day is None:
            await ctx.send("I dont think that day exists.")
            return
        
        result = list(Webtoon.get_webtoons_by_day(day))
        
        embed = discord.Embed(title=f"Webtoon releases on {query.capitalize()}", color=discord.Colour.red())
        
        description = ""
        for webtoon in result:
            description += f"● [{webtoon.title + ' `By ' + webtoon.author + '`'}]({webtoon.url})\n\n"
            
        embed.description = description
        embed.set_thumbnail(url=Webtoons.webtoon_logo)
        
        await ctx.send(embed=embed) 

def setup(client):
    client.add_cog(Webtoons(client))