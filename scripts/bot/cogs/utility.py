import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime
import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen

#! RECALLING FUNCTIONS
def check_command(ctx, member):
    roles = [role for role in member.roles]
    role_names = []
    for role in roles:
        role_names +=[role.mention]
    joined_at = member.joined_at.strftime("%a, %d %B %Y %H:%M:%S UTC")
    created_at = member.created_at.strftime("%a, %d %B %Y %H:%M:%S UTC")
    
    embed = discord.Embed(colour=member.colour, 
                          title = f"User info of {member.name}",
                          url = str(member.avatar_url),
                          timestamp=ctx.message.created_at)



    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
    embed.add_field(name="ID: ",value=member.id)
    embed.add_field(name="Guild's Nickname: ",value=member.nick)
    
    embed.add_field(name="Top role: ",value=member.top_role.mention)
    embed.add_field(name=f"Roles ({len(roles)})",value=" | ".join(role_names) ,inline = False)
    embed.add_field(name="Joined at",value=joined_at)
    embed.add_field(name="Created at",value=created_at)
    
    return embed

def avatar_command(ctx,member):
    embed = discord.Embed(colour=member.colour, 
                          title = f"Avatar info of {member.name}",
                          url = str(member.avatar_url),
                          timestamp=ctx.message.created_at)

    

    embed.set_image(url=member.avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
    
    return embed
class Utility(commands.Cog):
    ''':tools: These commands are of great UTILITY.'''

    def __init__(self, client):
        self.client = client
        
        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown

    def log(self, msg):  # ! funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    #* PING
    @commands.command()
    async def ping(self, ctx):
        '''It really means nothing, but well it tells the DAMN PING.'''

        await ctx.send(f">>> ME! PING: `{round(self.client.latency* 1000)}ms` ")

    #* INFO 
    @commands.command()
    async def info(self, ctx):
        '''Lemme tell you about ME!!!'''

        info = discord.Embed(
            colour = discord.Colour.red(),
            title = "ME!ME!ME!",
            description = """Hello, I am sex-slave owned by **Saksy-sama** and the epicest man alive **Blonteractor**.
            `I feel horny.
            I wanna ride on your ugly bastard ass.
            Oh Yes Daddy, Slap me like every ratchet whores from A bad neighbourhood.`
            """
            )
        await ctx.send(embed = info)
        await ctx.send(">>> `Watch my favourite music video:` https://youtu.be/rkBCfF3vUNk")

    #* CLEAR
    @commands.command()
    async def clear(self, ctx, amount=10):
        '''I can delete the evidence of a bully, no one shall know.'''

        if amount>0:
            await ctx.channel.purge(limit=amount+1)
            await ctx.send(f">>> {amount} messages deleted boss. Now no one will know you were bullied")
            await asyncio.sleep(1)
            await ctx.channel.purge(limit=1)
        else:
            ctx.send('>>>REALLY? no wait Really? Are You Dumb or something?')

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(">>> Enter the amount of mesages to be cleared if you dont want spanky / or do (depending on who you are)")
        elif isinstance(error,commands.UserInputError):
            await ctx.send(">>> We are numericons' people not Texticons, you traitor.")
    #* SUGGEST
    @commands.command()
    async def suggest(self,ctx,*,suggestion):
        '''Suggest stuff, or maybey not'''

        await ctx.channel.purge(limit=1)
        embed = discord.Embed(
            colour = discord.Colour.from_rgb(255,0,0),
            title = "Suggestion",
            
            description = suggestion

        )
        embed.set_author(name =ctx.author.name,icon_url = ctx.author.avatar_url)
        await ctx.send(embed = embed)
   
    #*Check
       
    @commands.command(aliases = ["about"])
    async def check(self,ctx, member: discord.Member):
        '''Tells you about your status in our server.'''
        
        embed = check_command(ctx,member)
        await ctx.send(embed=embed) 
       
    @check.error
    async def check_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            member =  ctx.author
            embed = check_command(ctx,member)
            await ctx.send(embed=embed) 
            
    #*AVATAR    
    
    @commands.command(aliases = ["av"])
    async def avatar(self,ctx,member: discord.Member ):
        '''Gives your damn avatar so you can tell everyone how cool it looks.'''
        
        await ctx.send(embed=avatar_command(ctx,member))
        
    @avatar.error
    async def avatar_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            member =  ctx.author
            await ctx.send(embed=avatar_command(ctx,member))

    @commands.group()
    async def setup(self, ctx):
        embed = discord.Embed(title="Current setUp", color=discord.Color.from_rgb(150, 77, 232))
        
        embed.add_field(name="juke box", value=gen.juke_box_channel)
        embed.add_field(name="auto meme", value=gen.auto_meme_channel)
        embed.add_field(name="extra cooldown", value=gen.extra_cooldown)
        
        await ctx.send(embed=embed)
    
    @setup.command()     
    async def juke(self, ctx, channel: discord.TextChannel):
        rem = ["disable", "remove"]
        if str(channel) in rem:
            gen.juke_box_channel = None
            await ctx.send(f">>> Juke box removed")
            return    
        gen.juke_box_channel = channel
        
        await ctx.send(f">>> Juke box channel set to `{channel.name}`")
        
    @setup.command(aliases=["ameme", "aoutom"])     
    async def automeme(self, ctx, channel: discord.TextChannel):
        rem = ["disable", "remove"]
        if str(channel) in rem:
            gen.auto_meme_channel = None
            await ctx.send(f">>> Auto meme removed")
            return    
        gen.auto_meme_channel = channel
        
        await ctx.send(f">>> Auto meme channel set to `{channel.name}`")
    
    @setup.command(aliases=["cool"])     
    async def cooldown(self, ctx, extra: int):
        rem = ["disable", "remove", "0"]
        if str(extra) in rem:
            gen.extra_cooldown = 0
            await ctx.send(f">>> Extra cooldown removed")
            return    
        gen.auto_meme_channel = extra
        
        await ctx.send(f">>> Cooldown of all commands increased by `{extra}`")
        
    @setup.command(aliases=["dj"])     
    async def djrole(self, ctx, role: discord.Role):
        rem = ["disable", "remove"]
        if str(role) in rem:
            gen.dj_role = None
            await ctx.send(f">>> DJ role removed")
            return    
        gen.auto_meme_channel = role
        
        await ctx.send(f">>> DJ role changed to `{role.name}`")    
    
   
        
def setup(client):
    client.add_cog(Utility(client))
