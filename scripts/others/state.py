import discord
from discord.utils import get
from general import db_receive, db_update
from discord.ext.commands import Context

class GuildState:
    """Stores state variables of a guild"""
    
    properties = ["rank_roles", "rank_levels", "juke_box", "auto_meme", "vc_text", "level_up", "dj_role", "extra_cooldown", "auto_pause", "auto_disconnect", "doujin_category", "prefix"]
    
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        
        [self.new_property(pr) for pr in self.properties if self.get_property(pr, rtr=True) is None]
        
    def get_channel(self, name) -> discord.TextChannel:
        return get(self.guild.channels, name=name)
    
    def get_role(self, name) -> discord.Role:
        return get(self.guild.roles, name=name)
    
    def reset(self):
        return [self.new_property(pr) for pr in self.properties]
    
    def set_property(self, property_name: str, property_val):
        temp = self.state_variables
    
        if type(property_val) == int:
            temp[property_name] = str(property_val)
        else:
            temp[property_name] = property_val
    
        states = db_receive("states")
        states[str(self.guild.id)] = temp
        
        db_update("states", states)
        
    def get_property(self, property_name: str, rtr=False):
        state_variables = self.state_variables
        exists = property_name in state_variables
        
        if not exists:
            if not rtr:
                raise AttributeError(f"{property_name} not found in the state variables")
            elif rtr:
                return None
   
        return state_variables[property_name]
        
    def new_property(self, property_name, property_val=None):
        state_variables = self.state_variables
        
        state_variables[property_name] = property_val
        
        states = db_receive("states")
        
        states[str(self.guild.id)] = state_variables
        
        db_update("states", states)
        
    @property
    def state_variables(self):
        states = db_receive("states")
        if not str(self.guild.id) in states:
            states[str(self.guild.id)] = {}

            db_update("states", states)      
            
        return db_receive("states")[str(self.guild.id)]
    
    @property
    def ranks(self) -> dict:
        roles = [self.get_role(role) for role in self.get_property("rank_roles")]
        levels = [int(level) for level in self.get_property("rank_levels")]
        
        return dict(zip(levels, roles))
    
    @property
    def juke_box_channel(self) -> discord.TextChannel:
        name = self.get_property("juke_box")
    
        return self.get_channel(name)
       
    @property
    def auto_meme_channel(self) -> discord.TextChannel:
        name = self.get_property("auto_meme")
           
        return self.get_channel(name)
    
    @property
    def voice_text_channel(self) -> discord.TextChannel:
        name = self.get_property("vc_text")
        
        return self.get_channel(name)
    
    @property
    def level_up_channel(self) -> discord.TextChannel:
        name = self.get_property("level_up")
        
        return self.get_channel(name)
    
    @property
    def dj_role(self) -> discord.Role:
        name = self.get_property("dj_role")
        
        return self.get_role(name)
    
    @property
    def extra_cooldown(self) -> str:
        res = self.get_property("extra_cooldown")
        return str(res) if res is not None else "0"
    
    @property
    def auto_pause_time(self) -> str:
        res = self.get_property("auto_pause")
        return res if res is not None else "0"
    
    @property
    def auto_disconnect_time(self) -> str:
        res = self.get_property("auto_disconnect")
        return res if res is not None else "0"
    
    @property
    def doujin_category(self) -> str:
        return self.get_property("doujin_category")
    
    @property
    def prefix(self) -> str:
        return self.get_property("prefix")
    
    @ranks.setter
    def ranks(self, new):
        new_ranks = {str(rank): role.name for rank, role in new.items()}
        ranks = list(new_ranks.keys())
        roles = list(new_ranks.values())
        
        self.set_property(property_name="rank_nums", property_val=ranks)
        self.set_property(property_name="rank_roles", property_val=roles)
        
    @juke_box_channel.setter
    def juke_box_channel(self, channel: discord.TextChannel):
        self.set_property(property_name="juke_box", property_val=channel.name)
        
    @auto_meme_channel.setter
    def auto_meme_channel(self, channel: discord.TextChannel):
        self.set_property(property_name="auto_meme", property_val=channel.name)
        
    @voice_text_channel.setter
    def voice_text_channel(self, channel: discord.TextChannel):
        self.set_property(property_name="voice_text", property_val=channel.name)
        
    @level_up_channel.setter
    def level_up_channel(self, channel: discord.TextChannel):
        self.set_property(property_name="level_up", property_val=channel.name)
    
    @extra_cooldown.setter
    def extra_cooldown(self, cooldown: int):
        self.set_property(property_name="extra_cooldown", property_val=cooldown)
        
    @auto_pause_time.setter
    def auto_pause_time(self, time: int):
        self.set_property(property_name="auto_pause", property_val=time)

    @auto_disconnect_time.setter
    def auto_disconnect_time(self, time: int):
        self.set_property(property_name="auto_disconnect", property_val=time)
      
    @dj_role.setter
    def dj_role(self, role: discord.Role):
        self.set_property(property_name="dj_role", property_val=role.name)
        
    @doujin_category.setter
    def doujin_category(self, name):
        self.set_property(property_name="doujin_category", property_val=name)
        
    @prefix.setter
    def prefix(self, new):
        self.set_property(property_name="prefix", property_val=new)
        

class CustomContext(Context):
    """Use ctx = await bot.get_context(ctx.message, cls=CustomContext) in every command"""
    
    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.GuildState = GuildState(self.guild)
        