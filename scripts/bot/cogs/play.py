import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands,tasks
from discord.ext.commands.core import Command, cooldown
from discord.utils import get
import asyncio
from asyncio import sleep, TimeoutError
import re
import general as gen
from state import TempState
from Youtube import YoutubePlaylist, YoutubeVideo, driver

def clear_pl(state): #! clears empty playlists
    queue = state.queue
    queue_ct = state.queue_ct
    full_queue_ct = state.full_queue_ct
    for i in range(len(queue)):
        if i != len(queue)-1:
            if isinstance(queue[i], str) and queue[i] == queue[i+1]:
                if "----" in state.queue[i]:
                    temp = queue[i]
                    queue.remove(temp)
                    queue.remove(temp)
                else:
                    temp = queue[i]
                    queue.remove(temp)
                    queue.remove(temp)
                    temp = temp[2:][:-2]
                    for j in range(len(queue_ct)):
                        if queue_ct[j].title == temp:
                            temp = queue_ct.pop(j)
                            full_queue_ct += [temp]
                            break
                state.queue = queue
                state.queue_ct = queue_ct
                state.full_queue_ct = full_queue_ct
                clear_pl(state) 

class Play(commands.Cog):
    ":play_pause: Playing music(or anything really) from YouTube"
    
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
   

    def __init__(self, client):
        self.client = client      

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown

        self.clock.start()

    def cog_unload(self):
        driver.quit()


    def log(self, msg):                     #! funciton for logging if developer mode is on
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

    @tasks.loop(seconds=1)
    async def clock(self):
        for guild in gen.time_l:
            TempState(guild).time += 1

    def ytvid(self, id: str,info:dict = None,requested_by:str = None):
        return YoutubeVideo(id,info,requested_by)
    
    def ytpl(self, id: str,info:dict = None,requested_by:str = None):
        return YoutubePlaylist(id,info,requested_by)

    async def player(self, ctx, voice):  #! checks queue and plays the song accordingly
        state = TempState(ctx.guild)
        def check_queue():  #! deletes 1st element of list
            if (not state.loop_song) or (state.skip_song):
                if state.skip_song:
                    state.skip_song = False
                try:
                    queue = [x for x in state.queue if not type(x) == str]
                    temp = queue[0]
                    queue2 = state.queue
                    queue2.remove(temp)
                    state.queue = queue2
                    
                    if state.full_queue == []:
                        state.full_queue += [temp]
                    elif state.full_queue[-1] != temp:
                        state.full_queue += [temp]

                    if state.loop_q:
                        state.queue += [temp]

                    if temp in state.queue_ct:
                        queue2 = state.queue_ct
                        queue2.remove(temp)
                        state.queue_ct = queue2

                        if state.full_queue_ct == []:
                            state.full_queue_ct += [temp]

                        elif state.full_queue_ct[-1] != temp:
                            state.full_queue_ct += [temp]
                        
                        if state.loop_q:
                            state.queue_ct += [temp] 

                    clear_pl(state)
                except:
                    pass
            fut = asyncio.run_coroutine_threadsafe(
                self.player(ctx, voice), ctx.bot.loop)
            try:
                fut.result()
            except:
                pass

        flag = True
        while flag:
            queue = [x for x in state.queue if not type(x) == str]
            #! plays the song
            if queue != []:
                try:
                    ch = ctx.States.Guild.voice_text_channel
                    if ch is not None and not ch == "disabled":
                        await ch.send(f"{queue[0].title} playing now.")
                    else:
                        if ch == "disabled":
                            pass
                        else:
                            await ctx.send(f"{queue[0].title} playing now.")
                            
                    self.log("Downloaded song.")
                   
                    voice.play(discord.FFmpegPCMAudio(queue[0].audio_url, executable="./Bin/ffmpeg.exe", before_options="-loglevel quiet -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                               after=lambda e: check_queue())

                    state.time = 0
                    
                    if ctx.author.guild not in gen.time_l:
                        gen.time_l.append(ctx.guild)
            
                    if state.shuffle_lim:   
                        state.shuffle_var += 1
                        if state.shuffle_var == state.shuffle_lim:
                            await ctx.invoke(self.client.get_command("shuffle"))
                            state.shuffle_var = 0

                    self.log(f"{queue[0].title} is playing.")
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    
                except Exception as e:
                    print(e.error)
                    self.log(e)
                    self.log(f"{queue[0].title} cannot be played.")
                    
                    ch = ctx.States.Guild.voice_text_channel
                    if ch is not None and not ch == "disabled":
                        await ch.send(f"{queue[0].title} cannot be played.")
                    else:
                        if ch == "disabled":
                            pass
                        else:
                            await ctx.send(f"{queue[0].title} cannot be played.")
                    
                    queue2 = state.queue
                    queue2.remove(queue[0])
                    state.queue = queue2
                    if queue[0] in state.queue_ct:
                        queue2 = state.queue_ct
                        queue2.remove(queue[0])
                        state.queue_ct = queue2
                    queue.pop(0)
                else:
                    flag = False
            else:
                
                ch = ctx.States.Guild.voice_text_channel
                if ch is not None and not ch == "disabled":
                     await ch.send(">>> All songs played. No more songs to play.")
                else:
                    if ch == "disabled":
                        pass
                    else:
                        await ctx.send(">>> All songs played. No more songs to play.")
                self.log("Ending the queue")
                if ctx.author.guild in gen.time_l:
                    gen.time_l.remove(ctx.guild)
                    state.time = 0
                break
    
    # ? SEARCHING
    
    async def searching(self, ctx, query, isVideo: bool = True, VideoClass: bool = True):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        if isVideo:
            results = YoutubeVideo.from_query(query, 5)
        else:
            results = YoutubePlaylist.from_query(query, 5)
            
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            await ctx.send(f"No results returnded for `{query}`")
            return

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

    @commands.command()
    async def play(self, ctx, *, query):
        '''Plays the audio of the video in the provided VTUBE url.'''
       
        state = TempState(ctx.author.guild)
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        if "http" in query:
            if "www.youtube.com" in query:
                split_list = re.split("/|=|&", query)
                if "watch?v" in split_list:
                    vid = YoutubeVideo(split_list[split_list.index("watch?v")+1], requested_by=ctx.author.name)

                elif "playlist?list" in split_list:
                    vid = YoutubePlaylist(split_list[split_list.index("playlist?list")+1], requested_by=ctx.author.name)
                else:
                    await ctx.send("Couldn't find neither video or playlist.")
                    return

            else:
                await ctx.send("This command only works with youtube.")
                return
        else:
            try:
                vid = YoutubeVideo(YoutubeVideo.from_query(query=query)[0][0], requested_by=ctx.author.name)
            except:
                await ctx.send("There was a problem in playing your song, sorry.")
                
        #! Queueing starts here
        voice = get(self.client.voice_clients, guild=ctx.guild)
       
        old_queue = [x for x in state.queue if type(x) != str]
    
        q_num = len(old_queue) + 1

        self.loading_emoji = str(discord.utils.get(
            ctx.guild.emojis, name="loading"))
        
        message = await ctx.send(f"Searching song `{query}`.... {self.loading_emoji}")
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

        if isinstance(vid, YoutubeVideo):
            old_queue = [x for x in state.queue if type(x) != str]
            state.queue += [vid]
        
            if len(old_queue) == 0:
                await self.player(ctx, voice)
            
            else:
                self.log("Song added to queue")
        else:
            state.queue += [f"--{vid.title}--"]
            temp = []
            
            flog = False
            for i in range(len(vid.entries)):
                old_queue = [x for x in TempState(ctx.author.guild).queue if type(x) != str]
                _vid = YoutubeVideo(vid.entries[i][0])
                             
                if len(old_queue) == 0:
                    state.queue += [_vid]
                    flog = True
                    await self.player(ctx, voice)
                    
                else:
                    self.log("Song added to queue")
                    
                temp.append(_vid)
                 
            if flog:
                state.queue += temp[1:]
            else:
                state.queue += temp
            vid._info["entries"] = temp
            state.queue += [f"--{vid.title}--"]


    # ? PLAY PLAYLIST
    @commands.command(name="play-playlist", aliases=["ppl"])
    async def play_playlist(self, ctx, *, query):
        """Plays a playlist? What did you even expect"""
        
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

    @commands.command()
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
    async def search_playlist(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        if not (await ctx.invoke(self.client.get_command("join"))):
            return
        result = await self.searching(ctx, query, False)
        if result:
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=f"https://www.youtube.com/playlist?list={result.id}")

            

def setup(client):
    client.add_cog(Play(client))
