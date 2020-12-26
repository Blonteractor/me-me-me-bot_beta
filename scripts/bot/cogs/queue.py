import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands,tasks
from discord.ext.commands.core import Command, cooldown
from discord.utils import get
from asyncio import sleep, TimeoutError
import general as gen
from state import TempState

def vc_check():
    async def predicate(ctx):           # Check if the user is in vc to run the command
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if ctx.author not in voice.channel.members:
                await ctx.send(f"You either are not in a VC or in a wrong VC. Join `{voice.channel.name}`")
                return False
            else:
                return True
        else:
            return False
    return commands.check(predicate)

class Queue(commands.Cog):
    ":notebook_with_decorative_cover: Queue modification and veiwing"
    
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
   
    def __init__(self, client):
        self.client = client      

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
    
    def chunks(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    async def embed_pages(self, _content, ctx: commands.Context, embed_msg: discord.Message, check=None, wait_time=90):

        if type(_content) == str:
            if len(_content) < 2048:
                return

        async def reactions_add(message, reactions):
            for reaction in reactions:
                await message.add_reaction(reaction)

        def default_check(reaction: discord.Reaction, user):
            return user == ctx.author and reaction.message.id == embed_msg.id

        if check is None:
            check = lambda reaction, user: user == ctx.author and reaction.message.id == embed_msg.id

    
        if type(_content) == str:
            content_list = _content.split("\n")
            content = []
            l = ""
            for i in content_list:
                if len(l+i) > 2048:
                    content += [l]
                    l = ""
                l += i
                l += "\n"    
            else:
                content += [l]

        elif type(_content) == list:
            content = _content

        pages = len(content)
        page = 1

        embed: discord.Embed = embed_msg.embeds[0]

        def embed_update(page):
            embed.description = content[page - 1]
            return embed

        await embed_msg.edit(embed=embed_update(page=page))

        reactions = {"back": "⬅", "delete": "❌", "forward": "➡"}

        self.client.loop.create_task(reactions_add(
            reactions=reactions.values(), message=embed_msg))

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
                    if response == reactions["forward"]:
                        page += 1
                        if page > pages:
                            page = pages
                    elif response == reactions["back"]:
                        page -= 1
                        if page < 1:
                            page = 1
                    elif response == reactions["delete"]:
                        await embed_msg.delete(delay=3)

                        return

                    await embed_msg.edit(embed=embed_update(page=page))

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
            
    # ? QUEUE
    @commands.group(name="queue", aliases=['q'])

    async def Queue(self, ctx):
        '''Shows the current queue.'''
        state = TempState(ctx.author.guild)
        if ctx.invoked_subcommand is None:
            i = 0
            j = 1
            desc = ""
            while i < len(state.queue):
                if isinstance(state.queue[i], str):
                    desc += f"***{state.queue[i]}*** \n"
                    i += 1      
                else:
                    desc += f"{j}. {state.queue[i].title} ({state.queue[i].duration}) \n"
                    i += 1
                    j += 1
                    

            desc_l = []
            for chunk in list(self.chunks(desc.split("\n"), n=5)):
                desc_l.append("\n".join(chunk))

            embed = discord.Embed(title="QUEUE",
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            embed_msg = await ctx.send(embed=embed)

            await self.embed_pages(_content=desc_l, ctx=ctx, embed_msg=embed_msg, wait_time=120)

    # ? QUEUE REPLACE
    @Queue.command(aliases = ['move'])
    @vc_check()
    async def replace(self, ctx, change1, change2):
        '''Replaces two queue members.'''
        state = TempState(ctx.author.guild)
        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.queue if type(x) != str]
        if change1 > 1 and change2 > 1 and change1 <= len(queue) and change2 <= len(queue):
            squeue = state.queue
            squeue[squeue.index(queue[change1-1])], squeue[squeue.index(queue[change2-1])] = squeue[squeue.index(queue[change2-1])], squeue[squeue.index(queue[change1-1])]
            state.queue = squeue
            await ctx.send(f">>> Switched the places of **{queue[change2-1].title}** and **{queue[change1-1].title}**")
            
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? QUEUE REMOVE
    @Queue.command()
    @vc_check()
    async def remove(self, ctx, remove):
        '''Removes the Queue member.'''
        state = TempState(ctx.author.guild)
        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.queue if type(x) != str]
        if remove > 1 and remove <= len(queue):
            queue2 = state.queue
            queue2.remove(queue[remove-1])
            state.queue = queue2
            await ctx.send(f">>> Removed **{(queue[remove - 1].title)}** from the queue.")
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? QUEUE NOW
    @Queue.command()
    @vc_check()
    async def now(self, ctx, change):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)
        try:
            change = int(change)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = [x for x in state.queue if type(x) != str]
        if change > 1 and change <= len(queue):
            temp = queue[change-1]
            queue2 = state.queue
            queue2.remove(temp)
            queue2.remove(queue[0])
            queue2.insert(0, temp)
            state.queue = queue2
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("restart"))

    # ?CONTRACTED
    @commands.group(aliases=['ct'])
    async def contracted(self, ctx):

        state = TempState(ctx.author.guild)
        if ctx.invoked_subcommand is None:
            i = 0
            desc = ""
            while i < len(state.queue_ct):
                desc += f"{i+1}. {state.queue_ct[i].title} ({state.queue_ct[i].duration}) \n"
                i += 1    

            desc_l = []
            for chunk in list(self.chunks(desc.split("\n"), n=5)):
                desc_l.append("\n".join(chunk))

            embed = discord.Embed(title="QUEUE",
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            embed_msg = await ctx.send(embed=embed)

            await self.embed_pages(_content=desc_l, ctx=ctx, embed_msg=embed_msg, wait_time=120)


    # ? CONTRACTED REMOVE
    @contracted.command(name = "remove")
    async def ct_remove(self, ctx, remove):
        '''Removes the Queue member.'''
        
        state = TempState(ctx.author.guild)
        try:
            remove = int(remove)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.queue_ct
        squeue = state.queue
        if remove > 0 and remove <= len(queue):
            temp = queue[remove-1]
            queue.remove(temp)
            
            if type(temp).__name__ == "YoutubeVideo":
                if remove == 1:
                    await ctx.send("The number you entered is just as irrelevant as your existence.")
                    return
                squeue.remove(temp)
                await ctx.send(f">>> Removed **{(temp.title)}** from the queue.")
            else:
                if remove == 1:
                    for i in squeue:
                        if i == f"--{temp.title}--":
                            vid = [x for x in state.queue if type(x)!=str][0]
                            squeue = [vid] + squeue
                            queue = [vid] + queue
                            break
                        elif type(i).__name__ == "YoutubeVideo" or type(i).__name__ == "YoutubePlaylist": 
                            break 
                i1 = squeue.index(f"--{temp.title}--")
                i2 = squeue[i1+1:].index(f"--{temp.title}--")
                squeue[i1:i1+i2+2] = []

                state.queue=squeue
                state.queue_ct = queue
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return

    # ? CONTRACTED REPLACE
    @contracted.command(name = "replace")
    @vc_check()
    async def ct_replace(self, ctx, change1, change2):
        '''Replaces two queue members.'''

        state = TempState(ctx.author.guild)
        try:
            change1, change2 = int(change1), int(change2)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.queue_ct
        if change1 > 0 and change2 > 0 and change1 <= len(queue) and change2 <= len(queue):
            squeue = state.queue
            if change1 == 1:
                if type(queue[change1-1]).__name__ == "YoutubeVideo":
                    await ctx.send("The numbers you entered are just as irrelevant as your existence.")
                    return
                else:
                    for i in squeue:
                        if i == f"--{queue[change1-1].title}--":
                            vid = [x for x in state.queue if type(x)!=str][0]
                            squeue.remove(vid)
                            squeue =  [vid] + squeue
                            queue = [vid] + queue
                            change1 += 1
                            change2 += 1
                            break
                        elif type(i).__name__ == "YoutubeVideo" or type(i).__name__ == "YoutubePlaylist": 
                            break

            if change2 == 1:
                if type(queue[change2-1]).__name__ == "YoutubeVideo":
                    await ctx.send("The numbers you entered are just as irrelevant as your existence.")
                    return
                else:
                    for i in squeue:
                        if i == f"--{queue[change1-1].title}--":
                            vid = [x for x in state.queue if type(x)!=str][0]
                            squeue.remove(vid)
                            squeue =  [vid] + squeue
                            queue = [vid] + queue
                            change1 += 1
                            change1 += 1
                            break
                        elif type(i).__name__ == "YoutubeVideo" or type(i).__name__ == "YoutubePlaylist": 
                            break

            temp1 = queue[change2-1]
            temp2 = queue[change1-1]

            queue[change1-1], queue[change2-1] = queue[change2-1], queue[change1-1] 

            if type(temp1).__name__ == "YoutubeVideo":
                i11 = squeue.index(temp1)
                i12 = -1
            else:
                i11 = squeue.index(f"--{temp1.title}--")
                i12 = squeue[i11+1:].index(f"--{temp1.title}--")

            if type(temp2).__name__ == "YoutubeVideo":
                i21 = squeue.index(temp2)
                i22 = -1
            else:
                i21 = squeue.index(f"--{temp2.title}--")
                i22 = squeue[i21+1:].index(f"--{temp2.title}--")

            squeue[i11:i12+i11+2], squeue[i21:i22+i21+2] = squeue[i21:i22+i21+2], squeue[i11:i12+i11+2]
            state.queue = squeue
            state.queue_ct = queue
            await ctx.send(f">>> Switched the places of **{temp1.title}** and **{temp2.title}**")
        else:
            await ctx.send("The numbers you entered are just as irrelevant as your existence.")
            return

    # ? CONTRACTED NOW

    @contracted.command(name = "now")
    @vc_check()
    async def ct_now(self, ctx, change):
        '''Plays a queue member NOW.'''
        state = TempState(ctx.author.guild)
        try:
            change = int(change)
        except: 
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.queue_ct
        squeue = state.queue
        if change > 1 and change <= len(queue):
            temp1 = queue[change-1]
            temp2 = queue[0]
            
            queue.pop(change-1)
            queue.insert(0,temp1)

            squeue.remove([x for x in squeue if type(x) != str][0])

            if type(temp1).__name__ == "YoutubeVideo":
                squeue.remove(temp1)
                squeue.insert(0,temp1)
            else:
                i11 = squeue.index(f"--{temp1.title}--")
                i12 = squeue[i11+1:].index(f"--{temp1.title}--")
                pl = squeue[i11:i12+i11+2]
                squeue[i11:i12+i11+2] = []
                squeue = pl  + squeue


            if type(temp2).__name__ == "YoutubeVideo":
                queue.remove(temp2)

            state.queue = squeue
            state.queue_ct = queue
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("restart"))


    # ? FULL
    @commands.group(aliases=['history'])
    async def full(self, ctx):

        state = TempState(ctx.author.guild)
        if ctx.invoked_subcommand is None:
            i = 0
            desc = ""
            while i < len(state.full_queue):
                desc += f"{i+1}. {state.full_queue[i].title} ({state.full_queue[i].duration}) \n"
                i += 1    

            desc_l = []
            for chunk in list(self.chunks(desc.split("\n"), n=5)):
                desc_l.append("\n".join(chunk))

            embed = discord.Embed(title="QUEUE",
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            embed_msg = await ctx.send(embed=embed)

            await self.embed_pages(_content=desc_l, ctx=ctx, embed_msg=embed_msg, wait_time=120)

    
    # ? FULL NOW

    @full.command(name = "now")
    @vc_check()
    async def f_now(self, ctx, start_index, last_index = None):
        '''Plays a sub queue Now. if not last_index then only 1 song played'''
        state = TempState(ctx.author.guild)
        if not last_index:
            last_index = start_index
        try:
            start_index, last_index = int(start_index), int(last_index)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.full_queue
        if start_index > 0 and last_index > 0 and start_index <= len(queue) and last_index <= len(queue) and last_index >= start_index:
            temp = queue[start_index-1:last_index]
            queue = state.queue
            queue_ct = state.queue_ct
            if type(queue_ct[0]).__name__ == "YoutubeVideo":
                queue_ct.pop(0) 
            queue.remove([x for x in queue if type(x) != str][0])
            queue = temp + queue
            queue_ct = temp +queue_ct
            state.queue = queue
            state.queue_ct = queue_ct
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("restart"))


    # ? FULL ADD

    @full.command(name = "add")
    @vc_check()
    async def f_add(self, ctx, start_index, last_index = None):
        '''adds a sub queue of fullqueue to the end of the queue. if not last_index then only 1 song added'''
        state = TempState(ctx.author.guild)
        if not last_index:
            last_index = start_index
        try:
            start_index, last_index = int(start_index), int(last_index)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.full_queue
        if start_index > 0 and last_index > 0 and start_index <= len(queue) and last_index <= len(queue) and last_index >= start_index:
            temp = queue[start_index-1:last_index]
            queue = state.queue
            queue_ct = state.queue_ct
            queue += temp
            queue_ct += temp
            state.queue = queue
            state.queue_ct = queue_ct

        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
            

    # ? FULL CONTRACTED
    @commands.group(aliases=['history-ct'])
    async def fullct(self, ctx):

        state = TempState(ctx.author.guild)
        if ctx.invoked_subcommand is None:
            i = 0
            desc = ""
            while i < len(state.full_queue_ct):
                desc += f"{i+1}. {state.full_queue_ct[i].title} ({state.full_queue_ct[i].duration}) \n"
                i += 1    

            desc_l = []
            for chunk in list(self.chunks(desc.split("\n"), n=5)):
                desc_l.append("\n".join(chunk))

            embed = discord.Embed(title="QUEUE",
                                  color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                             icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            embed.set_footer(text=f"Requested By: {ctx.message.author.display_name}",
                             icon_url=ctx.message.author.avatar_url)

            embed_msg = await ctx.send(embed=embed)

            await self.embed_pages(_content=desc_l, ctx=ctx, embed_msg=embed_msg, wait_time=120)

    
    # ? FULL CT NOW

    @fullct.command(name = "now")
    @vc_check()
    async def f_ct_now(self, ctx, start_index, last_index = None):
        '''Plays a sub queue Now. if not last_index then only 1 song played'''
        state = TempState(ctx.author.guild)
        if not last_index:
            last_index = start_index
        try:
            start_index, last_index = int(start_index), int(last_index)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.full_queue
        if start_index > 0 and last_index > 0 and start_index <= len(queue) and last_index <= len(queue) and last_index >= start_index:
            temp = queue[start_index-1:last_index]
            queue = state.queue
            queue_ct = state.queue_ct
            if type(queue_ct[0]).__name__ == "YoutubeVideo":
                queue_ct.pop(0) 
            queue.remove([x for x in queue if type(x) != str][0])
            queue_ct = temp +queue_ct
            
            for i in temp[::-1]:
                if type(i).__name__ == "YoutubePlaylist":
                  
                    queue = [f"--{i.title}--"] + i._entries + [f"--{i.title}--"] + queue
                else:
                    queue = [i] + queue


            state.queue = queue
            state.queue_ct = queue_ct
        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
        await ctx.invoke(self.client.get_command("restart"))


    # ? FULL CT ADD

    @fullct.command(name = "add")
    @vc_check()
    async def f_ct_add(self, ctx, start_index, last_index = None):
        '''adds a sub queue of fullqueue to the end of the queue. if not last_index then only 1 song added'''
        state = TempState(ctx.author.guild)
        if not last_index:
            last_index = start_index
        try:
            start_index, last_index = int(start_index), int(last_index)
        except:
            await ctx.send("NUMBERS GODDAMN NUMBERS")
            return
        queue = state.full_queue
        if start_index > 0 and last_index > 0 and start_index <= len(queue) and last_index <= len(queue) and last_index >= start_index:
            temp = queue[start_index-1:last_index]
            queue = state.queue
            queue_ct = state.queue_ct
            queue_ct += temp

            for i in temp:
                if type(i).__name__ == "YoutubePlaylist":
                    queue += [f"--{i.title}--"] + i._entries + [f"--{i.title}--"]
                else:
                    queue += [i]

            state.queue = queue
            state.queue_ct = queue_ct

        else:
            await ctx.send("The number you entered is just as irrelevant as your existence.")
            return
            



def setup(client):
    client.add_cog(Queue(client))
