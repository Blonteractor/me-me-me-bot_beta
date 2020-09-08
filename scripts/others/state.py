import os
import discord
import json
from typing import Union
from discord.utils import get
from discord.ext.commands import Context
from general import db_receive, db_update, DBPATH
import imp
import _pickle as pickle
from itertools import repeat
import weakref

def make_db_if_not_exists(path: str):
    if not os.path.exists(path):
        with open(path, "w+b") as f:
            f.write(b"{}")
            
temp_data = {}
    
class GuildState:
    """Stores state variables of a guild"""
    
    properties = ["rank_roles", "rank_levels", "jb_channel","jb_embed_id","jb_queue_id","jb_image_id","jb_loading_id", "auto_meme", "vc_text", "level_up", "dj_role", "extra_cooldown", "auto_pause", "auto_disconnect", "doujin_category", "prefix"]
    
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.db_name = "guild-states"
        
        make_db_if_not_exists(path=f"{DBPATH}\\{self.db_name}.json")
        
        [self.new_property(pr) for pr in self.properties if self.get_property(pr, rtr=True) is None]
    
    def get_role(self, **kwargs) -> discord.Role:
        return get(self.guild.roles, name=kwargs.get("name")) if "name" in kwargs else get(self.guild.roles, id=int(kwargs.get("id")))
    
    def reset(self):
        return [self.new_property(pr) for pr in self.properties]
    
    @property
    def temp_data(self):
        if not self in temp_data:
            temp_data[self] = {}
        return temp_data[self] 
    
    def set_property(self, property_name: str, property_val, temp=False):
        if not temp:
            temp = self.state_variables
        
            if type(property_val) == int:
                temp[property_name] = str(property_val)
            else:
                temp[property_name] = property_val
        
            states = db_receive(self.db_name)
            states[str(self.guild.id)] = temp
            
            db_update("guild-states", states)
        else:
            try:
                self.temp_data[property_name] = property_val
            except:
                pass
        
    def get_property(self, property_name: str, rtr=False, temp=False):
        
        if not temp:
            state_variables = self.state_variables
            exists = property_name in state_variables
            
            if not exists:
                if not rtr:
                    raise AttributeError(f"{property_name} not found in the state variables")
                elif rtr:
                    return None

            return state_variables[property_name]
        else:
            return self.temp_data[property_name] if property_name in self.temp_data else self.set_property(property_name=property_name, property_val=None)
        
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

        if self.get_property("rank_roles") is None or self.get_property("rank_nums") is None:
            return {}
        
        levels = [int(level) for level in self.get_property("rank_nums")]
        roles = [self.get_role(id=role) for role in self.get_property("rank_roles")]
        
        return dict(zip(levels, roles))
    
    @property
    def jb_channel(self) -> discord.TextChannel:
        id = self.get_property("jb_channel")
        return self.guild.get_channel(int(id)) if id != None else id
    
    @property
    def jb_queue_id(self):
        return self.get_property("jb_queue")
    
    @property
    def jb_embed_id(self):
        return self.get_property("jb_embed")
    
    @property
    def jb_image_id(self):
        return self.get_property("jb_image")
    
    @property
    def jb_loading_id(self):
        return self.get_property("jb_loading")
       
    @property
    def auto_meme_channel(self) -> discord.TextChannel:
        id = self.get_property("auto_meme")
           
        return self.guild.get_channel(int(id)) if id != None else id
    
    @property
    def voice_text_channel(self) -> discord.TextChannel:
        id = self.get_property("vc_text")
        
        return self.guild.get_channel(int(id)) if id != None else id
    
    @property
    def level_up_channel(self) -> discord.TextChannel:
        id = self.get_property("level_up")
        return self.guild.get_channel(int(id)) if id != None else id
    
    @property
    def dj_role(self) -> discord.Role:
        role = self.get_property("dj_role")
        
        try:
            return self.get_role(id=role)
        except:
            return None
    
    @property
    def extra_cooldown(self) -> str:
        res = self.get_property("extra_cooldown")
        return str(res) if res is not None else "0"
    
    @property
    def auto_pause_time(self) -> str:
        res = self.get_property("auto_pause")
        return res if res is not None else "1"
    
    @property
    def auto_disconnect_time(self) -> str:
        res = self.get_property("auto_disconnect")
        return res if res is not None else "1"
    
    @property
    def doujin_category(self) -> str:
        return self.get_property("doujin_category")
    
    @property
    def prefix(self) -> str:
        return self.get_property("prefix")
    
    @property
    def exp_counting(self) -> bool:
        return not self.ranks == {}
    
    @ranks.setter
    def ranks(self, new):
        new_ranks = {str(rank): int(role.id) for rank, role in new.items()}
        ranks = list(new_ranks.keys())
        roles = list(new_ranks.values())
        
        self.set_property(property_name="rank_nums", property_val=ranks)
        self.set_property(property_name="rank_roles", property_val=roles)
        
    @jb_channel.setter
    def jb_channel(self, channel: discord.TextChannel):
        self.set_property(property_name="jb_channel", property_val=channel.id)
    
    @jb_embed_id.setter
    def jb_embed_id(self, embed_id):
        self.set_property(property_name="jb_embed",property_val=embed_id)
    
    @jb_image_id.setter
    def jb_image_id(self, image_id):
        self.set_property(property_name="jb_image",property_val=image_id)
    
    @jb_queue_id.setter
    def jb_queue_id(self, queue_id):
        self.set_property(property_name="jb_queue",property_val=queue_id)
    
    @jb_loading_id.setter
    def jb_loading_id(self, queue_id):
        self.set_property(property_name="jb_loading",property_val=queue_id)

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
        self.set_property(property_name="dj_role", property_val=int(role.id))
        
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
    
    properties = ["exp", "messages", "rank", "active"]
    
    def __init__(self, member: discord.Member):
        
        self.member = member
        self.db_name = f"member-states----{self.member.guild.id}"
        
        if member.bot:
            del self
            return
        
        self.guild_state = GuildState(member.guild)
        
        make_db_if_not_exists(path=f"{DBPATH}\\{self.db_name}.json")
        
        [self.new_property(pr) for pr in self.properties if self.get_property(pr, rtr=True) is None]
        
    def __del__(self):
        if self.member.bot:
            db = db_receive(self.db_name)
            
            if str(self.member.id) in db:
                db.pop(str(self.member.id))
            
            db_update(self.db_name, db)
        
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
        
    def get_designation(self, level_member: int):
        roles = self.guild_state.ranks
        
        # a = list(roles.keys())
        # for i in range(len(a)):
        #     if a[i] > level:
        #         rel_role = a[i - 1]
        #         break

        #     else:
        #         rel_role = a[-1]

        # for role, level in roles.items():
        #     if level == rel_role:
        #         return role
        
        temp = list(roles.items())[0][1]
        for level, role in roles.items():
            if level_member > level:
                temp = role
            else:
                break
        else:
            return list(roles.items())[-1][1]
            
        return temp
            
    def update_ranks(self):
        states = self.database
        
        exp_values = [int(value["exp"]) for value in list(states.values()) if "exp" in value and value["exp"] is not None]
        exp_to_rank = self.rank_gen(exp_values)
        exp = states[str(self.member.id)]["exp"] if states[str(self.member.id)]["exp"] is not None else 0
      
        for _exp, rank in exp_to_rank.items():
            if str(_exp) == str(exp):
                self.set_property(property_name="rank", property_val=rank)
                return
            
    @staticmethod
    def total_exp_needed(lvl):
        total_xp_needed = 0
        
        for i in range(lvl):
            total_xp_needed += ((5 * (i ** 2)) + (50 * i) + 100)
            
        return total_xp_needed
            
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
        return self.get_designation(self.level) 
    
    @property
    def level(self) -> int:
        return self.info["level"]
    
    @property
    def xp(self) -> int:
        prop = self.get_property(property_name="exp")
        
        return int(prop) if prop is not None else 0
    
    @property
    def messages(self) -> int:
        prop = self.get_property(property_name="messages")
        
        return int(prop) if prop is not None else 0
    
    @property
    def rel_xp(self) -> int:
        prop = self.info["rel_xp"]
        
        return int(prop) if prop is not None else 0
    
    @property
    def rel_bar(self) -> int:
        prop = self.info["rel_bar"]
        
        return int(prop) if prop is not None else 0
    
    @property
    def active(self) -> bool:
        prop = self.get_property(property_name="active")

        return prop if prop is not None else False
    
    @property
    def rank(self) -> int:
        prop = self.get_property(property_name="rank")
        return prop if prop is not None else 0
    
    @xp.setter
    def xp(self, new: int):
        self.set_property(property_name="exp", property_val=new)
        
        self.update_ranks()
    
    @messages.setter
    def messages(self, new: int):
        self.set_property(property_name="messages", property_val=new)
        
    @active.setter
    def active(self, new):
        self.set_property(property_name="active", property_val=new)
    
