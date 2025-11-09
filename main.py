import os
import asyncio
import discord
from discord.ext import commands
import wavelink
from move.voice_manager import VoiceManager
from database.db_manager import DatabaseManager

# Import command modules
from core_commands import setup_core_commands
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

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    """Called when Wavelink node is ready"""
    print(f"🎵 Wavelink Node connected: {payload.node!r} | Resumed: {payload.resumed}")

@bot.event
async def setup_hook():
    """Setup hook to connect to Lavalink"""
    print("🔗 Connecting to Lavalink server...")
    try:
        nodes = [wavelink.Node(uri="http://127.0.0.1:2333", password="youshallnotpass")]
        await wavelink.Pool.connect(nodes=nodes, client=bot, cache_capacity=100)
        print("✅ Connected to Lavalink server")
    except Exception as e:
        print(f"❌ Failed to connect to Lavalink: {e}")
        print("💡 Make sure Lavalink server is running! Run: python start_lavalink.py")

# Initialize voice manager and database
voice_manager = None
db_manager = None

@bot.event
async def on_ready():
    global voice_manager, db_manager
    print('🎯 Bot ready event triggered')
    
    print('🎤 Initializing voice manager...')
    voice_manager = VoiceManager(bot)
    
    print('💾 Initializing database...')
    db_manager = DatabaseManager()
    
    print('⚙️ Setting up command modules...')
    setup_core_commands(bot)
    print('  ✅ Core commands loaded')
    
    setup_voice_commands(bot, voice_manager)
    print('  ✅ Voice commands loaded')
    
    print('🎵 Loading Wavelink music system...')
    try:
        await bot.load_extension('music.player')
        print('  ✅ Wavelink music system loaded')
    except Exception as e:
        print(f'  ❌ Failed to load music system: {e}')
        import traceback
        traceback.print_exc()
    
    # Debug: Print all registered commands
    print('📋 Registered commands:')
    for command in bot.commands:
        print(f'  - !{command.name}: {command.help or "No description"}')
    
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
        
        # List all commands we're trying to sync
        all_commands = bot.tree.get_commands()
        print(f'📋 Commands to sync: {len(all_commands)}')
        for cmd in all_commands:
            print(f'  - {cmd.name}: {cmd.description}')
        
        synced = await asyncio.wait_for(bot.tree.sync(), timeout=60.0)
        print(f'✅ Synced {len(synced)} slash commands')
        for cmd in synced:
            print(f'  ✓ /{cmd.name}: {cmd.description}')
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
                print(f'❌ Error type: {type(retry_e).__name__}')
                if hasattr(retry_e, 'status'):
                    print(f'❌ HTTP status: {retry_e.status}')
                if hasattr(retry_e, 'response'):
                    print(f'❌ Response: {retry_e.response}')
                import traceback
                traceback.print_exc()
        else:
            print(f'❌ Failed to sync commands: {e}')
            # Try guild-specific sync as last resort
            try:
                print('🔄 Attempting guild-specific sync...')
                for guild in bot.guilds:
                    guild_synced = await bot.tree.sync(guild=guild)
                    print(f'✅ Synced {len(guild_synced)} commands for guild: {guild.name}')
            except Exception as guild_e:
                print(f'❌ Guild sync also failed: {guild_e}')
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
async def on_message(message):
    """Debug message processing"""
    if message.author.bot:
        return
    
    if message.content.startswith('!'):
        print(f'🔍 Processing command: {message.content} from {message.author}')
    
    await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'❌ Error in event {event}: {args}')
    import traceback
    traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    print(f'❌ Command error in {ctx.command}: {error}')
    import traceback
    traceback.print_exc()
    
    # Send error message to user
    if hasattr(error, 'original'):
        await ctx.send(f'❌ Error: {error.original}')
    else:
        await ctx.send(f'❌ Error: {error}')

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