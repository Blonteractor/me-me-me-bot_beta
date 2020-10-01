import sys
import os 
sys.path.append(os.path.abspath("./scripts/others/"))

import discord
from discord.ext import commands
from webtoon import Webtoon, Days, Genres

class Webtoons(commands.Cog):
    def __init__(self, client):
        self.client = client 
        
def setup(client):
    client.add_cog(Webtoons(client))