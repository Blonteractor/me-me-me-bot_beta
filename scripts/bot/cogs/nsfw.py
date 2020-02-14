import discord
from discord.ext import commands

from random import choice, randint, randrange
from asyncio import TimeoutError
from typing import List
import requests


import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen

imp.load_source("nhenpy", os.path.join(
    os.path.dirname(__file__), "../../others/nhenpy.py"))

import nhenpy




#* DECORATOR FOR CHECKING IF COMMAND IS BEING RUN IN A NSFW CHANNEL
def nsfw_command():
    async def predicate(ctx):
        channel = ctx.message.channel
        if channel.is_nsfw():
            return True
        else:
            await channel.send(">>> Ya know this server has children in it go to a NSFW channel or something ffs.")
            return False
    return commands.check(predicate)


class nsfw(commands.Cog):
    ''':high_heel: Commands for big boiz.'''

    #* INIT AND PREQUISITES
    def __init__(self, client):
        self.nhentai_logo = "https://i.imgur.com/uLAimaY.png" #! nhentai logo url
        self.doujins_category_name = "Doujins 📓"             #! name of category in which doujins are posted
        self.tags:  List[str] = gen.db_receive("nos")["tags"] #! the tags by which doujins are searched
        self.nh = nhenpy.NHentai()                            #! nhentai client
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


    def update_doujin_page_creater(self, embed: discord.Embed, doujin): #! function which creates a function to update page of embed
        def update_page(page):
            embed.set_image(url=doujin.get_images()[page - 1])

            embed.clear_fields()
            embed.add_field(
                name="Page", value=f"**{page}** of ***{len(doujin.get_images())}***")

            return embed

        return update_page

    def doujin_embed(self, doujin, author, doujin_id=0): #! creaters an embed of a doujin
        url = f"https://nhentai.net/g/{doujin_id}/"
        doujin_info = doujin.labels
        try:
            language_type = doujin_info["language"][0]
            language = doujin_info["language"][1]
        except:
            language_type = "native"
            language = doujin_info["language"][0]

        category = doujin_info["category"][0]
        cover_url = doujin.get_images()[0]
        doujin_tags = doujin_info["tags"]

        try:
            doujin_artist = doujin_info["artist"][0]
        except IndexError:
            doujin_artist = "unknown"
        doujin_pages = len(doujin.pages)

        tags = ""
        i = 0
        for i in range(len(doujin_tags)):
            if not i == 0:
                tags += f"| `{doujin_tags[i]}` "
            else:
                tags += f" `{doujin_tags[i]}` "

        embed = discord.Embed(title=doujin.title, url=url,
                              color=discord.Colour.red())
        embed.set_author(name="Me!Me!Me!",
                         icon_url=self.client.user.avatar_url)
        embed.set_footer(
            text=f"Requested By: {author.display_name}", icon_url=author.avatar_url)
        embed.add_field(name="Language", value=language_type + ", " + language)
        embed.add_field(name="Pages", value=doujin_pages)
        if doujin_id != 0:
            embed.add_field(name="ID", value=doujin_id)
        embed.add_field(name="Category", value=category)
        embed.add_field(name="Artist", value=doujin_artist)
        embed.add_field(name=f"Tags", value=tags, inline=False)
        embed.set_image(url=cover_url)
        embed.set_thumbnail(url=self.nhentai_logo)

        return embed

    async def doujin_found(self, doujin, channel=None): #! checks if doujin exists
        if len(doujin.pages) <= 0:
            if not channel is None:
                await channel.send(">>> Couldn't find the doujin, sorry")
            return False
        else:
            return True

    #* ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log("Check Failed for nsfw channel.")
        else:
            pass

    #* MAIN

    @commands.command(aliases=["4k"])
    @nsfw_command()
    async def porn(self, ctx):   #! sends 4k porn pics
        '''4K, hacc certified pics'''

        image_found = False

        while not image_found:
            index = randrange(1, 1460)
            hacc = f"https://cdn.boob.bot/4k/4k{index}.jpg"

            response = requests.get(hacc)
            image_found = response.ok

            embed = discord.Embed(
                title="Here, satisfied yet?", color=discord.Colour.dark_magenta())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_footer(
                text=f"Requested By: {ctx.message.author.display_name}", icon_url=ctx.message.author.avatar_url)
            embed.set_image(url=hacc)

            await ctx.send(embed=embed)
        else:
            return

    @commands.command()
    async def read(self, ctx, doujin_id): #! makes a different channel in the doujins categoryand posts all doujin images there
        '''Read the doujin, will create a seperate channel and post all images there. Recomend muting the doujin category.'''

        doujin = nhenpy.NHentaiDoujin(f"/g/{doujin_id}")
        doujin_pages = len(doujin.pages)
        url = f"https://nhentai.net/g/{doujin_id}/"

        if not await self.doujin_found(doujin, ctx.message.channel):
            return

        guild = ctx.message.guild
        guild: discord.Guild
        category = discord.utils.get(
            guild.categories, name=self.doujins_category_name)
        category: discord.CategoryChannel

        channel_exists = False
        channel_exists = not discord.utils.get(
            guild.text_channels, name=doujin_id) == None

        if not channel_exists:
            channel = await ctx.guild.create_text_channel(str(doujin_id), nsfw=True, category=category)

            await ctx.send(f">>> Go to {channel.mention} and enjoy your doujin!")

            doujin_images = doujin.pages

            embed = discord.Embed(title=doujin.title,
                                  url=url, color=discord.Colour.red())
            embed.set_footer(
                text=f"Requested By: {ctx.message.author.display_name}", icon_url=ctx.message.author.avatar_url)

            image_index = 1
            for image in doujin_images:
                embed.description = f"Page **{image_index}** of ***{doujin_pages}***"
                embed.set_image(url=image)

                image_index += 1

                await channel.send(embed=embed)

        elif channel_exists:
            channel = discord.utils.get(guild.text_channels, name=doujin_id)

            await ctx.send(f">>> Go to {channel.mention} and enjoy your doujin!")

    @commands.command(aliases=["show"])
    @nsfw_command()
    async def watch(self, ctx, doujin_id, page_number=1): #! reaction navigation approach to read command
        '''Watch the doujin, like a slideshow. Navigate using reactions. The doujin will self delete after being left idle for 3 minutes.'''

        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        reactions = {"long_back": "⏪", "back": "⬅", "forward": "➡",
                     "long_forward": "⏩", "info": "ℹ", "delete": "❌"}
        page = page_number
        wait_time = 180

        doujin = nhenpy.NHentaiDoujin(f"/g/{doujin_id}")
        doujin_pages = doujin.get_images()
        url = f"https://nhentai.net/g/{doujin_id}/"

        if not await self.doujin_found(doujin, ctx.message.channel):
            return

        embed = discord.Embed(title=doujin.title, url=url,
                              color=discord.Colour.red())

        update_page = self.update_doujin_page_creater(embed, doujin)
        embed = update_page(page_number)

        embed_msg = await ctx.send(embed=embed)
        embed_msg: discord.Message

        def check(reaction: discord.Reaction, user):
            return user == ctx.author and reaction.message.id == embed_msg.id

        self.client.loop.create_task(
            reactions_add(embed_msg, reactions.values()))

        while True:

            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await ctx.send(f">>> Everyone done reading `{doujin_id}`, so I deleted it.")
                await embed_msg.delete()

                return

            else:
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.values():

                    if str(reaction.emoji) == reactions["forward"]:
                        page += 1

                        if page >= len(doujin_pages):
                            # ? equal pe equal kyu bhai
                            page = len(doujin_pages)

                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)

                    elif str(reaction.emoji) == reactions["back"]:
                        page -= 1

                        if page <= 0:
                            page = 1  # ? equal pe equal kyu bhai

                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)

                    elif str(reaction.emoji) == reactions["long_back"]:
                        page -= len(doujin_pages) // 10

                        if page < 0:
                            page = 1

                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)

                    elif str(reaction.emoji) == reactions["long_forward"]:
                        page += len(doujin_pages) // 10

                        if page >= len(doujin_pages):
                            page = len(doujin_pages)

                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)

                    elif str(reaction.emoji) == reactions["info"]:
                        await ctx.send(embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))

                    elif str(reaction.emoji) == reactions["delete"]:
                        await embed_msg.delete(delay=1)

                        return

                else:
                    pass

    @commands.group(aliases=["doujin", "doujinshi"])
    @nsfw_command()
    async def nhentai(self, ctx, doujin_id: str): #! veiw information about the doujin, nama, artist, etc. 
        '''View the doujin, tags, artist and stuff.'''

        if doujin_id.isnumeric():
            doujin = nhenpy.NHentaiDoujin(f"/g/{doujin_id}")
            doujin_info = doujin.labels

            if not await self.doujin_found(doujin, ctx.message.channel):
                return

            await ctx.send(embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))

        elif doujin_id.lower() == "random":
            await ctx.invoke(self.client.get_command("random"))

        else:
            await ctx.send(">>> Enter the `ID` of the doujin you wanna look up.")

    @commands.command()
    @nsfw_command()
    async def random(self, ctx): #! gives info about a random doujin, selected from specific tags
        '''Gives you a random doujin to enjoy yourself to'''
        search_tag = str(choice(self.tags))
        search = self.nh.search(f"tag:{search_tag}", 1)

        doujin = choice(search)
        doujin_id = str(doujin).split("]")[0][2:]

        await ctx.send(embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))


def setup(client):
    client.add_cog(nsfw(client))
