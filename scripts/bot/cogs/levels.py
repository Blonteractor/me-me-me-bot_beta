import discord
from random import randint
from discord.ext import commands, tasks
import requests
import io
import asyncio
from threading import Thread
from colorama import Fore, Back, Style, init
from PIL import Image, ImageDraw, ImageOps, ImageFont
import imp
import os

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))
from state import State, CustomContext, GuildState

class levels(commands.Cog):
    ''':up: Level up by sending messages, earn new ranks and powers by doing so.'''

    cooldown = 0
    # roles = {"Prostitute": [0, [230, 126, 34]], "Rookie": [5, [153, 45, 34]], "Adventurer": [10, [173, 20, 87]], "Player": [
    #     25, [241, 196, 15]], "Hero": [50, [46, 204, 113]], "Council of Numericons": [85, [0, 255, 240]]}

    def __init__(self, client):
        self.client = client
        self.client: commands.Bot

        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]

        self.cooldown += gen.extra_cooldown

        self.give_exp.start()

    def log(self, msg):  # ! funciton for logging if developer mode is on
        cog_name = os.path.basename(__file__)[:-3]
        debug_info = gen.db_receive("var")["cogs"]
        try:
            debug_info[cog_name]
        except:
            debug_info[cog_name] = 0
        if debug_info[cog_name] == 1:
            return gen.error_message(msg, gen.cog_colours[cog_name])

    def cog_unload(self):
        self.give_exp.cancel()

    def gen_xp(self):
        return randint(15, 25)

    @tasks.loop(seconds=10)
    async def give_exp(self):
        for guild in self.client.guilds:
            if GuildState(guild).exp_counting:
                for member in guild.members:
                    state = State(member).Member 
                    if state.active:
                        prev_des = state.role
                        state.xp += self.gen_xp() 
                        state.active = False
                        new_des = state.role
                        
                        if not new_des == prev_des:
                            await member.remove_roles(prev_des)
                            await member.add_roles(new_des)
                    

    def rank_creation(self, ctx, member, roles):

        state = State(member).Member
        level = state.level
        rank = state.rank
        response = requests.get(member.avatar_url)
        avatar_photo = Image.open(io.BytesIO(response.content))

        size = (600, 600)
        avatar_photo = avatar_photo.resize(size)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)

        avatar_photo = ImageOps.fit(
            avatar_photo, mask.size, centering=(0.5, 0.5))
        avatar_photo.putalpha(mask)

        percent = state.rel_xp / state.rel_bar
        arc_length = percent*(360)
        if arc_length > 360:
            arc_length = 360
        arc_start = -90
        arc_end = arc_length-90

        a = list(roles.keys())
       

        for i in range(0,len(a)):
            if level < roles[a[i]][0]:
                if i == 0:                                                                  #! hardcoded
                    role = "Undefined"
                    role_cap, role_colour =(0,[255,255,255])
                    role_colour = role_colour[:]
                    role_next, role_next_colour = roles[a[0]]
                else:
                    role = a[i-1]
                    role_cap, role_colour = roles[a[i-1]]
                    role_colour = role_colour[:]
                    role_next, role_next_colour = roles[a[i]]

                break    

            
        role_percent = (level - role_cap)/(role_next - role_cap)

        for i in range(3):
        
            colour_diff = int(
                (role_next_colour[i] - role_colour[i])*role_percent)
            role_colour[i] += colour_diff
        role_colour = tuple(role_colour)

        bg = Image.new("RGB", (1000, 1000), color=role_colour)
        fg = Image.new("RGB", (1000, 980), color=(0, 0, 0))
        bg.paste(fg, (0, 0))
        bg.paste(avatar_photo, (200, 100), avatar_photo)

        draw = ImageDraw.Draw(bg)
        draw.arc([(190, 90), (810, 710)], start=arc_start,
                 end=arc_end, fill=role_colour, width=10)

        name = member.name
        if len(name) > 15:
            name = name[:11]+'...'
        discrim = member.discriminator
        nanotech = ImageFont.truetype('./Fonts/NanoTech Regular.otf', 100)
        roboto_cond = ImageFont.truetype('./Fonts/RobotoCondensed-Light.ttf', 60)
        d = nanotech.getsize(name)[0]

        draw.text((50, 750), name, font=nanotech)
        draw.text((70+d, 750), f"#{discrim}", font=roboto_cond)

        roboto_black = ImageFont.truetype('Roboto-Black.ttf', 110)

        d = roboto_cond.getsize("LEVEL")[0]
        draw.text((600, 850), "LEVEL", font=roboto_cond, fill=role_colour)
        draw.text((620+d, 810), str(level),
                  font=roboto_black, fill=role_colour)

        d = roboto_cond.getsize("RANK")[0]
        draw.text((50, 50), "RANK", font=roboto_cond)
        draw.text((70+d, 10), str(rank), font=roboto_black)

        if len(role) > 13:
            role = role.split()
            nrole = []
            for i in role:
                nrole += [i[0]]
            if len(nrole)<=6:
                role = " ".join(nrole)
            else:
                role = "".join(nrole)
            
        if len(role) > 13:
            role = role[:13]


        x = 10
        for i in role.upper():
            draw.text((950, x), i, font=roboto_cond, fill=role_colour)
            x += roboto_cond.getsize(i)[0]+40

        bg.save(f"{member.guild.id + member.id}.png")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            state = State(message.author)
            state.Member.messages += 1
            state.Member.active = True

    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def rank(self, ctx, member=''):
        '''Shows your level and rank, all epic style.'''
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        if not ctx.States.Guild.exp_counting:
            await ctx.send(f">>> Counting exp is disabled in this server, setUp the ranks using `{ctx.prefix}setup roles` to enable.")
            return

        try:
            int(member)

        except:
            try:

                member1 = member
                member2 = ''
                for i in member1:
                    if i.isnumeric():
                        member2 += i

                member1 = int(member2)

                member1 = ctx.channel.guild.get_member(member1)
            except:

                member1 = ctx.channel.guild.get_member_named(member)
                if not member1:

                    member = ctx.author
                else:

                    member = member1
            else:
                member = member1
        else:
            member1 = ctx.channel.guild.get_member(int(member))
            if not member1:
                member = ctx.author
            else:
                member = member1
        if member.bot:
            return
        
    
        levels = [level for level,role in list(ctx.States.Guild.ranks.items())]
        levels.sort()
        roles = {}
       
        for ulevel in levels:
            for level, role in list(ctx.States.Guild.ranks.items()):
                
                if level == ulevel:
                    roles[role.name] =  [int(level), list(role.color.to_rgb())]
                    break
                    
    
        thrd = Thread(target=self.rank_creation, args=(ctx, member, roles))
        thrd.start()
        thrd.join()
        filename = f"{member.guild.id + member.id}.png"
        await ctx.send(file=discord.File(filename))
        
        os.remove(filename)
        
    @commands.group()
    async def exp(self, ctx):
        """Change the member's exp count, only for my admins"""
        
        await ctx.send(f"_ _")
    
    @exp.command()
    @commands.has_role(gen.admin_role_id)
    async def add(self, ctx: commands.Context, ammount: int, member: discord.Member):
        """Give exp to a member"""
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        ctx.State.Member.xp += ammount
        
        await ctx.send(f">>> `{ammount}`xp given to {member.mention}")
    
    @exp.command()
    @commands.has_role(gen.admin_role_id)
    async def sub(self, ctx: commands.Context, ammount: int, member: discord.Member):
        """Take exp from a member"""
        
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        ctx.State.Member.xp += ammount
        
        await ctx.send(f">>> `{ammount}`xp taken from {member.mention}")

def setup(client):
    client.add_cog(levels(client))
