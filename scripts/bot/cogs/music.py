
import discord
from discord.ext.commands.core import Command, cooldown
from discord.utils import get
import aiohttp
from discord.ext import commands, tasks
import json
from typing import List, Any
import re
import requests
from asyncio import sleep, TimeoutError
import asyncio
import youtube_dl
import lyricsgenius
import random
from lyricsgenius.song import Song
from datetime import timedelta
import imp
import os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

imp.load_source("Youtube", os.path.join(
    os.path.dirname(__file__), "../../others/Youtube.py"))
from Youtube import YoutubePlaylist, YoutubeVideo, driver
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))

from state import CustomContext, GuildState, TempState

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


def vote(votes_required: float, vote_msg: str, yes_msg: str, no_msg: str, vote_duration=15):
    async def predicate(ctx: commands.Context):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        admin_emoji = "🔑"
        
        if ctx.voice_client is None:
            return True

        members = ctx.guild.voice_client.channel.members

        already_voted: List[int] = []
        reactions = {"yes": "✔", "no": "❌", "admin": admin_emoji}

        def check(reaction: discord.Reaction, user):
            return user in members and reaction.message.id == msg.id and str(reaction) in reactions.values() and not user == ctx.bot.user

        msg = await ctx.send(content=f">>> {vote_msg}")
        msg: discord.Message

        ctx.bot.loop.create_task(reactions_add(msg, reactions.values()))

        while True:
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=vote_duration,
                                                        check=lambda reaction, user: user in members and reaction.message.id == msg.id and str(reaction) in reactions.values() and not user == ctx.bot.user)
                
                if str(reaction) == reactions["admin"]:
                    supposed_admins = await reaction.users().flatten()
                    
                    for supposed_admin in supposed_admins:
                        if supposed_admin.top_role.permissions.administrator:
                            await msg.clear_reactions()
                            await msg.edit(content=">>> Admin abooz, pls demote!")
                            await msg.edit(content="Admin power excercised: " + yes_msg)
                            
                            return True
                        
            except TimeoutError:
                yes = no = 0
                admin_re = None
                new_message: discord.Message = await ctx.channel.fetch_message(msg.id)
                
                for reaction in new_message.reactions:
                    if str(reaction) == reactions["yes"]:
                        yes = reaction.count - 1
                    elif str(reaction) == reactions["no"]:
                    	no = reaction.count - 1

                total = yes + no
                result = (yes / total) >= votes_required

                if result:
                    await msg.edit(content=yes_msg + f"\n{reactions['yes']}: *{yes}* \t\t {reactions['no']}: *{no}*")
                if not result:
                    await msg.edit(content=no_msg + f"\n{reactions['yes']}: {yes}{reactions['no']}: {no}")

                await new_message.clear_reactions()
                
                return result

            else:
                if user.id not in already_voted:
                    already_voted.append(user.id)
                else:
                    await msg.remove_reaction(str(reaction), user)

    return commands.check(predicate=predicate)

def is_dj():
    def predicate(ctx):
        dj_role = GuildState(ctx.author.guild).dj_role
        
        if dj_role is None:
            return True

        for role in ctx.author.roles:
            if role.id == dj_role.id:
                return True
            
        return False
        
    return commands.check(predicate=predicate)


genius = lyricsgenius.Genius(os.environ.get("LYRICS_GENIUS_KEY"))
genius.verbose = False


