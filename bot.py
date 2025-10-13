import os
import discord
from discord.ext import commands
from discord import app_commands
from music.music_player import MusicPlayer
from move.voice_manager import VoiceManager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize music player and voice manager
music_player = None
voice_manager = None

@bot.event
async def on_ready():
    global music_player, voice_manager
    music_player = MusicPlayer(bot)
    voice_manager = VoiceManager(bot)
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
        for cmd in synced:
            print(f'  - /{cmd.name}: {cmd.description}')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
    
    print(f'✅ {bot.user.name} is online!')

@bot.command()
async def ping(ctx):
    """Test command"""
    await ctx.send('🏓 Pong!')

@bot.command()
async def hello(ctx):
    """Greet the user"""
    await ctx.send(f'👋 Hello {ctx.author.mention}! I\'m UN BOT!')

# Music commands
@bot.command()
async def play(ctx, *, query):
    """Play music from YouTube"""
    if not query:
        await ctx.send('❌ Please provide a song name or YouTube URL!')
        return
    
    await music_player.play(ctx, query)

@bot.command()
async def skip(ctx):
    """Skip current song"""
    await music_player.skip(ctx)

@bot.command()
async def stop(ctx):
    """Stop music and clear queue"""
    await music_player.stop(ctx)

@bot.command()
async def pause(ctx):
    """Pause music"""
    await music_player.pause(ctx)

@bot.command()
async def resume(ctx):
    """Resume music"""
    await music_player.resume(ctx)

@bot.command()
async def queue(ctx):
    """Show current queue"""
    await music_player.show_queue(ctx)

@bot.command()
async def volume(ctx, vol: int):
    """Set volume (0-100)"""
    await music_player.set_volume(ctx, vol)

@bot.command()
async def leave(ctx):
    """Leave voice channel"""
    await music_player.leave(ctx)

@bot.command()
async def join(ctx):
    """Join voice channel"""
    await music_player.join(ctx)

# Voice channel management commands
@bot.command()
async def move(ctx, *, channel_name=None):
    """Move bot to a specific voice channel or your current channel"""
    await voice_manager.move_bot_to_channel(ctx, channel_name)

@bot.command()
async def moveall(ctx, *, channel_name=None):
    """Move all users from current channel to target channel (requires Move Members permission)"""
    await voice_manager.move_all_users_to_channel(ctx, channel_name)

@bot.command()
async def channels(ctx):
    """List all voice channels in the server"""
    await voice_manager.list_voice_channels(ctx)

@bot.command()
async def vcinfo(ctx):
    """Show current voice channel information"""
    await voice_manager.show_current_channel_info(ctx)

# Slash Commands with Channel Selector
@bot.tree.command(name="moveall", description="Move all users to a selected voice channel")
@app_commands.describe(channel="Select the voice channel to move everyone to")
async def moveall_slash(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """Move all users from current channel to selected voice channel with dropdown"""
    # Check if user has permissions
    if not interaction.user.guild_permissions.move_members:
        await interaction.response.send_message('❌ You need "Move Members" permission to use this command!', ephemeral=True)
        return
    
    # Get bot's current voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if not voice_client or not voice_client.channel:
        await interaction.response.send_message('❌ Bot is not in a voice channel!', ephemeral=True)
        return
    
    current_channel = voice_client.channel
    
    # Don't move to same channel
    if channel == current_channel:
        await interaction.response.send_message('❌ Already in that channel!', ephemeral=True)
        return

    await interaction.response.defer()

    try:
        members_to_move = current_channel.members.copy()
        moved_count = 0
        
        for member in members_to_move:
            if member != interaction.guild.me:  # Don't move the bot itself
                try:
                    await member.move_to(channel)
                    moved_count += 1
                except:
                    continue  # Skip if can't move (no permission, etc.)
        
        # Move bot too
        await voice_client.move_to(channel)
        
        await interaction.followup.send(f'✅ Moved {moved_count} members and bot to **{channel.name}**!')
        
    except Exception as e:
        print(f"Slash moveall error: {e}")
        await interaction.followup.send(f'❌ Failed to move members to **{channel.name}**!')

@bot.tree.command(name="move", description="Move bot to a selected voice channel")
@app_commands.describe(channel="Select the voice channel to move bot to (optional)")
async def move_slash(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    """Move bot to selected voice channel with dropdown"""
    guild = interaction.guild
    
    # If no channel provided, move to user's current channel
    if not channel:
        if interaction.user.voice and interaction.user.voice.channel:
            channel = interaction.user.voice.channel
        else:
            await interaction.response.send_message('❌ You need to be in a voice channel or select a channel!', ephemeral=True)
            return

    try:
        # Check if bot is currently in a voice channel
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
        
        if voice_client:
            await voice_client.move_to(channel)
            await interaction.response.send_message(f'✅ Moved to **{channel.name}**!')
        else:
            # Bot not in voice, join the target channel
            await channel.connect()
            await interaction.response.send_message(f'✅ Joined **{channel.name}**!')
            
    except Exception as e:
        print(f"Slash move error: {e}")
        await interaction.response.send_message(f'❌ Failed to move to **{channel.name}**!', ephemeral=True)

# Run the bot
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('❌ No DISCORD_TOKEN found in .env file!')
    else:
        bot.run(token)