import discord
from discord.ext import commands
from chat.chat_manager import GlobalChatManager

class GlobalChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_manager = GlobalChatManager(bot)
    
    @commands.group(name='globalchat', aliases=['gc'], invoke_without_command=True)
    async def globalchat(self, ctx):
        """Global chat management commands"""
        embed = discord.Embed(
            title="🌐 Global Chat Commands",
            color=0x00ff00,
            description="Cross-server chat system"
        )
        
        embed.add_field(
            name="📝 Room Management",
            value="`!globalchat createroom <name>` - Create new chat room\n"
                  "`!globalchat rooms` - List available rooms",
            inline=False
        )
        
        embed.add_field(
            name="📝 Registration",
            value="`!globalchat register <room>` - Register channel to room\n"
                  "`!globalchat unregister` - Unregister current channel",
            inline=False
        )
        
        embed.set_footer(text="Use !globalchat <command> for more details")
        
        await ctx.send(embed=embed)
    
    
    @globalchat.command(name='createroom')
    async def create_room(self, ctx, *, room_name: str):
        """Create a new chat room"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to create rooms.")
            return
        
        success = self.chat_manager.db.create_chat_room(room_name, str(ctx.author.id))
        
        if success:
            await ctx.send(f"✅ Created chat room: **{room_name}**")
        else:
            await ctx.send(f"❌ Room '{room_name}' already exists.")
    
    @globalchat.command(name='rooms')
    async def list_rooms(self, ctx):
        """List all available chat rooms"""
        rooms = self.chat_manager.db.get_chat_rooms()
        
        if not rooms:
            embed = discord.Embed(
                title="🏠 Chat Rooms",
                description="No chat rooms available. Create one with `!globalchat createroom <name>`",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏠 Available Chat Rooms",
            color=0x00ff00,
            description=f"Total: {len(rooms)} rooms"
        )
        
        room_list = []
        for room in rooms:
            room_list.append(f"**{room['room_name']}** ({room['subscriber_count']} servers)")
        
        embed.add_field(
            name="Rooms",
            value="\n".join(room_list),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @globalchat.command(name='register')
    async def register_channel(self, ctx, room_name: str, channel: discord.TextChannel = None):
        """Register a channel to a chat room"""
        target_channel = channel or ctx.channel
        
        result = await self.chat_manager.register_channel(
            ctx.guild, 
            target_channel,
            room_name,
            ctx.author
        )
        
        await ctx.send(result)
    
    @globalchat.command(name='unregister')
    async def unregister_channel(self, ctx, channel: discord.TextChannel = None):
        """Unregister a channel from global chat"""
        target_channel = channel or ctx.channel
        
        result = await self.chat_manager.unregister_channel(
            ctx.guild, 
            target_channel, 
            ctx.author
        )
        
        await ctx.send(result)
    
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in global chat channels"""
        await self.chat_manager.handle_message(message)
    
    @globalchat.error
    async def globalchat_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(GlobalChatCommands(bot))