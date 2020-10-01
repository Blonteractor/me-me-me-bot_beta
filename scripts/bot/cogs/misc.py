import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands
from discord.utils import get
from lyricsgenius.song import Song
import requests,json
import re
import youtube_dl
import aiohttp

import asyncio
import general as gen
from state import TempState

import lyricsgenius
genius = lyricsgenius.Genius(os.environ.get("LYRICS_GENIUS_KEY"))
genius.verbose = False

class Misc(commands.Cog):
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
    DPATH = os.path.join(
        os.path.dirname(__file__), '../../../cache.bot/Download')
    DPATH = os.path.abspath(DPATH)
   
    def __init__(self, client):
        self.client = client      

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
    
    def log(self, msg):                     # funciton for logging if developer mode is on
        debug_info = gen.db_receive("var")
        try:
            debug_info["cogs"][self.qualified_name]
        except:
            debug_info["cogs"][self.qualified_name] = debug_info["DEV"]
            gen.db_update("var",debug_info)

        if debug_info["cogs"][self.qualified_name] == 1:
            if self.qualified_name in gen.cog_colours:
                return gen.error_message(msg, gen.cog_colours[self.qualified_name])
            else:
                return gen.error_message(msg, gen.cog_colours["default"])


    # ? LYRICS
    @commands.command()
    async def lyrics(self, ctx: commands.Context):
        """Get lyrics to the currently playing song (or not, depends on the song)"""
        
        state = TempState(ctx.author.guild)

        queue = [x for x in state.queue if type(x) != str]
        vid = queue[0]
        song = genius.search_song(vid.title)
        if not song:
            await ctx.send("Can't Find lyrics. Try using choose-lyrics command.")
            return
        lyrics = song.lyrics

        embed = discord.Embed(title=f"LYRICS - {song.title}", 
                              url=song.url,
                              color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)

        embed_msg = await ctx.send(embed=embed)

        await self.client.get_cog("Queue").embed_pages(ctx=ctx, _content=lyrics, embed_msg=embed_msg, wait_time=120)
        
    @commands.command(name="choose-lyrics",aliases = ['clyrics'])
    async def clyrics(self, ctx: commands.Context,query = None):
        """Get the lyrics not ANY(susceptible to terms and conditions) song."""
        state = TempState(ctx.author.guild)
        if not query and state.queue == []:
            await ctx.send("no song sad lyf")
        elif not query:
            query = state.queue[0].title
        
        title = query
        response = genius.search_genius_web(title)

        hits = response['sections'][0]['hits']
        sections = sorted(response['sections'],
                                key=lambda sect: sect['type'] == "song",
                                reverse=True)
                
                
        hits =[hit for section in sections for hit in section['hits'] if hit['type'] == "song"][0:5]
        if hits ==[]:
            await ctx.send("Can't Find lyrics. Use different name of the song.")
            return
       
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        wait_time = 60

        reactions = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}

        embed = discord.Embed(title="Search returned the following",
                              color=discord.Colour.dark_green())

        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=self.music_logo)

        embed_msg = await ctx.send(embed=embed)

        
        for index, result in enumerate(hits):
            result = result["result"]
            embed.add_field(name=f"*{index + 1}.*",
                            value=f"**{result['title_with_featured']} - {result['primary_artist']['name']}**", inline=False)

        await embed_msg.edit(content="", embed=embed)

        self.client.loop.create_task(reactions_add(embed_msg, list(reactions.keys())[:len(hits)]))
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time,
                                                             check=lambda reaction, user: user == ctx.author and reaction.message.id == embed_msg.id)
            except TimeoutError:
                await ctx.send(f">>> I guess no ones wants to see some sweet lyrics.")
                await embed_msg.delete()

                return None

            else:
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.keys():
                    await embed_msg.delete(delay=3)
                    hit = hits[reactions[str(reaction.emoji)] - 1]  
                                      
                    song_info =hit["result"]
                    lyrics = genius._scrape_song_lyrics_from_url(song_info['url'])
                    
                    song = Song(song_info,lyrics)
                    embed = discord.Embed(title=f"LYRICS - {song.title} - {song.artist}",  # TODO make a function
                              url=song.url,
                              description="",
                              color=discord.Colour.blurple())
                    
                    embed.set_author(name="Me!Me!Me!",
                                        icon_url=self.client.user.avatar_url)
                    embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                                        icon_url=ctx.message.author.avatar_url)

                    embed_msg = await ctx.send(embed=embed)

                    await self.client.get_cog("Queue").embed_pages(ctx=ctx, _content=lyrics, embed_msg=embed_msg, wait_time=120)

    # ? SONG_INFO

    @commands.command(name="song-info", aliases=["sinfo", "sf"])
    async def song_info(self, ctx, *, query):
        """Gets info about a song, who could have guessed."""
        result = await self.client.get_cog("Play").searching(ctx, query)
        embed = discord.Embed(title=f"{result.title} ({result.duration}) - {result.uploader}",
                              url=result.url,
                              description=result.description,
                              color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=result.thumbnail)

        embed.add_field(name="Date of Upload", value=result.date)
        embed.add_field(name="Views", value=result.views)
        embed.add_field(name="Likes/Dislikes",
                        value=f"{result.likes}/{result.dislikes}")
        await ctx.send(embed=embed)

    # ? PLAYLIST_INFO
    @commands.command(name="playlist-info", aliases=["plinfo", "pf"])
    async def playlist_info(self, ctx, *, query):
        """Gets info about a playlist, who could have guessed."""
        
        result = await self.client.get_cog("Play").searching(ctx, query, False)

        embed = discord.Embed(title=f"{result.title} ({result.duration}) - {result.uploader}",
                              url=result.url,
                              color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=result.thumbnail)

        embed.add_field(name="Date of Upload", value=result.date)
        embed.add_field(name="No of entries", value=len(
            result.entries), inline=False)
        for index, vid in enumerate(result.entries):
            embed.add_field(
                name=f"**{index +1}. {vid[2]} ({vid[1]})**", value="** **")

        await ctx.send(embed=embed)

    # ? DOWNLOAD
    @commands.command()
    async def download(self, ctx, *, query = None):
        '''Downloads a song for you, so your pirated ass doesn't have to look for it online.'''
        
        if query:
            if "http" in query:
                if "www.youtube.com" in query:
                    split_list = re.split("/|=|&", query)
                    if "watch?v" in split_list:
                        vid = self.client.get_cog("Play").ytvid(split_list[split_list.index("watch?v")+1], requested_by=ctx.author.name)
            else:
                vid = await self.client.get_cog("Play").searching(ctx, query)
        else:
            vid = TempState(ctx.guild).queue[0]
        if not os.path.exists(self.DPATH):
            os.makedirs(self.DPATH)
        async with aiohttp.ClientSession() as cs:
            async with cs.get(vid.audio_url) as r:

                data = await r.read()
                filename = f"{self.DPATH}\\{vid.id}.{vid.ext}"
                
                with open(filename, 'wb+') as temp:
                    temp.write(b"")
                    temp.write(data)

                file = discord.File(filename, filename=f'{vid.title}.mp3')

                try:
                    await ctx.send(file=file)
                except discord.Forbidden:
                    await ctx.send("Song you requested was too mega, only files less than 8MB can be sent.")
            
                os.remove(filename)

    # ? EXPORT

    @commands.command()
    async def export(self, ctx, isFull="queue"):
        """Convert your playlist to text, gives a pastebin url"""
        
        if not(isFull.lower() == "full" or isFull.lower() == "queue" or isFull.lower() == "q"):
            await ctx.send("only full or q or queue")
            return 
        state = TempState(ctx.guild)
        if isFull.lower() == "full":
            queue = state.full_queue
        else:
            queue = [x for x in state.queue if type(x) != str]

        for i in range(len(queue)):
            queue[i] = {"url": queue[i].url, "title": queue[i].title}
  
        url = "https://hastebin.com/documents"
        response = requests.post(url, data=json.dumps(queue))
        try:
            the_page = "https://hastebin.com/raw/" + response.json()['key']
            await ctx.send(f"Here is your page Master, {the_page}")
        except:
            await ctx.send(f"Cant export")

    # ? IMPORT
    @commands.command(name="import")
    async def _import(self, ctx, url):
        """Have your playlist saved as text, provide a pastebin url to play the playlist"""
        
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)

        response = requests.get(url)
        content = response.content.decode("utf-8")
        try:
            content = json.loads(content)
        except:
            await ctx.send("Please recheck your link.")
            return

        if type(content) != list:
            await ctx.send("Please recheck your link.")
            return

        for i in content:
            if type(i) != dict:
                await ctx.send("Please recheck your link.")
                return
            if "title" not in i or "url" not in i:
                await ctx.send("Please recheck your link.")
                return

        for i in content:
            query = i["url"]
            if "http" in query:
                if "www.youtube.com" in query:
                    split_list = re.split("/|=|&", query)
                    if "watch?v" in split_list:
                        vid = self.client.get_cog("Play").ytvid(split_list[split_list.index(
                            "watch?v")+1], requested_by=ctx.author.name)
                        state = TempState(ctx.author.guild)
                        state.queue +=[vid]
                        state.queue_ct +=[vid] 
                        if len(state.queue) == 1:
                            await self.client.get_cog("Play").player(ctx, voice)
                        

    @commands.command(name="generic-play", aliases=["gp", "genplay"])
    async def generic_play(self, ctx, url):
        """This commands tries its hardest to play any video (not just YouTube), provided the link"""
        
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        ydl_opts = {
            "quiet": True,
            "no_warnings": True            
        }
        try:
            info = youtube_dl.YoutubeDL(
                ydl_opts).extract_info(url, download=False)
        except:
            await ctx.send("cant play that")
            return
        need = ["id",
                "uploader",
                "upload_date",
                "title",
                "thumbnail",
                "duration",
                "description",
                "webpage_url",
                "view_count",
                "like_count",
                "dislike_count",
                "thumbnails",
                "format_id",
                "url",
                "ext"
                ]
      
        info2 = {}
        for i in need:
            if i in info:
                info2[i] = info[i]
            else:
                info2[i] = "0"
     
        try:
            
            vid = self.client.get_cog("Play").ytvid(info2["id"], info2, ctx.author.name)

            
            embed = discord.Embed(title=f"{vid.title} ({vid.duration}) - {vid.uploader}",
                                        url=vid.url,
                                        description=vid.description,
                                        color=discord.Colour.blurple())
            embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                            icon_url=ctx.message.author.avatar_url)
            embed.set_thumbnail(url=vid.thumbnail)

            embed.add_field(name="Date of Upload", value=vid.date)
            embed.add_field(name="Views", value=vid.views)
            embed.add_field(name="Likes/Dislikes",
                            value=f"{vid.likes}/{vid.dislikes}")
            await ctx.send(embed=embed)

        
            if TempState(ctx.guild).queue == []: 
                TempState(ctx.guild).queue += [vid]
                await self.client.get_cog("Play").player(ctx, voice)
            else:
                TempState(ctx.guild).queue += [vid]
        except:
            await ctx.send("cant play that")
            return

def setup(client):
    client.add_cog(Misc(client))
