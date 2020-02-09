import discord
from discord.ext import commands

class Testing(commands.Cog):
    ''':spy: TESTING 123'''

    def __init__(self, client):
        self.client = client  
    
    def log(self, msg):  # ! funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    @commands.command()
    async def roles(self,ctx):
        '''Shows all your WORTHLESS roles.'''

        await ctx.send(ctx.author.roles)
        
    @commands.command()
    async def role_rgb(self,ctx,role:discord.Role):
        await ctx.send(role.color.to_rgb())

def setup(client):
    client.add_cog(Testing(client))
