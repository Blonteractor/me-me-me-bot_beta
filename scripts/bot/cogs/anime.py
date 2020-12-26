import sys
import os

from discord.ext.commands.cooldowns import BucketType
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
import asyncio
from random import choice
from discord.ext import commands
from MAL import Anime, Manga, MALConfig
from dotenv import load_dotenv
load_dotenv()

class Weeb(commands.Cog):
      
    config = MALConfig(
    client_id = os.environ.get("MAL_CLIENT_ID"),
    client_secret = os.environ.get("MAL_CLIENT_SECRET"),
    access_token = os.environ.get("MAL_ACCESS_TOKEN"),
    refresh_token = os.environ.get("MAL_REFRESH_TOKEN")
    )
    
    MAL_LOGO = "https://upload.wikimedia.org/wikipedia/commons/7/7a/MyAnimeList_Logo.png"
    
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        
    @staticmethod
    def format_list(l) -> str:
        result = ""
        for i, j in enumerate(l):
            if not i == len(l) - 1:
                result += f"`{j}` | "
            else:
                result += f"`{j}`"
                
        return result
    
    async def weeb_embed(self, ctx, search_message, weeb_abc, type):
        embed_1 = discord.Embed(title=f"{weeb_abc.english_title} `{weeb_abc.japenese_title}`", url=weeb_abc.url, color=discord.Colour.red())
        embed_1.set_author(name="Me!Me!Me!", icon_url=self.client.user.avatar_url)
        embed_1.set_thumbnail(url=Weeb.MAL_LOGO)
        embed_1.set_image(url=weeb_abc.cover)
        
        description = weeb_abc.synopsis + "\n\n" + weeb_abc.background
        
        if len(description) > 2048:
            embed_1.description = description[:2044] + "..."
        else:
            embed_1.description = description
        
        embed_2 = discord.Embed(title=f"{weeb_abc.english_title} `{weeb_abc.japenese_title}`", url=weeb_abc.url, color=discord.Colour.red())
        embed_2.set_author(name="Me!Me!Me!", icon_url=self.client.user.avatar_url)
        embed_2.set_thumbnail(url=Weeb.MAL_LOGO)
        embed_2.set_image(url=choice(weeb_abc.pictures))
        
        embed_2.add_field(name="Score", value=f"`{weeb_abc.score}`")
        embed_2.add_field(name="Rank", value = f"`{weeb_abc.rank}`")
        embed_2.add_field(name="Popularity", value = f"`{weeb_abc.popularity}`")
        
        if type == "anime":
            embed_2.add_field(name="Number of episodes", value = f"`{weeb_abc.number_of_episodes}`")
            embed_2.add_field(name="Season", value = f"`{weeb_abc.season}`")
            embed_2.add_field(name="Broadcast", value = f"`{weeb_abc.broadcast.capitalize()}`")
            embed_2.add_field(name="Studio(s)", value = self.format_list(weeb_abc.studios))
            embed_2.add_field(name="Age rating", value = f"`{weeb_abc.age_rating.upper()}`")                
        elif type == "manga":
            embed_2.add_field(name="Number of volumes", value = f"`{weeb_abc.number_of_volumes}`")
            embed_2.add_field(name="Number of chapters", value = f"`{weeb_abc.number_of_chapters}`")
            embed_2.add_field(name="Author(s)", value = self.format_list(weeb_abc.authors))
            
        embed_2.add_field(name="Release", value = f"`{weeb_abc.release_date}`")
        embed_2.add_field(name="End", value = f"`{weeb_abc.end_date}`")  
        embed_2.add_field(name="Status", value = f"`{weeb_abc.status.capitalize()}`")
        embed_2.add_field(name="Genres", value=self.format_list(weeb_abc.genres))
        
        embed_pages = [embed_1, embed_2]
        current_page = 0
        
        await search_message.edit(content="", embed=embed_1)
        
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        reactions = {"⬅" : "back", "➡" : "forward"}

        def reaction_check(reaction, user):
            return (not user.bot) and reaction.message.id == search_message.id and str(reaction) in reactions.keys()

        self.client.loop.create_task(reactions_add(search_message, reactions.keys()))
        
        while True:

            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60, check=reaction_check)
            except asyncio.TimeoutError:
                await search_message.clear_reactions()
                return
            else:
                reaction_response = reactions[str(reaction)]
                await search_message.remove_reaction(str(reaction.emoji), user)
                
                if reaction_response == "forward":
                    if not current_page == len(embed_pages) - 1:
                        current_page += 1
                    else:
                        current_page = 0
                
                elif reaction_response == "back":
                    if not current_page == 0:
                        current_page -= 1
                    else:
                        current_page = len(embed_pages) - 1
                        
                await search_message.edit(embed=embed_pages[current_page])
        
    @commands.command()
    @commands.cooldown(rate=3, per=4, type=BucketType.member)
    async def anime(self, ctx, *, query):
        result = list(Anime.search(query=query, limit=10, basic=True, config=Weeb.config))
        if len(result) == 0:
            await ctx.send(f"No anime of name `{query}` found.")
            return
        
        msg_content = "Respond with the index of the anime you want, 'c' to cancel\n"
        for index, anime in enumerate(result):
            anime_name = anime["name"]
            msg_content += f"{index + 1}. **{anime_name}**\n"
        
        search_message = await ctx.send(msg_content)
        
        def check(message) -> bool:
            return message.author == ctx.author and ((message.content.isdigit() or message.content[1:].isdigit()) or message.content.lower() == "c")
        
        the_chosen_id = None
        errors_commited = 0
        
        while True:
              
            if errors_commited >= 3:
                await search_message.edit(content="Bruh you are too retarded I give up")
                return
                
            try:
                response = await self.client.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("I got no response sadly, try refining your search term if you didn't find your anime.")
                return
            else:
                response_content = response.content.lower()
              
                if response_content == "c":
                    await search_message.edit(content="Command cancelled, try refining your search term if you didn't find your anime.")
                    
                    try:
                        await response.delete(delay=3)
                    except discord.Forbidden:
                        pass
                    
                    return
                
                elif int(response_content) <= 0:
                    await ctx.send("Respond with a natural number, should have been obvious enuff.")
                    errors_commited += 1
                    continue
                
                elif int(response_content) > len(result):
                    await ctx.send("I dont even have that many results bro, try again.")
                    errors_commited += 1
                    continue
                
                else:
                    the_chosen_id = result[int(response_content) - 1]["anime_id"]
                    
                    try:
                        await response.delete(delay=3)
                    except discord.Forbidden:
                        pass
                    
                    break
                
        found_anime = Anime(the_chosen_id, Weeb.config)
        await self.weeb_embed(ctx=ctx, search_message=search_message, weeb_abc=found_anime, type="anime")
        
    @commands.command()
    @commands.cooldown(rate=3, per=4, type=BucketType.member)
    async def manga(self, ctx, *, query):
        result = list(Manga.search(query=query, limit=10, basic=True, config=Weeb.config))
        if len(result) == 0:
            await ctx.send(f"No manga of name `{query}` found.")
            return
        
        msg_content = "Respond with the index of the manga you want, 'c' to cancel\n"
        for index, manga in enumerate(result):
            manga_name = manga["name"]
            msg_content += f"{index + 1}. **{manga_name}**\n"
        
        search_message = await ctx.send(msg_content)
        
        def check(message) -> bool:
            return message.author == ctx.author and ((message.content.isdigit() or message.content[1:].isdigit()) or message.content.lower() == "c")
        
        the_chosen_id = None
        errors_commited = 0
        
        while True:
                
            if errors_commited >= 3:
                await search_message.edit(content="Bruh you are too retarded I give up")
                return
                
            try:
                response = await self.client.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("I got no response sadly, try refining your search term if you didn't find your anime.")
                return
            else:
                response_content = response.content.lower()
                
                if response_content == "c":
                    await search_message.edit(content="Command cancelled, try refining your search term if you didn't find your manga.")
                    
                    try:
                        await response.delete(delay=3)
                    except discord.Forbidden:
                        pass
                    
                    return
                
                elif int(response_content) <= 0:
                    await ctx.send("Respond with a natural number, should have been obvious enuff.")
                    errors_commited += 1
                    continue
                
                elif int(response_content) > len(result):
                    await ctx.send("I dont even have that many results bro, try again.")
                    errors_commited += 1
                    continue
                
                else:
                    the_chosen_id = result[int(response_content) - 1]["manga_id"]
                    
                    try:
                        await response.delete(delay=3)
                    except discord.Forbidden:
                        pass
                    
                    break
                
        found_anime = Manga(the_chosen_id, Weeb.config)
        await self.weeb_embed(ctx=ctx, search_message=search_message, weeb_abc=found_anime, type="manga")
        
        

def setup(client):
    client.add_cog(Weeb(client))