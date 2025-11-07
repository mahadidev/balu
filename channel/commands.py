import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from channel.channel_manager import ChannelManager

class ChannelCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_manager = ChannelManager(bot)
    
    @commands.command(name='clear_text_channel')
    async def clear_text_channel(self, ctx, *, channel_name_confirmation: str):
        """Clear all messages from current text channel (Admin only)"""
        current_channel = ctx.channel
        
        # Check permissions first
        permission_check = self.channel_manager.check_permissions(
            current_channel, ctx.author, ctx.guild.me
        )
        if not permission_check["valid"]:
            await ctx.send(permission_check["message"])
            return
        
        # Check if the input matches the current channel name
        if not self.channel_manager.validate_channel_name(current_channel.name, channel_name_confirmation):
            await ctx.send(f"❌ Channel name confirmation failed!\n"
                          f"**Current channel:** `{current_channel.name}`\n"
                          f"**You typed:** `{channel_name_confirmation}`\n\n"
                          f"For safety, please type the exact channel name: `!clear_text_channel {current_channel.name}`")
            return
        
        # Send confirmation message
        confirm_msg = await ctx.send(f"⚠️ **WARNING: This will delete ALL messages in #{current_channel.name}**\n\n"
                                   f"This action cannot be undone! React with ✅ to confirm or ❌ to cancel.\n"
                                   f"*Confirmation expires in 30 seconds.*")
        
        # Add reaction options
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == confirm_msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send("✅ Channel clear cancelled.")
                return
            elif str(reaction.emoji) == "✅":
                # Proceed with clearing
                await ctx.send("🧹 Starting channel clear... This may take a while.")
                
                # Clear the channel
                result = await self.channel_manager.clear_text_channel(current_channel, ctx.author)
                
                if result["success"]:
                    try:
                        # Send success message to new channel
                        await result["new_channel"].send(result["message"])
                    except discord.Forbidden:
                        # If we can't send to new channel, that's okay - the clear was successful
                        print(f"Channel {result['new_channel'].name} cleared but couldn't send confirmation message")
                    except Exception as e:
                        print(f"Channel cleared but error sending confirmation: {e}")
                else:
                    # Only try to send error message if the original channel still exists
                    try:
                        await ctx.send(result["message"])
                    except (discord.NotFound, discord.Forbidden):
                        print(f"Channel clear failed: {result['message']}")
                    
        except asyncio.TimeoutError:
            await ctx.send("⏰ Confirmation timed out. Channel clear cancelled.")
    
    @app_commands.command(name="clear_channel", description="Clear all messages from current text channel (Admin only)")
    @app_commands.describe(channel_name_confirmation="Type the exact channel name to confirm")
    async def clear_channel_slash(self, interaction: discord.Interaction, channel_name_confirmation: str):
        """Clear all messages from current text channel (Admin only)"""
        current_channel = interaction.channel
        
        # Check permissions first
        permission_check = self.channel_manager.check_permissions(
            current_channel, interaction.user, interaction.guild.me
        )
        if not permission_check["valid"]:
            await interaction.response.send_message(permission_check["message"], ephemeral=True)
            return
        
        # Check if the input matches the current channel name
        if not self.channel_manager.validate_channel_name(current_channel.name, channel_name_confirmation):
            await interaction.response.send_message(
                f"❌ Channel name confirmation failed!\n"
                f"**Current channel:** `{current_channel.name}`\n"
                f"**You typed:** `{channel_name_confirmation}`\n\n"
                f"For safety, please type the exact channel name.",
                ephemeral=True
            )
            return
        
        # Send confirmation message
        await interaction.response.send_message(
            f"⚠️ **WARNING: This will delete ALL messages in #{current_channel.name}**\n\n"
            f"This action cannot be undone! React with ✅ to confirm or ❌ to cancel.\n"
            f"*Confirmation expires in 30 seconds.*"
        )
        
        # Get the message to add reactions
        confirm_msg = await interaction.original_response()
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == interaction.user and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == confirm_msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await interaction.followup.send("✅ Channel clear cancelled.")
                return
            elif str(reaction.emoji) == "✅":
                # Proceed with clearing
                await interaction.followup.send("🧹 Starting channel clear... This may take a while.")
                
                # Clear the channel
                result = await self.channel_manager.clear_text_channel(current_channel, interaction.user)
                
                if result["success"]:
                    try:
                        # Send success message to new channel
                        await result["new_channel"].send(result["message"])
                    except discord.Forbidden:
                        # If we can't send to new channel, that's okay - the clear was successful
                        print(f"Channel {result['new_channel'].name} cleared but couldn't send confirmation message")
                    except Exception as e:
                        print(f"Channel cleared but error sending confirmation: {e}")
                else:
                    try:
                        await interaction.followup.send(result["message"])
                    except (discord.NotFound, discord.Forbidden):
                        print(f"Channel clear failed: {result['message']}")
                    
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Confirmation timed out. Channel clear cancelled.")
    
    @clear_text_channel.error
    async def clear_text_channel_error(self, ctx, error):
        """Handle clear_text_channel command errors"""
        try:
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Please provide the channel name for confirmation.\n"
                              f"Usage: `!clear_text_channel {ctx.channel.name}`")
            else:
                await ctx.send(f"❌ An error occurred: {str(error)}")
        except (discord.NotFound, discord.Forbidden):
            # Channel might have been deleted, log the error instead
            print(f"Error in clear_text_channel command: {str(error)}")

async def setup(bot):
    await bot.add_cog(ChannelCommands(bot))