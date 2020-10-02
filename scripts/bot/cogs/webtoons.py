import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands
from webtoon import Webtoon, Days, Genres
from random import choice
from fuzzywuzzy import fuzz

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
        embed.add_field(name="Status", value=webtoon.status.replace("UP", "UP ").lower().capitalize()) if webtoon.status.startswith("UP") else embed.add_field(name="Status", value=webtoon.status.lower().capitalize())
        embed.add_field(name="Last Updated", value=webtoon.last_updated)
        
        return embed
    
    @commands.group()
    async def webtoon(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.webtoon)
     
    @webtoon.command(name="name")
    async def webtoon_name(self, ctx, *, query):
        webtoons = Webtoon.search(query)
        
        webtoons_to_ratio = {webtoon: fuzz.ratio(webtoon.title.lower(), query) for webtoon in webtoons}
        max_match = max(list(webtoons_to_ratio.values()))
        webtoon = None
        for _webtoon, ratio in webtoons_to_ratio.items():
            if ratio == max_match:
                webtoon = _webtoon
        
        embed = self.make_webtoon_embed(webtoon)
        
        await ctx.send(embed=embed)
        
    @webtoon.command(name="search")
    async def webtoon_search(self, ctx, *, query):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        reactions = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}
                
        webtoons = Webtoon.search(query)
        
        if len(webtoons) == 1:
            embed = self.make_webtoon_embed(webtoons[0])
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(title=f"Search for '{query}' returned the following", color=discord.Colour.red())
        
        description = ""
        for index, webtoon in enumerate(webtoons):
            description += f"{index + 1}. [{webtoon.title + ' `By ' + webtoon.author + '`'}]({webtoon.url})\n\n"
        
        embed.description = description
        
        embed_msg = await ctx.send(embed=embed)
        
        self.client.loop.create_task(reactions_add(embed_msg, list(reactions.keys())[:len(webtoons)]))
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=30, check=lambda reaction, user: user == ctx.author and reaction.message.id == embed_msg.id and str(reaction.emoji) in reactions.keys())
            except TimeoutError:
                await ctx.send(f">>> I guess no ones wants any webtoons")
                await embed_msg.delete()

                return None

            else:
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)
                await embed_msg.delete(delay=1)
                
                num = reactions[str(reaction)]
                webtoon = webtoons[num - 1]
                embed = self.make_webtoon_embed(webtoon)
                await ctx.send(embed=embed)
                return
        
    @webtoon.command()
    async def genre(self, ctx, *, query):
        logic = {
        ("drama",) : Genres.DRAMA,
        ("fantasy", "fan") : Genres.FANTASY,
        ("comedy", "com") : Genres.COMEDY,
        ("action",) : Genres.ACTION,
        ("slice of life", "sol") : Genres.SLICE_OF_LIFE,
        ("romance", "rom") : Genres.ROMANCE,
        ("superhero",) : Genres.SUPERHERO,
        ("sci fi", "science fiction") : Genres.SCI_FI,
        ("thriller",) : Genres.THRILLER,
        ("supernatural",) : Genres.SUPERNATURAL,
        ("mystery",) : Genres.MYSTERY,
        ("sports",) : Genres.SPORTS,
        ("historical", "history") : Genres.HISTORICAL,
        ("heartwarming", "warming") : Genres.HEARTWARMING,
        ("horror",) : Genres.HORROR,
        ("informative", "info") : Genres.INFORMATIVE
    }
        query = query.lower()
        
        genre = None
        for i, j in logic.items():
            if query in i:
                genre = j
        if genre is None:
            await ctx.send("I dont think that genre exists.")
            return
                
        result = list(Webtoon.get_webtoons_by_genre(genre))
        webtoon = choice(result)
        embed = self.make_webtoon_embed(webtoon)
        await ctx.send(embed=embed)
        
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