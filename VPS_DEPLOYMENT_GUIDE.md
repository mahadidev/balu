# Discord Music Bot VPS Deployment Guide

## 🚀 Complete Setup Documentation

### Server Information
- **VPS Provider**: Hostinger
- **Server**: srv748072
- **User**: root
- **Bot Directory**: `/root/mahadi/balu`
- **Lavalink Port**: 2333
- **Bot Name**: Balu

---

## 📋 Prerequisites Setup Commands

### 1. Install Java 17
```bash
sudo apt update
sudo apt install openjdk-17-jdk

# Verify installation
java --version
```

### 2. Install Python Dependencies
```bash
# Install required Python packages
pip install discord.py wavelink aiohttp python-dotenv

# Or if using requirements.txt
pip install -r requirements.txt
```

---

## 🎵 Lavalink Server Setup

### 1. Download Lavalink
```bash
cd /root/mahadi/balu
wget https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar
```

### 2. Download YouTube Plugin
```bash
mkdir -p plugins
cd plugins
wget https://github.com/lavalink-devs/youtube-source/releases/latest/download/youtube-plugin-1.7.2.jar
cd ..
```

### 3. Create Lavalink Configuration
```bash
nano application.yml
```

**application.yml content:**
```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  plugins:
    - dependency: "dev.lavalink.youtube:youtube-plugin:1.7.2"
      repository: "https://maven.lavalink.dev/releases"
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      soundcloud: true
      bandcamp: true
      http: true
    playerUpdateInterval: 1
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    bufferDurationMs: 400
    frameBufferDurationMs: 2000
    opusEncodingQuality: 10

logging:
  level:
    root: INFO
    lavalink: INFO

plugins:
  youtube:
    enabled: true
    allowSearch: true
    allowDirectVideoIds: true
    allowDirectPlaylistIds: true
    clients:
      - MUSIC
      - WEB
      - ANDROID_TESTSUITE
      - TVHTML5EMBEDDED
```

### 4. Create Lavalink Service
```bash
sudo nano /etc/systemd/system/lavalink.service
```

**lavalink.service content:**
```ini
[Unit]
Description=Lavalink Audio Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/mahadi/balu
ExecStart=/usr/bin/java -Xmx2G -jar Lavalink.jar
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## 🤖 Discord Bot Setup

### 1. Create Environment File
```bash
nano .env
```

**Environment variables:**
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

### 2. Create Bot Service
```bash
sudo nano /etc/systemd/system/discord-bot.service
```

**discord-bot.service content:**
```ini
[Unit]
Description=Discord Music Bot
After=network.target lavalink.service
Requires=lavalink.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/mahadi/balu
ExecStart=/root/mahadi/balu/.venv/bin/python main.py
Restart=always
RestartSec=15
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## ⚡ Service Management Commands

### Enable and Start Services
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable lavalink
sudo systemctl enable discord-bot

# Start services
sudo systemctl start lavalink
sudo systemctl start discord-bot
```

### Check Service Status
```bash
# Check individual services
sudo systemctl status lavalink
sudo systemctl status discord-bot

# Check if auto-start is enabled
sudo systemctl is-enabled lavalink
sudo systemctl is-enabled discord-bot

# List enabled services
sudo systemctl list-unit-files --state=enabled | grep -E "(lavalink|discord-bot)"
```

### Restart Services
```bash
# Restart individual services
sudo systemctl restart lavalink
sudo systemctl restart discord-bot

# Restart both services
sudo systemctl restart lavalink discord-bot
```

### Stop Services
```bash
# Stop individual services
sudo systemctl stop lavalink
sudo systemctl stop discord-bot

# Stop both services
sudo systemctl stop lavalink discord-bot
```

---

## 📊 Monitoring and Logs

### View Real-time Logs
```bash
# Lavalink logs only
sudo journalctl -u lavalink -f

# Discord bot logs only
sudo journalctl -u discord-bot -f

# Both services logs
sudo journalctl -u lavalink -u discord-bot -f

# Last 50 lines of logs
sudo journalctl -u discord-bot -n 50
```

### Test Lavalink Connection
```bash
# Test if Lavalink is responding
curl http://localhost:2333/v4/info

# Should return JSON with server information
```

---

## 🔧 Troubleshooting Commands

### Common Issues

#### 1. Service Won't Start
```bash
# Check detailed status
sudo systemctl status lavalink --no-pager -l
sudo systemctl status discord-bot --no-pager -l

