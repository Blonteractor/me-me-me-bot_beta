import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
import random
from discord.ext import commands
import general as gen
from state import CustomContext as cc 



class Currency(commands.Cog):
    ''':moneybag: Virtual money dudes'''
    
    cooldown = 0

    def __init__(self, client):
        self.client = client      
        
        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
            
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

    
    #! BET
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def bet(self, ctx, amount : int):
        '''Use this command to bet souls you had earned.'''
        
        #! GET COINS
        coins = int(ctx.States.User.souls)

        #! REAL BITCH ASS CODE
        if amount <= coins and amount>0:
            player_dye = random.randint(1,6)
            cpu_dye = random.randint(1,6)
            if player_dye > cpu_dye:
                won_lost = "Bet Won"
                amount_rec = int((amount)*(((player_dye-cpu_dye-0.9)**(1/3))-1))
                Multiplier = 100 + int((((player_dye-cpu_dye-0.9)**(1/3))-1)*100)
            elif player_dye==cpu_dye:
                won_lost = "Bet Won"
                amount_rec=(amount)
                Multiplier = 200
            else:
                won_lost = "Bet Lost"
                amount_rec = -(amount)
                Multiplier = -100
                
            coins+=amount_rec

            ctx.States.User.souls = coins
            
        elif amount<= 0:
            await ctx.send(f">>> You are a little daring today, aren't you, {ctx.author.name}.")
        else:
            await ctx.send(">>> Not enough SOULS man, go hunt.")

        #! EMBED
        if won_lost == "Bet Won":
            colour = discord.Colour.green()

        else:
            colour = discord.Colour.from_rgb(255,0,0)
        bet_list = discord.Embed(
            title = "ME! BET RESULT",
            description = "Lets begin the betting of your souls then.",
            colour = colour
        )

        bet_list.add_field(name="Souls Bet", value =amount ,inline=False)
        bet_list.add_field(name="Your Roll", value = player_dye,inline = True)
        bet_list.add_field(name="ME! Roll", value = cpu_dye,inline = True)
        bet_list.add_field(name = "WON/LOST",value =won_lost ,inline=True)
        bet_list.add_field(name = "Multiplier",value = f"{Multiplier}%",inline=True)
        bet_list.add_field(name = "Amount Recieved",value = amount_rec,inline=True)
        bet_list.add_field(name = "Total Souls Left",value = coins ,inline=True)
        bet_list.set_author(name = f"{ctx.author.name}'s BET", icon_url = ctx.author.avatar_url)

        await ctx.send(embed = bet_list)
        #! SAVE THOSE DAMN COINS

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(">>> You need to bet something to gamble, seems like common sense tbh.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(">>> U need to have actual souls, go hunt POET.")
    
    #? BANK
    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def bank(self, ctx):
        '''When you are broke, cry in front of the GOVT. and get some loan to use in a game which will have no impact on your true irl broke ass.'''
        a = random.randrange(1,10)
        coins = ctx.States.User.souls

        if coins == 0:
            await ctx.send(f">>> Given {a} SOULS to {ctx.author.name}, get rekt.")
            ctx.States.User.souls += a
        else:
            await ctx.send(">>> You are way too rich for us, get lost.") 

    #? SOULS
    @commands.command(aliases=['bal','coins'])
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def souls(self, ctx):
        '''Just the balance of your souls. THATS IT.'''
        await ctx.send(f">>> Souls of {ctx.author.name}: {ctx.States.User.souls}.")


def setup(client):
    client.add_cog(Currency(client))
