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

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))

from state import CustomContext as cc


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
    
    cooldown = 0

    nhentai_logo = "https://i.imgur.com/uLAimaY.png" #! nhentai logo url
    tags:  List[str] = gen.db_receive("nos")["tags"] #! the tags by which doujins are searched
    
    #* INIT AND PREQUISITES
    def __init__(self, client):
        self.client = client 
        self.nh = nhenpy.NHentai()                            #! nhentai client
        
        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.qualified_name]
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
        
    def vault_add(self, user: discord.User, item):
        vault = gen.db_receive("vault")
        user_id = str(user.id)
        
        if user_id not in vault.keys():
            vault[user_id] = {}
            
        vault[user_id][len(vault[user_id]) + 1] = item
        
        gen.db_update("vault", vault)
    
    def vault_remove(self, user: discord.User, index):
        vault = gen.db_receive("vault")
        user_id = str(user.id)
        
        if len(vault[user_id].keys()) < int(index):
            return None

        removed = vault[user_id].pop(index)
        
        gen.db_update("vault", vault)
        
        return removed

    def update_doujin_page_creater(self, embed: discord.Embed, doujin): #! function which creates a function to update page of embed
        def update_page(page):
            embed.set_image(url=doujin.get_images()[page - 1])

            embed.clear_fields()
            embed.add_field(
                name="Page", value=f"**{page}** of ***{len(doujin.get_images())}***")

            return embed

        return update_page
    
    async def doujin_react(self, doujin, ctx: commands.Context, embed_msg: discord.Message, check=None, wait_time=90):  
        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)
                
        def default_check(reaction: discord.Reaction, user):
            return user == ctx.author and reaction.message.id == embed_msg.id
                
        if check is None:
            check = default_check 
            
        doujin_id = str(doujin).split("]")[0][2:]   
                
        reactions = {"read": "📖","delete": "❌", "save": "💾"}
        
        self.client.loop.create_task(reactions_add(reactions=reactions.values(), message=embed_msg))
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=wait_time, check=check)
            except TimeoutError:
                await embed_msg.clear_reactions()
                
                return

            else:
                response = str(reaction.emoji)
                
                await embed_msg.remove_reaction(response, ctx.author)

                if response in reactions.values():
                    if response == reactions["read"]:
                        await self.watch(ctx, doujin_id=doujin_id)

                    elif response == reactions["save"]:
                        self.vault_add(user=ctx.author, item=doujin_id)
                        
                    elif response == reactions["delete"]:
                        await embed_msg.delete(delay=3)
                        
                        return

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
        
    async def find_doujins(self, search_by, search_tag, page_limit):
        found = False
        prev = 0
        rand = randint(1, page_limit)
        while not found:
            prev = rand
            search = self.nh.search(f"{search_by}:{search_tag}", rand)
            found = await self.doujin_found(search)
            if not found:
                rand = randint(1, prev)
        else:
            return search

    #* ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log("Check Failed for nsfw channel.")
        else:
            pass

    #* MAIN

    @commands.command(aliases=["4k"])
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    @nsfw_command()
    async def porn(self, ctx):   #! sends 4k porn pics
        '''4K, hacc certified pics'''

        image_found = False

        while not image_found:
            index = randrange(1, 1460)
            hacc = f"https://cdn.boob.bot/4k/4k{index}.jpg"

            response = requests.get(hacc)
            image_found = response.ok

        else:
            embed = discord.Embed(title="Here, satisfied yet?",
                                  color=discord.Colour.dark_magenta())
            embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                            icon_url=ctx.message.author.avatar_url)
            embed.set_image(url=hacc)
            
            await ctx.send(embed=embed)
            return
        

    @commands.command(usage="<doujin id>")
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @nsfw_command()
    async def read(self, ctx, doujin_id): #! makes a different channel in the doujins categoryand posts all doujin images there
        '''Read the doujin, will create a seperate channel and post all images there. Recomend muting the doujin category.'''

        doujin = nhenpy.NHentaiDoujin(f"/g/{doujin_id}")
        doujin_pages = len(doujin.pages)
        url = f"https://nhentai.net/g/{doujin_id}/"

        if not await self.doujin_found(doujin, ctx.message.channel):
            return

        category = discord.utils.get(
            ctx.guild.categories, name=ctx.GuildState.doujin_category)
        category: discord.CategoryChannel

        channel_exists = False
        channel_exists = not discord.utils.get(
            ctx.guild.text_channels, name=doujin_id) == None

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

    @commands.command(aliases=["show"], usage="<doujin id> [page number -> 1]")
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
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

        self.client.loop.create_task(reactions_add(embed_msg, reactions.values()))

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

                        if page > len(doujin_pages):
                            page = len(doujin_pages)

                        embed = update_page(page)
                        await embed_msg.edit(embed=embed)

                    elif str(reaction.emoji) == reactions["back"]:
                        page -= 1

                        if page < 0:
                            page = 1  

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

    @commands.group(aliases=["doujin", "doujinshi"], usage="<doujin id>")
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @nsfw_command()
    async def nhentai(self, ctx, doujin_id: str,*, query=""): #! veiw information about the doujin, nama, artist, etc. 
        '''View the doujin, tags, artist and stuff, powered by nhentai.net, subcommands for more specific searches available'''

        if doujin_id.isnumeric():
            doujin = nhenpy.NHentaiDoujin(f"/g/{doujin_id}")

            if not await self.doujin_found(doujin, ctx.message.channel):
                return

            embed_msg = await ctx.send(embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))
            await self.doujin_react(doujin=doujin, ctx=ctx, embed_msg=embed_msg, wait_time=120)

        elif doujin_id.lower() == "random":
            await self.random(ctx)
            
        elif doujin_id.lower() == "parody":
            await self.parody(ctx, query=query)
            
        elif doujin_id.lower() == "artist":
            await self.artist(ctx, query=query)
            
        elif doujin_id.lower() == "character":
            await self.character(ctx, query=query)

        else:
            await ctx.send(">>> Enter the `ID` of the doujin you wanna look up.")

    @nhentai.command()
    @nsfw_command()
    async def random(self, ctx): 
        '''Gives you a random doujin to enjoy yourself to'''
        self.loading_emoji = str(discord.utils.get(ctx.guild.emojis, name="loading"))
        embed_msg = await ctx.send(f"Searching for doujins on nhentai.......{self.loading_emoji}")
        
        search = await self.find_doujins(search_by="tag", search_tag=str(choice(self.tags)), page_limit=50)

        doujin = choice(search)
        doujin_id = str(doujin).split("]")[0][2:]

        await embed_msg.edit(content="", embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))
        await self.doujin_react(doujin=doujin, ctx=ctx, embed_msg=embed_msg, wait_time=120)
        
    @nhentai.command()
    @nsfw_command()
    async def parody(self, ctx,*, query): 
        '''Gives you a doujin on the parody you specified'''

        self.loading_emoji = str(discord.utils.get(ctx.guild.emojis, name="loading"))
        embed_msg = await ctx.send(f"Searching for doujins on nhentai, parody of `{query}`.......{self.loading_emoji}")
            
        search = await self.find_doujins(search_by="parody", search_tag=query, page_limit=20)
        
        if len(search) > 0:
            doujin = choice(search)
            doujin_id = str(doujin).split("]")[0][2:]

            await embed_msg.edit(content="", embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))
            await self.doujin_react(doujin=doujin, ctx=ctx, embed_msg=embed_msg, wait_time=120)
        else:
            await embed_msg.edit(content=f">>> No doujin found parodying `{query}`", embed=None)
            
    @nhentai.command()
    @nsfw_command()
    async def artist(self, ctx,*, query): 
        '''Gives you a doujin of the artist you specified'''

        self.loading_emoji = str(discord.utils.get(ctx.guild.emojis, name="loading"))
        embed_msg = await ctx.send(f"Searching for doujins on nhentai by `{query}`.......{self.loading_emoji}")

        search = await self.find_doujins(search_by="artist", search_tag=query, page_limit=10)

        if len(search) > 0:
            doujin = choice(search)
            doujin_id = str(doujin).split("]")[0][2:]

            await embed_msg.edit(content="", embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))
            await self.doujin_react(doujin=doujin, ctx=ctx, embed_msg=embed_msg, wait_time=120)
        else:
            await embed_msg.edit(content=f">>> No doujin found of {query}", embed=None)
            
    @nhentai.command()
    @nsfw_command()
    async def character(self, ctx,*, query): 
        '''Gives you a doujin featuring the character you specified'''
        
        self.loading_emoji = str(discord.utils.get(ctx.guild.emojis, name="loading"))
        embed_msg = await ctx.send(f"Searching for doujins on nhentai with character `{query}` .......{self.loading_emoji}")

        search = await self.find_doujins(search_by="character", search_tag=query, page_limit=15)

        if len(search) > 0:
            doujin = choice(search)
            doujin_id = str(doujin).split("]")[0][2:]

            await embed_msg.edit(content="", embed=self.doujin_embed(doujin, ctx.message.author, doujin_id))
            await self.doujin_react(doujin=doujin, ctx=ctx, embed_msg=embed_msg, wait_time=120)
        else:
            await embed_msg.edit(content=f">>> No doujin found featuring {query}", embed=None)
            
    @commands.group()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    @nsfw_command()
    async def vault(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            user_vault = list(gen.db_receive("vault")[str(ctx.author.id)].values())
            content = [nhenpy.NHentaiDoujin(f"/g/{item}") for item in user_vault]
            
            embed: discord.Embed = discord.Embed(title=f"{ctx.author.name}'s vault",
                                                color=discord.Color.from_rgb(255, 9, 119))
            embed.set_thumbnail(url=self.nhentai_logo) 
            embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
            
            for index, item in enumerate(content):
                item_id = str(item).split("]")[0][2:]
                embed.add_field(name=f"{index + 1}.", value=f"{item.title} --> ***{item_id}***", inline=False)
                
            await ctx.send(embed=embed)
        
    @vault.command()
    async def release(self, ctx: commands.Context):
        user_vault = list(gen.db_receive("vault")[str(ctx.author.id)].values())      
        content = [nhenpy.NHentaiDoujin(f"/g/{item}") for item in user_vault]
        
        await ctx.send(">>> Your whole vault is being sent to your DM.")
        await ctx.author.send(">>> Here's your vault, enjoy!")
        
        for item in content:
            await ctx.author.send(embed=self.doujin_embed(doujin=item, author=ctx.author, doujin_id=str(item).split("]")[0][2:]))
            
        await ctx.author.send("That's all folks.")
    
    @vault.command()
    @nsfw_command()
    async def pop(self, ctx: commands.Context, index):
        try:
            i = int(index)
        except:
            await ctx.send(">>> Indexes are supposed to be numbers.")
            return
        
        removed_id = self.vault_remove(ctx.author, index=index)
        removed_name = nhenpy.NHentaiDoujin(f"/g/{removed_id}").name
        
        if removed_id is None:
            await ctx.send(">>> The index you entered is bigger than the size of your vault.")
            return
        
        await ctx.send(f">>> Removed `{removed_name}` from your vault")
    

def setup(client):
    client.add_cog(nsfw(client))
