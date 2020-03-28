import discord
from discord.utils import get
from general import db_receive, db_update, DBPATH
from discord.ext.commands import Context
from typing import Union
import os

class GuildState:
    """Stores state variables of a guild"""
    
    properties = ["rank_roles", "rank_levels", "juke_box", "auto_meme", "vc_text", "level_up", "dj_role", "extra_cooldown", "auto_pause", "auto_disconnect", "doujin_category", "prefix"]
    
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.db_name = "guild-states"
        
        with open(f"{DBPATH}/{self.db_name}.json", "w+") as f:
            if f.read() == "":
                f.write("{}")
        
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
    
        states = db_receive(self.db_name)
        states[str(self.guild.id)] = temp
        
        db_update("guild-states", states)
        
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
        
        states = db_receive(self.db_name)
        
        states[str(self.guild.id)] = state_variables
        
        db_update(self.db_name, states)
        
    @property
    def admin_role(self):
        for role in guild.roles:
            if role.permissions.administrator:
                return role
        
    @property
    def state_variables(self):
        states = db_receive(self.db_name)
        if not str(self.guild.id) in states:
            states[str(self.guild.id)] = {}

            db_update(self.db_name, states)      
            
        return db_receive(self.db_name)[str(self.guild.id)]
    
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
        if len(new) == 1:
            self.set_property(property_name="prefix", property_val=new)
        else:
            self.set_property(property_name="prefix", property_val=new + " ")
            
class MemberState:
    """Stores guild specific states which change between guilds"""
    
    properties = ["exp", "messages", "rank"]
    
    def __init__(self, member: discord.Member):
        self.member = member
        self.guild_state = GuildState(member.guild)
        self.db_name = f"member-states->{self.member.guild.id}"
        self.active = False
        
        with open(f"{DBPATH}/{self.db_name}.json", "w+") as f:
            if f.read() == "":
                f.write("{}")
        
        [self.new_property(pr) for pr in self.properties if self.get_property(pr, rtr=True) is None]
        
    def get_role(self, name) -> discord.Role:
        return get(self.member.roles, name=name)
    
    def reset(self):
        return [self.new_property(pr) for pr in self.properties]
    
    def set_property(self, property_name: str, property_val):
        temp = self.state_variables
    
        if type(property_val) == int:
            temp[property_name] = str(property_val)
        else:
            temp[property_name] = property_val
    
        states = db_receive(self.db_name)
        states[str(self.member.id)] = temp
        
        db_update(self.db_name, states)
        
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
        
        states = db_receive(self.db_name)
        
        states[str(self.member.id)] = state_variables
        
        db_update(self.db_name, states)
        
    def get_designation(self, level: int):
        roles = self.guild_state.ranks
        
        a = list(roles.values())
        for i in range(len(a)):
            if a[i][0] > level:
                rel_role = a[i - 1][0]
                break

            else:
                rel_role = a[-1][0]

        for role, level in roles.items():
            if level[0] == rel_role:
                return role
            
    @staticmethod
    def total_exp_needed(lvl):
        total_xp_needed = 0
        
        for i in range(lvl):
            total_xp_needed += ((5 * (i ** 2)) + (50 * i) + 100)
            
    @staticmethod
    def rank_gen(l: list) -> dict:
        output = [0] * len(l)
        for i, x in enumerate(sorted(range(len(l)), key=lambda y: l[y], reverse=True)):
            output[x] = i+1
        
        return dict(zip(l, output))
        
    @property
    def info(self):
        info = {}
        exp = self.xp
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
        rel_exp = exp - self.total_exp_needed(i)

        info["level"] = i
        info["rel_xp"] = rel_exp
        info["rel_bar"] = rel_bar

        return info
        
    @property
    def state_variables(self):
        states = self.database
        if not str(self.member.id) in states:
            states[str(self.member.id)] = {}

            db_update(self.db_name, states)      
            
        return self.database[str(self.member.id)] 
    
    @property
    def database(self) -> dict:
        return db_receive(self.db_name)
    
    @property
    def role(self) -> discord.Role:
        return self.guild_state.get_role(self.get_designation(self.level))
    
    @property
    def level(self) -> int:
        return self.info["level"]
    
    @property
    def xp(self) -> int:
        return int(self.get_property(property_name="exp"))
    
    @property
    def messages(self) -> int:
        return int(self.get_property(property_name="messages"))
    
    @property
    def rel_xp(self) -> int:
        return int(self.info["rel_xp"])
    
    @property
    def rel_bar(self) -> int:
        return int(self.info["rel_bar"])
    
    @property
    def rank(self) -> int:
        states = self.database
        
        exp_values = [value["exp"] for value in list(states.values())]
        
        exp_to_rank = self.rank_gen(exp_values)
    
    @xp.setter
    def xp(self, new: int):
        self.set_property(property_name="exp", property_val=new)
    
    @messages.setter
    def messages(self, new: int):
        self.set_property(property_name="messages", property_val=new)
    
    @rank.setter
    def rank(self, new: int):
        self.set_property(property_name="rank", property_val=new)
    
class UserState:
    """Stores global states which don't change between guilds."""
    
    properties = ["vault", "souls", "playlist", "phone"]
    
    def __init__(self, user: Union[discord.User, discord.Member]):
        self.user = user
        self.db_name = "user-states"
        
        with open(f"{DBPATH}/{self.db_name}.json", "w+") as f:
            if f.read() == "":
                f.write("{}")
        
        [self.new_property(pr) for pr in self.properties if self.get_property(pr, rtr=True) is None]
    
    def reset(self):
        return [self.new_property(pr) for pr in self.properties]
    
    def set_property(self, property_name: str, property_val):
        temp = self.state_variables

        if type(property_val) == int:
            temp[property_name] = str(property_val)
        else:
            temp[property_name] = property_val
    
        states = db_receive(self.db_name)
        states[str(self.user.id)] = temp
        
        db_update(self.db_name, states)
        
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
        
        states = db_receive(self.db_name)
        
        states[str(self.user.id)] = state_variables
        
        db_update(self.db_name, states)
        
    @property
    def state_variables(self):
        states = db_receive(self.db_name)
        if not str(self.user.id.id) in states:
            states[str(self.user.id)] = {}

            db_update(self.db_name, states)      
            
        return db_receive(self.db_name)[str(self.user.id)]
        
    @property
    def vault(self):
        return self.get_property(property_name="vault")
    
    @property
    def souls(self):
        return self.get_property(property_name="souls")
    
    @property
    def phone(self):
        return self.get_property(property_name="phone")
    
    @property
    def playlist(self):
        return self.get_property(property_name="playlist")
    
    @vault.setter
    def vault(self, new):
        return self.set_property(property_name="vault", property_val=new)
    
    @souls.setter
    def souls(self, new):
        return self.set_property(property_name="souls", property_val=new)
    
    @playlist.setter
    def playlist(self, new):
        return self.set_property(property_name="playlist", property_val=new)
    
    @phone.setter
    def phone(self, new):
        return self.set_property(property_name="phone", property_val=new)
        
        
class State:
    """Stores all the state objects"""
    
    def __init__(self, member: discord.Member, user: discord.User=None, guild: discord.Guild=None):
        if user is None:
            user = member
        if guild is None:
            guild = member.guild
            
        self.User = UserState(member)
        self.Member = MemberState(member)
        self.Guild = GuildState(guild)
        
        
class CustomContext(Context):
    """Use ctx = await bot.get_context(ctx.message, cls=CustomContext) in every command"""
    
    def __init__(self, **attrs):
        super().__init__(**attrs)
        
        self.States = State(self.author)
        