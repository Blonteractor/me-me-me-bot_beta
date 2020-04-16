import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime
import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))

import general as gen
from state import CustomContext as cc

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
        self.client: commands.Bot
        
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
    @commands.has_permissions(manage_messages=True)
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
        if ctx.invoked_subcommand is None:
            ctx = await self.client.get_context(ctx.message, cls=cc)
            
            embed = discord.Embed(title="Current setUp", color=discord.Color.from_rgb(150, 77, 232))
            
            embed.add_field(name="Prefix",
                             value=ctx.States.Guild.prefix if ctx.States.Guild.prefix is not None else "epic/me!", inline=False)
            embed.add_field(name="Juke box",
                             value=ctx.States.Guild.juke_box_channel.mention if ctx.States.Guild.juke_box_channel is not None else "Not set", inline=False)
            embed.add_field(name="Auto meme",
                             value=ctx.States.Guild.auto_meme_channel.mention if ctx.States.Guild.auto_meme_channel is not None else "Not set", inline=False)
            embed.add_field(name="Level up",
                             value=ctx.States.Guild.level_up_channel.mention if ctx.States.Guild.level_up_channel is not None else "Not set", inline=False)
            embed.add_field(name="VC text",
                             value=ctx.States.Guild.voice_text_channel.mention if ctx.States.Guild.voice_text_channel is not None else "Not set", inline=False)
            embed.add_field(name="Extra cooldown",
                             value=f"`{ctx.States.Guild.extra_cooldown}`" + " seconds", inline=False)
            embed.add_field(name="Auto-disconenct time",
                             value=f"`{ctx.States.Guild.auto_disconnect_time}`" + " seconds", inline=False)
            embed.add_field(name="Auto-pause time",
                             value=f"`{ctx.States.Guild.auto_pause_time}`" + " seconds", inline=False)
            embed.add_field(name="DJ role",
                             value=ctx.States.Guild.dj_role.mention if ctx.States.Guild.dj_role is not None else "@everyone", inline=False)
            
            await ctx.send(embed=embed)
        
    @setup.command()  
    @commands.has_permissions(administrator=True)   
    async def juke(self, ctx, channel: discord.TextChannel):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        rem = ["disable", "remove"]
        if str(channel) in rem:
            ctx.States.Guild.juke_box_channel = None
            await ctx.send(f">>> Juke box removed")
            return    
        
        ctx.States.Guild.juke_box_channel = channel
        
        self.client.get_cog("music").juke_box.start()
       
        await ctx.send(f">>> Juke box channel set to {channel.mention}")
        
    @setup.command(aliases=["ameme", "aoutom"])     
    @commands.has_permissions(administrator=True)
    async def automeme(self, ctx, channel: discord.TextChannel):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        rem = ["disable", "remove"]
        
        if str(channel) in rem:
            ctx.States.Guild.auto_meme_channel = None
            await ctx.send(f">>> Auto meme removed")
            return    
        
        ctx.States.Guild.auto_meme_channel = channel
        
        self.client.get_cog("meme").a_meme.start()
        
        await ctx.send(f">>> Auto meme channel set to {channel.mention}")
    
    @setup.command(aliases=["cool"])     
    @commands.has_permissions(administrator=True)
    async def cooldown(self, ctx, extra: int):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        rem = ["disable", "remove", "0"]
        if str(extra) in rem:
            gen.extra_cooldown = 0
            await ctx.send(f">>> Extra cooldown removed")
            return    
        ctx.States.Guild.extra_cooldown = extra
        
        await ctx.send(f">>> Cooldown of all commands increased by `{extra}`")
        
    @setup.command(aliases=["dj"])     
    @commands.has_permissions(administrator=True)
    async def djrole(self, ctx, role: discord.Role):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        rem = ["disable", "remove"]
        if str(role) in rem:
            ctx.States.Guild.dj_role = None
            await ctx.send(f">>> DJ role removed")
            return    
        ctx.States.Guild.dj_role = role
        
        await ctx.send(f">>> DJ role changed to {role.mention}")  
        
    @setup.command(aliases=["lvl", "lvlup"])  
    @commands.has_permissions(administrator=True)   
    async def levelup(self, ctx, channel: discord.TextChannel):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        rem = ["disable", "remove"]
        if str(channel) in rem:
            ctx.States.Guild.level_up_channel = None
            await ctx.send(f">>> The level up channel was removed")
            return    
        ctx.States.Guild.level_up_channel = channel
        
        await ctx.send(f">>> The level up channel chaged to to {channel.mention}")  
        
    @setup.command()     
    @commands.has_permissions(administrator=True)
    async def vc(self, ctx, channel: discord.TextChannel):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        rem = ["disable", "remove"]
        if str(channel) in rem:
            ctx.States.Guild.voice_text_channel = None
            await ctx.send(f">>> The primary voice text channel was removed")
            return    
        ctx.States.Guild.voice_text_channel = channel
        
        await ctx.send(f">>> The primary voice text channel chaged to to {channel.mention}") 
        
    @setup.command(name="doujin-category", aliases=["djcat"])
    @commands.has_permissions(administrator=True)
    async def doujin_category(self, ctx, name):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        rem = ["disable", "remove"]
        if name in rem:
            ctx.States.Guild.doujin_category = None
            await ctx.send(">> All doujin channels will not be created in any category.")
            return
        
        ctx.States.Guild.doujin_category = name
        
        await ctx.send(f">>> All doujin channels will be created in `{name}` from now on.")
        
    @setup.command(aliases=["roles"])
    @commands.has_permissions(administrator=True)
    async def ranks(self, ctx):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        rem = ["disable", "remove"]
        res = {}
        
        await ctx.send(""">>> Send the ranks you want to add like this `add @role level_required`, a total of 6 will be accepted, say `stop` when done.
                        You can only add a maximum of 10 roles""")
        
        while len(res) <= 10:
        
            try:
                message = await self.client.wait_for("message", check=lambda m: m.author == ctx.author and m.content.startswith("add "), timeout=60)
                message: discord.Message
            except asyncio.TimeoutError:
                await ctx.send("Looks like no one is adding any more roles")
                res = {}
                break
            else:
                if message.content in rem:
                    res = {}
                    await ctx.send("All rank roles removed, exp counting disabled.")
                    break
                elif message.content.startswith("add @"):
                    spl = message.content.split()
                    role = discord.utils.get(ctx.guild.roles, id=int(spl[1][3:][:-1]))
                    rank = int(spl[2])
                    
                    if role in res.values():
                        await ctx.send("That's a duplicate you phoccin.", delete_after=5)
                        continue
                    if rank in res.keys():
                        await ctx.send("Two roles cant have the same level requirement u phoccin", delete_after=5)
                    
                    res[rank] = role
                elif message.content == "stop":
                    break
                else:
                    await ctx.send(f"`{message.content}` is not a valid response.")
        else:
            await ctx.send("All 6 roles added")
        
        ctx.States.Guild.ranks = res
        
    @setup.command(aliases=["default"])
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        yes = ["perhaps", "yea", "yes", "y", "yup", "yeah", "ofc"]
        no = ["nope", "nah", "no", "n", "nop"]
        
        await ctx.send(">>> You sure you wanna reset the setup?")
          
        while True:
        
            try:
                message = await self.client.wait_for("message", check=lambda m: m.author == ctx.author, timeout=20)
                message: discord.Message
            except asyncio.TimeoutError:
                await ctx.send("Looks like you couldn't decide")
                return
            else:
                response = message.content
                if response in yes:
                    await ctx.send(">>> All the setUp has been reset")
                    ctx.States.Guild.reset()
                    return
                
                elif response in no:
                    await ctx.send(">>> You lack the balls hehehehehe.")
                    return
                else:
                    await ctx.send(">>> Reply in human language.", delete_after=5)
                    continue

    @setup.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, *, pre):
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        ctx.States.Guild.prefix = pre
        
        await ctx.send(f"Bot prefix changed to `{ctx.States.Guild.prefix}`")
        
def setup(client):
    client.add_cog(Utility(client))
