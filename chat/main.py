import os
import sys
import asyncio
import discord
from discord.ext import commands

# Add project root to Python path
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import shared components
from shared.database.manager import db_manager
from shared.cache.redis_client import redis_client

# Import command modules
from commands import GlobalChatCommands

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)



@bot.event
async def on_ready():
    print('🎯 Bot ready event triggered')
    
    print('💾 Initializing database...')
    await db_manager.initialize()
    print('  ✅ Database initialized')
    
    print('💾 Initializing Redis...')
    await redis_client.initialize()
    print('  ✅ Redis initialized')
    
    print('💬 Adding chat system cog...')
    # Check if cog is already loaded to avoid duplicate loading
    if 'GlobalChatCommands' not in bot.cogs:
        await bot.add_cog(GlobalChatCommands(bot))
        print('  ✅ Chat system loaded')
    else:
        print('  ℹ️ Chat system already loaded')
    
    
    # Only sync slash commands if needed (avoid rate limits)
    try:
        all_commands = bot.tree.get_commands()
        if len(all_commands) > 0:
            print(f'📋 Found {len(all_commands)} slash commands to potentially sync')
            
            # Check if we should sync (avoid rate limiting)
            should_sync = os.getenv('FORCE_COMMAND_SYNC', 'false').lower() == 'true'
            
            if should_sync:
                print('🔄 Force syncing slash commands...')
                synced = await asyncio.wait_for(bot.tree.sync(), timeout=60.0)
                print(f'✅ Synced {len(synced)} slash commands')
            else:
                print('ℹ️ Skipping command sync to avoid rate limits. Set FORCE_COMMAND_SYNC=true in .env if needed.')
                print('ℹ️ Commands should already be registered from previous runs.')
        else:
            print('ℹ️ No slash commands to sync')
    except discord.HTTPException as e:
        if e.status == 429:  # Rate limited
            print('⚠️ Rate limited by Discord. Skipping command sync.')
            print('ℹ️ Commands should already be registered from previous runs.')
        elif e.status == 400 and "Entry Point command" in str(e):
            print('⚠️ Entry Point command detected, skipping sync.')
        else:
            print(f'❌ Failed to sync commands: {e.status} - {e.text}')
    except asyncio.TimeoutError:
        print('⚠️ Command sync timed out. Continuing without sync...')
    except Exception as e:
        print(f'⚠️ Command sync failed: {e}. Continuing...')
    
    print(f'✅ {bot.user.name} is online!')
    print('ℹ️ Tip: If slash commands aren\'t working, set FORCE_COMMAND_SYNC=true in .env and restart once.')

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
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print('❌ No DISCORD_BOT_TOKEN found in .env file!')
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