# Check configuration syntax
java -jar Lavalink.jar --check-config
```

#### 2. Bot Connection Issues
```bash
# Check if Lavalink is listening
netstat -tlnp | grep 2333
ss -tlnp | grep 2333

# Check firewall
sudo ufw status
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R root:root /root/mahadi/balu
sudo chmod +x /root/mahadi/balu/.venv/bin/python
```

### Update Bot Code
```bash
# Navigate to bot directory
cd /root/mahadi/balu

# Pull latest changes
git pull origin main

# Restart bot to apply changes
sudo systemctl restart discord-bot
```

---

## 🎮 Discord Bot Commands

### Available Commands
- `/play [song/url]` - Play music
- `/pause` - Pause current song
- `/resume` - Resume current song
- `/skip` - Skip to next song
- `/stop` - Stop music and clear queue
- `/queue` - Show current queue
- `/volume [0-100]` - Set volume
- `/controls` - Show music control buttons
- `/disconnect` - Disconnect from voice channel

### Traditional Commands (with !)
- `!play [song/url]`
- `!skip`
- `!pause`
- `!resume`
- `!stop`
- `!controls`

---

## 🔒 Security Notes

### Firewall Configuration
```bash
# Allow Lavalink port (if needed for external connections)
sudo ufw allow 2333

# Check firewall status
sudo ufw status
```

### Important Security Points
1. **Password Protection**: Lavalink uses password `"youshallnotpass"`
2. **Internal Network**: Bot connects to `localhost:2333` (secure)
3. **Environment Variables**: Discord token stored in `.env` file
4. **User Permissions**: Services run as root (adjust if needed)

---

## 📁 File Structure
```
/root/mahadi/balu/
├── main.py                    # Bot main file
├── .env                       # Environment variables (Discord token)
├── application.yml            # Lavalink configuration
├── Lavalink.jar              # Lavalink server
├── plugins/                   # Lavalink plugins
│   └── youtube-plugin-1.7.2.jar
├── music/                     # Bot music modules
│   ├── player.py             # Main music player
│   ├── playlist_manager.py   # Playlist management
│   ├── track_history.py      # Track history
│   └── controls.py           # Music controls UI
└── requirements.txt          # Python dependencies
```

---

## 🔄 Auto-Update Script (Optional)

### Create Update Script
```bash
nano /root/update-bot.sh
```

**Script content:**
```bash
#!/bin/bash
echo "🔄 Updating Discord Bot..."
cd /root/mahadi/balu
git pull origin main
echo "♻️ Restarting bot service..."
sudo systemctl restart discord-bot
echo "✅ Bot updated and restarted successfully!"
sudo systemctl status discord-bot --no-pager -l
```

```bash
# Make executable
chmod +x /root/update-bot.sh

# Run update
./update-bot.sh
```

---

## 📞 Quick Reference

### Emergency Commands
```bash
# If bot is stuck/unresponsive
sudo systemctl restart discord-bot

# If Lavalink issues
sudo systemctl restart lavalink

# Nuclear option - restart both
sudo systemctl restart lavalink discord-bot

# Check what's running
ps aux | grep -E "(java|python.*main.py)"
```

### System Info
```bash
# Check system resources
htop
df -h
free -h

# Check Java process
ps aux | grep java
```

---

## ✅ Deployment Checklist

- [x] Java 17 installed
- [x] Python dependencies installed
- [x] Lavalink.jar downloaded
- [x] YouTube plugin downloaded
- [x] application.yml configured
- [x] lavalink.service created and enabled
- [x] Discord bot token configured
- [x] discord-bot.service created and enabled
- [x] Both services auto-start on boot
- [x] Lavalink responding on port 2333
- [x] Bot connected to Lavalink
- [x] Bot online and responding to commands

---

## 📝 Notes

- **Server Reboot Safe**: Both services start automatically after reboot
- **Log Rotation**: Systemd handles log rotation automatically
- **Memory Usage**: Lavalink allocated 2GB RAM (`-Xmx2G`)
- **Restart Policy**: Services auto-restart if they crash
- **Last Updated**: November 9, 2025

---

**🎉 Your Discord Music Bot is fully deployed and operational on VPS!**

For support or issues, check the logs first:
```bash
sudo journalctl -u discord-bot -u lavalink -f
```