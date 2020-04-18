from dotenv import load_dotenv #? ENV
load_dotenv()

#? OS/SYS
import os
import sys
import imp

#? DISCORD
import discord
from discord.ext import commands, tasks
from discord.utils import oauth_url

#? ALL OTHERS
from itertools import cycle
import asyncio
from selenium.webdriver import Chrome as webdriver

#? FILES
import Help

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../others/general.py"))

import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../others/state.py"))

from state import GuildState

PATHS = ["./Bin"]
TOKEN = os.environ.get("DISCORD_BOT_SECRET")
CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
COGS_PATH = os.path.join(os.path.dirname(__file__), "cogs")
PERMISSIONS = discord.Permissions(administrator=True,
                                  manage_channels=True,
                                  add_reactions=True,
                                  read_messages=True,
                                  send_messages=True,
                                  manage_messages=True,
                                  embed_links=True,
                                  attach_files=True,
                                  external_emojis=True,
                                  connect=True,
                                  speak=True,
                                  manage_roles=True,
                                  manage_emojis=True
                                  )
WELCOME_MSG = """
asasas
"""
EMOJIS_PATH = os.path.abspath("./assets/emojis")
# * CLIENT SETUP
prefix = gen.permu("me! ") + gen.permu("epic ")
async def determine_prefix(bot, message):
    if message.guild:
        state_prefix = GuildState(message.guild).prefix
        return state_prefix if state_prefix is not None else prefix
    else:
        return prefix

client = commands.Bot(command_prefix=determine_prefix, case_insensitive=True)
status = cycle(gen.status)

# * COG SET UP STUFF

is_cog = lambda filename: filename.endswith(".py") and not filename.endswith("-d.py")

@client.command(aliases=["enable"])
#@commands.has_role(gen.admin_role_id)
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")
    await ctx.send(f">>> {extension.capitalize()} commands are now ready to deploy.")
    
@client.command(aliases=["enable_all"])
#@commands.has_role(gen.admin_role_id)
async def load_all(ctx):
    cog_load_startup()

@client.command(aliases=["disable"])
#@commands.has_role(gen.admin_role_id)
async def unload(ctx, extension):
    
    client.unload_extension(f"cogs.{extension}")
    await ctx.send(f">>> {extension.capitalize()} commands were stopped, Master. ")

@client.command(aliases=["disable_all"])
#@commands.has_role(gen.admin_role_id)
async def unload_all(ctx):
    
    for filename in os.listdir(COGS_PATH):
        if is_cog(filename=filename):        
            client.unload_extension(f"cogs.{filename[:-3]}")

@client.command(aliases=["refresh"])
#@commands.has_role(gen.admin_role_id)
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    await ctx.send(f">>> {extension.capitalize()} commands drank some coke, they are now refreshed. ")


@client.command(aliases=["refresh_all"])
#@commands.has_role(gen.admin_role_id)
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
#@commands.has_role(gen.admin_role_id)
async def backup(ctx, *, msg=""):
    done = gen.commit(f"| Manual - {msg} |")
    if not msg == "" and done:
        await ctx.send(f">>> Everything backed up with message - ```{msg}```")
    elif msg == "":
        await ctx.send(">>> Everything backed up with no message because your lazy ass could'nt be bothered to type")
    else:
        await ctx.send(">>> Couldn't Backup Since Commit upto the mark.")

@client.command(aliases = ["reboot"])
#@commands.has_role(gen.admin_role_id)
async def re_init(ctx):
    
    await ctx.invoke(client.get_command("unload_all"))
    await ctx.send("DONE")
    os.execv(sys.executable, ['python'] + sys.argv)  

@client.command(aliases=["Debug","Development"])
#@commands.has_role(gen.admin_role_id)
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

@client.command()
async def invite(ctx: commands.Context):
    url = oauth_url(CLIENT_ID, permissions=PERMISSIONS) 
    embed = discord.Embed(color=discord.Color.dark_magenta(),
                            url=url,
                            timestamp=ctx.message.created_at,
                            title= "Invite Me!",
                            description="Invite Me! to your guild by clicking on the title.",
                            )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
    embed.set_thumbnail(url=client.user.avatar_url)
    
    await ctx.send(embed=embed)

# ? EVENTS

# * STATUS CHANGE
@tasks.loop(seconds=6)
async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))

@tasks.loop(hours = 24)
async def auto_backup():
    if not gen.db_receive("var")["DEV"]:
        gen.commit("| Auto |")

# * ON READY
@client.event
async def on_ready():
    [os.sys.path.append(os.path.abspath(path)) for path in PATHS]
    client.help_command = Help.MyHelpCommand()
    change_status.start()
    #auto_backup.start() 
    cog_load_startup()
    
    #gen.reset()

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
async def on_command_error(ctx, error):
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
    else:
        if not isinstance(error,commands.MissingRequiredArgument):
            gen.error_message(error)    

client.run(TOKEN)
