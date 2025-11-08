import os
import asyncio
import discord
from discord.ext import commands
from music.music_player import MusicPlayer
from move.voice_manager import VoiceManager
from database.db_manager import DatabaseManager

# Import command modules
from core_commands import setup_core_commands
from music.commands import setup_music_commands  # This now points to the file above
from move.commands import setup_voice_commands
from chat.commands import GlobalChatCommands
from channel.commands import ChannelCommands

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
    print('🎯 Bot ready event triggered')
    
    print('🎵 Initializing music player...')
    music_player = MusicPlayer(bot)
    
    print('🎤 Initializing voice manager...')
    voice_manager = VoiceManager(bot)
    
    print('💾 Initializing database...')
    db_manager = DatabaseManager()
    
    print('⚙️ Setting up command modules...')
    setup_core_commands(bot)
    setup_music_commands(bot, music_player)  # This will use the function from music/commands.py
    setup_voice_commands(bot, voice_manager)
    
    print('💬 Adding chat system cog...')
    await bot.add_cog(GlobalChatCommands(bot))
    
    print('📂 Adding channel management cog...')
    try:
        await bot.add_cog(ChannelCommands(bot))
        print('✅ Channel commands loaded successfully')
    except Exception as e:
        print(f'❌ Failed to load channel commands: {e}')
        import traceback
        traceback.print_exc()
    
    # Sync slash commands with timeout
    try:
        print('🔄 Syncing slash commands...')
        # Clear existing commands first, then sync
        bot.tree.clear_commands(guild=None)
        synced = await asyncio.wait_for(bot.tree.sync(), timeout=30.0)
        print(f'✅ Synced {len(synced)} slash commands')
        for cmd in synced:
            print(f'  - /{cmd.name}: {cmd.description}')
    except discord.HTTPException as e:
        if e.status == 400 and "Entry Point command" in str(e):
            print('⚠️ Entry Point command detected, attempting individual sync...')
            try:
                # Try syncing without clearing commands
                synced = await asyncio.wait_for(bot.tree.sync(), timeout=30.0)
                print(f'✅ Synced {len(synced)} slash commands')
                for cmd in synced:
                    print(f'  - /{cmd.name}: {cmd.description}')
            except Exception as retry_e:
                print(f'❌ Failed to sync commands on retry: {retry_e}')
        else:
            print(f'❌ Failed to sync commands: {e}')
    except asyncio.TimeoutError:
        print('⏰ Slash command sync timed out, continuing without sync...')
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
    print('🔍 Checking for Discord token...')
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('❌ No DISCORD_TOKEN found in .env file!')
        return
    
    print('✅ Discord token found')
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
        print('🚀 Starting bot main...')
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        print('👋 Bot stopped by user')
    except Exception as e:
        print(f'❌ Bot failed to start: {e}')
        import traceback
        traceback.print_exc()