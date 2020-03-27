import discord
from discord.ext import commands
import concurrent.futures

import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen

imp.load_source("command", os.path.join(
    os.path.dirname(__file__), "../../others/command.py"))

def multi(func):
    def wrapper(*args, **kwargs):
        if __name__ == "cogs.testing":
            return func(*args, **kwargs)
        else:
            return "no"
    return wrapper

@multi
def process(func, wargs):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        p = executor.submit(func, wargs)

    return p.result()

@multi
def thread(func, wargs):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        t = executor.submit(func, wargs)
        
    return "".join(t.result())

class Testing(commands.Cog):
    ''':spy: TESTING 123'''
    
    def test(self, ok):
        return ok

    def __init__(self, client):
        self.client = client  
        
        
    async def cooldown_check(self, ctx):
        self._cd = commands.CooldownMapping.from_cooldown(1, gen.cog_cooldown["default"] + 10, commands.BucketType.user)
       
        bucket = self._cd.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            raise commands.CommandOnCooldown
    
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
    async def role_rgb(self,ctx,role: discord.Role):
        await ctx.send(role.color.to_rgb())
        
    @commands.command()
    async def tes(self, ctx, okok):
        await self.cooldown_check(ctx)
        okokok = thread(self.test, [okok])
        await ctx.send(f">>> {okokok}")

def setup(client):
    client.add_cog(Testing(client))
