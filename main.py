import os
import asyncio
import discord
from discord.ext import commands
from music.music_player import MusicPlayer
from move.voice_manager import VoiceManager
from database.db_manager import DatabaseManager

# Import command modules
from core_commands import setup_core_commands
from music.commands import setup_music_commands
from move.commands import setup_voice_commands
from chat.commands import GlobalChatCommands

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize music player, voice manager, and database
music_player = None
voice_manager = None
db_manager = None

@bot.event
async def on_ready():
    global music_player, voice_manager, db_manager
    music_player = MusicPlayer(bot)
    voice_manager = VoiceManager(bot)
    db_manager = DatabaseManager()
    
    # Setup command modules
    setup_core_commands(bot)
    setup_music_commands(bot, music_player)
    setup_voice_commands(bot, voice_manager)
    
    # Add global chat cog
    await bot.add_cog(GlobalChatCommands(bot))
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
        for cmd in synced:
            print(f'  - /{cmd.name}: {cmd.description}')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
    
    print(f'✅ {bot.user.name} is online!')

@bot.event
async def on_disconnect():
    print('⚠️ Bot disconnected from Discord')

@bot.event
async def on_resumed():
    print('✅ Bot reconnected to Discord')

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'❌ Error in event {event}: {args}')
    import traceback
    traceback.print_exc()


# Run the bot with retry logic
async def run_bot_with_retry():
    """Run bot with automatic reconnection on failure"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('❌ No DISCORD_TOKEN found in .env file!')
        return
    
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            print(f'🚀 Starting bot (attempt {retry_count + 1}/{max_retries})')
            await bot.start(token)
        except discord.ConnectionClosed as e:
            retry_count += 1
            print(f'⚠️ Connection closed (code {e.code}), retrying in {retry_count * 5} seconds...')
            if retry_count < max_retries:
                await asyncio.sleep(retry_count * 5)
            else:
                print('❌ Max retries reached, exiting...')
                break
        except Exception as e:
            retry_count += 1
            print(f'❌ Unexpected error: {e}')
            if retry_count < max_retries:
                print(f'Retrying in {retry_count * 5} seconds...')
                await asyncio.sleep(retry_count * 5)
            else:
                print('❌ Max retries reached, exiting...')
                break

if __name__ == '__main__':
    try:
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        print('👋 Bot stopped by user')