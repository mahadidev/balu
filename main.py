import os
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


# Run the bot
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('❌ No DISCORD_TOKEN found in .env file!')
    else:
        bot.run(token)