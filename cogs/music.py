import discord
from discord.utils import get
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks

from typing import List
from threading import Thread
import shutil
from lxml import etree
import lxml
import re
import urllib.parse
import urllib.request
from asyncio import sleep
import asyncio
from youtube_dl import YoutubeDL
import youtube_dl

from os import system
import os
import imp

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../general.py"))
import general as gen


def vc_check():
    async def predicate(ctx):  # ! Check if the user is in vc to run the command
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


class Music(commands.Cog):
    ''':musical_note: The title says it all, commands related to music and stuff.'''

    # ! stores all the songs info ie the queue in format [url,path,title,thumbnail]
    queues: List[str] = []
    loop_song = False  # ! variable used for looping song
    skip_song = False  # ! variable used for skipping song
    time_for_disconnect = 300  # ! time for auto disconnect
    # ! url of the image of thumbnail (vTube)
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"

    # * INIT AND PREREQUISITIES
    def __init__(self, client):
        self.client = client
        self.auto_pause.start()  # ! starting loops for auto pause and disconnect
        self.auto_disconnector.start()

    def log(self, msg):  # ! funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    def disconnect_check(self, voice):  # ! chech if there is no one listening to the bot
        flag = False
        if voice and voice.is_connected():

            flag = True
            for user in voice.channel.members:
                if not user.bot:
                    flag = False
        return flag

    def get_title(self, url: str):  # ! gets YouTube title
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return info.get('title', None)

    def get_thumbnail(self, url: str):  # ! getsYouTube thumbnail
        return "http://img.youtube.com/vi/%s/0.jpg" % url[31:]

    def join_list(self, ls):  # ! joins list
        return " ".join(ls)

    def url_get(self, query, all=False):  # ! searches and gives out the url of the requested song
        is_url = query.startswith("https://") or query.startswith("http://")

        if not is_url:
            query_string = urllib.parse.urlencode({"search_query": query})
            html_content = urllib.request.urlopen(
                "http://www.youtube.com/results?" + query_string)
            search_results = re.findall(
                r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
            if not all:
                url = "http://www.youtube.com/watch?v=" + search_results[0]
            if all:
                url = []
                for result in search_results:
                    url.append(f"http://www.youtube.com/watch?v={result}")
        else:
            url = query
        return url


    def queue_delete(self):  # ! Deleting Queue folder

        Queue_infile = os.listdir("./Queue")

        if Queue_infile:
            shutil.rmtree("./Queue")

    #* ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log("Check Failed user in VC.")
        else:
            pass

    
    # * TASKS
    @tasks.loop(seconds=2)
    async def auto_pause(self):  # ! auto pauses the player if it no one is in the vc
        guild = self.client.get_guild(gen.server_id)
        awoo_channel = self.client.get_channel(gen.awoo_id)
        voice = get(self.client.voice_clients, guild=guild)

        if self.disconnect_check(voice):

            if voice.is_playing():
                self.log("Player AUTO paused")
                voice.pause()
                await awoo_channel.send(f"Everyone left `{voice.channel.name}`, player paused.")
                self.auto_resume.start()

    @tasks.loop(seconds=2)
    # ! disconnect if player is idle for the disconnecting time provided
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
            self.auto_resume.stop()

    @tasks.loop(seconds=1)
    async def auto_resume(self):  # ! resumes the song if the user re-joins the vc
        guild = self.client.get_guild(gen.server_id)
        awoo_channel = self.client.get_channel(gen.awoo_id)
        voice = get(self.client.voice_clients, guild=guild)

        if voice and voice.is_paused() and not self.disconnect_check(voice):
            self.log("Music AUTO resumed")
            voice.resume()
            await awoo_channel.send(f"Looks like someone joined `{voice.channel.name}`, player resumed.")
            self.auto_resume.stop()

    async def auto_disconnect(self):  # ! actual disconnecting code

        guild = self.client.get_guild(gen.server_id)
        voice = get(self.client.voice_clients, guild=guild)
        awoo_channel = self.client.get_channel(gen.awoo_id)

        await voice.disconnect()

        await awoo_channel.send(f"Nothing much to do in the vc so left `{voice.channel.name}`")
        self.log(f"Auto disconnected from {voice.channel.name}")
        self.queues.clear()

    # * MAIN

    # ? PLAYER
    def player(self, voice):  # ! checks queue and plays the song accordingly
        def check_queue():
            DIR = os.path.abspath(os.path.realpath("./Queue"))
            length = len(os.listdir(DIR))
            if ((not self.loop_song) or (self.skip_song)):
                os.remove(self.queues[0][1])
                self.queues.pop(0)
                self.skip_song = False

            if length > 0:

                self.log(f"\nSong done, playing {self.queues[0][2]}")
                self.log(f"Songs still in queue: {len(self.queues)}")

                voice.play(discord.FFmpegPCMAudio(self.queues[0][1]),
                           after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.4
            else:
                self.queues.clear()
                # await ctx.send(">>> All songs played. No more songs to play.")
                self.log("Ending the queue")
                return

        self.log(f"{self.queues[0][2]} is playing.")
        voice.play(discord.FFmpegPCMAudio(self.queues[0][1]),
                   after=lambda e: check_queue())
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.4

    # ? DOWNLOADER
    def download_music(self, url, name, path, mtype):

        queue_path = os.path.abspath(f"{path}/{name}.{mtype}")
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'outtmpl': queue_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': mtype,
            }],
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                self.log("Downloading stuff now")
                ydl.download([url])
        except:
            pass
        return queue_path

    # * COMMANDS

    # ? JOIN
    @commands.command()
    async def join(self, ctx):
        '''Joins the voice channel you are currently in.'''

        try:  # ! user not in vc
            channel = ctx.message.author.voice.channel
        except:
            await ctx.send("You should be in VC dumbo.")
            return False

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if not voice:  # ! bot not in vc
            voice = await channel.connect()
            await ctx.send(f">>> Joined `{channel}`")
            return True

        elif ctx.author in voice.channel.members:  # ! bot and user in same vc
            return True

        # ! bot and user in diff vc but bot can switch
        elif voice and self.disconnect_check(voice):
            await voice.move_to(channel)
            await ctx.send(f">>> Joined `{channel}`")
            return True

        else:  # ! bot and user in diff vc and bot cant switch
            await ctx.send(f"I am already connected to a voice channel and someone is listening to the songs. Join {voice.channel.name}")
            return False

     # ? PLAY
    @commands.command()
    async def play(self, ctx, *, query):
        '''Plays the audio of the video in the provided YOUTUBE url.'''

        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        url = self.url_get(query)

        #! Queueing starts here
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if ctx.author not in voice.channel.members:
            await ctx.send(f"You are not even in the VC. Join {voice.channel.name}")
            return
        Queue_infile = os.path.isdir(f"{os.getcwd()}/Queue")
        if voice and (not voice.is_playing()):
            try:
                Queue_folder = f"{os.getcwd()}/Queue"
                if Queue_infile:
                    self.log("removed old queue folder")
                    shutil.rmtree(Queue_folder)
            except:
                self.log("No old queue folder")

        if not Queue_infile:
            os.mkdir("Queue")

        q_num = len(self.queues)+1

        title = str(self.get_title(url))
        thumbnail = str(self.get_thumbnail(url))

        embed = discord.Embed(title="Song Added to Queue",  # TODO make a function
                              url=url, color=discord.Colour.blurple())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.add_field(name=f"**#{q_num}**",
                        value=title)
        embed.set_image(url=thumbnail)
        embed.set_thumbnail(url=self.music_logo)
        await ctx.send(embed=embed)
        if self.queues == []:
            l = 1
        else:
            l = int(self.queues[-1][1].split("\\")[-1].split(".")[0][4:])+1

        self.log("Song added to queue")

        path = self.download_music(url, f"song{l}", "./Queue", "webm")
        self.queues += [[url, path, title, thumbnail]]
        self.log("Downloaded")

        if len(self.queues) == 1:
            thrd = Thread(target=self.player, args=(voice,))
            thrd.start()

    #? SEARCH
    @commands.command()
    @vc_check()
    async def search(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""
        
        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        results = self.url_get(query, all=True)
        results_filtered: List[str] = []
        wait_time = 60

        reactions = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}

        for result in results:
            if result not in results_filtered:
                results_filtered.append(result)

        embed = discord.Embed(title="Search returned the following",
                              color=discord.Colour.dark_green())
            
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=self.music_logo)

        for index, result in enumerate(results_filtered):
            embed.add_field(name=f"*{index + 1}.*",
                            value=f"**{self.get_title(result)}**", inline=False)
            if index == 4:
                break
        
        embed_msg = await ctx.send(embed=embed)
        embed_msg: discord.Message
        
        def check(reaction: discord.Reaction, user):  
            return user == ctx.author and reaction.message.id == embed_msg.id

        self.client.loop.create_task(reactions_add(embed_msg, reactions.keys()))

        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await ctx.send(f">>> I guess no ones wants to play.")
                await embed_msg.delete()

                return

            else: 
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.keys():
                    await embed_msg.delete(delay=3)
                    play_command = self.client.get_command("play")
                    await ctx.invoke(play_command, query=results_filtered[reactions[str(reaction.emoji)] - 1])

    # ? LOOP

    @commands.command(aliases=['lp'])
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

    @commands.command()
    @vc_check()
    async def restart(self, ctx):
        '''Restarts the current song.'''

        temp = self.loop_song
        self.loop_song = True
        voice = get(self.client.voice_clients, guild=ctx.guild)
        voice.stop()
        await asyncio.sleep(0.1)
        self.loop_song = temp

    # ? QUEUE

    @commands.group(aliases=['q'])
    async def queue(self, ctx):
        '''Shows the current queue.'''

        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="QUEUE",
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            for i in range(1, len(self.queues)+1):

                embed.add_field(
                    name="** **", value=f"{i}. {self.queues[i-1][2]}", inline=False)

            await ctx.send(embed=embed)

    # ? QUEUE REPLACE
    @queue.command(aliases=['move'])
    @vc_check()
    async def replace(self, ctx, change1, change2):
        '''Replaces two queue members.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return

        if change1 > 1 and change2 > 1 and change1 <= len(self.queues) and change2 <= len(self.queues):
            await ctx.send(f">>> Switched the places of **{self.queues[change2-1][2]}** and **{self.queues[change1-1][2]}**")
            self.queues[change1-1], self.queues[change2 -
                                                1] = self.queues[change2-1], self.queues[change1-1]
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? QUEUE REMOVE
    @queue.command()
    @vc_check()
    async def remove(self, ctx, remove):
        '''Removes the Queue member.'''

        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return

        if remove > 1 and remove <= len(self.queues):
            os.remove(self.queues[remove-1][1])
            await ctx.send(f">>> Removed **{(self.queues[remove - 1][2])}** from the queue.")
            self.queues.pop(remove-1)
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? QUEUE NOW
    @queue.command()
    @vc_check()
    async def now(self, ctx, change):
        '''Plays a queue member NOW.'''

        try:
            change = int(change)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        if change > 1 and change <= len(self.queues):
            temp = self.queues[change-1]
            self.queues.pop(change-1)
            self.queues.insert(1, temp)
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))

   # ? PAUSE
    @commands.command(aliases=['p'])
    @vc_check()
    async def pause(self, ctx):
        '''Pauses the current music.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            self.log("Player paused")
            voice.pause()
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
            await ctx.send(">>> Resumed Music")
        else:
            self.log("Resume failed")
            await ctx.send(">>> Ya know to resume stuff, stuff also needs to be paused first.")

    # ? STOP
    @commands.command(aliases=['st', 'yamero'])
    @vc_check()
    async def stop(self, ctx):
        '''Stops the current music AND clears the current queue.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)
        self.queues.clear()

        if voice and voice.is_playing:
            self.log("Player stopped")
            voice.stop()
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")
        self.queue_delete()

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
            await ctx.send(f">>> Left ```{voice.channel.name}```")
            self.queues.clear()

        else:
            await ctx.send(">>> I cannot leave a voice channel I have not joined, thought wouldn't need to explain basic shit like this.")

        self.queue_delete()

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
            await ctx.send(">>> Enter the amount of mesages to be cleared if you dont want spanky / or do (depending on who you are)")
        elif isinstance(error, commands.UserInputError):
            await ctx.send(">>> We are numericons' people not Texticons, you traitor.")
    #? PLAYLIST
    @commands.group(aliases=["pl"])
    async def playlist(self,ctx):
        '''Shows your Playlist. Subcommands can alter your playlist'''    
        if ctx.invoked_subcommand is None:
            
            playlist_db = gen.db_receive("playlist")
            try:
                playlist = playlist_db[str(ctx.author.id)]
            except:  
                playlist_db[str(ctx.author.id)] = []
                playlist = [] 
            embed = discord.Embed(title=f"{ctx.author.name}'s Playlist",
                                color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            no = 1
            for song in playlist:
                embed.add_field(name=f"**{no}**", value=f"**{song[1]}**")
                no+=1
            await ctx.send(embed=embed)
            gen.db_update("playlist",playlist_db)
    
    #? PLAYLIST ADD
    @playlist.command()
    async def add(self,ctx,*,query):
        '''Adds a song to your Playlist.'''
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        results = self.url_get(query, all=True)
        results_filtered: List[str] = []
        wait_time = 60

        reactions = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}

        for result in results:
            if result not in results_filtered:
                results_filtered.append(result)

        embed = discord.Embed(title="Search returned the following",
                              color=discord.Colour.dark_green())
            
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=self.music_logo)

        for index, result in enumerate(results_filtered):
            embed.add_field(name=f"*{index + 1}.*",
                            value=f"**{self.get_title(result)}**", inline=False)
            if index == 4:
                break
        
        embed_msg = await ctx.send(embed=embed)
        embed_msg: discord.Message
        
        def check(reaction: discord.Reaction, user):  
            return user == ctx.author and reaction.message.id == embed_msg.id

        self.client.loop.create_task(reactions_add(embed_msg, reactions.keys()))

        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await ctx.send(f">>> I guess no ones wants to play.")
                await embed_msg.delete()

                return

            else: 
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.keys():
                    await embed_msg.delete(delay=3)
                    url = results_filtered[reactions[str(reaction.emoji)] - 1]
                    
                    playlist_db = gen.db_receive("playlist")
                    try:
                        playlist_db[str(ctx.author.id)]
                    except:  
                        playlist_db[str(ctx.author.id)] = []
                    playlist_db[str(ctx.author.id)] += [[url, self.get_title(url),self.get_thumbnail(url)]]
                    await ctx.send(f"**{self.get_title(url)}** added to your Playlist")

                    gen.db_update("playlist",playlist_db)
    
    #? PLAYLIST REARRANGE
    @playlist.command(aliases = ["re","change","replace"])
    async def rearrange(self,ctx,P1:int,P2:int):
        playlist_db = gen.db_receive("playlist")
        
        try:
            playlist_db[str(ctx.author.id)]
        except:  
            playlist_db[str(ctx.author.id)] = []
            await ctx.send("Your playlist has been created.")
            return
                         
        else:
            if len(playlist_db[str(ctx.author.id)])<2:
                await ctx.send("Your playlist too smol for rearrangement.")
                return
            
            if P1<1 or P1>len(playlist_db[str(ctx.author.id)]) or P2<1 or P2>len(playlist_db[str(ctx.author.id)]):
                return
            
            playlist_db[str(ctx.author.id)][P1-1],playlist_db[str(ctx.author.id)][P2-1]=playlist_db[str(ctx.author.id)][P2-1],playlist_db[str(ctx.author.id)][P1-1]
            await ctx.send(f"Number {P1} and {P2} have been rearranged.")

        gen.db_update("playlist",playlist_db)


    # ? DOWNLOAD

    @commands.command(aliases=["dnld"])
    async def download(self, ctx, *, query):
        '''Downloads a song for you, so your pirated ass doesn't have to look for it online.'''

        url = self.url_get(query)
        embed = discord.Embed(title="Now downloading",
                              color=discord.Colour.dark_purple(), url=url)
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_image(url=self.get_thumbnail(url))
        embed.add_field(name="**  **", value=f"**{self.get_title(url)}**")

        await ctx.send(embed=embed)

        files = os.listdir("./Download")
        if files == []:
            i = 1
        else:
            last_file = files[-1]
            i = int(last_file.split(".")[0][4:])+1

        path = self.download_music(url, f"dnld{i}", "./Download", "webm")
        self.log("Downloaded")

        mp3 = discord.File(path, filename=self.get_title(url)+".mp3")

        await ctx.channel.send(file=mp3)
        os.remove(path)


def setup(client):
    client.add_cog(Music(client))
