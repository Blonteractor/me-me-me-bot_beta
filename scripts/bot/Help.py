import discord
from discord.ext import commands, tasks
from asyncio import TimeoutError

class MyHelpCommand(commands.HelpCommand):
    
    def __init__(self):
        super().__init__(command_attrs={
	    		'help': 'Shows help about the bot, a command, or a category',
	    		'cooldown': commands.Cooldown(1, 3.0, commands.BucketType.member)})

    nsfw_cog_name = "Nsfw"

    footer_text = "[optional fields]    <necessary fields>    (aliases)"

    def get_command_signature(self, command):
        """Method to return a commands name and signature"""

        ctx=self.context

        if not command.signature and isinstance(command,commands.Group) and not command.parent:
            return f'`{ctx.prefix}{command.name}` `[subcommands]`'

        elif command.signature and isinstance(command,commands.Group) and not command.parent:
            return f'`{ctx.prefix}{command.name}` `{command.signature}` `[subcommands]`'

        elif not command.signature and command.parent and isinstance(command,commands.Group):
            return f' {self.get_command_signature(command.parent).replace("`[subcommands]`","")} `{command.name}` `[subcommands]`'

        elif command.signature and command.parent and isinstance(command,commands.Group):
            return f' {self.get_command_signature(command.parent).replace("`[subcommands]`","")} `{command.name}` `{command.signature}` `[subcommands]`'

        elif not command.signature and not command.parent:  # checking if it has no args and isn't a subcommand
            return f'`{ctx.prefix}{command.name}`'

        elif command.signature and not command.parent:  # checking if it has args and isn't a subcommand
            return f'`{ctx.prefix}{command.name}` `{command.signature}`'

        elif not command.signature and command.parent:  # checking if it has no args and is a subcommand
            return f' {self.get_command_signature(command.parent).replace("`[subcommands]`","")} `{command.name}`'
        
        
        else:  # else assume it has args a signature and is a subcommand
            return f'{self.get_command_signature(command.parent).replace("`[subcommands]`","")} `{command.name}` `{command.signature}`'

    def get_command_aliases(self, command):  # this is a custom written method along with all the others below this
        """Method to return a commands aliases"""
        if not command.aliases:  # check if it has any aliases
            return ''
        else:
            return f'`({"` | `".join([alias for alias in command.aliases])})`'

    def get_command_description(self, command):
        """Method to return a commands short doc/brief"""

        if not command.short_doc:  # check if it has any brief
            return 'There is no documentation for this command currently'
        else:
            return command.short_doc

    def get_command_help(self, command):
        """Method to return a commands full description/doc string"""

        if not command.help:  # check if it has any brief or doc string
            return 'There is no documentation for this command currently'
        else:
            return command.help


    async def send_bot_help(self, mapping):
   
        ctx=self.context
        embeds=[]
        cogs_list = []

        for cog in mapping:
            if cog: 
                cog_name = cog.qualified_name.capitalize()
                try:
                    emoji,desc = cog.description.split(maxsplit = 1)
                except:
                    emoji = ":construction_worker:"
                    desc = "This is under construction, Now Skiddadle Skidoodle."

                commands = cog.get_commands()
                cog_split = [commands[i:i + 25] for i in range(0, len(commands), 25)]
                n  = len(cog_split)
                if n ==1:
                    embed = discord.Embed(title = f"{emoji} **{cog_name}** ", description = desc, color=discord.Colour.magenta())
                    for command in commands:
                        embed.add_field(name = f'{self.get_command_signature(command)} {self.get_command_aliases(command)}',value = self.get_command_description(command))
                    embed.set_footer(text = self.footer_text )
                    embeds += [embed]
                    cogs_list+=[cog_name]
                else:
                    for i in range(1,n+1):
                        embed = discord.Embed(title = f"{emoji} **{cog_name} {i}/{n}** ", description = desc, color=discord.Colour.magenta())
                        for command in cog_split[i-1]:
                            embed.add_field(name = f'{self.get_command_signature(command)} {self.get_command_aliases(command)}',value = self.get_command_description(command))
                        embed.set_footer(text = self.footer_text)
                        embeds += [embed]
                        cogs_list+=[cog_name+f' {i}/{n}']

    
                
        embed = discord.Embed(title = f"{ctx.prefix}HELP",
                                description = f"All the types of command ME! has to offer \n\nPREFIX ->  `{ctx.prefix}`\n",
                                color=discord.Colour.magenta())
                
        for cog in mapping:
            try:
                emoji,desc = cog.description.split(maxsplit=1)
            except:
                emoji = ":construction_worker:"
                desc = "This is under construction, Now Skiddadle Skidoodle."
            if cog:
                cog_name = cog.qualified_name.capitalize()
                embed.add_field(name = f"{emoji} **{cog_name}**", value= f">>> `{ctx.prefix}HELP {cog_name}`")
        embed.set_footer(text = self.footer_text)

        embeds.insert(0,embed)
        
        wait_time = 180
        page = 0 
        embed_msg = await ctx.send(embed = embeds[0])
        embed_msg: discord.Message

        async def reactions_add(message, reactions):
                for reaction in reactions:
                    await message.add_reaction(reaction)

        reactions = {"back": "⬅", "forward": "➡", "nsfw": "🍆", "delete": "❌"}
        ctx.bot.loop.create_task(reactions_add(embed_msg, reactions.values())) 

        def check(reaction: discord.Reaction, user):  
                return user == ctx.author and reaction.message.id == embed_msg.id

        while True:

            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=wait_time, check=check)
            
            except TimeoutError:
                await ctx.send(f">>> Deleted Help Command due to inactivity.")
                await embed_msg.delete()

                return

            else: 
                await embed_msg.remove_reaction(str(reaction.emoji), ctx.author)

                if str(reaction.emoji) in reactions.values():

                    if str(reaction.emoji) == reactions["forward"]: 
                        page += 1
                        
                        if page >= len(embeds):
                            page = len(embeds)-1

                        
                        await embed_msg.edit(embed=embeds[page])

                    elif str(reaction.emoji) == reactions["back"]: 
                        page -= 1

                        if page < 0:
                            page = 0
                        
                        
                        await embed_msg.edit(embed=embeds[page])

                    elif str(reaction.emoji) == reactions["nsfw"]: 
                        for i in cogs_list:
                            if self.nsfw_cog_name in i:
                                page = cogs_list.index(i)+1
                                break
                     
                        await embed_msg.edit(embed=embeds[page])


                    elif str(reaction.emoji) == reactions["delete"]: 
                        await embed_msg.delete(delay=1)
                        return
                else:
                    pass
    
    async def send_command_help(self, command):
        ctx=self.context
      
        embed = discord.Embed(title =  f"{self.get_command_signature(command)} {self.get_command_aliases(command)}",description=self.get_command_help(command), color=discord.Colour.magenta())
        embed.set_footer(text = self.footer_text)
        await ctx.send(embed=embed)

    async def send_cog_help(self, cog):
        ctx=self.context

        cog_name = cog.qualified_name.capitalize()
        try:
            emoji,desc = cog.description.split(maxsplit = 1)
        except:
            emoji = ":construction_worker:"
            desc = "This is under construction, Now Skiddadle Skidoodle."

        commands = cog.get_commands()
        cog_split = [commands[i:i + 25] for i in range(0, len(commands), 25)]
        n  = len(cog_split)
        if n ==1:
            embed = discord.Embed(title = f"{emoji} **{cog_name}** ", description = desc, color=discord.Colour.magenta())
            for command in commands:
                embed.add_field(name = f'{self.get_command_signature(command)} {self.get_command_aliases(command)}',value = self.get_command_description(command))
            embed.set_footer(text = self.footer_text)
            await ctx.send(embed=embed)

        else:
            for i in range(1,n+1):
                embed = discord.Embed(title = f"{emoji} **{cog_name} {i}/{n}** ", description = desc, color=discord.Colour.magenta())
                for command in cog_split[i-1]:
                    embed.add_field(name = f'{self.get_command_signature(command)} {self.get_command_aliases(command)}',value = self.get_command_description(command))
                embed.set_footer(text = self.footer_text)
                await ctx.send(embed=embed)   



    async def send_group_help(self, group):
        ctx=self.context

        parent_command = list(group.commands)[0].parent

        commands = list(group.commands)
        com_split = [commands[i:i + 25] for i in range(0, len(commands), 25)]
        n  = len(com_split)
        if n ==1:
            embed = discord.Embed(title =  f"{self.get_command_signature(parent_command)} {self.get_command_aliases(parent_command)}",description=self.get_command_help(parent_command), color=discord.Colour.magenta())
            for command in commands:
                embed.add_field(name = f'{self.get_command_signature(command)} {self.get_command_aliases(command)}',value = self.get_command_description(command))
            embed.set_footer(text = self.footer_text)
            await ctx.send(embed=embed)

        else:
            for i in range(1,n+1):
                embed = discord.Embed(title =  f"{self.get_command_signature(parent_command)} {self.get_command_aliases(parent_command)} {i}/{n}",description=self.get_command_help(parent_command), color=discord.Colour.magenta())
                for command in com_split[i-1]:
                    embed.add_field(name = f'{self.get_command_signature(command)} {self.get_command_aliases(command)}',value = self.get_command_description(command))
                embed.set_footer(text = self.footer_text)
                await ctx.send(embed=embed) 
    
    async def command_not_found(self,string):

        ctx = self.context
        cog = ctx.bot.get_cog(string.capitalize())
        if not cog:
            await ctx.send(f"No command {string} found.")
        else:
            await self.send_cog_help(cog)

    async def send_error_message(self,string):
        pass