class Music(commands.Cog):
    ''':musical_note: The title says it all, commands related to music and stuff.'''
    
    properties = ["queue", "full_queue", "queue_ct", "full_queue_ct", "cooldown", "loop_song", "loop_q", "skip_song", "time_for_disconnect", "shuffle_lim", "shuffle_var", "juke_box_embed_msg"]
    
    queue: List[Any] = [
    ]                                      # queue of the format [items,"playlist name",playlist items,"/playlist name",items]
    full_queue: List[Any] = []
    queue_ct: List[Any] = []
    full_queue_ct: List[Any] = []
    
    cooldown = 0

    # variable used for looping song
    loop_song = False
    loop_q = False

    skip_song = False
    # variable used for skipping song
    # time for auto disconnect
    time_for_disconnect = 300

    # str of loading emoji
    loading_emoji = ""

    # url of the image of thumbnail (vTube)
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
    juke_box_url = "https://media.discordapp.net/attachments/623969275459141652/680480864316030996/juke_box.jpg"

    time = 0

    DPATH = os.path.join(
        os.path.dirname(__file__), '../../../cache.bot/Download')
    DPATH = os.path.abspath(DPATH)
    
    dj_role_id = 0

    shuffle_lim = None
    shuffle_var = 0
   # * ------------------------------------------------------------------------------PREREQUISITES--------------------------------------------------------------------------------------------------------------

    def __init__(self, client):
        self.client = client
        self.auto_pause.start()             # starting loops for auto pause and disconnect
        self.auto_disconnector.start()
        self.guild_dis = []
        self.guild_res_cancel = []
        self.time_l = []
        
        self.clock.start()

        self.client: discord.Client
        
        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.qualified_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
        
    def exception_catching_callback(self, task):
        if task.exception():
            task.print_stack()

    def cog_unload(self):
        driver.quit()

    def cog_unload(self):
        driver.quit()

    def log(self, msg):                     # funciton for logging if developer mode is on
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[self.qualified_name]
        except:
            debug_info[self.qualified_name] = 0
        if debug_info[self.qualified_name] == 1:
            return gen.error_message(msg, gen.cog_colours[self.qualified_name])

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
        async def pause(guild):
            awoo_channel = GuildState(guild).voice_text_channel
            voice = get(self.client.voice_clients, guild=guild)

            for i in range(GuildState(guild).auto_pause_time):
                if self.disconnect_check(voice) and voice.is_playing():
                    await sleep(1)
                else:
                    break
            else:
                self.log("Player AUTO paused")
                voice.pause()
                # self.auto_resume.start()
                self.guild_res_cancel.append(guild.id) if guild.id not in self.guild_res_cancel else None
                
                if awoo_channel is None:
                    return
                
                await awoo_channel.send(f"Everyone left `{voice.channel.name}`, player paused.")
            
        coros = [pause(guild) for guild in self.client.guilds]
        
        await asyncio.gather(*coros)

    @tasks.loop(seconds=1)
    async def clock(self):
        for guild in self.time_l:
            TempState(guild).time += 1
        

    @tasks.loop(seconds=2)
    # disconnect if player is idle for the disconnecting time provided
    async def auto_disconnector(self):
        async def disconnect(guild):
            voice = get(self.client.voice_clients, guild=guild)

            for i in range(GuildState(guild).auto_disconnect_time):
                if voice and not voice.is_playing():
                    await asyncio.sleep(1)
                else:
                    break
            else:
                # await self.auto_disconnect()
                self.guild_dis.append(guild.id)
                self.guild_res_cancel.pop(guild.id) if guild.id in self.guild_res_cancel else None
                # self.auto_resume.cancel()
                
        coros = [disconnect(guild) for guild in self.client.guilds]
        
        await asyncio.gather(*coros)
        

    @tasks.loop(seconds=1)
    async def auto_resume(self):  # resumes the song if the user re-joins the vc
        
        for guild in self.client.guilds:
            if guild.id not in self.guild_res_cancel:
                continue
        
            awoo_channel = GuildState(guild).voice_text_channel
            voice = get(self.client.voice_clients, guild=guild)
            
            if voice and voice.is_paused() and not self.disconnect_check(voice):
                self.log("Music AUTO resumed")
                voice.resume()
                self.auto_resume.cancel()
                
                if awoo_channel is None:
                    continue
                await awoo_channel.send(f"Looks like someone joined `{voice.channel.name}`, player resumed.")

    @tasks.loop(seconds=1)
    async def auto_disconnect(self):  # actual disconnecting code
        for guild in self.client.guilds:
            if guild.id not in self.guild_dis:
                continue
            
            voice = get(self.client.voice_clients, guild=guild)
            awoo_channel = GuildState(guild).voice_text_channel
    
            await voice.disconnect()
            TempState(guild).queue.clear()
            self.log(f"Auto disconnected from {voice.channel.name}")
            
            if awoo_channel is None:
                continue
            await awoo_channel.send(f"Nothing much to do in the vc so left `{voice.channel.name}`")

    # * MAIN

    # ? PLAYER
     
    async def player(self, ctx, voice):  # checks queue and plays the song accordingly
        state = TempState(ctx.author.guild)
        def check_queue():
            state = TempState(ctx.author.guild)
            if (not state.loop_song) or (state.skip_song):
                if state.skip_song:
                    state.skip_song = False
                try:
                    queue = [x for x in state.queue if not type(x) == str]
                    temp = queue[0]
                    queue2 = state.queue[:]
                    queue2.remove(temp)
                    state.queue = queue2
                    if state.loop_q:
                        state.queue += [temp]
                        state.queue_ct += [temp]
                        state.full_queue += [temp]
                        state.full_queue_ct += [temp]
                        state.full_queue.remove(temp)
                        
                        queue2 = state.full_queue[:]
                        queue2.remove(temp)
                        state.full_queue = queue2
                        try:
                            state.full_queue_ct.remove(temp)
                            queue2 = state.full_queue_ct[:]
                            queue2.remove(temp)
                            state.full_queue_ct = queue2
                        except:
                            pass

                    try:
                        state.queue_ct.remove(temp)
                        
                        queue2 = state.queue_ct[:]
                        queue2.remove(temp)
                        state.queue_ct = queue2
                        if state.loop_q:
                            state.queue_ct += [temp]
                    except:
                        pass

                    def clear_pl():
                        for i in range(len(state.queue)):
                            if i != len(state.queue)-1:
                                if isinstance(state.queue[i], str) and state.queue[i] == state.queue[i+1]:
                                    if "----" in state.queue[i]:
                                        temp = state.queue[i]
                                        state.queue.remove(temp)
                                        state.queue.remove(temp)
                                        
                                        queue2 = state.queue[:]
                                        queue2.remove(temp)
                                        state.queue = queue2
                                        
                                        queue2 = state.queue[:]
                                        queue2.remove(temp)
                                        state.queue = queue2
                                        clear_pl()
                                    else:
                                        temp = state.queue[i]
                                        state.queue.remove(temp)
                                        state.queue.remove(temp)
                                        
                                        queue2 = state.queue[:]
                                        queue2.remove(temp)
                                        state.queue = queue2
                                        queue2 = state.queue[:]
                                        queue2.remove(temp)
                                        state.queue = queue2
                                        temp = temp[2:][:-2]
                                        for j in range(len(state.queue_ct)):

                                            if state.queue_ct[j].title == temp:
                                                state.queue_ct.pop(j)
                                                queue2 = state.queue_ct[:]
                                                queue2.pop(j)
                                                state.queue_ct = queue2
                                        clear_pl()

                    clear_pl()
                except:
                    pass
            fut = asyncio.run_coroutine_threadsafe(
                self.player(ctx, voice), ctx.bot.loop)
            try:
                fut.result()
            except:
                # an error happened sending the message
                pass

        flag = True
        while flag:
            
            queue = [x for x in state.queue if not type(x) == str]
           
            if queue != []:
                try:
                    await ctx.send(f"{queue[0].title} playing now.")
                    self.log("Downloaded song.")
                   
                    voice.play(discord.FFmpegPCMAudio(queue[0].audio_url, before_options="-nostats -hide_banner -loglevel 1 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                               after=lambda e: check_queue())

                    TempState(ctx.author.guild).time = 0
                    
                    # if (self.clock.current_loop == 0): #! WOT
                    #     self.clock.start()
                    if ctx.author.guild not in self.time_l:
                        self.time_l.append(ctx.author.guild)
            
                    if self.shuffle_lim:
                        
                        state.shuffle_var += 1
                        if state.shuffle_var == state.shuffle_lim:
                            await ctx.invoke(self.client.get_command("shuffle"))
                            state.shuffle_var = 0

                    self.log(f"{queue[0].title} is playing.")
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    
                except Exception as e:
                    
                    self.log(e)
                    self.log(f"{queue[0].title} cannot be played.")
                    await ctx.send(f"{queue[0].title} cannot be played.")

                    state.queue.remove(queue[0])
                    
                    queue2 = state.queue[:]
                    queue2.remove(queue[0])
                    state.queue = queue2
                    try:
                        state.queue_ct.remove(queue[0])
                        
                        queue2 = state.queue_ct[:]
                        queue2.remove(queue[0])
                        state.queue_ct = queue2
                    except:
                        pass
                    queue.pop(0)
                else:
            
                    flag = False

            else:
                
                await ctx.send(">>> All songs played. No more songs to play.")
                self.log("Ending the queue")
                if ctx.author.guild not in self.time_l:
                    self.time_l.append(ctx.author.guild)
               
                break

    async def embed_pages(self, _content, ctx: commands.Context, embed_msg: discord.Message, check=None, wait_time=90):

        if type(_content) == str:
            if len(_content) < 2048:
                return

        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        def default_check(reaction: discord.Reaction, user):
            return user == ctx.author and reaction.message.id == embed_msg.id

        if check is None:
            check = lambda reaction, user: user == ctx.author and reaction.message.id == embed_msg.id

    
        if type(_content) == str:
            content_list = _content.split("\n")
            content = []
            l = ""
            for i in content_list:
                if len(l+i) > 2048:
                    content += [l]
                    l = ""
                l += i
                l += "\n"
            else:
                content += [l]

        elif type(_content) == list:
            content = _content

        pages = len(content)
        page = 1

        embed: discord.Embed = embed_msg.embeds[0]

        def embed_update(page):
            embed.description = content[page - 1]
            return embed

        await embed_msg.edit(embed=embed_update(page=page))

        reactions = {"back": "⬅", "delete": "❌", "forward": "➡"}

        self.client.loop.create_task(reactions_add(
            reactions=reactions.values(), message=embed_msg))

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
                        await embed_msg.delete(delay=3)

                        return

                    await embed_msg.edit(embed=embed_update(page=page))

    # ? SEARCHING
    async def searching(self, ctx, query, isVideo: bool = True, VideoClass: bool = True):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        if isVideo:
            results = YoutubeVideo.from_query(query, 5)
        else:
            results = YoutubePlaylist.from_query(query, 5)

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

        if isVideo:
            for index, result in enumerate(results):
                embed.add_field(name=f"*{index + 1}.*",
                                value=f"**{result[1]} ({result[3]}) - {result[2]}**", inline=False)

        else:

            for index, result in enumerate(results):
                embed.add_field(name=f"*{index + 1}.*",
                                value=f"**{result.title} ({result.duration}) - {result.uploader}**", inline=False)

        await embed_msg.edit(content="", embed=embed)

        self.client.loop.create_task(
            reactions_add(embed_msg,list(reactions.keys())[:len(results)]))

        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time,
                                                             check=lambda reaction, user: user == ctx.author and reaction.message.id == embed_msg.id)
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

    @commands.command(aliases=["j"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @is_dj()
    async def join(self, ctx: CustomContext) -> bool:
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
    @commands.command(aliases=["plae"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def play(self, ctx, *, query):
        '''Plays the audio of the video in the provided VTUBE url.'''
       
        state = TempState(ctx.author.guild)
        
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        if "http" in query:
            if "www.youtube.com" in query:
                split_list = re.split("/|=|&", query)
                if "watch?v" in split_list:
                    vid = YoutubeVideo(split_list[split_list.index(
                        "watch?v")+1], requested_by=ctx.author.name)

                elif "playlist?list" in split_list:
                    vid = YoutubePlaylist(split_list[split_list.index(
                        "playlist?list")+1], requested_by=ctx.author.name)
                else:
                    await ctx.send("Couldn't find neither video or playlist.")
                    return

            else:
                await ctx.send("This command only works with youtube.")
                return
        else:
            try:
                vid = YoutubeVideo(YoutubeVideo.from_query(query=query)[
                                0][0], requested_by=ctx.author.name)
            except:
                await ctx.send("There was a problem in playing your song, sorry.")
                
        
       
        #! Queueing starts here
        voice = get(self.client.voice_clients, guild=ctx.guild)
       
        old_queue = [x for x in state.queue if type(x) != str]
    
        q_num = len(old_queue) + 1

        self.loading_emoji = str(discord.utils.get(
            ctx.guild.emojis, name="loading"))
        
        message = await ctx.send(f"Searching song `{vid.title}`.... {self.loading_emoji}")
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
        
        await message.edit(content="", embed=embed)

        state.queue_ct += [vid]
        state.full_queue_ct += [vid]

        if isinstance(vid, YoutubeVideo):
            old_queue = [x for x in state.queue if type(x) != str]
            state.queue += [vid]
            state.full_queue += [vid]
         
            if len(old_queue) == 0:
                await self.player(ctx, voice)
            
            else:
                self.log("Song added to queue")
        else:
            state.queue += [f"--{vid.title}--"]
            state.full_queue += [f"--{vid.title}--"]
            temp = []
            
            flog = False
            for i in range(len(vid.entries)):
                old_queue = [x for x in TempState(ctx.author.guild).queue if type(x) != str]
                _vid = YoutubeVideo(vid.entries[i][0])
                             
                if len(old_queue) == 0:
                    print(_vid)
                    state.queue += [_vid]
                    flog = True
                    print(state.queue)
                    await self.player(ctx, voice)
                    
                else:
                    self.log("Song added to queue")
                    
                temp.append(_vid)
                 
            if flog:
                state.queue += temp[1:]
            else:
                state.queue += temp
            state.full_queue += temp
            vid._info["entries"] = temp
            
            state.queue += [f"--{vid.title}--"]
            state.full_queue += [f"--{vid.title}--"]

    # ? PLAY PLAYLIST
    @commands.command(name="play-playlist", aliases=["ppl"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def play_playlist(self, ctx, *, query):
        play_command = self.client.get_command("play")
        if("https://www.youtube.com/playlist?list" in query):
            await ctx.invoke(play_command, query=query)
        else:
            vid_list = YoutubePlaylist.from_query(query)
            if vid_list == []:
                await ctx.send(">>> Cant find playlist.")
                return
            else:
                vid = vid_list[0]
                await ctx.invoke(play_command, query=f"https://www.youtube.com/playlist?list={vid.id}")

    # ? SEARCH

    @commands.command(aliases=["s"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def search(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        if not (await ctx.invoke(self.client.get_command("join"))):
            return
        result = await self.searching(ctx, query, VideoClass=False)
        if result:
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=f"https://www.youtube.com/watch?v={result[0]}")

    # ? SEARCH_PLAYLIST
    @commands.command(name="search-playlist", aliases=["spl"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def search_playlist(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        if not (await ctx.invoke(self.client.get_command("join"))):
            return
        result = await self.searching(ctx, query, False)
        if result:
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=f"https://www.youtube.com/playlist?list={result.id}")

    # ? NOW PLAYING

    @commands.command(name="now-playing", aliases=["np"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def now_playing(self, ctx):
        state = TempState(ctx.author.guild)
        queue = [x for x in state.queue if type(x) != str]
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
            ntime = f"{state.time//60}:{two_dig(state.time%60)}"
        else:
            ntime = f"{state.time//3600}:{two_dig(state.time%3600//60)}:{two_dig(state.time//60)}"
            
        ntime = str(timedelta(seconds=state.time))
        
        embed.add_field(name=f"{vid.title}", value="**  **", inline=False)
        
        amt = int(state.time/vid.seconds*10)
        
        ntime = ntime.split(":")
        for i in range(3 - len(vid.duration.split(":"))):
            ntime.pop(i)
        ntime = ":".join(ntime)
        
        embed.add_field(
            name=f"{ntime}/{vid.duration} {':black_square_button:'*amt +':black_large_square:'*(10-amt) }", value="**  **", inline=False)

        await ctx.send(embed=embed)

    # ? LYRICS
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def lyrics(self, ctx: commands.Context):
        
        state = TempState(ctx.author.guild)
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        queue = [x for x in state.queue if type(x) != str]
        vid = queue[0]
        song = genius.search_song(vid.title)
        if not song:
            await ctx.send("Can't Find lyrics. Try using choose-lyrics command.")
            return
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

        await self.embed_pages(ctx=ctx, _content=lyrics, embed_msg=embed_msg, wait_time=120)
        
    @commands.command(name="choose-lyrics")
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def clyrics(self, ctx: commands.Context,query = None):
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

        self.client.loop.create_task(reactions_add(embed_msg, reactions.keys()[:len(hits)]))
        
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

                    await self.embed_pages(ctx=ctx, _content=lyrics, embed_msg=embed_msg, wait_time=120)

    # ? SONG_INFO

    @commands.command(name="song-info", aliases=["sinfo", "sf"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def song_info(self, ctx, *, query):
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
    @commands.command(name="playlist-info", aliases=["plinfo", "pf"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def playlist_info(self, ctx, *, query):

        result = await self.searching(ctx, query, False)

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


# *-------------------------------------------------------QUEUE------------------------------------------------------------------------------------------------------------------------

    # ? QUEUE


    @commands.group(name="queue", aliases=['q'])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def Queue(self, ctx):
        '''Shows the current queue.'''
        state = TempState(ctx.author.guild)
        if ctx.invoked_subcommand is None:
            i = 0
            j = 1
            desc = ""
            while i < len(state.queue):
                if isinstance(state.queue[i], YoutubeVideo):
                    desc += f"{j}. {state.queue[i].title} ({state.queue[i].duration}) \n"
                    i += 1
                    j += 1
                else:
                    desc += f"***{state.queue[i]}*** \n"
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
    @Queue.command()
    @vc_check()
    async def replace(self, ctx, change1, change2):
        '''Replaces two queue members.'''
        state = TempState(ctx.author.guild)
        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.queue if type(x) != str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue):
            await ctx.send(f">>> Switched the places of **{queue[change2-1].title}** and **{queue[change1-1].title}**")
            state.queue[state.queue.index(queue[change1-1])], state.queue[state.queue.index(queue[change2-1])
                                                                       ] = state.queue[state.queue.index(queue[change2-1])], state.queue[state.queue.index(queue[change1-1])]
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? QUEUE REMOVE
    @Queue.command()
    @vc_check()
    async def remove(self, ctx, remove):
        '''Removes the Queue member.'''
        state = TempState(ctx.author.guild)
        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.queue if type(x) != str]
        if remove > 1 and remove <= len(queue):
            await ctx.send(f">>> Removed **{(queue[remove - 1].title)}** from the queue.")
            state.queue.remove(queue[remove-1])
            
            queue2 = state.queue[:]
            queue2.remove(queue[remove-1])
            state.queue = queue2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? QUEUE NOW
    @Queue.command()
    @vc_check()
    async def now(self, ctx, change):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)
        try:
            change = int(change)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.queue if type(x) != str]
        if change > 1 and change <= len(queue):
            temp = queue[change-1]
            state.queue.pop(state.queue.index(queue[change-1]))
            queue2 = state.queue[:]
            queue2.pop(state.queue.index(queue[change-1]))
            state.queue = queue2
            
            state.queue.insert(state.queue.index(queue[0]) + 1, temp)
            
            queue2 = state.queue[:]
            queue2.insert(state.queue.index(queue[0]) + 1, temp)
            state.queue = queue2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? QUEUE CONTRACTED
    @Queue.group(aliases=['ct'])
    async def contracted(self, ctx):
        if ctx.invoked_subcommand is None:
            desc = ""
            #TODO shit

            for index in range(len(TempState(ctx.author.guild).queue_ct)):
                i = TempState(ctx.author.guild).queue_ct[index]

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

    # ? CONTRACTED REMOVE
    @contracted.command()
    async def remm(self, ctx, remove):
        '''Removes the Queue member.'''
        
        state = TempState(ctx.author.guild)
        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.queue_ct
        if remove > 1 and remove <= len(queue):
            temp = queue[remove-1]
            state.queue_ct.remove(temp)
            
            queue2 = state.queue_ct[:]
            queue2.remove(temp)
            state.queue_ct = queue2
            if isinstance(temp, YoutubeVideo):

                state.queue.remove(temp)
                queue2 = state.queue[:]
                queue2.remove(temp)
                state.queue = queue2
                await ctx.send(f">>> Removed **{(temp.title)}** from the queue.")
            else:

                i1 = state.queue.index(f"--{temp.name}--")
                i2 = state.queue[i1+1:].index(f"--{temp.name}--")
                state.queue[i1:i2+1] = []

        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? CONTRACTED REPLACE
    @contracted.command()
    @vc_check()
    async def repla(self, ctx, change1, change2):
        '''Replaces two queue members.'''
        state = TempState(ctx.author.guild)
        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.queue_ct
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue):
            temp1 = queue[change2-1]
            temp2 = queue[change1-1]
            await ctx.send(f">>> Switched the places of **{temp1.title}** and **{temp2.title}**")
            state.queue_ct[state.queue_ct.index(temp1)], state.queue_ct[state.queue_ct.index(
                temp2)] = state.queue_ct[state.queue_ct.index(temp2)], state.queue_ct[state.queue_ct.index(temp1)]

            if isinstance(temp1, YoutubeVideo):
                i11 = state.queue.index(temp1)
                i12 = i11 + 1
            else:
                i11 = state.queue.index(f"--{temp1.name}--")
                i12 = state.queue[i11+1:].index(f"--{temp1.name}--") + 1

            if isinstance(temp2, YoutubeVideo):
                i21 = state.queue.index(temp2)
                i22 = i21 + 1
            else:
                i21 = state.queue.index(f"--{temp2.name}--")
                i22 = state.queue[i21+1:].index(f"--{temp2.name}--") + 1

            state.queue[i11:i12], state.queue[i21:i22] = state.queue[i21:i22], state.queue[i11:i12]
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? CONTRACTED NOW

    @contracted.command()
    @vc_check()
    async def no(self, ctx, change):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)
        try:
            change = int(change)
        except: 
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.queue_ct
        if change > 1 and change <= len(queue):
            temp1 = queue[change-1]
            temp2 = queue[0]
            state.queue_ct.pop(state.queue.index(temp1))
            
            queue2 = state.queue_ct[:]
            queue2.pop(state.queue.index(temp1))
            state.queue_ct = queue2
            
            state.queue_ct.insert(1, temp1)
            queue2 = state.queue_ct[:]
            queue2.insert(1, temp1)
            state.queue_ct = queue2
            
            state.queue_ct.pop(0)
            queue2 = state.queue_ct[:]
            queue2.pop(0)
            state.queue_ct = queue2

            if isinstance(temp1, YoutubeVideo):
                i11 = state.queue.index(temp1)
                i12 = i11 + 1
            else:
                i11 = state.queue.index(f"--{temp1.name}--")
                i12 = TempState(ctx.author.guild).queue[i11+1:].index(f"--{temp1.name}--") + 1

            if isinstance(temp2, YoutubeVideo):
                i21 = state.queue.index(temp2)
                i22 = i21 + 1
            else:
                i21 = state.queue.index(f"--{temp2.name}--")
                i22 = state.queue[i21+1:].index(f"--{temp2.name}--") + 1

            queue = [x for x in state.queue if type(x) != str]
            state.queue[i11:i12], state.queue[i21:i22] = [
            ], queue[0:1] + [state.queue[i11:i12]]

        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? QUEUE FULL
    @Queue.group(name="full")
    async def full(self, ctx):
        state = TempState(ctx.author.guild)
        if ctx.invoked_subcommand is None:
            i = 0
            j = 1
            desc = ""
            while i < len(state.full_queue):
                if isinstance(state.full_queue[i], YoutubeVideo):
                    desc += f"{j}. {state.full_queue[i].title} ({state.full_queue[i].duration}) \n"
                    i += 1
                    j += 1
                else:
                    desc += f"***{state.full_queue[i]}*** \n"
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
    async def ow(self, ctx, change1, change2):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.full_queue if type(x) != str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            queue = [x for x in state.queue if type(x) != str]
            state.queue[state.queue.index(queue[0]) + 1, state.queue.index(queue[0]) + 1] = temp
            self, queue_ct[1:1] = temp
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? FULL ADD
    @full.command() #! yo wat
    @vc_check()
    async def ad(self, ctx, change1, change2):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.full_queue if type(x) != str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            state.queue += temp
            state.queue_ct += temp
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? FULL CONTRACTED

    @full.group(aliases=['fct'])
    async def full_contracted(self, ctx):
        state = TempState(ctx.author.guild)
        desc = ""
        for index, i in enumerate(state.queue_ct):
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
    async def cow(self, ctx, change1, change2):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)
        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.full_queue_ct
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            state.queue_ct[1, 1] = temp
            temp2 = []
            for i in temp:
                if not isinstance(i, YoutubeVideo):

                    temp2 += [f"--{i.name}--"]
                    temp2 += i.entries
                    temp2 += [f"--{i.name}--"]
                else:
                    temp2 += [i]
            queue = [x for x in state.queue if type(x) != str]
            state.queue[state.queue.index(
                queue[0]) + 1, state.queue.index(queue[0]) + 1] = temp2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

    # ? CONTRACTED ADD
    @full_contracted.command()
    @vc_check()
    async def cad(self, ctx, change1, change2):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.full_queue_ct
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue) and change2 >= change1:
            temp = queue[change1:change2+1]
            state.queue_ct += temp
            temp2 = []
            for i in temp:
                if not isinstance(i, YoutubeVideo):

                    temp2 += [f"--{i.name}--"]
                    temp2 += i.entries
                    temp2 += [f"--{i.name}--"]
                else:
                    temp2 += [i]
            queue = [x for x in state.queue if type(x) != str]
            state.queue += temp2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------

# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------

    # ? LOOP

    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def loop(self, ctx, toggle=""):
        state = TempState(ctx.author.guild)
        '''Loops the current song, doesn't affect the skip command tho. If on/off not passed it will toggle it.'''
    
        if toggle.lower() == "on":
            state.loop_song = True
            await ctx.send(">>> **Looping current song now**")

        elif toggle.lower() == 'off':
            state.loop_song = False
            await ctx.send(">>> **NOT Looping current song now**")

        else:

            if state.loop_song:
                state.loop_song = False
                await ctx.send(">>> **NOT Looping current song now**")

            else:
                state.loop_song = True
                await ctx.send(">>> **Looping current song now**")
        

    # ? LOOP_QUEUE

    @commands.command(name="loop-queue", aliases=["loopq", "lq"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def loop_queue(self, ctx, toggle=""):
        '''Loops the queue. If on/off not passed it will toggle it.'''
        state = TempState(ctx.author.guild)
        if toggle.lower() == "on":
            state.loop_q = True
            await ctx.send(">>> **Looping queue now**")

        elif toggle.lower() == 'off':
            state.loop_q = False
            await ctx.send(">>> **NOT Looping queue now**")

        else:

            if state.loop_q:
                state.loop_q = False
                await ctx.send(">>> **NOT Looping queue now**")

            else:
                state.loop_q = True
                await ctx.send(">>> **Looping queue now**")

    # ? RESTART

    @commands.command(aliases=["res"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def restart(self, ctx):
        '''Restarts the current song.'''
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            temp = state.loop_song
            state.loop_song = True

            voice.stop()
            await asyncio.sleep(0.1)
            state.loop_song = temp
        else:
            self.log("Restart failed")
            await ctx.send(">>> Ya know to restart stuff, stuff also needs to be playing first.")

   # ? PAUSE

    @commands.command(aliases=["p"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def pause(self, ctx):
        '''Pauses the current music.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            self.log("Player paused")
            voice.pause()
            if ctx.author.guild in self.time_l:
                self.time_l.remove(ctx.author.guild)
            await ctx.send(">>> Music Paused")
        else:
            self.log("Pause failed")
            await ctx.send(">>> Ya know to pause stuff, stuff also needs to be playing first.")

    # ? RESUME

    @commands.command(aliases=["r"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def resume(self, ctx):
        '''Resumes the current music.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            self.log("Music resumed")
            voice.resume()
            if ctx.author.guild not in self.time_l:
                self.time_l.append(ctx.author.guild)
            await ctx.send(">>> Resumed Music")
        else:
            self.log("Resume failed")
            await ctx.send(">>> Ya know to resume stuff, stuff also needs to be paused first.")

    # ? STOP
    @commands.command(aliases=["st"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def stop(self, ctx):
        '''Stops the current music AND clears the current queue.'''
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)
        state.queue = []
        state.queue_ct = []

        if voice and voice.is_playing:
            self.log("Player stopped")
            voice.stop()
            if ctx.author.guild in self.time_l:
                self.time_l.remove(ctx.author.guild)
            state.time = 0
            state.shuffle_lim = None
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")

    # ? HARD_STOP
    @commands.command(name="hardstop", aliases=["hst"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def hard_stop(self, ctx):
        '''Stops the current music AND clears the current queue.'''
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)
        state.queue = [] 
        state.full_queue = [] 
        state.queue_ct = [] 
        state.full_queue_ct = [] 

        if voice and voice.is_playing:
            self.log("Player stopped")
            voice.stop()
            if ctx.author.guild in self.time_l:
                self.time_l.remove(ctx.author.guild)
            state.time = 0
            state.shuffle_lim = None
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")
        try:
            self.queue_delete() #! WOT
        except:
            pass
    # ? SKIP

    @commands.command(aliases=["skip", "sk", "nxt"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    @vote(votes_required=0.5,
          vote_duration=20,
          vote_msg="Looks like somone wants to skip the current song, VOTE!",
          no_msg="Vote failed! Not skipping the current song.",
          yes_msg="Vote passed! Skipping the current song now...")
    async def next(self, ctx):
        '''Skips the current song and plays the next song in the queue.
        Requires atleast 50% of people to vote yes
        '''
        
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            state.skip_song = True
            self.log("Playing next song")
            voice.stop()
            await ctx.send(">>> ***Song skipped.***")
        else:
            self.log("Skip failed")
            await ctx.send(">>> Wat you even trynna skip? There is ***nothing to*** skip, I am surrounded by idiots")

    # ? BACK

    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def back(self, ctx):
        '''Plays previous song.'''
        
        def find_sub_list(sl,l):
            results=[]
            sll=len(sl)
            for ind in (i for i,e in enumerate(l) if e==sl[0]):
                if l[ind:ind+sll]==sl:
                    results.append((ind,ind+sll-1))
            return int(results[0][0])
        
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice:
            fq = [x for x in state.full_queue if not isinstance(x, str)]
            q = [x for x in state.queue if not isinstance(x, str)]
            
            state.queue = [fq[find_sub_list(q, fq) - 1]] + state.queue
            
            if not voice.is_playing():

                if len(state.queue) == 1:
                    await self.player(ctx, voice)
                elif voice.is_paused():
                    voice.resume()
                    await ctx.invoke(self.client.get_command("restart"))

            else:
                await ctx.invoke(self.client.get_command("restart"))

    # ? LEAVE
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def leave(self, ctx):
        '''Leaves the voice channel.'''
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            if ctx.author.guild in self.time_l:
                self.time_l.remove(ctx.author.guild)
            state.time = 0
            state.shuffle_lim = None
            await ctx.send(f">>> Left ```{voice.channel.name}```")
            state.queue.clear()
            state.full_queue.clear()
            state.queue_ct.clear()
            state.full_queue_ct.clear()
        else:
            await ctx.send(">>> I cannot leave a voice channel I have not joined, thought wouldn't need to explain basic shit like this.")

        try:
            self.queue_delete() #? WOT
        except:
            pass
    # ? VOLUME

    @commands.command(aliases=["v", "vl"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
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
        state = TempState(ctx.author.guild)
        queue = [x for x in state.queue if type(x) != str]
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

    #  # ? BACK
    # @commands.command()
    # @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    # @vc_check()
    # async def back(self, ctx):
    #     '''Plays previous song.'''
    #     state = TempState(ctx.author.guild)
    #     voice = get(self.client.voice_clients, guild=ctx.guild)

    #     if voice:
    #         fq = [x for x in state.full_queue if not isinstance(x, str)]
    #         q = [x for x in state.queue if not isinstance(x, str)]
    #         state.queue += [fq[-(len(q)+1)]]
    #         if not voice.is_playing():

    #             if len(state.queue) == 1:
    #                 await self.player(ctx, voice)
    #             elif voice.is_paused():
    #                 voice.resume()
    #                 await ctx.invoke(self.client.get_command("restart"))

    #         else:
    #             await ctx.invoke(self.client.get_command("restart"))

    # ?SEEK
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def seek(self, ctx, time):
        """Skip ahead to a timestamp in the current song"""
        state = TempState(ctx.author.guild)
        
        queue = [x for x in state.queue if type(x) != str]
        voice = get(self.client.voice_clients, guild=ctx.guild)

        time = await self.int_time(ctx, time)

        if time:
            voice.source = discord.FFmpegPCMAudio(
                queue[0].audio_url, before_options=f"-nostats -hide_banner -loglevel 1 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {time}")

            state.time = time
          
        else:
            return
    # ?FORWARD

    @commands.command(aliases=["fwd"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def forward(self, ctx, time):
        """Go forward by given seconds in the current song"""
        state = TempState(ctx.author.guild)
        queue = [x for x in state.queue if type(x) != str]

        voice = get(self.client.voice_clients, guild=ctx.guild)
        time = await self.int_time(ctx, time)

        if time:
            if time <= queue[0].seconds - state.time:
                voice.source = discord.FFmpegPCMAudio(
                    queue[0].audio_url, before_options=f"-nostats -hide_banner -loglevel 1 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {time + state.time}")
                state.time += time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return

    # ?REWIND
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def rewind(self, ctx, time):
        """Go back by given seconds in the current song"""
        state = TempState(ctx.author.guild)
        queue = [x for x in state.queue if type(x) != str]

        voice = get(self.client.voice_clients, guild=ctx.guild)
        time = await self.int_time(ctx, time)

        if time:
            if time <= state.time:
                voice.source = discord.FFmpegPCMAudio(
                    queue[0].audio_url, before_options=f"-nostats -hide_banner -loglevel 1 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {state.time - time}")
                state.time -= time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return

    # ? SHUFFLE
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @vc_check()
    async def shuffle(self, ctx, amount: int = None):
        state = TempState(ctx.author.guild)
        """Shuffle the current queue"""
        state.queue = [x for x in state.queue if type(x) != str]
        state.queue_ct = state.queue[:]
        next_queue = state.queue[1:]
        random.shuffle(next_queue)
        state.queue = [state.queue[0]] + next_queue
        if amount and amount > 0:
            state.shuffle_lim = amount

   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------

   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------

    # ? PLAYLIST
    
    @commands.group(aliases=["pl"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def playlist(self, ctx):
        if ctx.invoked_subcommand is None:
            pl_db = ctx.States.User.playlist
            
            embed = discord.Embed(title="",
                                color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                                icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            
            for no, playlist in enumerate(pl_db.keys()):
                embed.add_field(name=f"**{no + 1}.**", value=f"**{playlist}** \t\t `{len(pl_db[playlist])}`", inline=False)
            
            await ctx.send(embed=embed)
            
    @playlist.command(aliases=["make"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def new(self, ctx, name):
        playlist_db = ctx.States.User.playlist
        
        if name in playlist_db.keys():
            await ctx.send("Playlists can't have the same name, I know creativity is lacking but think of a different name.")
            return
            
        playlist_db = {**playlist_db, **{name: []}}
        ctx.States.User.playlist = playlist_db
        
        await ctx.send(f"A playlist with the name `{name}` was created, use the `playlist add` command to add songs.")
        

    @playlist.command(aliases=["v"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def view(self, ctx, name=None):
        '''Shows your Playlist. Subcommands can alter your playlist'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist
        try:
            if name:
                if name in playlist_db:
                    playlist = playlist_db[name]
                    pname = name
                elif name.isnumeric():
                    if int(name) > 0 and int(name) <= len(playlist_db):
                        playlist = list(playlist_db.values())[
                            int(name)-1]
                        pname = list(playlist_db.keys())[
                            int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return
                else:
                    playlist = list(
                        playlist_db.values())[0]
                    pname = list(playlist_db.keys())[0]
            else:
                playlist = list(
                    playlist_db.values())[0]
                pname = list(playlist_db.keys())[0]
        except Exception as e:
            self.log(e)
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            playlist = []
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"
            ctx.States.User.playlist = playlist_db

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
    @playlist.command()
    async def add(self, ctx, name, *, query):
        '''Adds a song to your Playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        if "http" in query:
            if "www.youtube.com" in query:
                split_list = re.split("/|=|&", query)
                if "watch?v" in split_list:
                    vid = YoutubeVideo(split_list[split_list.index(
                        "watch?v")+1], requested_by=ctx.author.name)
        else:
            vid = await self.searching(ctx, query)

        if vid:

            playlist_db = ctx.States.User.playlist
            try:

                if name in playlist_db:
                    pname = name
                elif name.isnumeric():
                    if int(name) > 0 and int(name) <= len(playlist_db):
                        pname = list(playlist_db.keys())[
                            int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return
                else:
                    await ctx.send("Could not find the playlist.")
                    return
            except:
                playlist_db = {
                    f"{ctx.author.name}Playlist": []}
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}Playlist"

            playlist_db[pname] += [{"id": vid.id, "title": vid.title}]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {pname}")
            
            ctx.States.User.playlist = playlist_db

    # ? PLAYLIST ADD_PLAYLIST
    @playlist.command(name="add-playlist", aliases=["addpl"])
    async def add_playlist(self, ctx, name, *, query):
        '''Adds a playlist to your Playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        vid = await self.searching(ctx, query, False)

        if vid:

            playlist_db = ctx.States.User.playlist
            try:

                if name in playlist_db:
                    pname = name
                elif name.isnumeric():
                    if int(name) > 0 and int(name) <= len(playlist_db):
                        pname = list(playlist_db.keys())[
                            int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return

                else:
                    await ctx.send("Could not find the playlist.")
                    return
            except:
                playlist_db = {
                    f"{ctx.author.name}Playlist": []}
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}Playlist"

            playlist_db[str(ctx.author.id)
                        ][pname] += [{"id": vid.id, "title": vid.title}]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {pname}")
            ctx.States.User.playlist = playlist_db

    # ? PLAYLIST REARRANGE
    @playlist.command(aliases=["rng"])
    async def rearrange(self, ctx, name, P1: int, P2: int):
        '''Rearranges 2 songs/playlist places of your playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist

        try:

            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            pass 
        else:
            await ctx.send("Your playlist too smol for rearrangement.")
            return

        if P1 < 1 or P1 > len(playlist_db[pname]) or P2 < 1 or P2 > len(playlist_db[pname]):
            return

        playlist_db[pname][P1-1], playlist_db[pname][P2 - 1] = playlist_db[pname][P2-1], playlist_db[pname][P1-1]
                                                                                                
        await ctx.send(f"Number {P1} and {P2} have been rearranged.")
        self.log(f"altered {pname}")

        ctx.States.User.playlist = playlist_db

    # ? PLAYLIST REMOVE
    @commands.command(name="plremove") #! experimentation
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def plremove(self, ctx, name, R: int):
        '''Removes a song/playlist from your playlist.'''
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist

        try:

            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:
            if len(playlist_db[pname]) < 1:
                await ctx.send("Your playlist too smol for alteration.")
                return

            if R < 1 or R > len(playlist_db[pname]):
                return

            playlist_db[pname].pop(R-1)
            await ctx.send(f"Number {R} has been removed.")
            self.log(f"altered {pname}")

        ctx.States.User.playlist = playlist_db

    # ? PLAYLIST NAME
    @playlist.command()
    async def name(self, ctx, name, new_name):
        """Give a name to your playlist"""
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist
        try:
            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:

            playlist_db[new_name] = playlist_db.pop(pname)
            
            ctx.States.User.playlist = playlist_db

    # ? PLAYLIST PLAY
    @playlist.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def plplay(self, ctx, name):
        '''Plays your playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        playlist_db = ctx.States.User.playlist
        state = TempState(ctx.author.guild)

        try:
            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:   
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:
            if len(playlist_db[pname]) < 1:
                await ctx.send("Your playlist doesn't have any songs to play")
                return

            else:
                if not (await ctx.invoke(self.client.get_command("join"))):
                    return

                voice = get(self.client.voice_clients, guild=ctx.guild)
                playlist = playlist_db[pname]
                for i in range(len(playlist)):
                    if len(playlist[i]["id"]) > 11:
                        playlist[i] = YoutubePlaylist(playlist[i]["id"])

                    else:
                        playlist[i] = YoutubeVideo(playlist[i]["id"])

                state.queue += [f"----{pname}----"]
                state.full_queue += [f"----{pname}----"]

                temp = []
                for i in playlist:
                    state.full_queue_ct += [i]
                    state.queue_ct += [i]

                    if isinstance(i, YoutubeVideo):
                        old_queue = [x for x in state.queue if type(x) != str]
                        state.queue += [i]
                        state.full_queue += [i]

                        if len(old_queue) == 0:
                            await self.player(ctx, voice)
                        else:
                            self.log("Song added to queue")

                    else:
                        state.queue += [f"--{i.title}--"]
                        state.full_queue += [f"--{i.title}--"]
                        for j in range(len(i.entries)):

                            _vid = YoutubeVideo(i.entries[j][0])

                            temp += [_vid]

                        old_queue = [x for x in state.queue if type(x) != str]
                        state.queue += temp
                        state.full_queue += temp
                        vid._info["entries"] = temp
                        if len(old_queue) == 0:
                            await self.player(ctx, voice)
                        else:
                            self.log("Song added to queue")

                        state.queue += [f"--{i.title}--"]
                        state.full_queue += [f"--{i.title}--"]

                state.queue += [f"----{pname}----"]

                state.full_queue += [f"----{pname}----"]

                await ctx.send("Your Playlist has been added to the Queue.")
                
    # ? PLAYLIST EXPAND
    @playlist.command(name="expand")
    async def expandd(self, ctx, name):
        playlist_db = ctx.States.User.playlist
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        try:
            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:
            playlist = playlist_db[pname]
            npl = []
            for i in range(len(playlist)):
                if len(playlist[i]["id"]) > 11:
                    entries = YoutubePlaylist(playlist[i]["id"]).entries
                    for vid in entries:
                        npl += [{"id": vid[0], "title":vid[2]}]
                else:
                    npl += [playlist[i]]
            playlist_db[pname] = npl
            
            ctx.States.User.playlist = playlist_db

# *------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# *------------------------------------DOWNLOAD----------------------------------------------------------------------------------------------------------------------------------------------------

    
    # ? DOWNLOAD


    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def download(self, ctx, *, query):
        '''Downloads a song for you, so your pirated ass doesn't have to look for it online.'''
        if "http" in query:
            if "www.youtube.com" in query:
                split_list = re.split("/|=|&", query)
                if "watch?v" in split_list:
                    vid = YoutubeVideo(split_list[split_list.index(
                        "watch?v")+1], requested_by=ctx.author.name)
        else:
            vid = await self.searching(ctx, query)
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
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def export(self, ctx, isFull="queue"):
        """Convert your playlist to text, gives a pastebin url"""
        
        if not(isFull.lower() == "full" or isFull.lower() == "queue" or isFull.lower() == "q"):
            await ctx.send("only full or q or queue")
            return 

        if isFull.lower() == "full":
            queue = [x for x in self.full_queue if type(x) != str]
        else:
            queue = [x for x in TempState(ctx.author.guild).queue if type(x) != str]

        for i in range(len(queue)):
            queue[i] = {"url": queue[i].url, "title": queue[i].title}
  
        url = "https://hastebin.com/documents"
        response = requests.post(url, data=json.dumps(queue))
        the_page = "https://hastebin.com/raw/" + response.json()['key']
        await ctx.send(f"Here is your page Master, {the_page}")

    # ? IMPORT
    @commands.command(name="import")
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
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
                        vid = YoutubeVideo(split_list[split_list.index(
                            "watch?v")+1], requested_by=ctx.author.name)
                        state = TempState(ctx.author.guild)
                        state.queue +=[vid]
                        state.full_queue +=[vid]
                        state.queue_ct +=[vid]
                        state.full_queue_ct +=[vid] 
                        if len(state.queue) == 1:
                            await self.player(ctx, voice)
                        

    @commands.command(name="generic-play", aliases=["gp", "genplay"])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def generic_play(self, ctx, url):
        """This commands tries its hardest to play any video (not just YouTube), provided the link"""
        
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)
        ydl_opts = {
            "quiet": True
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
                info2[i] = "** **"

        result = YoutubeVideo(info2["id"], info2, ctx.author)

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

        if TempState(ctx.author.guild).queue == []:
            TempState(ctx.author.guild).queue.append(result)
            await self.player(ctx, voice)
        else:
            TempState(ctx.author.guild).queue.append(result)

# *---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def setup(client):
    client.add_cog(Music(client))
