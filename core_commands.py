import discord
from discord.ext import commands

def setup_core_commands(bot):
    """Setup core bot commands"""
    
    @bot.command()
    async def ping(ctx):
        """Test command"""
        await ctx.send('🏓 Pong!')

    @bot.command()
    async def hello(ctx):
        """Greet the user"""
        await ctx.send(f'👋 Hello {ctx.author.mention}! I\'m UN BOT!')