import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from PIL import Image,ImageDraw
from discord.ext import commands
from threading import Thread
import general as gen
from state import CustomContext as cc
class Phone(commands.Cog):
    ''':iphone: PHONE SIMULATOR 2019.'''
    
    cooldown = 0

    def __init__(self, client):
        self.client = client
        
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
    
    def phone_create(self, i_d):
        i_d = str(i_d)
         
        phone_db = gen.db_receive("phone")        
        phones = gen.db_receive("phone_types") 
        
        Ptype = phone_db[i_d]["type"]
        bg_color = tuple(phone_db[i_d]["bg_colour"])
        body_color = tuple(phone_db[i_d]["body_colour"])
        bg_pos = tuple(phones[Ptype]["screen"])
        body_pos = tuple(phones[Ptype]["body"])

        vtube_pos = phones[Ptype]["icon-1"]
        vtube_pos[0] -= 50
        vtube_pos[1] -= 35
        vtube_pos = tuple(vtube_pos)
        
        image = Image.open(f"./assets/Phones/{Ptype}.png")
                
        ImageDraw.floodfill(image,xy = bg_pos,value = bg_color)
        ImageDraw.floodfill(image,xy = body_pos,value = body_color)
        Vtube = Image.open("./assets/icons/vtube.png")
        
        image.paste(Vtube,vtube_pos,Vtube)
        image.save(f'./assets/saved_phones/{i_d}.png') 
        
    @commands.group()
    @commands.cooldown(rate=1, per=cooldown, type=commands.BucketType.user)
    async def phone(self,ctx):
        '''Shows your Phone.'''
        ctx = await self.client.get_context(ctx.message, cls=cc)
        
        if ctx.invoked_subcommand is None:
            
            phone_db = gen.db_receive("phone")
            
            if str(ctx.author.id) not in phone_db.keys(): 
                phone_db[ctx.author.id] = {"bg_colour":[0,250,250,255],"type":"Pinapple X=Y","body_colour":[0,0,0,255]}
                
                gen.db_update("phone",phone_db)
                thrd = Thread(target=self.phone_create, args=(ctx.author.id,))
                thrd.start()
                await ctx.send("Your Phone has been created")
                                
            
            phone = discord.File(f"./assets/saved_phones/{ctx.author.id}.png")    
            await ctx.channel.send(file=phone)

    @phone.command(aliases = ["color"])
    async def colour(self,ctx,place,r:int,g:int,b:int):
        '''Changes wallpaper and body's colour.'''   
        
        ctx = await self.client.get_context(ctx.message, cls=cc)     

        if r>255 or g>255 or b>255 or r<0 or g<0 or b<0:
            await ctx.send("SHUT UP")
            return
        phone_db = gen.db_receive("phone")
        
        if place.lower() == "wallpaper":
            phone_db[str(ctx.author.id)]["bg_colour"]=[r,g,b,255]
        elif place.lower() == "body":
            phone_db[str(ctx.author.id)]["body_colour"] =[r,g,b,255]
        else:
            await ctx.send("Wrong Place.")
            return
        
        gen.db_update("phone",phone_db)
        thrd = Thread(target=self.phone_create, args=(ctx.author.id,))
        thrd.start()
        await ctx.send("DONE BOSS")

    @phone.command()
    async def type(self,ctx,*,Ptype = None):
        '''Well you can at least get new phones in this virtual world.'''
        
        ctx = await self.client.get_context(ctx.message, cls=cc)

        phone_db = gen.db_receive("phone")
        phones = gen.db_receive("phone_types")
        
        if Ptype in phones.keys():
            phone_db[str(ctx.author.id)]["type"]=Ptype
            gen.db_update("phone",phone_db)  
            thrd = Thread(target=self.phone_create, args=(ctx.author.id,))
            thrd.start()
            await ctx.send("DONE BOSS")
        else:
            send_string = '```Please choose out of the following:\n'
            for i in phones:
                send_string += f"-> {i} \n"
            send_string += "```"
            await ctx.send(send_string)

         
def setup(client):
    client.add_cog(Phone(client))
