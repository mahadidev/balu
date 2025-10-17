import discord
from discord.ext import commands
from discord import app_commands
from chat.category_manager import CategoryChatManager

class CategoryChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_manager = CategoryChatManager(bot)
    
    @commands.group(name='chat', aliases=['cat'], invoke_without_command=True)
    async def chat(self, ctx):
        """Category-based cross-server chat system"""
        embed = discord.Embed(
            title="📂 Category Chat Commands",
            color=0x00ff00,
            description="Organize cross-server communication by categories!"
        )
        
        embed.add_field(
            name="🏷️ Category Management",
            value="`!create <name>` - Create a new category\n"
                  "`!delete <name>` - Delete your category\n"
                  "`!list` - List all available categories\n"
                  "`!info <name>` - Show category information",
            inline=False
        )
        
        embed.add_field(
            name="📝 Subscription Management",
            value="`!subscribe <category>` - Subscribe to a category (AI matching)\n"
                  "`!unsubscribe <category>` - Unsubscribe from a category\n"
                  "`!subscriptions` - Show current subscriptions\n"
                  "`!members <category>` - Show category members\n"
                  "`!match <query>` - Test AI matching for a query",
            inline=False
        )
        
        embed.add_field(
            name="💬 Messaging",
            value="`[category] message` - Send to specific category\n"
                  "`message` - Send to all subscribed categories\n"
                  "Example: `[gaming] Looking for teammates!`",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Aliases",
            value="`!cat` - Short alias for chat commands\n"
                  "Example: `!cat list`, `!cat subscribe gaming`",
            inline=False
        )
        
        embed.set_footer(text="Use !chat <command> for more details")
        
        await ctx.send(embed=embed)
    
    @chat.command(name='create')
    async def create_category(self, ctx, *, name: str):
        """Create a new category"""
        result = await self.category_manager.create_category(
            name, str(ctx.author.id)
        )
        await ctx.send(result)
    
    @commands.command(name='create')
    async def create_category_short(self, ctx, *, name: str):
        """Create a new category (short command)"""
        result = await self.category_manager.create_category(
            name, str(ctx.author.id)
        )
        await ctx.send(result)
    
    @chat.command(name='delete')
    async def delete_category(self, ctx, *, name: str):
        """Delete a category you created"""
        result = await self.category_manager.delete_category(name, str(ctx.author.id))
        await ctx.send(result)
    
    @chat.command(name='list')
    async def list_categories(self, ctx):
        """List all available categories"""
        categories = self.category_manager.get_all_categories()
        
        if not categories:
            embed = discord.Embed(
                title="📂 Category Chat - No Categories",
                description="No categories are currently available.\nUse `!chat create <name> <description>` to create one!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📂 Available Categories",
            color=0x00ff00,
            description=f"Total: {len(categories)} categories"
        )
        
        # Group categories by pages (8 per page)
        page_size = 8
        pages = [categories[i:i + page_size] for i in range(0, len(categories), page_size)]
        
        for i, page in enumerate(pages):
            if i > 0:  # Only show first page for now
                break
                
            for category in page:
                subscriber_count = category['subscriber_count']
                max_servers = category['max_servers']
                
                field_name = f"🏷️ {category['category_name'].title()}"
                field_value = f"📊 {subscriber_count}/{max_servers} servers"
                
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=True
                )
        
        if len(pages) > 1:
            embed.set_footer(text=f"Showing page 1 of {len(pages)}. Use navigation for more.")
        else:
            embed.set_footer(text="Use !chat subscribe <category> to join a category!")
        
        await ctx.send(embed=embed)
    
    @chat.command(name='info')
    async def category_info(self, ctx, *, name: str):
        """Show detailed information about a category"""
        category = self.category_manager.get_category_info(name)
        
        if not category:
            await ctx.send(f"❌ Category **{name}** not found!")
            return
        
        subscribers = self.category_manager.get_category_subscribers(name)
        
        embed = discord.Embed(
            title=f"📂 Category: {category['category_name'].title()}",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {category['subscriber_count']}/{category['max_servers']}\n"
                  f"**Created:** {category['created_at'][:10]}\n"
                  f"**Creator:** <@{category['created_by']}>",
            inline=True
        )
        
        if subscribers:
            server_list = []
            for i, sub in enumerate(subscribers[:10], 1):  # Show max 10 servers
                server_list.append(f"{i}. **{sub['guild_name']}** - #{sub['channel_name']}")
            
            if len(subscribers) > 10:
                server_list.append(f"... and {len(subscribers) - 10} more servers")
            
            embed.add_field(
                name="🏛️ Connected Servers",
                value="\n".join(server_list),
                inline=False
            )
        
        embed.add_field(
            name="💬 How to Use",
            value=f"• Subscribe: `!chat subscribe {category['category_name']}`\n"
                  f"• Send message: `[{category['category_name']}] Hello everyone!`\n"
                  f"• Or just type normally if subscribed",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @chat.command(name='subscribe')
    async def subscribe_category(self, ctx, *, category_name: str):
        """Subscribe current channel to a category (supports AI matching)"""
        target_channel = ctx.channel
        
        # Use AI-powered matching
        result = await self.category_manager.smart_subscribe_channel(
            ctx.guild, target_channel, category_name, ctx.author
        )
        
        await ctx.send(result)
    
    @commands.command(name='subscribe')
    async def subscribe_category_short(self, ctx, *, category_name: str):
        """Subscribe current channel to a category (short command, supports AI matching)"""
        target_channel = ctx.channel
        
        # Use AI-powered matching
        result = await self.category_manager.smart_subscribe_channel(
            ctx.guild, target_channel, category_name, ctx.author
        )
        
        await ctx.send(result)
    
    @commands.command(name='unsubscribe')
    async def unsubscribe_category_short(self, ctx, *, category_name: str):
        """Unsubscribe current channel from a category (short command)"""
        target_channel = ctx.channel
        
        result = await self.category_manager.unsubscribe_channel(
            ctx.guild, target_channel, category_name, ctx.author
        )
        
        await ctx.send(result)
    
    @commands.command(name='subscriptions')
    async def show_subscriptions_short(self, ctx):
        """Show categories the current channel is subscribed to (short command)"""
        target_channel = ctx.channel
        
        subscriptions = self.category_manager.get_channel_subscriptions(
            str(ctx.guild.id), str(target_channel.id)
        )
        
        if not subscriptions:
            embed = discord.Embed(
                title="📂 No Subscriptions",
                description=f"{target_channel.mention} is not subscribed to any categories.\n"
                           f"Use `!subscribe <category>` to join categories!",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"📂 {target_channel.name} Subscriptions",
            color=0x00ff00,
            description=f"Subscribed to {len(subscriptions)} categories"
        )
        
        for sub in subscriptions:
            embed.add_field(
                name=f"🏷️ {sub['category_name'].title()}",
                value="Active subscription",
                inline=True
            )
        
        embed.add_field(
            name="💬 Usage",
            value="• Type normally to send to all categories\n"
                  "• Use `[category]` prefix for specific category\n"
                  f"• Example: `[{subscriptions[0]['category_name']}] Hello!`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='members')
    async def show_category_members_short(self, ctx, *, category_name: str):
        """Show all servers subscribed to a category (short command)"""
        category = self.category_manager.get_category_info(category_name)
        
        if not category:
            await ctx.send(f"❌ Category **{category_name}** not found!")
            return
        
        subscribers = self.category_manager.get_category_subscribers(category_name)
        
        if not subscribers:
            embed = discord.Embed(
                title=f"📂 {category_name.title()} - No Members",
                description="No servers are currently subscribed to this category.",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"📂 {category_name.title()} Members",
            color=0x00ff00,
            description=f"Total: {len(subscribers)} servers"
        )
        
        server_list = []
        for j, sub in enumerate(subscribers[:15], 1):  # Show max 15 servers
            server_list.append(f"{j}. **{sub['guild_name']}** - #{sub['channel_name']}")
        
        if len(subscribers) > 15:
            server_list.append(f"... and {len(subscribers) - 15} more servers")
        
        embed.add_field(
            name="🏛️ Connected Servers",
            value="\n".join(server_list),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='match')
    async def test_matching_short(self, ctx, *, query: str):
        """Test AI category matching (short command)"""
        best_match, confidence, all_matches = self.category_manager.smart_category_match(query)
        
        if not best_match:
            await ctx.send(f"🤖 **AI Analysis:** No matches found for `{query}`")
            return
        
        embed = discord.Embed(
            title="🤖 AI Category Matching Results",
            color=0x00ff00,
            description=f"**Search Query:** `{query}`"
        )
        
        embed.add_field(
            name="🎯 Best Match",
            value=f"**{best_match}** ({confidence*100:.1f}% confidence)",
            inline=False
        )
        
        if len(all_matches) > 1:
            other_matches = []
            for match_name, score in all_matches[1:4]:  # Show up to 3 other matches
                other_matches.append(f"• **{match_name}** ({score*100:.1f}%)")
            
            if other_matches:
                embed.add_field(
                    name="🔍 Other Matches",
                    value="\n".join(other_matches),
                    inline=False
                )
        
        confidence_level = "🎯 Excellent" if confidence >= 0.85 else "✅ Good" if confidence >= 0.6 else "❓ Low"
        embed.add_field(
            name="📊 Confidence Level",
            value=f"{confidence_level} ({confidence*100:.1f}%)",
            inline=True
        )
        
        embed.set_footer(text="Use !subscribe <query> to subscribe using AI matching")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='delete')
    async def delete_category_short(self, ctx, *, name: str):
        """Delete a category you created (short command)"""
        result = await self.category_manager.delete_category(name, str(ctx.author.id))
        await ctx.send(result)
    
    @commands.command(name='list')
    async def list_categories_short(self, ctx):
        """List all available categories (short command)"""
        categories = self.category_manager.get_all_categories()
        
        if not categories:
            embed = discord.Embed(
                title="📂 Category Chat - No Categories",
                description="No categories are currently available.\nUse `!create <name>` to create one!",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📂 Available Categories",
            color=0x00ff00,
            description=f"Total: {len(categories)} categories"
        )
        
        # Show categories
        for category in categories[:8]:  # Show max 8 categories
            subscriber_count = category['subscriber_count']
            max_servers = category['max_servers']
            
            field_name = f"🏷️ {category['category_name'].title()}"
            field_value = f"📊 {subscriber_count}/{max_servers} servers"
            
            embed.add_field(
                name=field_name,
                value=field_value,
                inline=True
            )
        
        if len(categories) > 8:
            embed.set_footer(text=f"Showing 8 of {len(categories)} categories. Use !chat list for full list.")
        else:
            embed.set_footer(text="Use !subscribe <category> to join a category!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='info')
    async def category_info_short(self, ctx, *, name: str):
        """Show detailed information about a category (short command)"""
        category = self.category_manager.get_category_info(name)
        
        if not category:
            await ctx.send(f"❌ Category **{name}** not found!")
            return
        
        subscribers = self.category_manager.get_category_subscribers(name)
        
        embed = discord.Embed(
            title=f"📂 Category: {category['category_name'].title()}",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {category['subscriber_count']}/{category['max_servers']}\n"
                  f"**Created:** {category['created_at'][:10]}\n"
                  f"**Creator:** <@{category['created_by']}>",
            inline=True
        )
        
        if subscribers:
            server_list = []
            for i, sub in enumerate(subscribers[:10], 1):  # Show max 10 servers
                server_list.append(f"{i}. **{sub['guild_name']}** - #{sub['channel_name']}")
            
            if len(subscribers) > 10:
                server_list.append(f"... and {len(subscribers) - 10} more servers")
            
            embed.add_field(
                name="🏛️ Connected Servers",
                value="\n".join(server_list),
                inline=False
            )
        
        embed.add_field(
            name="💬 How to Use",
            value=f"• Subscribe: `!subscribe {category['category_name']}`\n"
                  f"• Send message: `[{category['category_name']}] Hello everyone!`\n"
                  f"• Or just type normally if subscribed",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @chat.command(name='unsubscribe')
    async def unsubscribe_category(self, ctx, *, category_name: str):
        """Unsubscribe current channel from a category"""
        target_channel = ctx.channel
        
        result = await self.category_manager.unsubscribe_channel(
            ctx.guild, target_channel, category_name, ctx.author
        )
        
        await ctx.send(result)
    
    @chat.command(name='subscriptions')
    async def show_subscriptions(self, ctx, channel: discord.TextChannel = None):
        """Show categories the current or specified channel is subscribed to"""
        target_channel = channel or ctx.channel
        
        subscriptions = self.category_manager.get_channel_subscriptions(
            str(ctx.guild.id), str(target_channel.id)
        )
        
        if not subscriptions:
            embed = discord.Embed(
                title="📂 No Subscriptions",
                description=f"{target_channel.mention} is not subscribed to any categories.\n"
                           f"Use `!chat subscribe <category>` to join categories!",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"📂 {target_channel.name} Subscriptions",
            color=0x00ff00,
            description=f"Subscribed to {len(subscriptions)} categories"
        )
        
        for sub in subscriptions:
            embed.add_field(
                name=f"🏷️ {sub['category_name'].title()}",
                value="Active subscription",
                inline=True
            )
        
        embed.add_field(
            name="💬 Usage",
            value="• Type normally to send to all categories\n"
                  "• Use `[category]` prefix for specific category\n"
                  f"• Example: `[{subscriptions[0]['category_name']}] Hello!`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @chat.command(name='members')
    async def show_category_members(self, ctx, *, category_name: str):
        """Show all servers subscribed to a category"""
        category = self.category_manager.get_category_info(category_name)
        
        if not category:
            await ctx.send(f"❌ Category **{category_name}** not found!")
            return
        
        subscribers = self.category_manager.get_category_subscribers(category_name)
        
        if not subscribers:
            embed = discord.Embed(
                title=f"📂 {category_name.title()} - No Members",
                description="No servers are currently subscribed to this category.",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"📂 {category_name.title()} Members",
            color=0x00ff00,
            description=f"Total: {len(subscribers)} servers"
        )
        
        # Group subscribers by pages (15 per page)
        page_size = 15
        pages = [subscribers[i:i + page_size] for i in range(0, len(subscribers), page_size)]
        
        for i, page in enumerate(pages):
            if i > 0:  # Only show first page for now
                break
                
            server_list = []
            for j, sub in enumerate(page, 1 + (i * page_size)):
                server_list.append(f"{j}. **{sub['guild_name']}** - #{sub['channel_name']}")
            
            embed.add_field(
                name=f"🏛️ Servers {1 + (i * page_size)}-{min(len(subscribers), (i + 1) * page_size)}",
                value="\n".join(server_list),
                inline=False
            )
        
        if len(pages) > 1:
            embed.set_footer(text=f"Showing page 1 of {len(pages)}. Use navigation for more.")
        
        await ctx.send(embed=embed)
    
    @chat.command(name='help')
    async def chat_help(self, ctx):
        """Show detailed help for category chat system"""
        await self.category_manager.send_category_help(ctx.channel)
    
    @chat.command(name='match')
    async def test_matching(self, ctx, *, query: str):
        """Test AI category matching (shows what the AI would find)"""
        best_match, confidence, all_matches = self.category_manager.smart_category_match(query)
        
        if not best_match:
            await ctx.send(f"🤖 **AI Analysis:** No matches found for `{query}`")
            return
        
        embed = discord.Embed(
            title="🤖 AI Category Matching Results",
            color=0x00ff00,
            description=f"**Search Query:** `{query}`"
        )
        
        embed.add_field(
            name="🎯 Best Match",
            value=f"**{best_match}** ({confidence*100:.1f}% confidence)",
            inline=False
        )
        
        if len(all_matches) > 1:
            other_matches = []
            for match_name, score in all_matches[1:4]:  # Show up to 3 other matches
                other_matches.append(f"• **{match_name}** ({score*100:.1f}%)")
            
            if other_matches:
                embed.add_field(
                    name="🔍 Other Matches",
                    value="\n".join(other_matches),
                    inline=False
                )
        
        confidence_level = "🎯 Excellent" if confidence >= 0.85 else "✅ Good" if confidence >= 0.6 else "❓ Low"
        embed.add_field(
            name="📊 Confidence Level",
            value=f"{confidence_level} ({confidence*100:.1f}%)",
            inline=True
        )
        
        embed.set_footer(text="Use !chat subscribe <query> to subscribe using AI matching")
        
        await ctx.send(embed=embed)
    
    # Slash Commands
    @app_commands.command(name="chat_create", description="Create a new category")
    @app_commands.describe(name="Category name (2-30 characters, can include spaces)")
    async def chat_create_slash(self, interaction: discord.Interaction, name: str):
        """Create a new category via slash command"""
        result = await self.category_manager.create_category(
            name, str(interaction.user.id)
        )
        await interaction.response.send_message(result)
    
    @app_commands.command(name="chat_subscribe", description="Subscribe current channel to a category")
    @app_commands.describe(category="Category name to subscribe to (supports partial matching)")
    async def chat_subscribe_slash(self, interaction: discord.Interaction, category: str):
        """Subscribe to a category via slash command with AI matching"""
        result = await self.category_manager.smart_subscribe_channel(
            interaction.guild, interaction.channel, category, interaction.user
        )
        await interaction.response.send_message(result)
    
    @app_commands.command(name="chat_list", description="List all available categories")
    async def chat_list_slash(self, interaction: discord.Interaction):
        """List categories via slash command"""
        categories = self.category_manager.get_all_categories()
        
        if not categories:
            embed = discord.Embed(
                title="📂 Category Chat - No Categories",
                description="No categories are currently available.\nUse `/chat_create` to create one!",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📂 Available Categories",
            color=0x00ff00,
            description=f"Total: {len(categories)} categories"
        )
        
        for category in categories[:8]:  # Show max 8 categories
            subscriber_count = category['subscriber_count']
            max_servers = category['max_servers']
            
            field_name = f"🏷️ {category['category_name'].title()}"
            field_value = f"📊 {subscriber_count}/{max_servers} servers"
            
            embed.add_field(
                name=field_name,
                value=field_value,
                inline=True
            )
        
        if len(categories) > 8:
            embed.set_footer(text=f"Showing 8 of {len(categories)} categories. Use !chat list for full list.")
        else:
            embed.set_footer(text="Use /chat_subscribe to join a category!")
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in category chat channels"""
        await self.category_manager.handle_category_message(message)
    
    @chat.error
    async def chat_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(CategoryChatCommands(bot))