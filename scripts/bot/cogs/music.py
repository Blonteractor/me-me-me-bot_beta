import discord
from discord.utils import get
import aiohttp
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks

import json
from typing import List,Any
import shutil
from lxml import etree
import lxml
import re
import urllib.parse
import urllib.request
import requests
import urllib3
from asyncio import sleep,TimeoutError
import asyncio
from youtube_dl import YoutubeDL
import youtube_dl
import time as t
from os import system
import time
import lyricsgenius
import random

import imp
import os

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
imp.load_source("Youtube", os.path.join(
    os.path.dirname(__file__), "../../others/Youtube.py"))
import general as gen
from Youtube import YoutubePlaylist, YoutubeVideo, driver

from Youtube import YoutubePlaylist,YoutubeVideo,driver

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

def vote(votes_required: float, vote_msg: str, yes_msg: str, no_msg: str, vote_duration=20):
    async def predicate(ctx: commands.Context):   
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
 
        members = ctx.guild.voice_client.channel.members
        
        already_voted: List[int] = []
        reactions = {"yes": "✔", "no": "❌"}
        
        def check(reaction: discord.Reaction, user):
            return user in members and reaction.message.id == msg.id and str(reaction) in reactions.values()
        
        msg = await ctx.send(content=f">>> {vote_msg}")
        msg: discord.Message
        
        ctx.bot.loop.create_task(reactions_add(msg, reactions.values()))
        
        while True:
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=vote_duration, check=check)
                response = str(reaction)
            except TimeoutError:
                for reaction in msg.reactions:
                    if response == reactions["yes"]:
                        yes = reaction.count
                    elif response == reactions["no"]:
                        no = reaction.count
                
                total = yes + no
                result = (yes / total) >= votes_required
                
                if result:
                    await msg.edit(content=yes_msg)
                if not result:
                    await msg.edit(content=no_msg)
                    
                return result

            else:
                if user.id not in already_voted:
                    already_voted.append(user.id)
                else:
                    await msg.remove_reaction(response, user)
        
    return commands.check(predicate=predicate)


genius = lyricsgenius.Genius(
    "pGaaH8g-CxAeF1qaQ2DeVmLnmp84mIciWU8sbGoVKQO_MTlHQW4ZoxYeP8db1kDO")
genius.verbose = False


