import discord
import json
from discord.ext import commands
import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen

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
    async def stats(self, ctx):
        '''Shows stats of all the ACTIVE PEOPLE WHO HAVE NO LIFE.'''

        found=False
        for role in ctx.author.roles:
            if role.id == gen.admin_role_id:
                found=True  

        if found:
            mem_info = gen.db_receive("inf")
            
        
            for key in mem_info:
                stats = discord.Embed(
                title = "ME! Stats",
                colour = discord.Colour.from_rgb(0,0,0)
                )
                member = ctx.guild.get_member_named(mem_info[key]["name"])


                stats.set_author(name = mem_info[key]["name"], icon_url = member.avatar_url)
                stats.add_field(name = "Messages",value= mem_info[key]["messages"], inline = True)
                stats.add_field(name = "Level",value= mem_info[key]["level"], inline = True)
                stats.add_field(name = "Souls",value= mem_info[key]["coins"], inline = True)
                await ctx.send(embed = stats)

        else:
            await ctx.send("How cute, you thought you could do that.")

    #* RECORDING
    @commands.command()
    async def record_stats(self,ctx):
        '''Records stats of all the FUCKING SLAVES OF THIS SERVER.'''

        found=False
        for role in ctx.author.roles:
            if role.id == gen.admin_role_id:
                found=True  

        if found:
            for member in ctx.guild.members:
                mem_info = gen.db_receive("inf")
                disc = member.discriminator
                
                if disc in mem_info:
                    mem_info[disc]["name"] = member.name
                    gen.db_update("inf",mem_info)
                else:    
                    name = member.name
                    gen.new_entry(name,disc)
                    
                
            await ctx.send(f"Done boss")
        else:
            await ctx.send("How cute, you thought you could do that.")

    #* LEVEL
    @commands.command()
    async def level(self, ctx,member: discord.Member,level:int): 
        '''This is a MEE6 exclusive command, no puny mortal can use this.'''
        
        name = member.name
        disc = member.discriminator
        
        
        found=False
        
        for role in ctx.author.roles:                                                                               #! TODO make this a function
            if role.id == gen.admin_role_id:
                found=True    
        mee6_disc = gen.MEE6_disc
        
        if int(ctx.author.discriminator) == mee6_disc:
            found = True
        if found:      
        
            roles_list = member.roles
            for role in roles_list:
                if str(role) in gen.roles:
                    await member.remove_roles(role)
            if level < gen.level_Rookie:
                await member.add_roles(discord.utils.get(ctx.guild.roles, name="Prostitute"))
                leveler = "Prostitute"
            if level >=gen.level_Rookie and level < gen.level_Adventurer:
                await member.add_roles(discord.utils.get(ctx.guild.roles, name="Rookie"))
                leveler = "Rookie"
            if level >= gen.level_Adventurer and level <gen.level_Player:
                await member.add_roles(discord.utils.get(ctx.guild.roles, name="Adventurer"))
                leveler = "Adventurer"
            if level >= gen.level_Player and level <gen.level_Hero:
                await member.add_roles(discord.utils.get(ctx.guild.roles, name="Player"))
                leveler = "Player"
            if level >= gen.level_Hero and level <gen.level_CON:
                await member.add_roles(discord.utils.get(ctx.guild.roles, name="Hero"))
                leveler = "Hero"
            if level >= gen.level_CON:
                await member.add_roles(discord.utils.get(ctx.guild.roles, name="Council of Numericon"))  
                leveler = "Council of Numericon"

            mem_info = gen.db_receive("inf")

            if disc in mem_info:
                mem_info[disc]["level"] = leveler
            else:
                gen.new_entry(name,disc)
                mem_info[disc]["level"] = leveler

            gen.db_update("inf",mem_info)
            await ctx.send(f'Congrats **{member.display_name}** , You leveled up to Level {level}  :tada:. Now you are {leveler} :middle_finger:.')
                
        else:
            await ctx.send(">>> You Filthy Bastard ain't MEE6.")

    #* TOP SECRET DONT TOUCH
    @commands.command()
    async def admin(self, ctx):
        '''This is a top secret command, no using this.'''

        embed = discord.Embed(title = "ADMIN RIGHTS", description = "Short_Terminal_Cout_var_ADMIN_ROLE", colour = discord.Color.red(), url = gen.epic)

        await ctx.send(embed = embed)

def setup(client):
    client.add_cog(Immortal(client))