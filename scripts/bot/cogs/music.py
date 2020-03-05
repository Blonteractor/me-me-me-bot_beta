import discord
from discord.utils import get
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks

from typing import List, Any
import shutil
from lxml import etree
import lxml
import re
import urllib.parse
import urllib.request
from asyncio import sleep, TimeoutError
import asyncio
from youtube_dl import YoutubeDL
import youtube_dl
import time as t
from os import system
import time
import lyricsgenius

import imp
import os

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
imp.load_source("Youtube", os.path.join(
    os.path.dirname(__file__), "../../others/Youtube.py"))
import general as gen
from Youtube import YoutubePlaylist, YoutubeVideo, driver


def vc_check():
    async def predicate(ctx):           # Check if the user is in vc to run the command
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if ctx.author not in voice.channel.members:
                await ctx.send(f"You either not in a VC or in a wrong VC. Join `{voice.channel.name}`")
                return False
            else:
                return True
        else:
            return False
    return commands.check(predicate)


genius = lyricsgenius.Genius(
    "pGaaH8g-CxAeF1qaQ2DeVmLnmp84mIciWU8sbGoVKQO_MTlHQW4ZoxYeP8db1kDO")
genius.verbose = False


class Music(commands.Cog):
    ''':musical_note: The title says it all, commands related to music and stuff.'''
    queue: List[Any] = [
    ]                                      # queue of the format [items,"playlist name",playlist items,"/playlist name",items]
    full_queue: List[Any] = []
    queue_ct: List[Any] = []
    full_queue_ct: List[Any] = []

    # variable used for looping song
    loop_song = False
    # variable used for skipping song
    skip_song = False
    # time for auto disconnect
    time_for_disconnect = 300
    
    # str of loading emoji
    loading_emoji = "<a:loading:683921845430648833>"

    # url of the image of thumbnail (vTube)
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
    juke_box_url = "https://media.discordapp.net/attachments/623969275459141652/680480864316030996/juke_box.jpg"

    time = 0
    QPATH = os.path.join(
        os.path.dirname(__file__), '../../../Queue')
    QPATH = os.path.abspath(QPATH)

    DPATH = os.path.join(
        os.path.dirname(__file__), '../../../Download')
    DPATH = os.path.abspath(DPATH)



   # * ------------------------------------------------------------------------------PREREQUISITES--------------------------------------------------------------------------------------------------------------



    def __init__(self, client):
        self.client = client
        self.auto_pause.start()             # starting loops for auto pause and disconnect
        self.auto_disconnector.start()
        self.juke_box.start()
        
    def cog_unload(self):
        driver.quit()

    def log(self, msg):                     # funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    # check if there is no one listening to the bot
    def disconnect_check(self, voice) -> bool:
        flag = False
        if voice and voice.is_connected():

            flag = True
            for user in voice.channel.members:
                if not user.bot:
                    flag = False
        return flag

    def join_list(self, ls) -> str:  # joins list
        return " ".join(ls)

    def queue_delete(self):     # Deleting Queue folder

        Queue_infile = os.listdir(self.QPATH)

        if Queue_infile:
            shutil.rmtree(self.QPATH)
            
    def to_pages():
        pass

    # * ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log("Check Failed for user in VC.")
        else:
            pass

    # * TASKS

    @tasks.loop(seconds=2)
    async def auto_pause(self):  # auto pauses the player if it no one is in the vc
        guild = self.client.get_guild(gen.server_id)
        awoo_channel = self.client.get_channel(gen.awoo_id)
        voice = get(self.client.voice_clients, guild=guild)

        if self.disconnect_check(voice):

            if voice.is_playing():
                self.log("Player AUTO paused")
                voice.pause()
                await awoo_channel.send(f"Everyone left `{voice.channel.name}`, player paused.")
                self.auto_resume.start()

    @tasks.loop(seconds=1)
    async def clock(self):
        self.time += 1

    @tasks.loop(seconds=2)
    # disconnect if player is idle for the disconnecting time provided
    async def auto_disconnector(self):
        guild = self.client.get_guild(gen.server_id)
        voice = get(self.client.voice_clients, guild=guild)

        for i in range(self.time_for_disconnect):
            if voice and not voice.is_playing():
                await asyncio.sleep(1)
            else:
                break
        else:
            await self.auto_disconnect()
            self.auto_resume.cancel()

    @tasks.loop(seconds=1)
    async def auto_resume(self):  # resumes the song if the user re-joins the vc
        guild = self.client.get_guild(gen.server_id)
        awoo_channel = self.client.get_channel(gen.awoo_id)
        voice = get(self.client.voice_clients, guild=guild)

        if voice and voice.is_paused() and not self.disconnect_check(voice):
            self.log("Music AUTO resumed")
            voice.resume()
            await awoo_channel.send(f"Looks like someone joined `{voice.channel.name}`, player resumed.")
            self.auto_resume.cancel()

    async def auto_disconnect(self):  # actual disconnecting code

        guild = self.client.get_guild(gen.server_id)
        voice = get(self.client.voice_clients, guild=guild)
        awoo_channel = self.client.get_channel(gen.awoo_id)

        await voice.disconnect()

        await awoo_channel.send(f"Nothing much to do in the vc so left `{voice.channel.name}`")
        self.log(f"Auto disconnected from {voice.channel.name}")
        self.queue.clear()

    @tasks.loop(seconds=1)
    async def juke_box(self):

        for guild in self.client.guilds:
            channel = discord.utils.get(guild.text_channels, name="juke-box")

            if not channel:
                channel = await guild.create_text_channel("juke-box")  

            else:
                async for msg in self.client.logs_from(channel):
                    await client.delete_message(msg)
                
            file = os.path.join(os.path.dirname(
                __file__), '../../../assets/icons/we_tube_logo.png')
            file = os.path.abspath(file)
            file = discord.File(file)

            await channel.send(file=file)

            reactions = {"⏯️": "play/pause", "⏹️": "stop", "⏮️": "previous",
                            "⏭️": "forward", "🔁": "loop", "🔀": "shuffle"}

            embed = discord.Embed(title="Not Playing Anything right now.",
                                    color=discord.Colour.from_rgb(0, 255, 255))

            embed.set_image(url=self.juke_box_url)
            embed_msg = await channel.send(embed=embed)
            embed_msg: discord.Message

            self.juke_box_embed = embed
            self.juke_box_embed_msg = embed_msg

            def check(reaction: discord.Reaction, user):
                return reaction.message.id == embed_msg.id

            async def reactions_add(message, reactions):
                for reaction in reactions:
                    await message.add_reaction(reaction)

            self.client.loop.create_task(
                reactions_add(embed_msg, reactions.keys()))

            loading_bar = await channel.send(f"0:00/0:00 - {':black_large_square:'*10}")
            loading_bar: discord.Message

            self.juke_box_loading = loading_bar

            queue_msg = await channel.send("__QUEUE LIST__")
            queue_msg: discord.Message

            self.juke_box_queue = queue_msg

            self.juke_box_channel = channel

            self.juke_box.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            self.juke_box_channel
        except:
            pass
        else:
            if message.channel == self.juke_box_channel:
                if message.author != self.client.user:

                    await message.delete()
                else:
                    if message.id != self.juke_box_loading.id and message.id != self.juke_box_queue.id:
                        await message.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        try:
            self.juke_box_channel
        except:
            pass
        else:
            if user != self.client.user and reaction.message.id == self.juke_box_embed_msg.id:
                reactions = {"⏯️": "play/pause", "⏹️": "stop", "⏮️": "previous",
                             "⏭️": "forward", "🔁": "loop", "🔀": "shuffle"}
                voice = get(self.client.voice_clients,
                            guild=reaction.message.guild)
                if voice:
                    if str(reaction.emoji) in reactions:
                        ctx = await self.client.get_context(reaction.message)
                        if reactions[str(reaction.emoji)] == "play/pause":
                            if voice.is_playing():
                                await ctx.invoke(self.client.get_command("pause"))
                            elif voice.is_paused():
                                await ctx.invoke(self.client.get_command("resume"))

                        elif reactions[str(reaction.emoji)] == "stop":
                            await ctx.invoke(self.client.get_command("stop"))

                        elif reactions[str(reaction.emoji)] == "forward":
                            await ctx.invoke(self.client.get_command("skip"))

                        elif reactions[str(reaction.emoji)] == "loop":
                            await ctx.invoke(self.client.get_command("loop"))

                await reaction.remove(user)

    async def jbe_update(self, vid):
        embed = discord.Embed(title=vid.title,
                              color=discord.Colour.from_rgb(0, 255, 255))

        embed.set_image(url=vid.thumbnail)
        await self.juke_box_embed_msg.edit(embed=embed)

    async def jbq_update(self, vid):
        string = "__QUEUE__\n"
        for index in range(len(self.queue_ct)):
            i = self.queue_ct[index]

            string += f"{index+1}. {i.title} ({i.duration}) \n"

        await self.juke_box_queue.edit(content=string)

    @tasks.loop(seconds=1)
    async def jbl_update(self):

        queue = [x for x in self.queue if type(x) != str]
        if queue == []:
            jbl_update.cancel()
        vid = queue[0]

        def two_dig(number):
            if number < 10:
                return f"0{number}"
            else:
                return str(number)

        if vid.duration.count(":") == 1:
            ntime = f"{self.time//60}:{two_dig(self.time%60)}"
        else:
            ntime = f"{self.time//3600}:{two_dig(self.time%3600//60)}:{two_dig(self.time//60)}"

        amt = int(self.time/vid.seconds*10)

        await self.juke_box_loading.edit(content=f"{ntime}/{vid.duration}-{':black_square_button:'*amt +':black_large_square:'*(10-amt) }")

    # * MAIN

    # ? PLAYER

    async def player(self, ctx, voice):  # checks queue and plays the song accordingly
        def check_queue():

            if (not self.loop_song) or (self.skip_song):
                try:
                    queue = [x for x in self.queue if not type(x)== str]
                    self.queue.remove(queue[0])
                    try:
                        self.queue_ct.remove(queue[0])
                    except:
                        pass
                    
                    def clear_pl():
                        for i in range(len(self.queue)):
                            print(2)
                            if i != len(self.queue)-1:
                                
                                if isinstance(self.queue[i],str) and self.queue[i]==self.queue[i+1] :
                                    if "----" in self.queue[i]:
                                        temp = self.queue[i]
                                        self.queue.remove(temp)
                                        self.queue.remove(temp)
                                        clear_pl()      
                                    else:
                                        temp = self.queue[i]
                                        self.queue.remove(temp)
                                        self.queue.remove(temp)
                                        temp = temp[2:][:-2]
                                        for j in range(len(self.queue_ct)):
                                            
                                            if self.queue_ct[j].title == temp:
                                                self.queue_ct.pop(j)

                                        clear_pl()

                    clear_pl()
                except:
                    pass
            fut = asyncio.run_coroutine_threadsafe(self.player(ctx,voice), ctx.bot.loop)
            try:
                fut.result()
            except:
                # an error happened sending the message
                pass
    
        flag = True
        while flag:
            queue = [x for x in self.queue if not type(x)== str]    
            if queue != []:
                try:
                    if not os.path.exists(self.QPATH):
                        await self.download_music(
                            queue[0].url,self.QPATH)  
                        
                        ext = os.listdir(self.QPATH)[0].split(".")[1]
                    else:
                        for i in os.listdir(self.QPATH):
                            if i.split(".")[0]==queue[0].id:
                                ext = i.split(".")[1]
                        else:
                            await self.download_music(
                                queue[0].url,self.QPATH)  
                            
                            for i in os.listdir(self.QPATH):
                                if i.split(".")[0]==queue[0].id:
                                    ext = i.split(".")[1]
                        
                    await ctx.send(f"{queue[0].title} playing now.") 
                    self.log("Downloaded song.")
                    
                    voice.play(discord.FFmpegPCMAudio(f"{self.QPATH}\\{queue[0].id}.{ext}"),
                            after=lambda e: check_queue())
                    self.time = 0
                    if (self.clock.current_loop == 0):
                        self.clock.start()
                    await self.jbe_update(queue[0])
                    await self.jbq_update(queue[0])
                    
                    if (self.jbl_update.current_loop == 0):
                        self.jbl_update.start()
                        
                    self.log(f"{queue[0].title} is playing.")
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    
                except Exception as e:
                    self.log(e)
                    self.log(f"{queue[0].title} cannot be played.")
                    await ctx.send(f"{queue[0].title} cannot be played.") 

                    self.queue.remove(queue[0])
                    try:
                        self.queue_ct.remove(queue[0])
                    except:
                        pass
                    queue.pop(0)    
                else:
                    
                    flag = False
                
            else:
                await ctx.send(">>> All songs played. No more songs to play.") 
                self.log("Ending the queue")
                self.clock.cancel()
                self.jbl_update.cancel()
                await self.juke_box_embed_msg.edit(embed= self.juke_box_embed)
                await self.juke_box_queue.edit(content= "__QUEUE__")
                await self.juke_box_loading.edit(content = f"00:00/00:00 - {':black_large_square:'*10}")
                break

    # ? DOWNLOADER

    async def download_music(self, url, path) -> str:

        queue_path = os.path.abspath(f"{path}/%(id)s.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'outtmpl': queue_path,
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                self.log("Downloading stuff now")
                ydl.download([url])
                await asyncio.sleep(5)
        except Exception as e:
            self.log(e)

    # ? SEARCHING

    async def searching(self, ctx, query, isVideo: bool = True):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        embed_msg: discord.Message = await ctx.send(content=f"Searching for `{query}` on YouTube....{self.loading_emoji}")
        
        if isVideo:
            results = YoutubeVideo.from_query(query, 5)
        else:
            results = YoutubePlaylist.from_query(query, 5)
            
        print("ok")
        wait_time = 60

        reactions = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}

        embed = discord.Embed(title="Search returned the following",
                              color=discord.Colour.dark_green())

        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=self.music_logo)

        for index, result in enumerate(results):
            embed.add_field(name=f"*{index + 1}.*",
                            value=f"**{result.title}**", inline=False)

        await embed_msg.edit(content="", embed=embed)

        def check(reaction: discord.Reaction, user):
            return user == ctx.author and reaction.message.id == embed_msg.id

        self.client.loop.create_task(
            reactions_add(embed_msg, reactions.keys()))

        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await ctx.send(f">>> I guess no ones wants to play.")
                await embed_msg.delete()

                return None

            else:
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.keys():
                    await embed_msg.delete(delay=3)
                    return results[reactions[str(reaction.emoji)] - 1]



    # *---------------------------------------------------------------------------------------------COMMANDS-------------------------------------------------------------------------------------------------------------



    # ? JOIN

    @commands.command(name="join")
    async def join(self, ctx) -> bool:
        '''Joins the voice channel you are currently in.'''

        try:  # user not in vc
            channel = ctx.message.author.voice.channel
        except:
            await ctx.send("You should be in VC dumbo.")
            return False

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if not voice:  # bot not in vc
            voice = await channel.connect()
            await ctx.send(f">>> Joined `{channel}`")
            return True

        elif ctx.author in voice.channel.members:  # bot and user in same vc
            return True

        # bot and user in diff vc but bot can switch
        elif voice and self.disconnect_check(voice):
            await voice.move_to(channel)
            await ctx.send(f">>> Joined `{channel}`")
            return True

        else:  # bot and user in diff vc and bot cant switch
            await ctx.send(f"I am already connected to a voice channel and someone is listening to the songs. Join `{voice.channel.name}``")
            return False

    # ? PLAY
    @commands.command(name="play")
    async def play(self, ctx, *, query):
        '''Plays the audio of the video in the provided VTUBE url.'''

        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        if "http" in query:
            if "www.youtube.com" in query:
                split_list = re.split("/|=|&", query)
                if "watch?v" in split_list:
                    vid = YoutubeVideo(
                        split_list[split_list.index("watch?v")+1])

                elif "playlist?list" in split_list:
                    vid = YoutubePlaylist(
                        split_list[split_list.index("playlist?list")+1])
                else:
                    await ctx.send("Couldnt find neither video or playlist.")
                    return

            else:
                await ctx.send("This command only works with youtube.")
                return
        else:
            vid = YoutubeVideo.from_query(query=query)[0]
            
        vid: YoutubeVideo

        #! Queueing starts here
        voice = get(self.client.voice_clients, guild=ctx.guild)

        old_queue = [x for x in self.queue if type(x) != str]

        if voice and (not voice.is_playing()):
            Queue_infile = os.path.isdir(self.QPATH)

            if not Queue_infile:
                os.mkdir(self.QPATH)
            else:
                self.queue_delete()

        q_num = len(old_queue) + 1
        
        message = await ctx.send(f"Downloading song `{vid.title}`.... {self.loading_emoji}")
        message: discord.Message

        embed = discord.Embed(title="Song Added to Queue",  # TODO make a function
                              url=vid.url, color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.add_field(name=f"**#{q_num}**",
                        value=vid.title)
        embed.set_image(url=vid.thumbnail)
        embed.set_thumbnail(url=self.music_logo)

        self.queue_ct += [vid]
        self.full_queue_ct += [vid]

        if isinstance(vid, YoutubeVideo):
            old_queue = [x for x in self.queue if type(x) != str]
            self.queue += [vid]
            self.full_queue += [vid]

            await self.jbq_update(vid)
            if len(old_queue) == 0:
                await self.player(ctx, voice)
            else:
                self.log("Song added to queue")
        else:
            self.queue += [f"--{vid.title}--"]
            self.full_queue += [f"--{vid.title}--"]
            
            for i in range(len(vid.entries)):
                old_queue = [x for x in self.queue if type(x) != str]
                _vid = YoutubeVideo(vid.entries[i][0], vid.entries[i][1])
                
                self.queue += [_vid]
                self.full_queue += [_vid]
                
                if len(old_queue) == 0:
                    await self.player(ctx, voice)
                else:
                    self.log("Song added to queue")
                    
            
            self.queue += [f"--{vid.title}--"]
            self.full_queue += [f"--{vid.title}--"]
            
        await message.edit(content="", embed=embed)
            
    @commands.command(name="playplaylist")
    async def play_playlist(self, ctx, *, query):
        vid = YoutubeVideo.from_query(query=query)[0]     
        play_command = self.client.get_command("play")
        
        await ctx.invoke(play_command, query=f"https://www.youtube.com/playlist?list={vid.id}")

    # ? SEARCH

    @commands.command(name="search")
    async def search(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        
        result = await self.searching(ctx, query)
        if result:
            if not (await ctx.invoke(self.client.get_command("join"))):
                return
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=f"https://www.youtube.com/watch?v={result.id}")

    # ? SEARCH_PLAYLIST
    @commands.command(name="search playlist")
    async def search_playlist(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""

        result = await self.searching(ctx, query, False)
        if result:
            if not (await ctx.invoke(self.client.get_command("join"))):
                return
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=f"https://www.youtube.com/playlist?list={result.id}")

    # ? NOW PLAYING

    @commands.command(name="nplaying", aliases=["np", "playing"])
    async def now_playing(self, ctx):
        queue = [x for x in self.queue if type(x) != str]
        vid = queue[0]

        embed = discord.Embed(title="NOW PLAYING",  # TODO make a function
                              url=vid.url, color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)

        embed.set_thumbnail(url=vid.thumbnail)

        def two_dig(number):
            if number < 10:
                return f"0{number}"
            else:
                return str(number)

        if vid.duration.count(":") == 1:
            ntime = f"{self.time//60}:{two_dig(self.time%60)}"
        else:
            ntime = f"{self.time//3600}:{two_dig(self.time%3600//60)}:{two_dig(self.time//60)}"
        embed.add_field(name=f"{vid.title}", value="**  **", inline=False)
        amt = int(self.time/vid.seconds*10)
        embed.add_field(
            name=f"{ntime}/{vid.duration} {':black_square_button:'*amt +':black_large_square:'*(10-amt) }", value="**  **", inline=False)

        await ctx.send(embed=embed)

    # ? LYRICS
    @commands.command(name="lyrics", aliases=["l"])
    async def lyrics(self, ctx: commands.Context):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        queue = [x for x in self.queue if type(x) != str]
        print(queue)
        vid = queue[0]
        print(vid.title)
        song = genius.search_song(vid.title)
        print(song)
        
        lyrics = song.lyrics
        l_list = lyrics.split("\n")
        ly_list = []
        l = ""
        for i in l_list:
            if len(l+i) > 2048:
                ly_list += [l]
                l = ""
            l += i
            l += "\n"
        else:
            ly_list += [l]
            
        reactions = {"back": "⬅", "delete": "❌", "forward": "➡"}
            
        embed = discord.Embed(title=f"LYRICS - {song.title}",  # TODO make a function
                                  url=song.url,
                                  description=ly_list[0],
                                  color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                            icon_url=ctx.message.author.avatar_url)
        
        embed_msg = await ctx.send(embed=embed)
        embed_msg: discord.Message
            
        pages = len(ly_list)
        wait_time = 120
        page = 1
        
        self.client.loop.create_task(reactions_add(embed_msg, reactions.values()))
        
        def check(reaction: discord.Reaction, user):
            return user == ctx.author and reaction.message.id == embed_msg.id
        
        def update_page(page):
            embed.description = ly_list[page-1]
            return embed
        
        while True:

            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await embed_msg.clear_reactions()

                return

            else:
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.values():
                    if str(reaction.emoji) == reactions["forward"]:
                        page += 1
                        if page > pages:
                            page = pages
                            
                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)
                        
                    if str(reaction.emoji) == reactions["back"]:
                        page -= 1
                        if page > 1:
                            page = 1
                            
                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)
                        
                    if str(reaction.emoji) == reaction["delete"]:
                        embed_msg.delete(delay=2)
                        

    # ? SONG_INFO
    @commands.command(name="song", aliases=["sinfo"])
    async def song_info(self, ctx, query):
        result = await self.searching(ctx, query)
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




