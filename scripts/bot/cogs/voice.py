import discord
from discord.ext import commands,tasks
from discord.ext.commands.core import Command, cooldown
from discord.utils import get
import asyncio
import imp,os
import random
from datetime import timedelta

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))
from state import GuildState,TempState,CustomContext

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

def vc_check():
    async def predicate(ctx):           # Check if the user is in vc to run the command
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if ctx.author not in voice.channel.members:
                await ctx.send(f"You either are not in a VC or in a wrong VC. Join `{voice.channel.name}`")
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
    
class Voice(commands.Cog):
    
    def __init__(self, client):
        self.client = client      
        self.auto_voice_handler.start()

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown

    
    
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
    
    def disconnect_check(self, voice) -> bool: #! checks if it can disconnect
        flag = False
        if voice and voice.is_connected():
            flag = True
            for user in voice.channel.members:
                if not user.bot:
                    flag = False
        return flag

    @tasks.loop(seconds=1)
    async def auto_voice_handler(self):
        for guild in self.client.guilds:
            state = TempState(guild)
            voice = get(self.client.voice_clients, guild=guild)
            if voice:
                if self.disconnect_check(voice):
                    awoo_channel = GuildState(guild).voice_text_channel
                    if voice.is_playing():
                        state.voice_handler_time += 1
                        if state.voice_handler_time == int(GuildState(guild).auto_pause_time):
                            voice.pause()
                            self.log("Player AUTO paused")
                            state.paused_by_handler = True
                            if awoo_channel:
                                await awoo_channel.send(f"Everyone left `{voice.channel.name}`, player paused.")
                    elif voice.is_paused():
                        state.voice_handler_time += 1
                        if state.voice_handler_time == int(GuildState(guild).auto_disconnect_time):
                            state.queue = []
                            state.full_queue = []
                            state.queue_ct = []
                            state.full_queue_ct = []
                            await voice.disconnect()
                            self.log("Player AUTO Disconnected")
                            if awoo_channel:
                                await awoo_channel.send(f"player disconnected.")
                else:
                    if state.voice_handler_time > 0:
                        state.voice_handler_time = 0
                    if state.paused_by_handler:
                        state.voice_handler_time = 0
                        voice.resume()
                        state.paused_by_handler = False
                

    # ? NOW PLAYING

    @commands.command(name="now-playing", aliases=["np"])
    async def now_playing(self, ctx):
        state = TempState(ctx.author.guild)
        queue = [x for x in state.queue if type(x) != str]
        vid = queue[0]

        embed = discord.Embed(title="NOW PLAYING",  
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
    
    #? JOIN
    
    @commands.command()
    @is_dj()
    async def join(self, ctx: CustomContext) -> bool:
        '''Joins the voice channel you are currently in.'''
    
        try:  #! user not in vc
            channel = ctx.message.author.voice.channel
        except:
            await ctx.send("You should be in VC dumbo.")
            return False

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if not voice:  #! bot not in vc
            voice = await channel.connect()
            await ctx.send(f">>> Joined `{channel}`")
            return True

        elif ctx.author in voice.channel.members:  #! bot and user in same vc
            return True

        #! bot and user in diff vc but bot can switch
        elif voice and self.disconnect_check(voice):
            await voice.move_to(channel)
            await ctx.send(f">>> Joined `{channel}`")
            return True

        else:  #! bot and user in diff vc and bot cant switch
            await ctx.send(f"I am already connected to a voice channel and someone is listening to the songs. Join `{voice.channel.name}``")
            return False

    # ? RESTART

    @commands.command(aliases=["res"])
    @vc_check()
    async def restart(self, ctx):
        '''Restarts the current song.'''
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice:
            temp = state.loop_song
            state.loop_song = True
            voice.stop()
            await asyncio.sleep(0.01)
            state.loop_song = temp
        else:
            self.log("Restart failed")
            await ctx.send(">>> Ya know to restart stuff, stuff also needs to be playing first.")

   # ? PAUSE

    @commands.command(aliases=["p"])
    @vc_check()
    async def pause(self, ctx):
        '''Pauses the current music.'''
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            self.log("Player paused")
            voice.pause()
            if ctx.author.guild in gen.time_l:
                gen.time_l.remove(ctx.author.guild)
            await ctx.send(">>> Music Paused")
        else:
            self.log("Pause failed")
            await ctx.send(">>> Ya know to pause stuff, stuff also needs to be playing first.")

    # ? RESUME

    @commands.command(aliases=["r"])
    @vc_check()
    async def resume(self, ctx):
        '''Resumes the current music.'''

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            self.log("Music resumed")
            voice.resume()
            if ctx.author.guild not in gen.time_l:
                gen.time_l.append(ctx.author.guild)
            await ctx.send(">>> Resumed Music")
        else:
            self.log("Resume failed")
            await ctx.send(">>> Ya know to resume stuff, stuff also needs to be paused first.")

    # ? STOP
    @commands.command(aliases=["st"])
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
            if ctx.author.guild in gen.time_l:
                gen.time_l.remove(ctx.author.guild)
            state.time = 0
            state.shuffle_lim = None
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")

    # ? HARD_STOP
    @commands.command(name="hardstop", aliases=["hst"])
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
            if ctx.author.guild in gen.time_l:
                gen.time_l.remove(ctx.author.guild)
            state.time = 0
            state.shuffle_lim = None
            await ctx.send(">>> Music stopped")

        else:
            self.log("Stop failed")
            await ctx.send(">>> Ya know to stop stuff, stuff also needs to be playing first.")
        
    # ? SKIP

    @commands.command(aliases=["skip", "sk", "nxt"])
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
    @vc_check()
    async def back(self, ctx):
        '''Plays previous song.'''
        
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice:
            
            state.queue =  [state.full_queue[-1]] + state.queue
            print(state.queue)
            if not voice.is_playing():
                if len(state.queue) == 1:
                    play = self.client.get_cog("Play")
                    await play.player(ctx, voice)
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
        state = TempState(ctx.author.guild)
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            state.queue = []
            state.full_queue = []
            state.queue_ct = []
            state.full_queue_ct = []
            if voice.is_playing():
                voice.stop()
            await voice.disconnect()
            if ctx.author.guild in gen.time_l:
                gen.time_l.remove(ctx.author.guild)
            state.time = 0
            state.shuffle_lim = None
            await ctx.send(f">>> Left ```{voice.channel.name}```")
            
        else:
            await ctx.send(">>> I cannot leave a voice channel I have not joined, thought wouldn't need to explain basic shit like this.")

    # ? VOLUME

    @commands.command(aliases=["v", "vl"])
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

    # ?SEEK
    @commands.command()
    @vc_check()
    async def seek(self, ctx, time):
        """Skip ahead to a timestamp in the current song"""
        state = TempState(ctx.author.guild)
        
        queue = [x for x in state.queue if type(x) != str]
        voice = get(self.client.voice_clients, guild=ctx.guild)

        time = await self.int_time(ctx, time)

        if time:
            print(time)
            voice.source = discord.FFmpegPCMAudio(queue[0].audio_url, executable="./Bin/ffmpeg.exe", before_options=f"-loglevel quiet -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {time}")
            state.time = time
        else:
            return

    # ?FORWARD

    @commands.command(aliases=["fwd"])
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
                    queue[0].audio_url, executable="./Bin/ffmpeg.exe", before_options=f"-loglevel quiet -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {time + state.time}")
                state.time += time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return

    # ?REWIND
    @commands.command()
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
                    queue[0].audio_url,executable="./Bin/ffmpeg.exe", before_options=f"-loglevel quiet -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {state.time - time}")
                state.time -= time
            else:
                await ctx.send("The seek is greater than the song limit.")
        else:
            return

     # ? LOOP

    @commands.command()
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

    

    # ? SHUFFLE
    @commands.command()
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


def setup(client):
    client.add_cog(Voice(client))
