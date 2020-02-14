import discord
from discord.utils import get
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks

from typing import List,Any
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

import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen

import imp,os
imp.load_source("Youtube", os.path.join(
    os.path.dirname(__file__), "../../others/Youtube.py"))

from Youtube import YoutubePlaylist,YoutubeVideo

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



class Music(commands.Cog):
    ''':musical_note: The title says it all, commands related to music and stuff.'''
    queue:List[Any] = []                                      # queue of the format [items,"playlist name",playlist items,"/playlist name",items]
    loop_song = False                                         # variable used for looping song
    skip_song = False                                         # variable used for skipping song
    time_for_disconnect = 300                                 # time for auto disconnect
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"        # url of the image of thumbnail (vTube)

    QPATH = os.path.join(
    os.path.dirname(__file__),'../../../Queue')
    QPATH = os.path.abspath(QPATH) 

    DPATH = os.path.join(
    os.path.dirname(__file__),'../../../Queue')
    DPATH = os.path.abspath(DPATH) 

   # * ------------------------------------------------------------------------------PREREQUISITES--------------------------------------------------------------------------------------------------------------



    def __init__(self, client):
        self.client = client
        self.auto_pause.start()             # starting loops for auto pause and disconnect
        self.auto_disconnector.start()

    def log(self, msg):                     # funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    def disconnect_check(self, voice) -> bool:  # check if there is no one listening to the bot
        flag = False
        if voice and voice.is_connected():

            flag = True
            for user in voice.channel.members:
                if not user.bot:
                    flag = False
        return flag

    def join_list(self, ls) -> str:  # joins list
        return " ".join(ls)

    def queue_delete(self):          # Deleting Queue folder

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
            self.auto_resume.stop()

    @tasks.loop(seconds=1)
    async def auto_resume(self):  # resumes the song if the user re-joins the vc
        guild = self.client.get_guild(gen.server_id)
        awoo_channel = self.client.get_channel(gen.awoo_id)
        voice = get(self.client.voice_clients, guild=guild)

        if voice and voice.is_paused() and not self.disconnect_check(voice):
            self.log("Music AUTO resumed")
            voice.resume()
            await awoo_channel.send(f"Looks like someone joined `{voice.channel.name}`, player resumed.")
            self.auto_resume.stop()

    async def auto_disconnect(self):  # actual disconnecting code

        guild = self.client.get_guild(gen.server_id)
        voice = get(self.client.voice_clients, guild=guild)
        awoo_channel = self.client.get_channel(gen.awoo_id)

        await voice.disconnect()

        await awoo_channel.send(f"Nothing much to do in the vc so left `{voice.channel.name}`")
        self.log(f"Auto disconnected from {voice.channel.name}")
        self.queue.clear()

    # * MAIN

    # ? PLAYER
    def player(self, voice):  # checks queue and plays the song accordingly
        def check_queue():
       
            DIR = self.QPATH
            

            queue = [x for x in self.queue if not type(x)== str]
            DIR_list = os.listdir(DIR)
            
            for i in DIR_list:
                name,ext = i.split(".")
                if name == queue[0].id:
                    song_name = i
                    break
            
            SONG_DIR = DIR + f"\\{song_name}"
            print(SONG_DIR)

            if ((not self.loop_song) or (self.skip_song)):
                self.queue.remove(queue[0])
                queue.pop(0)
                self.skip_song = False
            
            DIR_list = os.listdir(DIR)
            length = len(DIR_list)
            
            for i in DIR_list:
                name,ext = i.split(".")
                if name == queue[0].id:
                    song_name = i
                    break
            SONG_DIR = DIR + f"\\{song_name}"
            if length > 0:
            

                self.log(f"\nSong done, playing {queue[0].title}")
                self.log(f"Songs still in queue: {len(queue)}")

                try:
                    self.download_music(
                        queue[1].url,self.QPATH)
                    self.log("Downloaded next song.")
                except:
                    self.log("Last song.")

                voice.play(discord.FFmpegPCMAudio(SONG_DIR),
                           after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)

            else:
                self.queue.clear()
                # await ctx.send(">>> All songs played. No more songs to play.")  #? implement this
                self.log("Ending the queue")
                return
        
        DIR = self.QPATH
        

        flag = True
        while flag:
            queue = [x for x in self.queue if not type(x)== str]    
            try:
                
                DIR_list = os.listdir(DIR)
        

                for i in DIR_list:
                    name,ext = i.split(".")
                    if name == queue[0].id:
                        song_name = i
                        break

                SONG_DIR = DIR + f"\\{song_name}"

                voice.play(discord.FFmpegPCMAudio(SONG_DIR),
                            after=lambda e: check_queue())
                self.log(f"{queue[0].title} is playing.")

                try:
                    self.download_music(
                        queue[1].url,self.QPATH)
                    self.log("Downloaded next song.")
                except:
                    self.log("Last song.")
            except:

                self.log(f"{queue[0].title} cannot be played.")
                #await ctx.send(f"{self.queue[0].title} cannot be played.") #? implement this

                self.queue.remove(queue[0])
                queue.pop(0)
            else:
                flag = False

        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.4

    # ? DOWNLOADER
    def download_music(self, url, path) -> str:

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
        except Exception as e:
            self.log(e)

        return queue_path

    # ? SEARCHING
    async def searching(self, ctx, query):
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        results = YoutubeVideo.from_query(query,5)
       
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


        embed_msg = await ctx.send(embed=embed)
        embed_msg: discord.Message

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

    @commands.command()
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
    @commands.command()
    async def play(self, ctx, *, query):
        '''Plays the audio of the video in the provided VTUBE url.'''

        if not (await ctx.invoke(self.client.get_command("join"))):
            return

        if "http" in query:
            if "www.youtube.com" in  query:
                split_list = re.split("/|=|&",query)
                if "watch?v" in split_list:
                    vid = YoutubeVideo(split_list[split_list.index("watch?v")+1])
                elif "playlist?list" in split_list:
                    vid = YoutubePlaylist(split_list[split_list.index("playlist?list")+1])
                else:
                    await ctx.send("Couldnt find neither video or playlist.")
                    return

            else:
                await ctx.send("This command only works with youtube.")
                return
        else:
            vid = YoutubeVideo.from_query(query=query)[0]            

        #! Queueing starts here
        voice = get(self.client.voice_clients, guild=ctx.guild)
        
        
        
        if voice and (not voice.is_playing()):
            Queue_infile = os.path.isdir(self.QPATH)
            
            if not Queue_infile:
                os.mkdir(self.QPATH)
            else:
                self.queue_delete()

        q_num = len(self.queue)+1

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
        await ctx.send(embed=embed)


        old_queue = [x for x in self.queue if type(x)!= str]
        
        if isinstance(vid,YoutubeVideo):
            self.queue += [vid]
        else:
            self.queue += [f"--{vid.title}--"]
            self.queue += vid.entries
            self.queue += [f"--{vid.title}--"]
        queue = [x for x in self.queue if type(x)!= str]
        if len(old_queue) == 1:

            self.download_music(queue[1].url, self.QPATH)
            self.log("Next Song Downloaded")

            
            self.log("Song added to queue")

        elif len(old_queue) == 0:
            
            self.download_music(queue[0].url, self.QPATH)
            self.log("Downloaded")
            self.log("Song added to queue")
        
                
            try:
                
                self.download_music(queue[1].url, self.QPATH)
                self.log("Downloaded next song")
                self.log("Song added to queue")

            except:
                pass

            thrd = Thread(target=self.player, args=(voice,))
            thrd.start()

        else:
            self.log("Song added to queue")

    # ? SEARCH
    @commands.command()
    async def search(self, ctx, *, query):
        """Search on youtube, returns 5 videos that match your query, play one of them using reactions"""

        result = await self.searching(ctx, query)
        if result:
            if not (await ctx.invoke(self.client.get_command("join"))):
                return
            play_command = self.client.get_command("play")
            await ctx.invoke(play_command, query=result.id)