class UserState:
    """Stores global states which don't change between guilds."""
    
    properties = ["vault", "souls", "playlist", "phone_type", "phone_bg", "phone_body", "card_blend"]
    
    def __init__(self, user: Union[discord.User, discord.Member]):
        
        self.user = user
        self.db_name = "user-states"
        
        if user.bot:
            del self
            return
        
        make_db_if_not_exists(path=f"{DBPATH}\\{self.db_name}.json")
        
        [self.new_property(pr) for pr in self.properties if self.get_property(pr, rtr=True) is None]
        
    def __del__(self):
        if self.user.bot:
            db = db_receive(self.db_name)
            
            if str(self.user.id) in db:
                db.pop(str(self.user.id))
            
            db_update(self.db_name, db)
        
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
        
    def get_property(self, property_name: str, rtr=False, default=None):
        state_variables = self.state_variables
        exists = property_name in state_variables
        
        if not exists:
            if not rtr:
                pass
            elif rtr:
                return None
   
        return state_variables[property_name] if state_variables[property_name] is not None else default
        
    def new_property(self, property_name, property_val=None):
        state_variables = self.state_variables
        
        state_variables[property_name] = property_val
        
        states = db_receive(self.db_name)
        
        states[str(self.user.id)] = state_variables
        
        db_update(self.db_name, states)
        
    @property
    def state_variables(self):
        states = db_receive(self.db_name)
        if not str(self.user.id) in states:
            states[str(self.user.id)] = {}

            db_update(self.db_name, states)      
            
        return db_receive(self.db_name)[str(self.user.id)]
        
    @property
    def vault(self):
        prop = self.get_property(property_name="vault")
        return prop if prop is not None else {}
    
    @property
    def souls(self):
        prop = self.get_property(property_name="souls")
        return prop if prop is not None else 0
    
    @property
    def phone_type(self):
        return self.get_property(property_name="phone_type")
    
    @property
    def phone_bg(self):
        return self.get_property(property_name="phone_bg")
    
    @property
    def phone_body(self):
        return self.get_property(property_name="phone_body")
    
    @property
    def playlist(self):
        return self.get_property(property_name="playlist", default={})
    
    @property
    def card_blend(self) -> bool:
        prop = self.get_property(property_name="card_blend")
        return prop if prop is not None else False
    
    @vault.setter
    def vault(self, new):
        return self.set_property(property_name="vault", property_val=new)
    
    @souls.setter
    def souls(self, new):
        return self.set_property(property_name="souls", property_val=new)
    
    @playlist.setter
    def playlist(self, new):
        return self.set_property(property_name="playlist", property_val=new)
    
    @phone_type.setter
    def phone_type(self, new):
        return self.set_property(property_name="phone_type", property_val=new)
    
    @phone_bg.setter
    def phone_bg(self, new):
        return self.set_property(property_name="phone_bg", property_val=new)
 
    @phone_body.setter
    def phone_body(self, new):
        return self.set_property(property_name="phone_body", property_val=new)
    
    @card_blend.setter
    def card_blend(self, new):
        return self.set_property(property_name="card_blend", property_val=new)
        
