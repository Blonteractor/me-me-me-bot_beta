import discord
from discord.ext import commands,tasks
from discord.ext.commands.core import Command, cooldown
from discord.utils import get
import re
import asyncio
import imp,os

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))
from state import GuildState,TempState,CustomContext


class Playlist(commands.Cog):
    
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
    
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

    @commands.group(aliases=["pl"])
    async def playlist(self, ctx):
        if ctx.invoked_subcommand is None:
            pl_db = ctx.States.User.playlist
            
            embed = discord.Embed(title="",
                                color=discord.Colour.dark_purple())
            embed.set_author(name="Me!Me!Me!",
                                icon_url=self.client.user.avatar_url)
            embed.set_thumbnail(url=self.music_logo)
            
            for no, playlist in enumerate(pl_db.keys()):
                embed.add_field(name=f"**{no + 1}.**", value=f"**{playlist}** \t\t `{len(pl_db[playlist])}`", inline=False)
            
            await ctx.send(embed=embed)
            
    @playlist.command(aliases=["make"])
    async def new(self, ctx, name):
        playlist_db = ctx.States.User.playlist
        
        if name in playlist_db.keys():
            await ctx.send("Playlists can't have the same name, I know creativity is lacking but think of a different name.")
            return
            
        playlist_db = {**playlist_db, **{name: []}}
        ctx.States.User.playlist = playlist_db
        
        await ctx.send(f"A playlist with the name `{name}` was created, use the `playlist add` command to add songs.")
        

    @playlist.command(aliases=["v"])
    async def view(self, ctx, name=None):
        '''Shows your Playlist. Subcommands can alter your playlist'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist
        try:
            if name:
                if name in playlist_db:
                    playlist = playlist_db[name]
                    pname = name
                elif name.isnumeric():
                    if int(name) > 0 and int(name) <= len(playlist_db):
                        playlist = list(playlist_db.values())[
                            int(name)-1]
                        pname = list(playlist_db.keys())[
                            int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return
                else:
                    playlist = list(
                        playlist_db.values())[0]
                    pname = list(playlist_db.keys())[0]
            else:
                playlist = list(
                    playlist_db.values())[0]
                pname = list(playlist_db.keys())[0]
        except Exception as e:
            self.log(e)
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            playlist = []
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"
            ctx.States.User.playlist = playlist_db

        embed = discord.Embed(title=pname,
                                color=discord.Colour.dark_purple())
        embed.set_author(name="Me!Me!Me!",
                            icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=self.music_logo)
        no = 1
        for song in playlist:
            title = song["title"]
            url = "https://www.youtube.com/watch?v={id}".format(id = song["id"])
            embed.add_field(name=f"**{no}**", value=f"**[{title}]({url})**")
            no += 1
        await ctx.send(embed=embed)

    # ? PLAYLIST ADD
    @playlist.command()
    async def add(self, ctx, name, *, query):
        '''Adds a song to your Playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        if "http" in query:
            if "www.youtube.com" in query:
                split_list = re.split("/|=|&", query)
                if "watch?v" in split_list:
                    vid = self.client.get_cog("Play").ytvid(split_list[split_list.index(
                        "watch?v")+1], requested_by=ctx.author.name)
        else:
            vid = await self.client.get_cog("Play").searching(ctx, query)

        if vid:

            playlist_db = ctx.States.User.playlist
            try:

                if name in playlist_db:
                    pname = name
                elif name.isnumeric():
                    if int(name) > 0 and int(name) <= len(playlist_db):
                        pname = list(playlist_db.keys())[
                            int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return
                else:
                    await ctx.send("Could not find the playlist.")
                    return
            except:
                playlist_db = {
                    f"{ctx.author.name}Playlist": []}
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}Playlist"

            playlist_db[pname] += [{"id": vid.id, "title": vid.title}]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {pname}")
            
            ctx.States.User.playlist = playlist_db

    # ? PLAYLIST ADD_PLAYLIST
    @playlist.command(name="add-playlist", aliases=["addpl"])
    async def add_playlist(self, ctx, name, *, query):
        '''Adds a playlist to your Playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        vid = await self.client.get_cog("Play").searching(ctx, query, False)

        if vid:

            playlist_db = ctx.States.User.playlist
            try:

                if name in playlist_db:
                    pname = name
                elif name.isnumeric():
                    if int(name) > 0 and int(name) <= len(playlist_db):
                        pname = list(playlist_db.keys())[
                            int(name)-1]
                    else:
                        await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                        return

                else:
                    await ctx.send("Could not find the playlist.")
                    return
            except:
                playlist_db = {
                    f"{ctx.author.name}Playlist": []}
                await ctx.send("Your playlist has been created.")
                pname = f"{ctx.author.name}Playlist"

            playlist_db[str(ctx.author.id)
                        ][pname] += [{"id": vid.id, "title": vid.title}]

            await ctx.send(f"**{vid.title}** added to your Playlist")

            self.log(f"altered {pname}")
            ctx.States.User.playlist = playlist_db

    # ? PLAYLIST REARRANGE
    @playlist.command(aliases=["rng"])
    async def rearrange(self, ctx, name, P1: int, P2: int):
        '''Rearranges 2 songs/playlist places of your playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist

        try:

            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            pass 
        else:
            await ctx.send("Your playlist too smol for rearrangement.")
            return

        if P1 < 1 or P1 > len(playlist_db[pname]) or P2 < 1 or P2 > len(playlist_db[pname]):
            return

        playlist_db[pname][P1-1], playlist_db[pname][P2 - 1] = playlist_db[pname][P2-1], playlist_db[pname][P1-1]
                                                                                                
        await ctx.send(f"Number {P1} and {P2} have been rearranged.")
        self.log(f"altered {pname}")

        ctx.States.User.playlist = playlist_db

    # ? PLAYLIST REMOVE
    @commands.command(name="plremove") #! experimentation
    async def plremove(self, ctx, name, R: int):
        '''Removes a song/playlist from your playlist.'''
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist

        try:

            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:
            if len(playlist_db[pname]) < 1:
                await ctx.send("Your playlist too smol for alteration.")
                return

            if R < 1 or R > len(playlist_db[pname]):
                return

            playlist_db[pname].pop(R-1)
            await ctx.send(f"Number {R} has been removed.")
            self.log(f"altered {pname}")

        ctx.States.User.playlist = playlist_db

    # ? PLAYLIST NAME
    @playlist.command()
    async def name(self, ctx, name, new_name):
        """Give a name to your playlist"""
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        playlist_db = ctx.States.User.playlist
        try:
            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:

            playlist_db[new_name] = playlist_db.pop(pname)
            
            ctx.States.User.playlist = playlist_db

    # ? PLAYLIST PLAY
    @playlist.command()
    async def plplay(self, ctx, name):
        '''Plays your playlist.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        playlist_db = ctx.States.User.playlist
        state = ctx.States.Temp

        try:
            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:   
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:
            if len(playlist_db[pname]) < 1:
                await ctx.send("Your playlist doesn't have any songs to play")
                return

            else:
                if not (await ctx.invoke(self.client.get_command("join"))):
                    return

                voice = get(self.client.voice_clients, guild=ctx.guild)
                playlist = playlist_db[pname]
                for i in range(len(playlist)):
                    if len(playlist[i]["id"]) > 11:
                        playlist[i] = self.client.get_cog("Play").ytpl(playlist[i]["id"])

                    else:
                        playlist[i] = self.client.get_cog("Play").ytvid(playlist[i]["id"])

                state.queue += [f"----{pname}----"] 

                temp = []
                for i in playlist:
                    state.queue_ct += [i]

                    if type(i).__name__ == "YoutubeVideo":
                        old_queue = [x for x in state.queue if type(x) != str]
                        state.queue += [i]

                        if len(old_queue) == 0:
                            await self.client.get_cog("Play").player(ctx, voice)
                        else:
                            self.log("Song added to queue")

                    else:
                        state.queue += [f"--{i.title}--"]
                        for j in range(len(i.entries)):

                            _vid = self.client.get_cog("Play").ytvid(i.entries[j][0])

                            temp += [_vid]

                        old_queue = [x for x in state.queue if type(x) != str]
                        state.queue += temp
                        i._info["entries"] = temp
                        if len(old_queue) == 0:
                            await self.client.get_cog("Play").player(ctx, voice)
                        else:
                            self.log("Song added to queue")

                        state.queue += [f"--{i.title}--"]

                state.queue += [f"----{pname}----"]

                await ctx.send("Your Playlist has been added to the Queue.")
                
    # ? PLAYLIST EXPAND
    @playlist.command(name="expand")
    async def expandd(self, ctx, name):
        playlist_db = ctx.States.User.playlist
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)

        try:
            if name in playlist_db:
                pname = name
            elif name.isnumeric():
                if int(name) > 0 and int(name) <= len(playlist_db):
                    pname = list(playlist_db.keys())[
                        int(name)-1]
                else:
                    await ctx.send("Your playlist number should be between 1 and the amount of playlist you have.")
                    return

            else:
                await ctx.send("Could not find the playlist.")
                return
        except:
            playlist_db = {
                f"{ctx.author.name}Playlist": []}
            await ctx.send("Your playlist has been created.")
            pname = f"{ctx.author.name}Playlist"

        else:
            playlist = playlist_db[pname]
            npl = []
            for i in range(len(playlist)):
                if len(playlist[i]["id"]) > 11:
                    entries = self.client.get_cog("Play").ytpl(playlist[i]["id"]).entries
                    for vid in entries:
                        npl += [{"id": vid[0], "title":vid[2]}]
                else:
                    npl += [playlist[i]]
            playlist_db[pname] = npl
            
            ctx.States.User.playlist = playlist_db

def setup(client):
    client.add_cog(Playlist(client))
