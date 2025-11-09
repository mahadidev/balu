#!/usr/bin/env python3
"""Simple test bot to verify Lavalink + Wavelink is working"""

import discord
import wavelink
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

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

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} is online!')
    print('🎵 Music bot with Lavalink ready!')

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"🎵 Wavelink Node connected: {payload.node!r}")

@bot.command()
async def test_play(ctx, *, query: str):
    """Test play command"""
    if not ctx.author.voice:
        await ctx.send("❌ You need to be in a voice channel!")
        return
    
    try:
        # Connect to voice channel
        player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        
        # Try multiple sources
        sources = [wavelink.TrackSource.SoundCloud, wavelink.TrackSource.YouTube, wavelink.TrackSource.YouTubeMusic]
        tracks = None
        
        for source in sources:
            try:
                tracks = await wavelink.Playable.search(query, source=source)
                if tracks:
                    await ctx.send(f"✅ Found tracks using {source}")
                    break
            except Exception as e:
                await ctx.send(f"❌ {source} failed: {e}")
                continue
        
        if not tracks:
            await ctx.send("❌ No tracks found from any source!")
            return
        
        track = tracks[0]
        await player.play(track)
        await ctx.send(f"🎵 Now playing: **{track.title}** by {track.author}")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def test_soundcloud(ctx, *, query: str):
    """Test SoundCloud specifically"""
    if not ctx.author.voice:
        await ctx.send("❌ You need to be in a voice channel!")
        return
    
    try:
        # Connect to voice channel
        player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        
        # Search SoundCloud specifically
        tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.SoundCloud)
        
        if not tracks:
            await ctx.send("❌ No SoundCloud tracks found!")
            return
        
        track = tracks[0]
        await player.play(track)
        await ctx.send(f"🎵 Now playing from SoundCloud: **{track.title}** by {track.author}")
        
    except Exception as e:
        await ctx.send(f"❌ SoundCloud Error: {e}")

if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('❌ No DISCORD_TOKEN found in .env file!')
    else:
        bot.run(token)