class Music(commands.Cog):
    ''':musical_note: The title says it all, commands related to music and stuff.'''
    queue:List[Any] = []                                      # queue of the format [items,"playlist name",playlist items,"/playlist name",items]
    full_queue:List[Any] = []
    queue_ct:List[Any] = []    
    full_queue_ct:List[Any]=[]

    loop_song = False                                         # variable used for looping song
    loop_q = False

    skip_song = False        
                                     # variable used for skipping song
    time_for_disconnect = 300                                 # time for auto disconnect
    
    # str of loading emoji
    loading_emoji = ""

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




    shuffle_lim = None
    shuffle_var = 0
   # * ------------------------------------------------------------------------------PREREQUISITES--------------------------------------------------------------------------------------------------------------



    def __init__(self, client):
        self.client = client
        self.auto_pause.start()             # starting loops for auto pause and disconnect
        self.auto_disconnector.start()
        self.juke_box.start()
        self.dj_role = "DJ"
        
        self.client: discord.Client
        
    def cog_unload(self):
        driver.quit()

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
        
    def chunks(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
        
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
                        
    
    async def jbe_update(self,vid):
        try:
            self.juke_box_embed_msg
        except:
            return
        embed = discord.Embed(title=vid.title,
                              color=discord.Colour.from_rgb(0, 255, 255))

        embed.set_image(url = vid.thumbnail)
        await self.juke_box_embed_msg.edit(embed = embed)
    
    async def jbq_update(self,vid):
        try:
            self.juke_box_queue
        except:
            return
        
        string = "__QUEUE__\n"
        for index in range(len(self.queue_ct)):
            i = self.queue_ct[index]

            string += f"{index+1}. {i.title} ({i.duration}) \n"

        await self.juke_box_queue.edit(content=string)

    @tasks.loop(seconds=1)
    async def jbl_update(self):
        
        try:
            self.juke_box_loading
        except:
            return
        queue = [x for x in self.queue if type(x)!= str]
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
        
        amt =int(self.time/vid.seconds*10)
        
        await self.juke_box_loading.edit(content = f"{ntime}/{vid.duration}-{':black_square_button:'*amt +':black_large_square:'*(10-amt) }")
        

    # * MAIN

    # ? PLAYER

    async def player(self, ctx, voice):  # checks queue and plays the song accordingly
        def check_queue():

            if (not self.loop_song) or (self.skip_song):
                try:
                    queue = [x for x in self.queue if not type(x)== str]
                    temp = queue[0]
                    
                    self.queue.remove(temp)
                    
                    if self.loop_q:
                        self.queue += [temp]
                    
                    try:
                        self.queue_ct.remove(temp)
                        if self.loop_q:
                            self.queue_ct += [temp]
                    except:
                        pass
                    
                    def clear_pl():
                        for i in range(len(self.queue)):
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
                    await ctx.send(f"{queue[0].title} playing now.") 
                    self.log("Downloaded song.")
                    voice.play(discord.FFmpegPCMAudio(queue[0].audio_url, before_options=" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                            after=lambda e: check_queue())
                    self.time = 0
                    if (self.clock.current_loop == 0):
                        self.clock.start()
                    await self.jbe_update(queue[0])
                    await self.jbq_update(queue[0])
                    if (self.jbl_update.current_loop == 0):
                        self.jbl_update.start()
                    
                    if self.shuffle_lim:
                        self.shuffle_var += 1
                        if self.shuffle_var == self.shuffle_lim:
                            await ctx.invoke(self.client.get_command("shuffle"))
                            self.shuffle_var = 0
                    
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

        
        def embed_update(page):
            embed.description = content[page - 1]
            return embed
        
        await embed_msg.edit(embed=embed_update(page=page))
                
        reactions = {"back": "⬅","delete": "❌", "forward": "➡"}
        
        self.client.loop.create_task(reactions_add(reactions=reactions.values(), message=embed_msg))
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await embed_msg.clear_reactions()
                
                return

            else:
                response = str(reaction.emoji)
                
                await embed_msg.remove_reaction(response, ctx.author)

                if response in reactions.values():
                    if response == reactions["forward"]:
                        page += 1
                        if page > pages:
                            page = pages
                    elif response == reactions["back"]:
                        page -= 1
                        if page < 1:
                            page = 1
                    elif response == reactions["delete"]:
                        embed_msg.delete(delay=3)
                        
                        return
                        
                    await embed_msg.edit(embed=embed_update(page=page))

    # ? SEARCHING
    async def searching(self, ctx, query , isVideo:bool = True, VideoClass:bool = True):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
        
        if isVideo:
            results = YoutubeVideo.from_query(query, 5)
        else:
            results = YoutubePlaylist.from_query(query,5)
            
        wait_time = 60

        reactions = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}

        embed = discord.Embed(title="Search returned the following",
                              color=discord.Colour.dark_green())

        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        
        embed_msg = await ctx.send(embewd=embed)
        
        if isVideo:        
            for index, result in enumerate(results):
                embed.add_field(name=f"*{index + 1}.*",
                                value=f"**{result[1]} ({result[3]}) - {result[2]}**", inline=False)

        else:      
            
            for index, result in enumerate(results):
                embed.add_field(name=f"*{index + 1}.*",
                                value=f"**{result.title} ({result.duration}) - {result.uploader}**", inline=False)

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
                    if isVideo:
                        if VideoClass:
                            return YoutubeVideo(results[reactions[str(reaction.emoji)] - 1][0])
                        
                        else:
                            return results[reactions[str(reaction.emoji)] - 1]
                    else:
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
                    vid = YoutubeVideo(split_list[split_list.index("watch?v")+1],requested_by=ctx.author.name)
                    
                elif "playlist?list" in split_list:
                    vid = YoutubePlaylist(split_list[split_list.index("playlist?list")+1],requested_by=ctx.author.name)
                else:
                    await ctx.send("Couldnt find neither video or playlist.")
                    return

            else:
                await ctx.send("This command only works with youtube.")
                return
        else:
            vid = YoutubeVideo(YoutubeVideo.from_query(query=query)[0][0], requested_by=ctx.author.name)            

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
        
        self.loading_emoji = str(discord.utils.get(ctx.guild.emojis, name="loading"))
        
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
        await self.jbq_update(vid)

        if isinstance(vid,YoutubeVideo):
            old_queue = [x for x in self.queue if type(x)!= str]
            self.queue += [vid]
            self.full_queue += [vid]
            
            
            if len(old_queue) == 0:
                await self.player(ctx, voice)
            else:
                self.log("Song added to queue")
        else:
            self.queue += [f"--{vid.title}--"]
            self.full_queue += [f"--{vid.title}--"]
            temp = []
            for i in range(len(vid.entries)):
                
                _vid = YoutubeVideo(vid.entries[i][0])
                
                temp += [_vid]

            old_queue = [x for x in self.queue if type(x)!= str]
            self.queue += temp
            self.full_queue += temp
            vid._entries = temp
            if len(old_queue) == 0:
                await self.player(ctx,voice)
            else:
                self.log("Song added to queue") 
            
            self.queue += [f"--{vid.title}--"]
            self.full_queue += [f"--{vid.title}--"]
            
    # ? PLAY PLAYLIST
    @commands.command()
    async def play_playlist(self, ctx, *, query):
        vid = YoutubePlaylist.from_query(query=query)[0]     
        play_command = self.client.get_command("play")
        await ctx.invoke(play_command, query=f"https://www.youtube.com/playlist?list={vid.id}")

        
    # ? SEARCH

    @commands.command(name="search")
    async def search(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        if not (await ctx.invoke(self.client.get_command("join"))):
            return
        result = await self.searching(ctx, query,VideoClass=False)
        if result:
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=f"https://www.youtube.com/watch?v={result[0]}")
    
    # ? SEARCH_PLAYLIST
    @commands.command(name="search playlist")
    async def search_playlist(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        if not (await ctx.invoke(self.client.get_command("join"))):
            return
        result = await self.searching(ctx, query,False)
        if result:
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
        vid = queue[0]
        song = genius.search_song(vid.title)
        
        lyrics = song.lyrics
        
        embed = discord.Embed(title=f"LYRICS - {song.title}",  # TODO make a function
                                  url=song.url,
                                  description="",
                                  color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                            icon_url=ctx.message.author.avatar_url)
        
        embed_msg = await ctx.send(embed=embed)
        
        await self.embed_pages(ctx=ctx, content_str=lyrics, embed_msg=embed_msg, wait_time=120)
                        

    # ? SONG_INFO
    @commands.command(aliases = ["sinfo"])
    async def song_info(self,ctx,*,query):
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

    # ? PLAYLIST_INFO
    @commands.command(aliases = ["plinfo"])
    async def playlist_info(self,ctx,*,query):
        
        result = await self.searching(ctx, query,False)
        
        embed = discord.Embed(title=f"{result.title} ({result.duration}) - {result.uploader}", 
                            url=result.url,
                            color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                        icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                        icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url = result.thumbnail)

        embed.add_field(name = "Date of Upload", value = result.date)
        embed.add_field(name = "No of entries", value = len(result.entries),inline = False)
        for index,vid in enumerate(result.entries):
            embed.add_field(name = f"**{index +1}. {vid[2]} ({vid[1]})**",value="** **")

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
                    
            desc_l = []
            for chunk in list(self.chunks(desc.split("\n"), n=5)):
                desc_l.append("\n".join(chunk))

            embed = discord.Embed(title="QUEUE",
                                  description=desc,
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            embed_msg = await ctx.send(embed=embed)
            
            await self.embed_pages(_content=desc_l, ctx=ctx, embed_msg=embed_msg, wait_time=120)

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
            await ctx.send(f">>> Removed **{(queue[remove - 1].title)}** from the queue.")
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
            self.queue.insert(self.queue.index(queue[0]) + 1, temp)
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))
    
    # ? QUEUE CONTRACTED  
    @Queue.group(aliases = ['ct'])
    async def contracted(self,ctx):
        if ctx.invoked_subcommand is None:
            desc =""
            
            for index in range(len(self.queue_ct)):
                i = self.queue_ct[index]
            
                desc += f"{index+1}. {i.title} ({i.duration}) \n"

            embed = discord.Embed(title="QUEUE",
            description = desc,
            color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                                icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                                icon_url=ctx.message.author.avatar_url)
        
            await ctx.send(embed=embed)
    
    # ? CONTRACTED REMOVE
    @contracted.command(aliases = ["rem"])
    async def remm(self, ctx, remove):
        '''Removes the Queue member.'''
        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = self.queue_ct
        if remove > 1 and remove <= len(queue):
            temp = queue[remove-1]
            self.queue_ct.remove(temp)
            if isinstance(temp,YoutubeVideo):
                
                self.queue.remove(temp)
                await ctx.send(f">>> Removed **{(temp.title)}** from the queue.")
            else:
                
                i1 = self.queue.index(f"--{temp.name}--")
                i2 = self.queue[i1+1:].index(f"--{temp.name}--")
                self.queue[i1:i2+1] = []

        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? CONTRACTED REPLACE
    @contracted.command(aliases=['move'])
    @vc_check()
    async def repla(self, ctx, change1, change2):
        '''Replaces two queue members.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = self.queue_ct
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue):
            temp1 = queue[change2-1]
            temp2 = queue[change1-1]
            await ctx.send(f">>> Switched the places of **{temp1.title}** and **{temp2.title}**")
            self.queue_ct[self.queue_ct.index(temp1)], self.queue_ct[self.queue_ct.index(temp2)] = self.queue_ct[self.queue_ct.index(temp2)], self.queue_ct[self.queue_ct.index(temp1)]
            
            if isinstance(temp1,YoutubeVideo):
                i11 = self.queue.index(temp1)
                i12 = i11 + 1
            else:
                i11 = self.queue.index(f"--{temp1.name}--")
                i12 = self.queue[i11+1:].index(f"--{temp1.name}--") + 1
            
            if isinstance(temp2,YoutubeVideo):
                i21 = self.queue.index(temp2)
                i22 = i21 + 1
            else:
                i21 = self.queue.index(f"--{temp2.name}--")
                i22 = self.queue[i21+1:].index(f"--{temp2.name}--") + 1
            
            self.queue[i11:i12],self.queue[i21:i22] = self.queue[i21:i22],self.queue[i11:i12]
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return
    

    # ? CONTRACTED NOW
    @contracted.command()
    @vc_check()
    async def no(self, ctx, change):
        '''Plays a queue member NOW.'''

        try:
            change = int(change)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = self.queue_ct 
        if change > 1 and change <= len(queue):
            temp1 = queue[change-1]
            temp2 = queue[0]
            self.queue_ct.pop(self.queue.index(temp1))
            self.queue_ct.insert(1, temp1)
            self.queue_ct.pop(0)

            if isinstance(temp1,YoutubeVideo):
                i11 = self.queue.index(temp1)
                i12 = i11 + 1
            else:
                i11 = self.queue.index(f"--{temp1.name}--")
                i12 = self.queue[i11+1:].index(f"--{temp1.name}--") + 1
            
            if isinstance(temp2,YoutubeVideo):
                i21 = self.queue.index(temp2)
                i22 = i21 + 1
            else:
                i21 = self.queue.index(f"--{temp2.name}--")
                i22 = self.queue[i21+1:].index(f"--{temp2.name}--") + 1
            
            queue = [x for x in self.queue if type(x)!= str]
            self.queue[i11:i12],self.queue[i21:i22] = [], queue[0:1] + [self.queue[i11:i12]]


        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

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


    # ? FULL NOW
    @full.command()
    @vc_check()
    async def ow(self, ctx, change1,change2):
        '''Plays a queue member NOW.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.full_queue if type(x)!= str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            queue = [x for x in self.queue if type(x)!= str]
            self.queue[self.queue.index(queue[0]) + 1,self.queue.index(queue[0]) + 1] = temp
            self,queue_ct[1:1] = temp
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? FULL ADD
    @full.command()
    @vc_check()
    async def ad(self, ctx, change1,change2):
        '''Plays a queue member NOW.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.full_queue if type(x)!= str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]            
            self.queue += temp
            self.queue_ct += temp
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        


    # ? FULL CONTRACTED  
    @full.group(aliases = ['fct'])
    async def full_contracted(self,ctx):
        desc =""
        for index,i in enumerate(self.queue_ct):
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


    # ? CONTRACTED NOW
    @full_contracted.command()
    @vc_check()
    async def cow(self, ctx, change1,change2):
        '''Plays a queue member NOW.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = self.full_queue_ct
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            self.queue_ct[1,1] = temp
            temp2 = []
            for i in temp:
                if not isinstance(i,YoutubeVideo):
                    
                    temp2 += [f"--{i.name}--"]
                    temp2 += i.entries
                    temp2 += [f"--{i.name}--"]
                else:
                    temp2 +=[i]
            queue = [x for x in self.queue if type(x)!= str]
            self.queue[self.queue.index(queue[0]) + 1,self.queue.index(queue[0]) + 1] = temp2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? CONTRACTED ADD
    @full_contracted.command()
    @vc_check()
    async def cad(self, ctx, change1,change2):
        '''Plays a queue member NOW.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = self.full_queue_ct
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            self.queue_ct += temp
            temp2 = []
            for i in temp:
                if not isinstance(i,YoutubeVideo):
                    
                    temp2 += [f"--{i.name}--"]
                    temp2 += i.entries
                    temp2 += [f"--{i.name}--"]
                else:
                    temp2 +=[i]
            queue = [x for x in self.queue if type(x)!= str]
            self.queue += temp2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
            
# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------

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

    # ? LOOP_QUEUE

    @commands.command(aliases=['lpq'])
    @vc_check()
    async def loop_queue(self, ctx, toggle=""):
        '''Loops the queue. If on/off not passed it will toggle it.'''

        if toggle.lower() == "on":
            self.loop_q = True
            await ctx.send(">>> **Looping queue now**")

        elif toggle.lower() == 'off':
            self.loop_q = False
            await ctx.send(">>> **NOT Looping queue now**")

        else:

            if self.loop_q:
                self.loop_q = False
                await ctx.send(">>> **NOT Looping queue now**")

            else:
                self.loop_q = True
                await ctx.send(">>> **Looping queue now**")
    
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
            self.shuffle_lim = None
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
            self.shuffle_lim=None
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
    @vote(votes_required=0.5,
           vote_duration=20,
           vote_msg="Looks like somone wants to skip the current song",
            no_msg="Vote failed! Not skipping the current song.",
            yes_msg="Vote passed! Skipping the current song now...")
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
            self.shuffle_lim = None
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
    async def seek(self,ctx,time):
        queue = [x for x in self.queue if type(x)!= str]
        voice = get(self.client.voice_clients, guild=ctx.guild)

        time = await self.int_time(ctx, time)

        if time:
            voice.source = discord.FFmpegPCMAudio(queue[0].audio_url,before_options = f" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {time}")
            self.time = time
        else:
            return
    # ?FORWARD

    @commands.command(aliases=["fwd"])
    @vc_check()
    async def forward(self, ctx, time):

        queue = [x for x in self.queue if type(x) != str]

       
        voice = get(self.client.voice_clients, guild=ctx.guild)
        time = await self.int_time(ctx, time)

        if time:
            if time <= queue[0].seconds - self.time :
                voice.source = discord.FFmpegPCMAudio(queue[0].audio_url,before_options = f" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {time + self.time}")
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

        voice = get(self.client.voice_clients, guild=ctx.guild)
        time = await self.int_time(ctx, time)

        if time:
            if time <= self.time :
                voice.source = discord.FFmpegPCMAudio(queue[0].audio_url,before_options = f" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {self.time - time}")
                self.time -= time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return

    #? SHUFFLE
    @commands.command(aliases = ["shuf"])
    @vc_check()
    async def shuffle(self,ctx,amount:int = None):
        self.queue = [x for x in self.queue if type(x) != str]
        self.queue_ct = self.queue[:]
        next_queue = self.queue[1:]
        random.shuffle(next_queue)
        self.queue = [self.queue[0]] + next_queue
        if amount and amount > 0:
            self.shuffle_lim = amount


   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------


   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------



    # ? PLAYLIST

    @commands.group(aliases=["pl"])
    async def playlist(self, ctx,name = None):
        '''Shows your Playlist. Subcommands can alter your playlist'''
        if ctx.invoked_subcommand is None:
            playlist_db = gen.db_receive("playlist")
            try:
                if name:
                    if name in playlist_db[str(ctx.author.id)]:
                        playlist =  playlist_db[str(ctx.author.id)][name]
                        pname = name
                    elif name.isnumeric():
                        if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                            playlist = list(playlist_db[str(ctx.author.id)].values())[int(name)-1]
                            pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                        else:
                            await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                            return
                    else:
                        playlist = list(playlist_db[str(ctx.author.id)].values())[0]
                        pname = list(playlist_db[str(ctx.author.id)].keys())[0]
                else:
                    playlist = list(playlist_db[str(ctx.author.id)].values())[0]
                    pname = list(playlist_db[str(ctx.author.id)].keys())[0]
            except Exception as e:
                self.log(e)
                playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
                playlist = []
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}'s Playlist"
                gen.db_update("playlist", playlist_db)
        
                        
            embed = discord.Embed(title=pname,
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            no = 1
            for song in playlist:
                title = song["title"]
                embed.add_field(name=f"**{no}**", value=f"**{title}**")
                no += 1
            await ctx.send(embed=embed)

    # ? PLAYLIST ADD
    @commands.command()
    async def add(self, ctx, name, *, query):
        '''Adds a song to your Playlist.'''

        vid = await self.searching(ctx, query)

        if vid:

            playlist_db = gen.db_receive("playlist")
            try:
               
                if name in playlist_db[str(ctx.author.id)]:
                    pname = name
                elif name.isnumeric():
                    if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                        pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return
                else:
                    await ctx.send("Could not find the playlist.")
                    return
            except:
                playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}'s Playlist"
              
            print(pname)

            playlist_db[str(ctx.author.id)][pname] += [{"id":vid.id,"title":vid.title}]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {pname}")
            gen.db_update("playlist", playlist_db)

    # ? PLAYLIST ADD_PLAYLIST
    @playlist.command()
    async def add_playlist(self, ctx,name, *, query):
        '''Adds a playlist to your Playlist.'''

        vid = await self.searching(ctx, query, False)

        if vid:

            playlist_db = gen.db_receive("playlist")
            try:
                
                if name in playlist_db[str(ctx.author.id)]:
                    pname = name
                elif name.isnumeric():
                    if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                        pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return
            
                else:
                    await ctx.send("Could not find the playlist.")
                    return
            except:
                playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}'s Playlist"
                        

            playlist_db[str(ctx.author.id)][pname] += [{"id":vid.id,"title":vid.title}]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {pname}")
            gen.db_update("playlist", playlist_db)

    # ? PLAYLIST REARRANGE
    @playlist.command(aliases=["re", "change", "replace", "switch"])
    async def rearrange(self, ctx,name, P1: int, P2: int):
        '''Rearranges 2 songs/playlist places of your playlist.'''
        playlist_db = gen.db_receive("playlist")

        try:
                
            if name in playlist_db[str(ctx.author.id)]:
                pname = name
            elif name.isnumeric():
                if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                    pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return
        
            else:
                await ctx.send("Could not find the playlist.")
                return
        else:
            await ctx.send("Your playlist too smol for rearrangement.")
            return

            if P1 < 1 or P1 > len(playlist_db[str(ctx.author.id)][pname]) or P2 < 1 or P2 > len(playlist_db[str(ctx.author.id)][pname]):
                return

            playlist_db[str(ctx.author.id)][pname][P1-1], playlist_db[str(ctx.author.id)][pname][P2 - 1] = playlist_db[str(ctx.author.id)][pname][P2-1], playlist_db[str(ctx.author.id)][pname][P1-1]
            await ctx.send(f"Number {P1} and {P2} have been rearranged.")
            self.log(f"altered {pname}")

        gen.db_update("playlist", playlist_db)

    # ? PLAYLIST REMOVE
    @commands.command(aliases=["prem"])
    async def premove(self, ctx,name, R: int):
        '''Removes a song/playlist from your playlist.'''
        playlist_db = gen.db_receive("playlist")

        try:
            
            if name in playlist_db[str(ctx.author.id)]:
                pname = name
            elif name.isnumeric():
                if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                    pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return
        
            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}'s Playlist"

        else:
            if len(playlist_db[str(ctx.author.id)][pname]) < 1:
                await ctx.send("Your playlist too smol for alteration.")
                return

            if R < 1 or R > len(playlist_db[str(ctx.author.id)][pname]):
                return

            playlist_db[str(ctx.author.id)][pname].pop(R-1)
            await ctx.send(f"Number {R} has been removed.")
            self.log(f"altered {pname}")

        gen.db_update("playlist", playlist_db)

    # ? PLAYLIST NAME
    @playlist.command(aliases = [])
    async def name(self,ctx,name,new_name):
        playlist_db = gen.db_receive("playlist")
        try:
            if name in playlist_db[str(ctx.author.id)]:
                pname = name
            elif name.isnumeric():
                if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                    pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return
        
            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}'s Playlist"
        
        else:
        
            playlist_db[str(ctx.author.id)][new_name] = playlist_db[str(ctx.author.id)].pop(pname)
            gen.db_update("playlist",playlist_db)

    # ? PLAYLIST PLAY
    @playlist.command(aliases=["pp"])
    async def pplay(self, ctx,name):
        '''Plays your playlist.'''
        
        playlist_db = gen.db_receive("playlist")

        try:
            if name in playlist_db[str(ctx.author.id)]:
                pname = name
            elif name.isnumeric():
                if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                    pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return
        
            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}'s Playlist"

        else:
            if len(playlist_db[str(ctx.author.id)][pname]) < 1:
                await ctx.send("Your playlist doesn't have any songs to play")
                return

            else:
                if not (await ctx.invoke(self.client.get_command("join"))):
                    return

                voice = get(self.client.voice_clients, guild=ctx.guild)
                playlist = playlist_db[str(ctx.author.id)][pname]
                for i in range(len(playlist)):
                    if len(playlist[i]["id"]) > 11:
                        playlist[i] = YoutubePlaylist(playlist[i]["id"])
                    
                    else:
                        playlist[i] = YoutubeVideo(playlist[i]["id"])
                        
                
               
                self.queue += [f"----{pname}----"]
                self.full_queue += [f"----{pname}----"]
                for i in playlist:
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
                        for j in range(len(vid.entries)):
                            
                            _vid = YoutubeVideo(vid.entries[j][0])
                            
                            temp += [_vid]

                        old_queue = [x for x in self.queue if type(x)!= str]
                        self.queue += temp
                        self.full_queue += temp
                        vid._entries = temp
                        if len(old_queue) == 0:
                            await self.player(ctx,voice)
                        else:
                            self.log("Song added to queue") 
                            
                        self.queue += [f"--{i.title}--"]
                        self.full_queue += [f"--{i.title}--"]
                
                self.queue += [f"----{pname}----"]

                self.full_queue += [f"----{pname}----"]
           
                await ctx.send("Your Playlist has been added to the Queue.")

    # ? PLAYLIST EXPAND
    @playlist.command()
    async def expandd(self,ctx,name):
        try:
            if name in playlist_db[str(ctx.author.id)]:
                pname = name
            elif name.isnumeric():
                if int(name)>0 and int(name)<= len(playlist_db[str(ctx.author.id)]):
                    pname = list(playlist_db[str(ctx.author.id)].keys())[int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return
        
            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db[str(ctx.author.id)] = {f"{ctx.author.name}'s Playlist":[]}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}'s Playlist"

        else:
            playlist = playlist_db[str(ctx.author.id)][pname]
            npl = []
            for i in range(len(playlist)):
                if len(playlist[i]["id"]) > 11:
                    entries = YoutubePlaylist(playlist[i]["id"]).entries
                    for vid in entries:
                        npl += [{"id":vid[0],"title":vid[2]}]
                else:
                    npl += [playlist[i]]
            playlist_db[str(ctx.author.id)][pname] = npl
            gen.db_update("playlist",playlist_db)
            
# *------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




# *------------------------------------DOWNLOAD----------------------------------------------------------------------------------------------------------------------------------------------------



    # ? DOWNLOAD

    @commands.command(aliases=["dnld"])
    async def download(self, ctx, *, query):
        '''Downloads a song for you, so your pirated ass doesn't have to look for it online.'''
    
        vid = await self.searching(ctx,query)
       
        async with aiohttp.ClientSession() as cs:
            async with cs.get(vid.audio_url) as r:
                
                data = await r.read()
                filename = f"{self.DPATH}\\{vid.id}.{vid.ext}"
                temp = open(filename, 'w+b')
                temp.write(data)
                
                file = discord.File(filename,filename = f'{vid.title}.mp3')
                
                await ctx.send(file = file)
                temp.close()
                os.remove(filename)



    # ? EXPORT

    @commands.command(aliases = ["ex"])
    async def export(self,ctx,isFull = "queue"):
        if isFull.lower() != "full" or isFull.lower() != "queue" or isFull.lower() != "q" :  
            await ctx.send("only full or q or queue")
            return
        
        if isFull.lower() == "full":
            queue = [x for x in self.full_queue if type(x) != str]
        else:
            queue = [x for x in self.queue if type(x) != str] 
        
        for i in range(len(queue)):
            queue[i] = {"url": queue[i].url,"title": queue[i].title}
        url = "http://pastebin.com/api/api_post.php"
        values = {'api_option' : 'paste',
                'api_dev_key' : 'd46b0fe89434b31ed9348e080a1a5142',
                'api_paste_code' : queue,
                'api_paste_private' : '0',
                'api_paste_name' : 'queue.php',
                'api_paste_expire_date' : 'N',
                'api_paste_format' : 'json',
                'api_user_key' : ''}
        
        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8') # data should be bytes
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = response.read().decode("utf-8")
        await ctx.send(f"here is your page Mister , {the_page}") 

    #? IMPORT
    @commands.command(aliases = ["ex"])
    async def export(self,ctx,url):
        if not (await ctx.invoke(self.client.get_command("join"))):
                    return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        
        if "https://www.pastebin.com/" not in url:
            await ctx.send("Suck a dick or die or sucker punch")
            return
        part = url[-8:]
        url = "https://www.pastebin.com/raw/" + part

        response = requests.get(url)
        content = response.content.decode("utf-8") 
        if "<!DOCTYPE HTML>" in content:
            await ctx.send("nigga shut up")
            return
        content = list(content)
        for i in range(len(content)):
            if content[i] == "'":
                content[i] = '"'
        content = "".join(content)
        try:
            content = json.loads(content) 
        except:
            await ctx.send("nigga shut up")
            return

        if type(content) != list:
            await ctx.send("nigga shut up")
            return

        for i in content:
            if type(i) != dict:
                await ctx.send("nigga shut up")
                return
            if "title" not in i or "url" not in i:
                await ctx.send("nigga shut up")
                return
            
        for i in content:
            query = i["url"]
            if "http" in query:
                if "www.youtube.com" in  query:
                    split_list = re.split("/|=|&",query)
                    if "watch?v" in split_list:
                        vid = YoutubeVideo(split_list[split_list.index("watch?v")+1],requested_by=ctx.author.name)
                        if self.queue == []:
                            self.queue.append(vid)
                            await self.player(ctx,voice)
                        else:
                            self.queue.append(vid)

    @commands.command()
    async def generic_play(self,ctx):
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        ydl_opts = {
            "quiet" = True
            } 
        try:
            info = youtube_dl.YoutubeDL(ydl_opts).extract_info(url,download = False)
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
                info2[i] = "** **"

        vid = YoutubeVideo(info2["id"],info2,ctx.author)
        embed = discord.Embed(title=f"{result.title} ({result.duration}) - {result.uploader}", 
                                    url=result.url, 
                                    description = result.description,
                                    color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                        icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                        icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url = result.thumbnail)

        embed.add_field(name = "Date of Upload", value = result.date)
        embed.add_field(name = "Views", value = result.views)
        embed.add_field(name = "Likes/Dislikes", value = f"{result.likes}/{result.dislikes}")
        await ctx.send(embed=embed)

        if self.queue == []:
            self.queue.append(vid)
            await self.player(ctx,voice)
        else:
            self.queue.append(vid)

# *---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def setup(client):
    client.add_cog(Music(client))
