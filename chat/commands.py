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
            name="📝 Registration",
            value="`!globalchat register` - Register current channel\n"
                  "`!globalchat unregister` - Unregister current channel",
            inline=False
        )
        
        embed.add_field(
            name="📊 Information",
            value="`!globalchat status` - Show connection status\n"
                  "`!globalchat list` - List all connected servers\n"
                  "`!globalchat info` - Show global chat information",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Settings (Admin Only)",
            value="`!globalchat settings` - View current settings\n"
                  "`!globalchat ratelimit <seconds>` - Set rate limit\n"
                  "`!globalchat maxlength <chars>` - Set max message length",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Aliases",
            value="`!gc` - Short alias for globalchat commands\n"
                  "Example: `!gc register`, `!gc status`",
            inline=False
        )
        
        embed.set_footer(text="Use !globalchat <command> for more details")
        
        await ctx.send(embed=embed)
    
    # New simplified chat commands
    @commands.command(name='chat_subscribe')
    async def chat_subscribe(self, ctx, channel: discord.TextChannel = None):
        """Subscribe current channel to global chat network"""
        target_channel = channel or ctx.channel
        
        result = await self.chat_manager.register_channel(
            ctx.guild, 
            target_channel, 
            ctx.author
        )
        
        await ctx.send(result)
    
    @commands.command(name='chat_create')
    async def chat_create(self, ctx, *, channel_name: str = None):
        """Create a new chat channel and subscribe it to global chat"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to create chat channels.")
            return
        
        if not channel_name:
            await ctx.send("❌ Please provide a channel name. Usage: `!chat_create <channel_name>`")
            return
        
        try:
            # Create new text channel
            new_channel = await ctx.guild.create_text_channel(
                name=channel_name,
                category=ctx.channel.category,
                topic="Global chat channel - Connected to the network"
            )
            
            # Automatically subscribe it to global chat
            result = await self.chat_manager.register_channel(
                ctx.guild, 
                new_channel, 
                ctx.author
            )
            
            await ctx.send(f"✅ Created {new_channel.mention} and {result.lower()}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create channels.")
        except Exception as e:
            await ctx.send(f"❌ Failed to create channel: {str(e)}")
    
    @commands.command(name='chat_status')
    async def chat_status(self, ctx):
        """Show global chat network status"""
        await self.chat_manager.send_status_message(ctx.channel)
    
    @globalchat.command(name='register')
    async def register_channel(self, ctx, channel: discord.TextChannel = None):
        """Register a channel for global chat"""
        target_channel = channel or ctx.channel
        
        result = await self.chat_manager.register_channel(
            ctx.guild, 
            target_channel, 
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
    
    @globalchat.command(name='status')
    async def status(self, ctx):
        """Show global chat status"""
        await self.chat_manager.send_status_message(ctx.channel)
    
    @globalchat.command(name='list')
    async def list_servers(self, ctx):
        """List all connected servers"""
        channels = self.chat_manager.get_registered_channels()
        
        if not channels:
            embed = discord.Embed(
                title="🌐 Global Chat - No Connections",
                description="No servers are currently connected to global chat.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🌐 Global Chat - Connected Servers",
            color=0x00ff00,
            description=f"Total: {len(channels)} servers"
        )
        
        # Group channels by pages (10 per page)
        page_size = 10
        pages = [channels[i:i + page_size] for i in range(0, len(channels), page_size)]
        
        for i, page in enumerate(pages):
            if i > 0:  # Only show first page for now
                break
                
            server_list = []
            for j, ch in enumerate(page, 1 + (i * page_size)):
                server_list.append(f"{j}. **{ch['guild_name']}** - #{ch['channel_name']}")
            
            embed.add_field(
                name=f"Servers {1 + (i * page_size)}-{min(len(channels), (i + 1) * page_size)}",
                value="\n".join(server_list),
                inline=False
            )
        
        if len(pages) > 1:
            embed.set_footer(text=f"Showing page 1 of {len(pages)}. Use navigation for more.")
        
        await ctx.send(embed=embed)
    
    @globalchat.command(name='info')
    async def info(self, ctx):
        """Show global chat information"""
        is_registered = self.chat_manager.is_registered_channel(
            str(ctx.guild.id), 
            str(ctx.channel.id)
        )
        
        embed = discord.Embed(
            title="🌐 Global Chat Information",
            color=0x00ff00 if is_registered else 0xff9900
        )
        
        embed.add_field(
            name="Current Channel Status",
            value="✅ Registered" if is_registered else "❌ Not Registered",
            inline=True
        )
        
        total_channels = len(self.chat_manager.get_registered_channels())
        embed.add_field(
            name="Total Connected Servers",
            value=str(total_channels),
            inline=True
        )
        
        embed.add_field(
            name="How it works",
            value="• Register your channel to join the global chat network\n"
                  "• Messages sent in registered channels are relayed to all other registered channels\n"
                  "• Rate limiting and content filtering are applied\n"
                  "• Only users with 'Manage Channels' permission can register channels",
            inline=False
        )
        
        embed.add_field(
            name="Features",
            value="• Cross-server messaging\n"
                  "• Image sharing support\n"
                  "• Rate limiting (3s default)\n"
                  "• Basic content filtering\n"
                  "• Message logging",
            inline=True
        )
        
        embed.add_field(
            name="Permissions Required",
            value="• Bot needs 'Send Messages' and 'Embed Links'\n"
                  "• Users need 'Manage Channels' to register",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @globalchat.command(name='settings')
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """View current global chat settings (Admin only)"""
        embed = discord.Embed(
            title="⚙️ Global Chat Settings",
            color=0x0099ff
        )
        
        embed.add_field(
            name="Rate Limit",
            value=f"{self.chat_manager.rate_limit_seconds} seconds",
            inline=True
        )
        
        embed.add_field(
            name="Max Message Length",
            value=f"{self.chat_manager.max_message_length} characters",
            inline=True
        )
        
        embed.add_field(
            name="Content Filtering",
            value="Enabled" if self.chat_manager.enable_filtering else "Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Blocked Words",
            value=", ".join(self.chat_manager.blocked_words) if self.chat_manager.blocked_words else "None",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @globalchat.command(name='ratelimit')
    @commands.has_permissions(administrator=True)
    async def set_ratelimit(self, ctx, seconds: int):
        """Set rate limit for global chat messages (Admin only)"""
        if seconds < 1 or seconds > 60:
            await ctx.send("❌ Rate limit must be between 1 and 60 seconds.")
            return
        
        self.chat_manager.db.update_global_chat_setting('rate_limit_seconds', str(seconds))
        self.chat_manager.rate_limit_seconds = seconds
        
        await ctx.send(f"✅ Rate limit set to {seconds} seconds.")
    
    @globalchat.command(name='maxlength')
    @commands.has_permissions(administrator=True)
    async def set_maxlength(self, ctx, length: int):
        """Set maximum message length for global chat (Admin only)"""
        if length < 100 or length > 2000:
            await ctx.send("❌ Message length must be between 100 and 2000 characters.")
            return
        
        self.chat_manager.db.update_global_chat_setting('max_message_length', str(length))
        self.chat_manager.max_message_length = length
        
        await ctx.send(f"✅ Maximum message length set to {length} characters.")
    
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