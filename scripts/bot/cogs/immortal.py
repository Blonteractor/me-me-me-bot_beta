import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands
import general as gen
from state import MemberState,UserState

class Immortal(commands.Cog):
    ''':ghost: These commands are not for some puny mortals, Only Immortal beings possess these commands.'''

    def __init__(self, client):
        self.client = client 

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

    #* STATS
    @commands.command()
    async def stats(self, ctx,member: discord.Member = None):
        '''Shows stats of all the ACTIVE PEOPLE WHO HAVE NO LIFE.'''
        if member:
            state =  MemberState(member)
            user = UserState(member)
            stats = discord.Embed(
            title = "ME! Stats",
            colour = discord.Colour.from_rgb(0,0,0)
            )
           

            stats.set_author(name = member.name, icon_url = member.avatar_url)
            stats.add_field(name = "Messages",value= state.messages, inline = True)
            stats.add_field(name = "Level",value= state.level, inline = True)
            stats.add_field(name = "Souls",value=user.souls , inline = True)
            await ctx.send(embed = stats)
            return
        
        embeds = []
        for member in ctx.guild.members:  
            if member.bot:
                continue
            
            state =  MemberState(member)
            user = UserState(member)
            stats = discord.Embed(
            title = "ME! Stats",
            colour = discord.Colour.from_rgb(0,0,0)
            )
            stats.set_author(name = member.name, icon_url = member.avatar_url)
            stats.add_field(name = "Messages",value= state.messages, inline = True)
            stats.add_field(name = "Level",value= state.level, inline = True)
            stats.add_field(name = "Souls",value=user.souls , inline = True)
            embeds += [stats]

        wait_time = 180
        page = 0 
        embed_msg = await ctx.send(embed = embeds[0])
        embed_msg: discord.Message

        async def reactions_add(message, reactions):
                for reaction in reactions:
                    await message.add_reaction(reaction)

        reactions = {"back": "⬅", "forward": "➡","delete": "❌"}
        ctx.bot.loop.create_task(reactions_add(embed_msg, reactions.values())) 

        def check(reaction: discord.Reaction, user):  
            return user == ctx.author and reaction.message.id == embed_msg.id

        while True:

            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=wait_time, check=check)
            
            except TimeoutError:
                await ctx.send(f">>> Deleted Help Command due to inactivity.")
                await embed_msg.delete()

                return

            else: 
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.values():

                    if str(reaction.emoji) == reactions["forward"]: 
                        page += 1
                        
                        if page >= len(embeds):
                            page = len(embeds)-1

                        await embed_msg.edit(embed=embeds[page])

                    elif str(reaction.emoji) == reactions["back"]: 
                        page -= 1

                        if page < 0:
                            page = 0
                        
                        await embed_msg.edit(embed=embeds[page])

                    elif str(reaction.emoji) == reactions["delete"]: 
                        await embed_msg.delete(delay=1)
                        return
                else:
                    pass
    @stats.error
    async def stats_error(self, ctx, error):
        await self.stats(ctx)

    #* TOP SECRET DONT TOUCH
    @commands.command()
    async def admin(self, ctx):
        '''This is a top secret command, no using this.'''

        embed = discord.Embed(title = "ADMIN RIGHTS", description = "Short_Terminal_Cout_var_ADMIN_ROLE", colour = discord.Color.red(), url = gen.epic)

        await ctx.send(embed = embed)

def setup(client):
    client.add_cog(Immortal(client))