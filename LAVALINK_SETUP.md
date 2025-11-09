# 🎵 Lavalink + Wavelink Music System

This bot now uses **Lavalink** with **Wavelink** for superior music performance and VPS compatibility!

## ✨ Benefits

- **No VPS YouTube issues** - Lavalink handles audio extraction server-side
- **Better performance** - Dedicated audio server
- **Multiple sources** - YouTube, YouTube Music, SoundCloud, Bandcamp
- **High quality audio** - Professional audio processing
- **Reliable on VPS** - No IP blocking issues

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Lavalink Server

```bash
python start_lavalink.py
```

This will:
- Check if Java is installed (install if needed)
- Download Lavalink automatically
- Start the Lavalink server on `http://127.0.0.1:2333`

### 3. Start Your Bot

```bash
python main.py
```

## 🎮 Slash Commands

The bot now uses modern slash commands:

- `/play <song>` - Play a song
- `/pause` - Pause current song
- `/resume` - Resume paused song
- `/skip` - Skip current song
- `/stop` - Stop and clear queue
- `/queue` - Show current queue
- `/volume <0-100>` - Set volume
- `/disconnect` - Leave voice channel

## 🔧 Configuration

### Lavalink Settings (application.yml)

```yaml
server:
  port: 2333
  address: 127.0.0.1

lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      soundcloud: true
      bandcamp: true
```

### Bot Settings

The bot automatically connects to Lavalink on startup. No additional configuration needed!

## 🏥 Troubleshooting

### Java Not Found
```bash
# macOS
brew install openjdk@17

# Ubuntu/Debian
sudo apt install openjdk-17-jdk

# CentOS/RHEL
sudo yum install java-17-openjdk-devel
```

### Lavalink Connection Failed
1. Make sure Lavalink is running: `python start_lavalink.py`
2. Check if port 2333 is available
3. Verify `application.yml` configuration

### No Audio Playing
1. Check bot has permission to connect to voice channels
2. Verify Lavalink server is responsive
3. Try different search terms or URLs

## 📁 File Structure

```
unbot/
├── music/                    # New Lavalink system
│   ├── __init__.py
│   └── player.py            # Wavelink music player
├── _music/                  # Old system (backup)
│   ├── commands.py
│   └── music_player.py
├── application.yml          # Lavalink configuration
├── start_lavalink.py       # Lavalink auto-setup
└── main.py                 # Updated bot entry point
```

## 🔄 Migration from Old System

The old music system has been moved to `_music/` as a backup. The new system:

- ✅ **Better VPS compatibility** - No more 403 Forbidden errors
- ✅ **Faster search** - Lavalink handles audio extraction
- ✅ **More reliable** - Professional audio server
- ✅ **Modern commands** - Slash commands with autocomplete
- ✅ **Multiple sources** - YouTube Music, SoundCloud, Bandcamp

## 🆘 Support

If you encounter issues:

1. **Check Lavalink logs** - Look for errors in the Lavalink console
2. **Verify Java version** - Requires Java 17 or higher
3. **Test connection** - Visit `http://127.0.0.1:2333` in browser
4. **Review bot logs** - Check Discord bot console for errors

## 🎉 Enjoy Your Music Bot!

Your music bot is now powered by professional-grade audio infrastructure. No more VPS YouTube issues! 🎵