class TempProperty:
    
    db_name = "temp.pkl"
    tempdb_path = os.path.join(DBPATH, db_name)
        
    def __init__(self, name, default=None):
        self.name = name
        self.default = default
        
    
    def __get__(self, instance, owner):
        d = self.data
        if instance.guild not in self.data:
            self.new_entry(entry=instance.guild)
            d = self.data
      
        return d[instance.guild][self.name] if self.name in d[instance.guild] else self.default   
      
    def __set__(self, instance, value):
        new = self.data
        if instance.guild not in new:
            self.new_entry(entry=instance.guild)
            
        new = self.data
        
        new[instance.guild][self.name] = value
        self.set_data(new_db=new) 
    
    @property
    def data(self):
        with open(self.tempdb_path, "rb") as output:
            try:
                return pickle.load(output)
            except EOFError:
                return {} 
    
    def set_data(self, new_db):
        with open(self.tempdb_path, "wb") as input:
            return pickle.dump(new_db, input, -1)

    def new_entry(self, entry):
        new_db = self.data

        new_db[entry] = {}
        
        with open(self.tempdb_path, "wb") as input:
            return pickle.dump(new_db, input, -1)

class TempState:
    time = TempProperty(name="time", default=0)
    cooldown = TempProperty(name="cooldown", default=0)
    
    queue = TempProperty(name="queue", default=[])
    full_queue = TempProperty(name="full_queue", default=[])
    queue_ct = TempProperty(name="queue_ct", default=[])
    full_queue_ct = TempProperty(name="full_queue_ct", default=[])
    
    loop_song = TempProperty(name="loop_song", default=False)
    loop_q = TempProperty(name="loop_q", default=False)
    skip_song = TempProperty(name="skip_song", default=False)
    
    time_for_disconnect = TempProperty(name="time_for_disconnect", default=0)
    
    shuffle_lim = TempProperty(name="shuffle_lim")                                                                                                                    
    shuffle_var = TempProperty(name="shuffle_var")
    
    playing = TempProperty(name="playing", default=False)
    old_queue_embed = TempProperty(name="old_queue_embed", default=[])
    old_queue_queue = TempProperty(name="old_queue_queue", default=[])
    
    def __init__(self, guild):
        self.guild = guild.id
    #     self._finalizer = weakref.finalize(self, self.reset)
    
    # @staticmethod
    # def reset():
    #     with open(TempProperty.tempdb_path, "wb") as f:
    #         f.write(b"")
            
    # def remove(self):
    #     self._finalizer   
        
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
        self.Temp = TempState(guild)
 
        
        
class CustomContext(Context):
    """Use ctx = await bot.get_context(ctx.message, cls=CustomContext) in every command"""
    
    def __init__(self, **attrs):
        super().__init__(**attrs)
        
        self.States = State(self.author)
        