import discord
from random import randint
import random
from discord.ext import commands, tasks
import requests
import io
import asyncio
from threading import Thread
from colorama import Fore, Back, Style, init
from PIL import Image, ImageDraw, ImageOps, ImageFont
import imp
import os
from colorthief import ColorThief

imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))
from state import State, CustomContext, GuildState

class Levels(commands.Cog):
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

    def cog_unload(self):
        self.give_exp.cancel()

    def gen_xp(self):
        return randint(15, 25)

    @tasks.loop(seconds=10)
    async def give_exp(self):
        for guild in self.client.guilds:
            if GuildState(guild).exp_counting:
                for member in guild.members:
                    if member.bot:
                        continue
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
        
        luminance = lambda r,g,b: (0.2126)*r + (0.7152)*g + (0.0722)*b
        
        BLACK_LUMINANCE_THRESHOLD = 40
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)

        state = State(member).Member
        blend = State(member).User.card_blend
        level = state.level
        rank = state.rank
        response = requests.get(member.avatar_url)
        content = response.content
        avatar_photo = Image.open(io.BytesIO(content))
        
        ct = ColorThief(io.BytesIO(content))

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
       
        role = None
        role_cap = None
        role_colour = None
        role_next = None
        role_next_colour = None
               
        for i in range(len(a)):
            
            if level < roles[a[i]][0]:
                if i == 0:                                                                  #! hardcoded
                    role = "Undefined"
                    role_cap, role_colour =(0, list(ct.get_color(quality=1)))
                    role_colour = role_colour[:]
                    role_next, role_next_colour = roles[a[0]]
                else:
                    role = a[i-1]
                    role_cap, role_colour = roles[role]
                    role_next, role_next_colour = roles[a[i]]
                    role_colour = role_colour[:]

                break
            
            elif level >= roles[a[-1]][0]:
                role = a[-1]
                role_cap, role_colour = roles[role]
                role_next, role_next_colour = role_cap, role_colour    
                
        if blend:
            dominant_colour = list(ct.get_color(quality=1))
            role_next_colour = role_colour = dominant_colour

            
        role_percent_1 = (level - role_cap)
        role_percent_2 = (role_next - role_cap)
        
        try:
            role_percent = role_percent_1 / role_percent_2
        except ZeroDivisionError:
            role_percent = 0

        for i in range(3):
        
            colour_diff = int(
                (role_next_colour[i] - role_colour[i])*role_percent)
            role_colour[i] += colour_diff
        role_colour = tuple(role_colour)

        bg = Image.new("RGB", (1000, 1000), color=role_colour)
        
        
        fg_colour = BLACK if luminance(*role_colour) >= BLACK_LUMINANCE_THRESHOLD else WHITE

        fg_colour = BLACK
        
        fg = Image.new("RGB", (1000, 980), color=fg_colour)
        
        MPATH = os.path.abspath(os.path.join(
                                os.path.dirname(__file__), "../../../assets/masks"))
        MDIR = os.listdir(MPATH)
        
        filename = random.choice(MDIR)
        mask = Image.open(os.path.join(MPATH, "mask1.png")).convert('L').resize((950,980))

        egg = Image.new("RGB", mask.size, color=(138,3,3))
        
        
        fg = Image.composite(egg,fg,mask)
        
        bg.paste(fg, (0, 0))
        # bg.paste(avatar_photo, (200, 100), avatar_photo)

        draw = ImageDraw.Draw(bg)
        # draw.arc([(190, 90), (810, 710)], start=arc_start,
        #          end=arc_end, fill=role_colour, width=10)

        name = member.name
        if len(name) > 15:
            name = name[:11]+'...'
        discrim = member.discriminator
        nanotech = ImageFont.truetype('./Fonts/NanoTech Regular.otf', 100)
        roboto_cond = ImageFont.truetype('./Fonts/RobotoCondensed-Light.ttf', 60)
        d = nanotech.getsize(name)[0]

        if fg_colour == BLACK:
            draw.text((50, 750), name, font=nanotech)
            draw.text((70+d, 750), f"#{discrim}", font=roboto_cond)

        elif fg_colour == WHITE:
            draw.text((50, 750), name, font=nanotech, fill=BLACK)
            draw.text((70+d, 750), f"#{discrim}", font=roboto_cond, fill=BLACK)

        roboto_black = ImageFont.truetype('./Fonts/Roboto-Black.ttf', 110)

        # d = roboto_cond.getsize("LEVEL")[0]
        # draw.text((600, 850), "LEVEL", font=roboto_cond, fill=role_colour)
        # draw.text((620+d, 810), str(level),
        #           font=roboto_black, fill=role_colour)

        d = roboto_cond.getsize("RANK")[0]
        
        if fg_colour == BLACK:
            draw.text((50, 50), "RANK", font=roboto_cond)
            draw.text((70+d, 10), str(rank), font=roboto_black)
        elif fg_colour == WHITE:
            draw.text((50, 50), "RANK", font=roboto_cond, fill=BLACK)
            draw.text((70+d, 10), str(rank), font=roboto_black, fill=BLACK)

        # if len(role) > 13:
        #     role = role.split()
        #     nrole = []
        #     for i in role:
        #         nrole += [i[0]]
        #     if len(nrole)<=6:
        #         role = " ".join(nrole)
        #     else:
        #         role = "".join(nrole)
            
        # if len(role) > 13:
        #     role = role[:13]


        # x = 10
        # for i in role.upper():
        #     draw.text((950, x), i, font=roboto_cond, fill=role_colour)
        #     x += roboto_cond.getsize(i)[0]+40

        bg.save(f"{member.guild.id + member.id}.png")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            state = State(message.author)
            state.Member.messages += 1
            if state.Guild.ranks:
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
        
    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def blend(self, ctx, response = None):
        """Turning this on will make your rank card accent color blend with the most doiminant color in your profile pic, so you can show off your anime pfp more you weeb."""
        ctx = await self.client.get_context(ctx.message, cls=CustomContext)
        
        yes = ["yes", "enable", "sure", "y","true","on"]
        no = ["nop", "disable", "no", "n","false","off"]
        
        state = ctx.States.User
        
        if not response:
            if state.card_blend:
                response = "nop"
            else:
                response = "yes"
        else:
            response = response.lower()

        if response in yes:
            state.card_blend = True
            await ctx.send("Your rank card color will now blend with your profile pic.")
            return
        
        elif response in no:
            state.card_blend = False
            await ctx.send("Your rank card color will now not blend with your profile pic.")
            return
        
        else:
            await ctx.send("Invalid response, reply on/off yes/no true/false.")
            return

def setup(client):
    client.add_cog(Levels(client))
