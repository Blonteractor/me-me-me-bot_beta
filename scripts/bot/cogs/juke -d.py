import discord
from discord.ext import commands,tasks

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))
from state import State, CustomContext, GuildState





class Juke(commands.Cog):
    def __init__(self, client):
        self.client = client      
        
        self.jb = channel
        self.jb_photo = photomsg
        self.jb_embed = embedmsg
        self.jb_queue = queuemsg

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
    
    @tasks.loop(seconds = 1)
    async def juke_update(self):
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if self.jb and voice:
            if jb is deleted:
                jb set none 
                return
            if jb_embed and embed is not deleted:
                    purge all reactions
                    refresh the embed
                    reaction listner
            else:
                jb_embed set None
            if jb_queue and queue is not deleted:
                    refresh the queue
            else:
                jb_queue set None
            for message in channel:
                if message.id != jbembed/jbqueue/jbimage:
                    if message = text:
                        if banda in vc:
                            search song and add
                    delete message

    
    @commands.command()
    async def reset(self,ctx):
        if jb = none:
            fuck u person use setup u sick fuck
        else:
            purge channel
            add shit in the channel

            


def setup(client):
    client.add_cog(Currency(client))
