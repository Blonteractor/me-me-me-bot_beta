import os
import discord
from typing import Union
from discord.utils import get
from discord.ext.commands import Context
from general import db_receive, db_update, DBPATH
import pickle
from json import JSONDecodeError
from inspect import signature

def make_db_if_not_exists(path: str):
    if not os.path.exists(path):
        with open(path, "w+b") as f:
            f.write(b"{}")
            
class PKLProperty:
    
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

class JSONProperty:
          
    def __init__(self, name, db_scope, is_unique, default=None, encoder=None, decoder=None):
        self.name = name
        self.default = default
        self.is_unique = is_unique
        
        self.db_name = f"{db_scope}-states" if is_unique else (db_scope + "-states" + "----{id}") 
        
        if encoder is not None and not callable(encoder):
            raise AttributeError("'encoder' must be a callable")
        
        if decoder is not None and not callable(decoder):
            raise AttributeError("'decoder' must be a callable")
        
        self.encoder = encoder
        self.decoder = decoder
        
    @property
    def db_path(self):
        return f"{DBPATH}\\{self.db_name}.json"
    
    def __get__(self, instance, owner):
        self.unique_num = instance.unique_num
        d = self.data
        
        self.db_name = self.db_name.format(id=instance.unique_num)
        make_db_if_not_exists(path=self.db_path)
        
        if instance.identifier not in self.data:
            self.new_entry(entry=instance.identifier, unique_num=instance.unique_num) if not self.is_unique else self.new_entry(entry=instance.identifier)
            d = self.data
        
        if self.name in d[instance.identifier]:
            result = d[instance.identifier][self.name] 
            if self.decoder is None:       
                return result
            else:
                params = len(signature(self.decoder).parameters)
                
                if params == 1:
                    return self.decoder(result)
                elif params == 2:
                    return self.decoder(instance, result)
                else:
                    raise Exception("Faulty Decoder, decoder must either take 1 or 2 arguments.")
        else:
            return self.default
      
    def __set__(self, instance, value):
        self.unique_num = instance.unique_num
        new = self.data
        
        self.db_name = self.db_name.format(id=instance.unique_num)
        make_db_if_not_exists(path=self.db_path)
        
        if instance.identifier not in new:
            self.new_entry(entry=instance.identifier, unique_num=instance.unique_num) if not self.is_unique else self.new_entry(entry=instance.identifier)
            
        new = self.data
        
        if self.encoder is None:
            new[instance.identifier][self.name] = value
        else:
            params = len(signature(self.encoder).parameters)
            if params == 1:
                new[instance.identifier][self.name] = self.encoder(value)
            elif params == 2:
                new[instance.identifier][self.name] = self.encoder(instance, value)
            else:
                raise Exception("Faulty Encocoder, decoder must either take 1 or 2 arguments.")
                
        self.set_data(new_db=new, unique_num=instance.unique_num) if not self.is_unique else self.set_data(new_db=new)
    
    @property
    def data(self):
        self.db_name = self.db_name.format(id=self.unique_num)
        make_db_if_not_exists(path=self.db_path)
        try:
            return db_receive(self.db_name)
        except JSONDecodeError:
            return {}
    
    def set_data(self, new_db, unique_num=None):
        self.db_name = self.db_name.format(id=unique_num)
        db_update(name=self.db_name, db=new_db)

    def new_entry(self, entry, unique_num=None):
        new_db = self.data

        new_db[entry] = {}
        
        self.db_name = self.db_name.format(id=unique_num)
        db_update(name=self.db_name, db=new_db)
        
