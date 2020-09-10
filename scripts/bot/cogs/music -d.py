
import discord
from discord.ext.commands.core import Command, cooldown
from discord.utils import get
import aiohttp
from discord.ext import commands, tasks
import json
from typing import List, Any
import re
import requests
from asyncio import sleep, TimeoutError
import asyncio
import youtube_dl
import lyricsgenius
import random
from lyricsgenius.song import Song
from datetime import timedelta
import imp
import os
imp.load_source("general", os.path.join(
    os.path.dirname(__file__), "../../others/general.py"))

imp.load_source("Youtube", os.path.join(
    os.path.dirname(__file__), "../../others/Youtube.py"))
from Youtube import YoutubePlaylist, YoutubeVideo, driver
import general as gen

imp.load_source("state", os.path.join(
    os.path.dirname(__file__), "../../others/state.py"))

from state import CustomContext, GuildState, TempState



genius = lyricsgenius.Genius(os.environ.get("LYRICS_GENIUS_KEY"))
genius.verbose = False


class Music(commands.Cog):
    ''':musical_note: The title says it all, commands related to music and stuff.'''
    
    properties = ["queue", "full_queue", "queue_ct", "full_queue_ct", "cooldown", "loop_song", "loop_q", "skip_song", "time_for_disconnect", "shuffle_lim", "shuffle_var"]
    # url of the image of thumbnail (vTube)
    music_logo = "https://cdn.discordapp.com/attachments/623969275459141652/664923694686142485/vee_tube.png"
   
    DPATH = os.path.join(
        os.path.dirname(__file__), '../../../cache.bot/Download')
    DPATH = os.path.abspath(DPATH)

    cooldown = 0
    
    
   # * ------------------------------------------------------------------------------PREREQUISITES--------------------------------------------------------------------------------------------------------------

    def __init__(self, client):
        self.client = client
        self.auto_pause.start()             # starting loops for auto pause and disconnect
        self.auto_disconnector.start()
        self.guild_dis = []
        self.guild_res_cancel = []
        self.time_l = []
        
        
        self.client: discord.Client
        
        if self.qualified_name in gen.cog_cooldown:
            self.cooldown = gen.cog_cooldown[self.qualified_name]
        else:
            self.cooldown = gen.cog_cooldown["default"]
            
        self.cooldown += gen.extra_cooldown
        
    def exception_catching_callback(self, task):
        if task.exception():
            task.print_stack()




    

   
    # * ERROR HANDLER
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log("Check Failed for user in VC.")
        else:
            pass

    # * TASKS

  

    # * MAIN

    # ? PLAYER
     
    


    


    

    



# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------

# *-------------------------------------------------------VOICE COMMANDS-----------------------------------------------------------------------------------------------------------------------------

   

   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------

   # * ----------------------------------------------------------PLAYLIST------------------------------------------------------------------------------------------------------------------------

    # ? PLAYLIST
    
    

# *------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# *------------------------------------DOWNLOAD----------------------------------------------------------------------------------------------------------------------------------------------------

    
    

# *---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def setup(client):
    client.add_cog(Music(client))