# *-------------------------------------------------------QUEUE------------------------------------------------------------------------------------------------------------------------



    # ? QUEUE

    @commands.group(name="queue", aliases=['q'])
    async def Queue(self, ctx):
        '''Shows the current queue.'''

        if ctx.invoked_subcommand is None:
            i = 0
            j = 1
            desc = ""
            while i < len(self.queue):
                if isinstance(self.queue[i], YoutubeVideo):
                    desc += f"{j}. {self.queue[i].title} ({self.queue[i].duration}) \n"
                    i += 1
                    j += 1
                else:
                    desc += f"***{self.queue[i]}*** \n"
                    i += 1

            embed = discord.Embed(title="QUEUE",
                                  description=desc,
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            await ctx.send(embed=embed)

    # ? QUEUE REPLACE
    @Queue.command(name="replace", aliases=['move'])
    @vc_check()
    async def replace(self, ctx, change1, change2):
        '''Replaces two queue members.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.queue if type(x) != str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue):
            await ctx.send(f">>> Switched the places of **{queue[change2-1].title}** and **{queue[change1-1].title}**")
            self.queue[self.queue.index(queue[change1-1])], self.queue[self.queue.index(queue[change2-1])
                                                                       ] = self.queue[self.queue.index(queue[change2-1])], self.queue[self.queue.index(queue[change1-1])]
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? QUEUE REMOVE
    @Queue.command(name="remove")
    @vc_check()
    async def remove(self, ctx, remove):
        '''Removes the Queue member.'''

        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.queue if type(x) != str]
        if remove > 1 and remove <= len(queue):
            DIR = self.QPATH
            DIR_list = os.listdir(DIR)

            for i in DIR_list:
                name, ext = i.split(".")
                if name == queue[remove - 1].id:
                    song_name = i
                    break

            SONG_DIR = DIR + f"\\{song_name}"
            os.remove(SONG_DIR)
            await ctx.send(f">>> Removed **{(self.queue[remove - 1].title)}** from the queue.")
            self.queue.remove(queue[remove-1])
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? QUEUE NOW
    @Queue.command(name="now")
    @vc_check()
    async def now(self, ctx, change):
        '''Plays a queue member NOW.'''

        try:
            change = int(change)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.queue if type(x) != str]
        if change > 1 and change <= len(queue):
            temp = queue[change-1]
            self.queue.pop(self.queue.index(queue[change-1]))
            self.queue.insert(1, temp)
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? QUEUE CONTRACTED
    @Queue.command(name="contracted", aliases=['ct'])
    async def contracted(self, ctx):
        desc = ""

        for index in range(len(self.queue_ct)):
            i = self.queue_ct[index]

            desc += f"{index+1}. {i.title} ({i.duration}) \n"

        embed = discord.Embed(title="QUEUE",
                              description=desc,
                              color=discord.Colour.dark_purple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)

        await ctx.send(embed=embed)

    # ? QUEUE FULL
    @Queue.group(name="full")
    async def full(self, ctx):
        if ctx.invoked_subcommand is None:
            i = 0
            j = 1
            desc = ""
            while i < len(self.full_queue):
                if isinstance(self.full_queue[i], YoutubeVideo):
                    desc += f"{j}. {self.full_queue[i].title} ({self.full_queue[i].duration}) \n"
                    i += 1
                    j += 1
                else:
                    desc += f"***{self.full_queue[i]}*** \n"
                    i += 1

            embed = discord.Embed(title="QUEUE",
                                  description=desc,
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            await ctx.send(embed=embed)

    # ? FULL CONTRACTED
    @full.command(name="fcontracted", aliases=['fct'])
    async def full_contracted(self, ctx):
        desc = ""
        for index, i in enumerate(self.queue_ct):
            desc += f"{index+1}. {i.title} ({i.duration}) \n"

        embed = discord.Embed(title="QUEUE",
                              description=desc,
                              color=discord.Colour.dark_purple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)

        await ctx.send(embed=embed)




# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------



    # ? LOOP

    @commands.command(name="loop", aliases=['lp'])
    @vc_check()
    async def loop(self, ctx, toggle=""):
        '''Loops the current song, doesn't affect the skip command tho. If on/off not passed it will toggle it.'''

        if toggle.lower() == "on":
            self.loop_song = True
            await ctx.send(">>> **Looping current song now**")

        elif toggle.lower() == 'off':
            self.loop_song = False
            await ctx.send(">>> **NOT Looping current song now**")

        else:

            if self.loop_song:
                self.loop_song = False
                await ctx.send(">>> **NOT Looping current song now**")

            else:
                self.loop_song = True
                await ctx.send(">>> **Looping current song now**")
                
    # ? RESTART

    @commands.command(name="restart")
    @vc_check()
    async def restart(self, ctx):
        '''Restarts the current song.'''
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            temp = self.loop_song
            self.loop_song = True
            
            voice.stop()
            await asyncio.sleep(0.1)
            self.loop_song = temp
        else:
            self.log("Restart failed")
            await ctx.send(">>> Ya know to restart stuff, stuff also needs to be playing first.")

   # ? PAUSE

    @commands.command(aliases=['p'])
    @vc_check()
    async def pause(self, ctx):
        '''Pauses the current music.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            self.log("Player paused")
            voice.pause()
            self.clock.cancel()
            self.jbl_update.cancel()
            await ctx.send(">>> Music Paused")
        else:
            self.log("Pause failed")
            await ctx.send(">>> Ya know to pause stuff, stuff also needs to be playing first.")

    # ? RESUME

    @commands.command(aliases=['r', 'res'])
    @vc_check()
    async def resume(self, ctx):
        '''Resumes the current music.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            self.log("Music resumed")
            voice.resume()
            self.clock.start()
            self.jbl_update.start()
            await ctx.send(">>> Resumed Music")
        else:
            self.log("Resume failed")
            await ctx.send(">>> Ya know to resume stuff, stuff also needs to be paused first.")

    # ? STOP
    @commands.command(aliases=['st', 'yamete'])
    @vc_check()
    async def stop(self, ctx):
        '''Stops the current music AND clears the current queue.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)
        self.queue.clear()
        self.queue_ct.clear()

        if voice and voice.is_playing:
            self.log("Player stopped")
            voice.stop()
            self.clock.cancel()
            self.jbl_update.cancel()
            self.time = 0
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")

    # ? HARD_STOP
    @commands.command(name="hardstop", aliases=['hs', 'hards', 'hstop', 'yamero'])
    @vc_check()
    async def hard_stop(self, ctx):
        '''Stops the current music AND clears the current queue.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)
        self.queue.clear()
        self.full_queue.clear()
        self.queue_ct.clear()
        self.full_queue_ct.clear()

        if voice and voice.is_playing:
            self.log("Player stopped")
            voice.stop()
            self.clock.cancel()
            self.jbl_update.cancel()
            self.time = 0
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")
        try:
            self.queue_delete()
        except:
            pass
    # ? SKIP

    @commands.command(aliases=['n', 'sk', 'skip'])
    @vc_check()
    async def next(self, ctx):
        '''Skips the current song and plays the next song in the queue.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            self.skip_song = True
            self.log("Playing next song")
            voice.stop()
            await ctx.send(">>> ***Song skipped.***")
        else:
            self.log("Skip failed")
            await ctx.send(">>> Wat you even trynna skip? There is ***nothing to*** skip, I am surrounded by idiots")

    # ? LEAVE
    @commands.command()
    @vc_check()
    async def leave(self, ctx):
        '''Leaves the voice channel.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            self.clock.cancel()
            self.jbl_update.cancel()
            self.time = 0
            await ctx.send(f">>> Left ```{voice.channel.name}```")
            self.queue.clear()
            self.full_queue.clear()
            self.queue_ct.clear()
            self.full_queue_ct.clear()
        else:
            await ctx.send(">>> I cannot leave a voice channel I have not joined, thought wouldn't need to explain basic shit like this.")

        try:
            self.queue_delete()
        except:
            pass
    # ? VOLUME

    @commands.command(aliases=["v"])
    @vc_check()
    async def volume(self, ctx, volume: int):
        '''Changes the volume of the player. Volume should be between 0 and 100.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if volume < 0 or volume > 100:
            await ctx.send("Volume needs to be between 0 and 100. Darling.")
            return
        voice.source.volume = volume/100
        await ctx.send(f"Volume is set to {volume}")

    @volume.error
    async def volume_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(">>> Enter the volume.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send(">>> We are numericons' people not Texticons, you traitor.")

    async def duration_check(self, ctx, time):
        queue = [x for x in self.queue if type(x) != str]
        try:
            if ":" in time:
                tl = list(map(int, time.split(":")))
                if tl[-1] > 59 or tl[-2] > 59 or tl[-1] < 0 or tl[-2] < 0:
                    await ctx.send("Seek in the format HH:MM:SS or S or something i don't know but this is incorrect.")
                    return False
                elif time.count(":") > 2:
                    await ctx.send("Seek in the format HH:MM:SS or S or something i don't know but this is incorrect.")
                    return False

                elif time.count(":") == 2:
                    sec = queue[0].seconds
                    if tl[0]*60*60 + tl[1]*60 + tl[2] > sec:
                        await ctx.send("Entered a wrong time I guess.")
                        return False
                elif time.count(":") == 1:
                    sec = queue[0].seconds
                    if tl[0]*60 + tl[1] > sec:
                        await ctx.send("Entered a wrong time I guess.")
                        return False

            else:
                if int(time) > queue[0].seconds:
                    await ctx.send("Entered a wrong time I guess.")
                    return False
        except Exception as e:
            print(e)
            await ctx.send("Seek in the format HH:MM:SS or S or something i don't know but this is incorrect.")
            return False
        else:
            return True

    async def int_time(self, ctx, time):
        if not await self.duration_check(ctx, time):
            return None
        if ":" in time:
            time = list(map(int, time.split(":")))
            ts = 0
            if len(time) == 3:
                ts += time[-3]*60*60
            ts += time[-2]*60
            ts += time[-1]
            time = ts
        else:
            time = int(time)

        return time
    
     # ? BACK
    @commands.command()
    @vc_check()
    async def back(self,ctx):
        '''Plays previous song.'''
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice:
            fq = [x for x in self.full_queue if not isinstance(x,str)]
            q = [x for x in self.queue if not isinstance(x,str)]
            self.queue +=  [fq[-(len(q)+1)]]
            if not voice.is_playing():
                
                if len(self.queue) == 1:    
                    await self.player(ctx,voice)
                elif voice.is_paused():
                    voice.resume()
                    await ctx.invoke(self.client.get_command("restart"))
                    
            else:
                await ctx.invoke(self.client.get_command("restart"))
    
    # ?SEEK
    @commands.command()
    @vc_check()
    async def seek(self, ctx, time):
        queue = [x for x in self.queue if type(x) != str]

        for i in os.listdir(self.QPATH):
            if i.split(".")[0] == queue[0].id:
                ext = i.split(".")[1]
                
        voice = get(self.client.voice_clients, guild=ctx.guild)

        time = await self.int_time(ctx, time)

        if time:
            voice.source = discord.FFmpegPCMAudio(
                f"{self.QPATH}\\{queue[0].id}.{ext}", before_options=f"-ss {time}")
            self.time = time
        else:
            return
    # ?FORWARD

    @commands.command(aliases=["fwd"])
    @vc_check()
    async def forward(self, ctx, time):

        queue = [x for x in self.queue if type(x) != str]

        for i in os.listdir(self.QPATH):
            if i.split(".")[0] == queue[0].id:
                ext = i.split(".")[1]
        voice = get(self.client.voice_clients, guild=ctx.guild)
        time = await self.int_time(ctx, time)

        if time:
            if time <= queue[0].seconds - self.time:
                voice.source = discord.FFmpegPCMAudio(
                    f"{self.QPATH}\\{queue[0].id}.{ext}", before_options=f"-ss {time + self.time}")
                self.time += time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return

    # ?REWIND
    @commands.command(aliases=["rew"])
    @vc_check()
    async def rewind(self, ctx, time):

        queue = [x for x in self.queue if type(x) != str]

        for i in os.listdir(self.QPATH):
            if i.split(".")[0] == queue[0].id:
                ext = i.split(".")[1]
        voice = get(self.client.voice_clients, guild=ctx.guild)
        time = await self.int_time(ctx, time)

        if time:
            if time <= self.time:
                voice.source = discord.FFmpegPCMAudio(
                    f"{self.QPATH}\\{queue[0].id}.{ext}", before_options=f"-ss {self.time - time}")
                self.time -= time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return



   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------



    # ? PLAYLIST

    @commands.group(aliases=["pl"])
    async def playlist(self, ctx):
        '''Shows your Playlist. Subcommands can alter your playlist'''
        if ctx.invoked_subcommand is None:

            playlist_db = gen.db_receive("playlist")
            try:
                playlist = playlist_db[str(ctx.author.id)][1]
            except:
                playlist_db[str(ctx.author.id)] = [
                    f"{ctx.author.name}'s Playlist", []]
                playlist = []

            for i in range(len(playlist)):
                if len(playlist[i]) == 11:
                    playlist[i] = YoutubeVideo(playlist[i])
                else:
                    playlist[i] = YoutubePlaylist(playlist[i])

            embed = discord.Embed(title=playlist_db[str(ctx.author.id)][0],
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            no = 1
            for song in playlist:
                embed.add_field(name=f"**{no}**", value=f"**{song.title}**")
                no += 1
            await ctx.send(embed=embed)

    # ? PLAYLIST ADD
    @playlist.command()
    async def add(self, ctx, *, query):
        '''Adds a song to your Playlist.'''

        vid = await self.searching(ctx, query)

        if vid:

            playlist_db = gen.db_receive("playlist")
            try:
                playlist_db[str(ctx.author.id)]
            except:
                playlist_db[str(ctx.author.id)] = [
                    f"{ctx.author.name}'s Playlist", []]

            playlist_db[str(ctx.author.id)][1] += [vid.id]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {playlist_db[str(ctx.author.id)][0]}")
            gen.db_update("playlist", playlist_db)

    # ? PLAYLIST ADD_PLAYLIST
    @playlist.command(name="addplaylist", aliases=["apl", "addpl"])
    async def add_playlist(self, ctx, *, query):
        '''Adds a playlist to your Playlist.'''

        vid = await self.searching(ctx, query, False)

        if vid:

            playlist_db = gen.db_receive("playlist")
            try:
                playlist_db[str(ctx.author.id)]
            except:
                playlist_db[str(ctx.author.id)] = [
                    f"{ctx.author.name}'s Playlist", []]

            playlist_db[str(ctx.author.id)][1] += [vid.id]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {playlist_db[str(ctx.author.id)][0]}")
            gen.db_update("playlist", playlist_db)

    # ? PLAYLIST REARRANGE
    @playlist.command(aliases=["re", "change", "replace", "switch"])
    async def rearrange(self, ctx, P1: int, P2: int):
        '''Rearranges 2 songs/playlist places of your playlist.'''
        playlist_db = gen.db_receive("playlist")

        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [
                f"{ctx.author.name}'s Playlist", []]
            await ctx.send("Your playlist has been created.")
            return

        else:
            if len(playlist_db[str(ctx.author.id)][1]) < 2:
                await ctx.send("Your playlist too smol for rearrangement.")
                return

            if P1 < 1 or P1 > len(playlist_db[str(ctx.author.id)][1]) or P2 < 1 or P2 > len(playlist_db[str(ctx.author.id)][1]):
                return

            playlist_db[str(ctx.author.id)][1][P1-1], playlist_db[str(ctx.author.id)][1][P2 -
                                                                                         1] = playlist_db[str(ctx.author.id)][1][P2-1], playlist_db[str(ctx.author.id)][1][P1-1]
            await ctx.send(f"Number {P1} and {P2} have been rearranged.")
            self.log(f"altered {playlist_db[str(ctx.author.id)][0]}")

        gen.db_update("playlist", playlist_db)

    # ? PLAYLIST REMOVE
    @commands.command(aliases=["prem"])
    async def premove(self, ctx, R: int):
        '''Removes a song/playlist from your playlist.'''
        playlist_db = gen.db_receive("playlist")

        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [
                f"{ctx.author.name}'s Playlist", []]
            await ctx.send("Your playlist has been created.")
            return

        else:
            if len(playlist_db[str(ctx.author.id)][1]) < 1:
                await ctx.send("Your playlist too smol for alteration.")
                return

            if R < 1 or R > len(playlist_db[str(ctx.author.id)][1]):
                return

            playlist_db[str(ctx.author.id)][1].pop(R-1)
            await ctx.send(f"Number {R} has been removed.")
            self.log(f"altered {playlist_db[str(ctx.author.id)][0]}")

        gen.db_update("playlist", playlist_db)

    # ? PLAYLIST NAME
    @playlist.command(aliases=[])
    async def name(self, ctx, name):
        playlist_db = gen.db_receive("playlist")
        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [
                f"{ctx.author.name}'s Playlist", []]
            await ctx.send("Your playlist has been created.")
            return
        else:
            playlist_db[str(ctx.author.id)][0] = name

            gen.db_update("playlist", playlist_db)

    # ? PLAYLIST PLAY
    @playlist.command(name="listplay", aliases=["pp"])
    async def pplay(self, ctx):
        '''Plays your playlist.'''
        
        playlist_db = gen.db_receive("playlist")

        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [
                f"{ctx.author.name}'s Playlist", []]
            
            await ctx.send("Your playlist has been created.")
            return

        else:
            if len(playlist_db[str(ctx.author.id)][1]) < 1:
                await ctx.send("Your playlist doesn't have any songs to play")
                return

            else:
                if not (await ctx.invoke(self.client.get_command("join"))):
                    return

                voice = get(self.client.voice_clients, guild=ctx.guild)
                playlist = playlist_db[str(ctx.author.id)]
                
                for i in range(len(playlist[1])):
                    if len(playlist[1][i]) == 11:
                        playlist[1][i] = YoutubeVideo(playlist[1][i])

                    else:
                        playlist[1][i] = YoutubePlaylist(playlist[1][i])

                self.queue += [f"----{playlist[0]}----"]
                self.full_queue += [f"----{playlist[0]}----"]
                
                for i in playlist[1]:
                    self.full_queue_ct += [i]
                    self.queue_ct += [i]
                    
                    if isinstance(i, YoutubeVideo):
                        old_queue = [x for x in self.queue if type(x) != str]
                        self.queue += [i]
                        self.full_queue += [i]

                        if len(old_queue) == 0:
                            await self.player(ctx, voice)
                        else:
                            self.log("Song added to queue")
                            
                    else:
                        self.queue += [f"--{i.title}--"]
                        self.full_queue += [f"--{i.title}--"]
                        
                        for j in range(len(i.entries)):
                            old_queue = [x for x in self.queue if type(x) != str]
                            _vid = YoutubeVideo(i.entries[j][0], i.entries[j][1])
                            
                            self.queue += [_vid]
                            self.full_queue += [_vid]
                            
                            if len(old_queue) == 0:
                                await self.player(ctx, voice)
                            else:
                                self.log("Song added to queue")
                                
                        self.queue += [f"--{i.title}--"]
                        self.full_queue += [f"--{i.title}--"]

                self.queue += [f"----{playlist[0]}----"]

                self.full_queue += [f"----{playlist[0]}----"]

                await ctx.send("Your Playlist has been added to the Queue.")


# *------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# *------------------------------------DOWNLOAD----------------------------------------------------------------------------------------------------------------------------------------------------



    # ? DOWNLOAD

    @commands.command(aliases=["dnld"])
    async def download(self, ctx, *, query):
        '''Downloads a song for you, so your pirated ass doesn't have to look for it online.'''

        vid = await self.searching(ctx, query)
        embed = discord.Embed(title="Now downloading",
                              color=discord.Colour.dark_purple(), url=vid.url)
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_image(url=vid.thumbnail)
        embed.add_field(name="**  **", value=f"**{vid.title}**")

        await ctx.send(embed=embed)

        files = os.listdir(self.DPATH)

        await self.download_music(vid.id, self.DPATH)
        self.log("Downloaded")

        for i in files:
            if i.split(".")[0] == vid.id:
                ext = i.split(".")[1]

        mp3 = discord.File(f'{self.DPATH}\\{vid.id}.{ext}',
                           filename=vid.title+".mp3")

        await ctx.channel.send(file=mp3)
        os.remove(f'{self.DPATH}\\{vid.id}.{ext}')


# *---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def setup(client):
    client.add_cog(Music(client))
