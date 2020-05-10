import discord
from discord.ext import commands

TOKEN = "NzAwMjkwNjk0OTE2NDcyODgy.XqaBVQ.FD0wqmpER3ikWNvXeYDFa1IU1oM"

bot = commands.Bot(command_prefix="&", case_insensitive=True)

@bot.event
async def on_ready():
    print("Big brane's 2 brain cells ready to work")
    
@bot.command()
async def tes(ctx, *, args):
    await ctx.send(f"Hello there, `_{args}_`")
    
bot.run(TOKEN)