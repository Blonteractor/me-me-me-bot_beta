from dotenv import load_dotenv #? ENV
load_dotenv()

#? OS/SYS
import os
import sys
import imp

#? DISCORD
import discord
from discord.ext import commands, tasks


#? ALL OTHERS
from itertools import cycle

import traceback    

#? FILES
from Help import MyHelpCommand

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../others/general.py"))

import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../others/state.py"))

from state import GuildState, CustomContext

PATHS = ["./Bin"]
TOKEN = os.environ.get("DISCORD_BOT_SECRET")

COGS_PATH = os.path.join(os.path.dirname(__file__), "cogs")

WELCOME_MSG = """
asasas
"""
EMOJIS_PATH = os.path.abspath("./assets/emojis")
DB_PATH = os.path.abspath("./Database")

prefix = gen.permu("me! ") + gen.permu("epic ")

OWNERS = [413287145323626496, 580282285002194966]

async def determine_prefix(bot, message):
    if message.guild:
        state_prefix = GuildState(message.guild).prefix
        return state_prefix if state_prefix is not None else prefix
    else:
        return prefix
    
class Bot(commands.Bot):
    async def on_message(self, message):
        ctx = await self.get_context(message, cls=CustomContext)
        await self.invoke(ctx)

client = Bot(command_prefix=determine_prefix, case_insensitive=True, help_command=MyHelpCommand())
status = []

# * COG SET UP STUFF

is_cog = lambda filename: filename.endswith(".py") and not filename.endswith("-d.py")

def mod_command():
    async def predicate(ctx):
        channel = ctx.message.channel
        if ctx.author.id in OWNERS:
            return True
        else:
            await channel.send("Really?")
            return False
    return commands.check(predicate)


@client.command(aliases=["enable"])
@mod_command()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")
    await ctx.send(f">>> {extension.capitalize()} commands are now ready to deploy.")
    
@client.command(aliases=["enable_all"])
@mod_command()
async def load_all(ctx):
    cog_load_startup()

@client.command(aliases=["disable"])
@mod_command()
async def unload(ctx, extension):
    
    client.unload_extension(f"cogs.{extension}")
    await ctx.send(f">>> {extension.capitalize()} commands were stopped, Master. ")

@client.command(aliases=["disable_all"])
@mod_command()
async def unload_all(ctx):
    
    for filename in os.listdir(COGS_PATH):
        if is_cog(filename=filename):        
            client.unload_extension(f"cogs.{filename[:-3]}")

@client.command(aliases=["refresh"])
@mod_command()
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    await ctx.send(f">>> {extension.capitalize()} commands drank some coke, they are now refreshed. ")


@client.command(aliases=["refresh_all"])
@mod_command()
async def reload_all(ctx):
    
    for filename in os.listdir(COGS_PATH):
        if is_cog(filename=filename):        
            client.unload_extension(f"cogs.{filename[:-3]}")
            client.load_extension(f"cogs.{filename[:-3]}")


def cog_load_startup():
    
    for filename in os.listdir(COGS_PATH):
        if is_cog(filename=filename):
            client.load_extension(f"cogs.{filename[:-3]}")

# * BACKING UP AND COMMIT STUFF
@client.command(aliases=["commit", "baccup"])
@mod_command()
async def backup(ctx, *, msg=""):
    done = gen.commit(f"| Manual - {msg} |")
    if not msg == "" and done:
        await ctx.send(f">>> Everything backed up with message - ```{msg}```")
    elif msg == "":
        await ctx.send(">>> Everything backed up with no message because your lazy ass could'nt be bothered to type")
    else:
        await ctx.send(">>> Couldn't Backup Since Commit upto the mark.")

@client.command(aliases = ["reboot"])
@mod_command()
async def re_init(ctx):
    
    await ctx.invoke(client.get_command("unload_all"))
    await ctx.send("DONE")
    os.execv(sys.executable, ['python'] + sys.argv)  

@client.command(aliases=["Debug","Development"])
@mod_command()
async def develop(ctx , on_off, cog=""):

    var = gen.db_receive("var")
    if on_off.lower() == "on" or on_off.lower() == "true":    
        var["DEV"] = 1

        if not cog == "":
            if cog in var["cogs"]:
                var["cogs"][cog] = 1
            else:
                await ctx.send("The cog doesn't even exist BIG BREN.")
                return
        else:
            for cog, debug in var["cogs"].items():
                var["cogs"][cog] = 1

        await ctx.send("DONE.") 

    elif on_off.lower() == "off" or on_off.lower() == "false":    

        if not cog == "":
            var["DEV"] = 1
            if cog in var["cogs"]:
                var["cogs"][cog] = 0
            else:
                await ctx.send("The cog doesn't even exist BIG BREN.")
                return
        else:
            var["DEV"] = 0
            for cog, debug in var["cogs"].items():
                var["cogs"][cog] = 0


        await ctx.send("DONE.")

    else:
        await ctx.send("ITS on OR off. (True or False).")
        
    gen.db_update("var",var)



# ? EVENTS

# * STATUS CHANGE
@tasks.loop(seconds=6)
async def change_status():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=next(status)))

@tasks.loop(hours = 24)
async def auto_backup():
    if not gen.db_receive("var")["DEV"]:
        gen.commit("| Auto |")

# * ON READY
@client.event
async def on_ready():
  
    change_status.start()
    #auto_backup.start() 
   
    cog_load_startup()
    
    global status
    status = cycle([f"me! help {name}" for name in list(client.cogs.keys())])
   
    #gen.reset()
    
    with open(os.path.join(DB_PATH, "temp.pkl"), "wb") as f:
        f.write(b"")

    print('Bot is ready as sef!')
    
#* WELCOME MESSAGE AND ADD NECESSARY EMOJIS OT GUILD WHEN BOT JOINS A GUILD
@client.event
async def on_guild_join(guild: discord.Guild):
    general = guild.text_channels[0]
    await general.send(WELCOME_MSG)
    
    for emoji_img in os.listdir(EMOJIS_PATH):
        name = emoji_img.split(".")[0]
        
        with open(os.path.join(EMOJIS_PATH, emoji_img), "rb") as emoji:
            b = emoji.read()
            
        await guild.create_custom_emoji(name=name,
                                        reason="This emoji is needed by the Me!Me!Me! bot to function properly",
                                        roles=discord.utils.get(guild.roles, name="Me!Me!Me!"),
                                        image=b
                                        )
# * COMMAND NOT FOUND
@client.event
async def on_command_error(ctx, error: discord.DiscordException):
    if isinstance(error, commands.CommandNotFound):
        message = await ctx.send(">>> That isn't even a command, you have again proven to be a ME!stake.")
        try:
            await message.delete()
        except:
            pass
    elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Woah woah, gonnae wait??",
                                  color = discord.Color.red(),
                                   description=f"We have cooldowns here, try again after `{round(error.retry_after, 1)}s` ")
            await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="Missing Permissions",
                                  color = discord.Color.red())
        
        description = "You are missing the following permsissions\n"
        for perm in error.missing_perms:
            description += f"\n`{perm}`"
        description += "\n\n You can go beg the mods for them or something idk."
        
        embed.description = description
        
        await ctx.send(embed=embed)
    else:
        if not isinstance(error,commands.MissingRequiredArgument):
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            gen.error_message(error)   

client.run(TOKEN)