class GuildState:
    class_properties = {"db_scope":"guild", "is_unique":True}
    
    channel_properties = {"encoder": lambda channel: str(channel.id), "decoder": lambda self, _id: self.guild.get_channel(channel_id=int(_id))}
    role_properties = {"encoder": lambda role: str(role.id), "decoder": lambda self, _id: self.guild.get_role(role_id=int(_id))}
    
    rank_roles = JSONProperty(**class_properties, name="rank_roles", default=[])
    rank_levels = JSONProperty(**class_properties, name="rank_levels", default=[])
    
    jb_channel = JSONProperty(**class_properties, **channel_properties, name="jb_channel")
    auto_meme_channel = JSONProperty(**class_properties, **channel_properties,  name="auto_meme")
    voice_text_channel = JSONProperty(**class_properties, **channel_properties,  name="vc_text")
    level_up_channel = JSONProperty(**class_properties, **channel_properties,  name="level_up")
    
    extra_cooldown = JSONProperty(**class_properties, name="extra_cooldown", default=0)
    auto_pause_time = JSONProperty(**class_properties, name="auto_pause", default=1)
    auto_disconnect_time = JSONProperty(**class_properties, name="auto_disconnect", default=15)
    
    dj_role = JSONProperty(**class_properties, **role_properties, name="dj_role")
    doujin_category = JSONProperty(**class_properties, name="doujin_category")
    prefix = JSONProperty(**class_properties, name="prefix", default=["me!", "epic"])
    
    jb_embed_id = JSONProperty(**class_properties, name="jb_embed_id")
    jb_queue_id = JSONProperty(**class_properties, name="jb_queue_id")
    jb_image_id = JSONProperty(**class_properties, name="jb_image_id")
    jb_loading_id = JSONProperty(**class_properties, name="jb_loading_id")
    
    def __init__(self, guild):
        self.identifier = str(guild.id)
        self.guild = guild
    
    @property
    def admin_role(self):
        for role in self.guild.roles:
            if role.permissions.administrator:
                return role
            
    @property
    def ranks(self) -> dict:

        if self.rank_roles is None or self.rank_levels is None:
            return {}
        
        levels = [int(level) for level in self.rank_levels]
        roles = [self.get_role(id=role) for role in self.rank_roles]
        
        return dict(zip(levels, roles))
    
class MemberState:
    """Stores guild specific states which change between guilds"""
    
    class_properties = {"db_scope":"member", "is_unique":False}
    
    xp = JSONProperty(**class_properties, name="exp", default=0)
    messages = JSONProperty(**class_properties, name="messages", default=0)
    rank = JSONProperty(**class_properties, name="rank", default=0)
    active = JSONProperty(**class_properties, name="active", default=False)
    
    def __init__(self, member: discord.Member):
        
        if member.bot:
            raise AttributeError("Bots cant have a memberState.")
        
        self.member = member
        self.guild_state = GuildState(member.guild)

        self.identifier = member.id
        self.unique_num = member.guild.id
        
    def get_role(self, name) -> discord.Role:
        return get(self.member.roles, name=name)
    
    def get_designation(self, level_member: int):
        roles = self.guild_state.ranks
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
                self.rank = rank
                
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
    def database(self) -> dict:
        return db_receive(self.db_name)
    
    @property
    def role(self) -> discord.Role:
        return self.get_designation(self.level) 
    
    @property
    def level(self) -> int:
        return self.info["level"]
        
class UserState:
    """"Stores global states which don't change between guilds."""
    
    class_properties = {"db_scope":"user", "is_unique":True}
    
    vault = JSONProperty(**class_properties, name="vault", default={})
    souls = JSONProperty(**class_properties, name="souls", default=0)
    playlist = JSONProperty(**class_properties, name="playlist", default={})
    card_blend = JSONProperty(**class_properties, name="card_blend", default=False)
    
    phone_type = JSONProperty(**class_properties, name="phone_type")
    phone_bg = JSONProperty(**class_properties, name="phone_bg")
    phone_body = JSONProperty(**class_properties, name="phone_body")
    
    def __init__(self, user: Union[discord.User, discord.Member]):
        
        if user.bot:
            raise AttributeError("Bots cant have a userState.")
        
        self.user = user
        self.identifier = user.id

class TempState:
    time = PKLProperty(name="time", default=0)
    cooldown = PKLProperty(name="cooldown", default=0)
    
    queue = PKLProperty(name="queue", default=[])
    full_queue = PKLProperty(name="full_queue", default=[])
    queue_ct = PKLProperty(name="queue_ct", default=[])
    full_queue_ct = PKLProperty(name="full_queue_ct", default=[])
    
    loop_song = PKLProperty(name="loop_song", default=False)
    loop_q = PKLProperty(name="loop_q", default=False)
    skip_song = PKLProperty(name="skip_song", default=False)
    
    time_for_disconnect = PKLProperty(name="time_for_disconnect", default=0)
    
    shuffle_lim = PKLProperty(name="shuffle_lim")                                                                                                                    
    shuffle_var = PKLProperty(name="shuffle_var",default = 0)
    
    playing = PKLProperty(name="playing", default=False)
    old_queue_embed = PKLProperty(name="old_queue_embed", default=[])
    old_queue_queue = PKLProperty(name="old_queue_queue", default=[])

    paused_by_handler = PKLProperty(name = "paused_by_handler", default= False)
    voice_handler_time = PKLProperty(name = "voice_handler_time", default=0)
    
    
    def __init__(self, guild):
        self.guild = str(guild.id)
 
        
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
    
    def __init__(self, **attrs):
        super().__init__(**attrs)
        
        self.States = State(self.author)
        