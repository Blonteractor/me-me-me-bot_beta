import discord
from random import randint
from discord.ext import commands, tasks
import requests
import io
import asyncio
from threading import Thread
from colorama import Fore, Back, Style, init
from PIL import Image,ImageDraw,ImageOps,ImageFont
import imp,os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

import general as gen

class levels(commands.Cog):
    ''':up: Level up by sending messages, earn new ranks and powers by doing so.'''
    
    cooldown = 0
    roles = {"Prostitute":[0,[230, 126, 34]],"Rookie":[5,[153, 45, 34]],"Adventurer":[10,[173, 20, 87]],"Player":[25,[241, 196, 15]],"Hero":[50,[46, 204, 113]],"Council of Numericons":[85,[0, 255, 240]]}
    
    def __init__(self, client):
        self.client = client
        self.exp_info = gen.db_receive('exp')
        
        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.quailifed_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
        
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

    def get_level(self, exp):
        info = {}

        lvl_found = False
        i = 0
        total_xp_needed_now = 0
        while not lvl_found:
            total_xp_needed_now += ((5 * (i ** 2)) + (50 * i) + 100)
            if exp < total_xp_needed_now:
                lvl_found = True
            else:
                i += 1

        rel_bar = (5 * (i ** 2) + 50 * i + 100)
        rel_exp = exp  - self.total_exp_needed(i)    

        info["level"] = i
        info["rel_xp"] = rel_exp
        info["rel_bar"] = rel_bar

        return info


    def total_exp_needed(self, lvl):
        total_xp_needed = 0
        for i in range(lvl):
            total_xp_needed += ((5 * (i ** 2)) + (50 * i) + 100)

        return total_xp_needed

    @tasks.loop(minutes =1)
    async def give_exp(self):
        self.log("\nRegular Check")
        for member in self.exp_info:
            if self.exp_info[member]["active"]:
                self.log(f"{self.exp_info[member]['name']}  is active.")
                self.exp_info[member]["xp"] += self.gen_xp()
                self.exp_info[member]["active"] = False
                level_dicc=self.get_level(self.exp_info[member]["xp"])
              
                self.exp_info[member]["rel_xp"] =level_dicc["rel_xp"]

                if level_dicc["level"] > self.exp_info[member]["level"]:
                    self.exp_info[member]["level"] =level_dicc["level"]
                    
                    self.log(f"{self.exp_info[member]['name']} leveled up to level {self.exp_info[member]['level']}")
                    channel = self.client.get_channel(629718364511797259)
                   
                    membob=channel.guild.get_member(int(member))
                    rolename=self.exp_info[member]["role"]
                    roles_list = membob.roles
                    
                    for role in roles_list:
                        if str(role) in self.roles and str(role) != "Council of Numericons":
                            await membob.remove_roles(role)
                   
                    roleob=discord.utils.get(channel.guild.roles, name=rolename)
                    await membob.add_roles(roleob)  
                
                    send = f'Congrats {channel.guild.get_member(int(member)).mention}, now you are of level {self.exp_info[member]["level"]} :middle_finger: .'
                    await channel.send(send)
                    
                self.exp_info[member]["rel_bar"] = level_dicc["rel_bar"]
               
                temp = self.exp_info[member]["role"]
                self.exp_info[member]["role"]=self.get_designation(self.exp_info[member]["level"])
                
                if temp != self.exp_info[member]["role"]:
                    channel = self.client.get_channel(629718364511797259)
                    self.log(f"\n {self.exp_info[member]['name']} is now a {self.exp_info[member]['role']} .")
                    membob=channel.guild.get_member(int(member))
                    rolename=self.exp_info[member]["role"]
                    roles_list = membob.roles
                    
                    for role in roles_list:
                        if str(role) in self.roles and str(role) != "Council of Numericons":
                            await membob.remove_roles(role)
                   
                    roleob=discord.utils.get(channel.guild.roles, name=rolename)
                    await membob.add_roles(roleob)  
                

                    send = f'Congrats {membob.mention}, now you are {roleob.mention} :middle_finger: .'
                    await channel.send(send)
    
        xplist=[]
        for i in self.exp_info:
            xplist+=[[self.exp_info[i]["xp"],i]]
       
        xplist = sorted(xplist, key=lambda x: x[0])
        for i in range(len(xplist)):
            self.exp_info[xplist[i][1]]["rank"]= len(xplist) - i

            
        gen.db_update("exp", self.exp_info)
 
    def rank_creation(self, ctx , member):

        try:
            mem_info = self.exp_info[str(member.id)]
        except:
            mem_info = self.user_entry(member)
                   
        level = mem_info["level"]
        rank = mem_info["rank"]
        response = requests.get(member.avatar_url)
        avatar_photo = Image.open(io.BytesIO(response.content))
    
        size = (600,600)
        avatar_photo = avatar_photo.resize(size)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)

        avatar_photo = ImageOps.fit(avatar_photo, mask.size, centering=(0.5, 0.5))
        avatar_photo.putalpha(mask)

        percent = mem_info["rel_xp"]/mem_info["rel_bar"]
        arc_length = percent*(360)
        if arc_length>360:
            arc_length=360
        arc_start = -90
        arc_end = arc_length-90

        a = list(self.roles.keys())
    
        for i in range(len(a)):
            if level<self.roles[a[i]][0]:
                role = a[i-1]
                role_cap,role_colour = self.roles[a[i-1]]
                role_colour = role_colour[:]
                role_next,role_next_colour = self.roles[a[i]]
                break
        else:
            role = "Council of Numericons"
            role_cap = 85
            role_colour = [0, 255, 240]
            role_next_colour = [0,255,240]
            role_next = level
        role_percent = (level - role_cap)/(role_next - role_cap)
    
        for i in range(3):
        
            colour_diff = int((role_next_colour[i] - role_colour[i])*role_percent)
            role_colour[i] += colour_diff
        role_colour = tuple(role_colour)
    

        bg = Image.new("RGB",(1000,1000),color = role_colour )
        fg = Image.new("RGB",(1000,980),color = (0,0,0))
        bg.paste(fg,(0,0))
        bg.paste(avatar_photo,(200,100),avatar_photo)
        
        draw = ImageDraw.Draw(bg)
        draw.arc([(190,90),(810,710)],start = arc_start,end = arc_end,fill =role_colour ,width =10)


        name = member.name
        if len(name)>15:
            name = name[:11]+'...'    
        discrim = member.discriminator
        nanotech = ImageFont.truetype('NanoTech Regular.otf', 100)
        roboto_cond = ImageFont.truetype('RobotoCondensed-Light.ttf', 60)
        d =nanotech.getsize(name)[0]
    
        draw.text((50,750),name,font=nanotech)
        draw.text((70+d,750),f"#{discrim}",font=roboto_cond )

        roboto_black = ImageFont.truetype('Roboto-Black.ttf', 110)

        d = roboto_cond.getsize("LEVEL")[0]
        draw.text((600,850),"LEVEL",font = roboto_cond,fill = role_colour)
        draw.text((620+d,810),str(level),font = roboto_black,fill = role_colour)

        d = roboto_cond.getsize("RANK")[0]
        draw.text((50,50),"RANK",font = roboto_cond)
        draw.text((70+d,10),str(rank),font = roboto_black)

        if role == "Council of Numericons":
            role = role.upper()
            x=10
            for i in range(11,20):
                draw.text((950,x),role[i],font = roboto_cond,fill = role_colour)
                x+= roboto_cond.getsize(role[i])[0]+40
        else:
            x = 10
            for i in role.upper():
                draw.text((950,x),i,font = roboto_cond,fill = role_colour)
                x+= roboto_cond.getsize(i)[0]+40

        bg.save("rank.png")

    def user_entry(self, user: discord.Member):
        member_info = {}
        member_info["name"] = user.name
        member_info["xp"] = 0
        member_info["level"] = 0
        member_info["rank"] = 0
        member_info["role"] = "Prostitute"
        member_info["messages"] = 1
        member_info["rel_bar"] = 100
        member_info["rel_xp"] = 0

        self.exp_info[str(user.id)] = member_info
        gen.db_update("exp", self.exp_info)

        return member_info

  


    def get_designation(self, level: int):
        a = list(self.roles.values())
        for i in range(len(a)):
            if a[i][0] > level:
                rel_role = a[i - 1][0]
                break

        else:
            rel_role=85

        for role,level in self.roles.items():
            if level[0] == rel_role:
                return role

    

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        
        
        if not message.author.bot:
            if str(message.author.id) not in self.exp_info.keys():
                member_info = self.user_entry(message.author)
            
            else:
                member_info = self.exp_info[str(message.author.id)]

            member_info["active"] = True
            member_info["messages"] += 1

            self.exp_info[str(message.author.id)] = member_info
          
        gen.db_update("exp", self.exp_info)





    @commands.command()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def rank(self, ctx,member = ''):
        '''Shows your level and rank, all epic style.'''

        try:
            int(member)
            
        except:
            try:
                    
                member1 = member
                member2=''
                for i in member1:
                    if i.isnumeric():
                        member2+=i
                
                member1 = int(member2)
                
                member1 = ctx.channel.guild.get_member(member1)
            except :
            

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
        thrd = Thread(target = self.rank_creation,args=(ctx,member))
        thrd.start()
        thrd.join()
        await ctx.send(file = discord.File("rank.png"))


def setup(client):
    client.add_cog(levels(client))
