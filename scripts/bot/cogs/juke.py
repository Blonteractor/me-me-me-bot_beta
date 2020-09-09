import discord
from discord.ext import commands,tasks
from discord.utils import get
from datetime import timedelta
import asyncio
import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))
from state import GuildState,TempState


class Juke(commands.Cog):
    juke_box_url = "https://media.discordapp.net/attachments/623969275459141652/680480864316030996/juke_box.jpg"
    we_tube_bg_url = "https://media.discordapp.net/attachments/623969275459141652/752798002912952360/we_tube_logo.png?width=1353&height=609"
    def __init__(self, client):
        self.client = client      

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
        self.reset_phase = False
        self.juke_update.start()

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

    @tasks.loop(seconds = 1)
    async def juke_update(self):
        for guild in self.client.guilds:
            state = GuildState(guild)
            voice = get(self.client.voice_clients, guild=guild)
            if state.jb_channel and voice:
                tstate = TempState(guild)
                queue = [x for x in tstate.queue if type(x) != str]
                if state.jb_embed_id:
                    embed_msg = await state.jb_channel.fetch_message(state.jb_embed_id)
                    if embed_msg:
                        if tstate.old_queue_embed != tstate.queue:
                            tstate.old_queue_embed = tstate.queue
                            if queue == []:
                                embed = discord.Embed(title="Not Playing Anything right now.",
                                        color=discord.Colour.from_rgb(0, 255, 255))
                                embed.set_image(url=self.juke_box_url)
                                await embed_msg.edit(embed=embed)
                            else:
                                vid = queue[0]
                                embed = discord.Embed(title=vid.title,
                                        color=discord.Colour.from_rgb(0, 255, 255))
                                embed.set_image(url=vid.thumbnail)

                                await embed_msg.edit(embed=embed)
                    else:   
                        state.jb_embed_id = None
                
                if state.jb_queue_id:
                    queue_msg = await state.jb_channel.fetch_message(state.jb_queue_id)
                    if queue_msg:
                        if tstate.old_queue_queue != tstate.queue:
                            tstate.old_queue_queue = tstate.queue
                            if queue == []:
                                
                                await queue_msg.edit(content = "__QUEUE LIST__")
                            else:
                                string = "__QUEUE__\n"
                                for index in range(len(tstate.queue)):
                                    i = tstate.queue[index]
                                    ostring = string[:]
                                    string += f"{index+1}. {i.title} ({i.duration}) - Requested by `{i.requester}`\n"
                                    if len(string)>2000:
                                        string = ostring
                                        break

                                await queue_msg.edit(content=string)
                    else:
                        state.jb_queue_id = None

                if state.jb_loading_id:
                    loading_msg = await state.jb_channel.fetch_message(state.jb_loading_id)
                    if loading_msg:
                        if voice.is_playing():
                            if queue != []:
                                vid = queue[0]
                                def two_dig(number):
                                    if number < 10:
                                        return f"0{number}"
                                    else:
                                        return str(number)

                                if vid.duration.count(":") == 1:
                                    ntime = f"{tstate.time//60}:{two_dig(tstate.time%60)}"
                                else:
                                    ntime = f"{tstate.time//3600}:{two_dig(tstate.time%3600//60)}:{two_dig(tstate.time//60)}"
                                    
                                ntime = str(timedelta(seconds=tstate.time))

                                amt = int(tstate.time/vid.seconds*10)
                                
                                ntime = ntime.split(":")
                                for i in range(3 - len(vid.duration.split(":"))):
                                    ntime.pop(i)
                                ntime = ":".join(ntime)
                    
                                await loading_msg.edit(content=f"{ntime}/{vid.duration} {':black_square_button:'*amt +':black_large_square:'*(10-amt)}")
                                
                       
                            else:
                                await loading_msg.edit(content = f"0:00/0:00 - {':black_large_square:'*10}")
                        
                    else:
                        state.jb_loading_id = None
            
    @commands.Cog.listener()
    async def on_message(self, message):
        state = GuildState(message.guild)
        jb_channel = state.jb_channel
        if jb_channel: 
            if message.channel == jb_channel:
                if message.author != self.client.user:
                    ctx = await self.client.get_context(message)
                    await ctx.invoke(self.client.get_command("play"),query = message.content)
                    await message.delete()
                else:
                    if not self.reset_phase:
                        await message.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        state = GuildState(user.guild)
        voice = get(self.client.voice_clients,guild=reaction.message.guild)
        if state.jb_channel and voice:
            if state.jb_embed_id:
                embed_msg = await state.jb_channel.fetch_message(state.jb_embed_id)
                if not embed_msg:
                    state.jb_embed_id = None
                else:
                    if user != self.client.user and reaction.message.id == int(state.jb_embed_id):
                        reactions = {"⏯️": "play/pause", "⏹️": "stop", "⏮️": "previous",
                                    "⏭️": "forward", "🔁": "loop", "🔀": "shuffle"}
                        
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

                            elif reactions[str(reaction.emoji)] == "previous":
                                await ctx.invoke(self.client.get_command("back"))
                            
                            elif reactions[str(reaction.emoji)] == "shuffle":
                                await ctx.invoke(self.client.get_command("shuffle"))

                        await reaction.remove(user)
    
    @commands.command()
    async def resetup(self,ctx):
        
        state = GuildState(ctx.guild)
        jb_channel = state.jb_channel
        if jb_channel == None:
            await ctx.send("Fuck U person, Use Setup Command, U Sick Fuck")
        else:
            try:
                self.reset_phase = True
                state.jb_embed_id=state.jb_queue_id=state.jb_image_id=state.jb_loading_id=None
                async for msg in jb_channel.history():
                    await msg.delete()

                #! IMAGE
                image_msg = await state.jb_channel.send(self.we_tube_bg_url)
                state.jb_image_id = image_msg.id   
        
                #! EMBED
                reactions = {"⏯️": "play/pause", "⏹️": "stop", "⏮️": "previous",
                            "⏭️": "forward", "🔁": "loop", "🔀": "shuffle"}
                embed = discord.Embed(title="Not Playing Anything right now.",
                                    color=discord.Colour.from_rgb(0, 255, 255))
                embed.set_image(url=self.juke_box_url)

                embed_msg = await state.jb_channel.send(embed=embed)
                state.jb_embed_id = embed_msg.id
                for reaction in reactions:

                    await embed_msg.add_reaction(reaction)
                #! LOADING
                loading_msg = await state.jb_channel.send( f"0:00/0:00 - {':black_large_square: '*10}")
                state.jb_loading_id = loading_msg.id 

                #! QUEUE
                queue_msg = await state.jb_channel.send("__QUEUE LIST__")
                state.jb_queue_id = queue_msg.id
                
                await state.jb_channel.send("Done")
                self.reset_phase = False
                 
                
            except:
                pass

def setup(client):
    client.add_cog(Juke(client))
