import discord
from discord.ext import commands

def setup_team_commands(bot, team_manager):
    """Setup team registration commands and events"""
    
    @bot.event
    async def on_reaction_add(reaction, user):
        """Handle reaction-based interactions"""
        # Ignore bot reactions
        if user.bot:
            return
        
        # Handle category selection reactions
        if team_manager:
            payload_like = type('obj', (object,), {
                'user_id': user.id,
                'message_id': reaction.message.id,
                'channel_id': reaction.message.channel.id,
                'emoji': reaction.emoji
            })
            await team_manager.handle_category_selection(payload_like)
    
    @bot.command()
    async def entry(ctx, *, registration_data=None):
        """Register team with AI parsing - supports various formats"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.register_team(ctx, registration_data=registration_data)

    @bot.command()
    async def teaminfo(ctx, user: discord.Member = None):
        """Show team registration info"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.show_team_info(ctx, user)

    @bot.command()
    async def teams(ctx):
        """List all registered teams in this server"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.list_teams(ctx)

    @bot.command()
    async def deleteteam(ctx):
        """Delete your team registration"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.delete_team_registration(ctx)

    @bot.command()
    async def players(ctx):
        """Show the last 5 updated teams ready to play"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.show_recent_players(ctx)

    @bot.command()
    async def subscribe(ctx, *, category=None):
        """Subscribe this channel to receive notifications when teams register globally"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.subscribe_to_updates(ctx, category_input=category)

    @bot.command()
    async def unsubscribe(ctx, *, category=None):
        """Unsubscribe this channel from global team registration notifications"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.unsubscribe_from_updates(ctx, category_input=category)

    @bot.command()
    async def subscriptions(ctx):
        """Show current subscription status for this channel"""
        if not team_manager:
            await ctx.send('⚠️ Team system is still starting up. Please try again in a moment.')
            return
        await team_manager.show_subscriptions(ctx)