# *-------------------------------------------------------QUEUE------------------------------------------------------------------------------------------------------------------------
   
   
   
    # ? QUEUE

    @commands.group(aliases=['q'])
    async def Queue(self, ctx):
        '''Shows the current queue.'''

        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="QUEUE",
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)
            i=0
            j=1
            while i<len(self.queue):
                if isinstance(self.queue[i],YoutubeVideo):
                    embed.add_field(
                        name="** **", value=f"{j}. {self.queue[i].title} ({self.queue[i].duration})", inline=False)
                    i+=1
                    j+=1
                else:
                    embed.add_field(
                        name=f"**{self.queue[i]}**", value="** **", inline=False)
                    i+=1
            await ctx.send(embed=embed)

    # ? QUEUE REPLACE
    @Queue.command(aliases=['move'])
    @vc_check()
    async def replace(self, ctx, change1, change2):
        '''Replaces two queue members.'''

        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.queue if type(x)!= str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue):
            await ctx.send(f">>> Switched the places of **{queue[change2-1].title}** and **{queue[change1-1].title}**")
            self.queue[self.queue.index(queue[change1-1])], self.queue[self.queue.index(queue[change2-1])] = self.queue[self.queue.index(queue[change2-1])], self.queue[self.queue.index(queue[change1-1])]
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? QUEUE REMOVE
    @Queue.command()
    @vc_check()
    async def remove(self, ctx, remove):
        '''Removes the Queue member.'''

        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.queue if type(x)!= str]
        if remove > 1 and remove <= len(queue):
            DIR = self.QPATH
            DIR_list = os.listdir(DIR)
    

            for i in DIR_list:
                name,ext = i.split(".")
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
    @Queue.command()
    @vc_check()
    async def now(self, ctx, change):
        '''Plays a queue member NOW.'''

        try:
            change = int(change)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in self.queue if type(x)!= str]
        if change > 1 and change <= len(queue):
            temp = queue[change-1]
            self.queue.pop(self.queue.index(queue[change-1]))
            self.queue.insert(1, temp)
            self.download_music(temp.url,self.QPATH)
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("next"))





# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------




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
        self.queue.clear()

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
            self.queue.clear()

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
                playlist_db[str(ctx.author.id)] = [f"{ctx.author.name}'s Playlist",[]]
                playlist = []
            print(1)
            for i in range(len(playlist)):
                try:
                    playlist[i] = YoutubeVideo(playlist[i])
                except:
                    playlist[i] = YoutubePlaylist(playlist[i])
            print(2)
            embed = discord.Embed(title=playlist_db[str(ctx.author.id)][0],
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            print(2)
            no = 1
            print(playlist)
            for song in playlist:
                print(song.title)
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
                playlist_db[str(ctx.author.id)] = [f"{ctx.author.name}'s Playlist",[]]
        

            playlist_db[str(ctx.author.id)][1] += [vid.id]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {playlist_db[str(ctx.author.id)][0]}")
            gen.db_update("playlist", playlist_db)

    # ? PLAYLIST REARRANGE
    @playlist.command(aliases=["re", "change", "replace", "switch"])
    async def rearrange(self, ctx, P1: int, P2: int):
        playlist_db = gen.db_receive("playlist")

        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [f"{ctx.author.name}'s Playlist",[]]
            await ctx.send("Your playlist has been created.")
            return

        else:
            if len(playlist_db[str(ctx.author.id)][1]) < 2:
                await ctx.send("Your playlist too smol for rearrangement.")
                return

            if P1 < 1 or P1 > len(playlist_db[str(ctx.author.id)][1]) or P2 < 1 or P2 > len(playlist_db[str(ctx.author.id)][1]):
                return

            playlist_db[str(ctx.author.id)][1][P1-1], playlist_db[str(ctx.author.id)][1][P2 - 1] = playlist_db[str(ctx.author.id)][1][P2-1], playlist_db[str(ctx.author.id)][1][P1-1]
            await ctx.send(f"Number {P1} and {P2} have been rearranged.")
            self.log(f"altered {playlist_db[str(ctx.author.id)][0]}")

        gen.db_update("playlist", playlist_db)

    # ? PLAYLIST REMOVE
    @playlist.command(aliases=["rem"])
    async def remove(self, ctx, R: int):
        playlist_db = gen.db_receive("playlist")

        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [f"{ctx.author.name}'s Playlist",[]]
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

    # ? PLAYLIST PLAY
    @playlist.command(aliases=["pp"])
    async def pplay(self, ctx):
        playlist_db = gen.db_receive("playlist")

        try:
            playlist_db[str(ctx.author.id)]
        except:
            playlist_db[str(ctx.author.id)] = [f"{ctx.author.name}'s Playlist",[]]
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
                    try:
                        playlist[1][i] = YoutubeVideo(playlist[1][i])
                    except:
                        playlist[1][i] = YoutubePlaylist(playlist[1][i])
                        
                old_queue = [x for x in self.queue if type(x) != str]
                
                self.queue += [f"----{playlist[0]}----"]

                for i in playlist[1]:
                    if isinstance(i,YoutubeVideo):
                        self.queue += [i]
                    else:
                        self.queue += [f"--{i.title}--"] + i.entries + [f"--{i.title}--"]
                
                self.queue += [f"----{playlist[0]}----"]

                if len(old_queue) == 0:
                    

                    queue = [x for x in self.queue if type(x) != str]

                    self.download_music(
                        queue[0].id,self.QPATH)
                    self.log("Downloaded First song.")
                    try:
                        self.download_music(
                            queue[1].id,self.QPATH)
                        self.log("Downloaded next song.")
                    except:

                        pass
                    
                    thrd = Thread(target=self.player, args=(voice,))
                    thrd.start()
                if len(self.queue) == 1:
                    queue = [x for x in self.queue if type(x) != str]
                    self.download_music(
                        queue[1], self.QPATH)
                    self.log("Downloaded next song.")

                await ctx.send("Your Playlist has been added to the Queue.")


# *------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





# *------------------------------------DOWNLOAD----------------------------------------------------------------------------------------------------------------------------------------------------




    # ? DOWNLOAD

    @commands.command(aliases=["dnld"])
    async def download(self, ctx, *, query):
        '''Downloads a song for you, so your pirated ass doesn't have to look for it online.'''

    
        vid = YoutubeVideo.from_query(query=query)
        embed = discord.Embed(title="Now downloading",
                              color=discord.Colour.dark_purple(), url = vid.url)
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                         icon_url=ctx.message.author.avatar_url)
        embed.set_image(url=vid.thumbnail)
        embed.add_field(name="**  **", value=f"**{vid.title}**")

        await ctx.send(embed=embed)

        files = os.listdir(self.DPATH)


        path = self.download_music(vid.id, self.DPATH)
        self.log("Downloaded")


        mp3 = discord.File(path, filename=vid.title+".mp3")

        await ctx.channel.send(file=mp3)
        os.remove(path)




# *---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



def setup(client):
    client.add_cog(Music(client))
