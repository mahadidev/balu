# Discord Bot VPS Deployment Guide

## 🚀 Complete Setup Documentation

### Server Information
- **VPS Provider**: Hostinger
- **Server**: srv748072
- **User**: root
- **Bot Directory**: `/root/mahadi/balu`
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
# Install required Python packages using requirements.txt
pip install -r requirements.txt
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
Description=Discord Bot
After=network.target

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

### Enable and Start Service
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable discord-bot

# Start service
sudo systemctl start discord-bot
```

### Check Service Status
```bash
# Check service status
sudo systemctl status discord-bot

# Check if auto-start is enabled
sudo systemctl is-enabled discord-bot

# List enabled services
sudo systemctl list-unit-files --state=enabled | grep discord-bot
```

### Restart Service
```bash
# Restart service
sudo systemctl restart discord-bot
```

### Stop Service
```bash
# Stop service
sudo systemctl stop discord-bot
```

---

## 📊 Monitoring and Logs

### View Real-time Logs
```bash
# Discord bot logs
sudo journalctl -u discord-bot -f

# Last 50 lines of logs
sudo journalctl -u discord-bot -n 50
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
1. **Environment Variables**: Discord token stored in `.env` file
2. **User Permissions**: Service runs as root (adjust if needed)
3. **File Permissions**: Ensure proper access to bot files

---

## 📁 File Structure
```
/root/mahadi/balu/
├── main.py                    # Bot main file
├── .env                       # Environment variables (Discord token)
├── core_commands.py           # Basic bot commands
├── requirements.txt           # Python dependencies
├── chat/                      # Global chat system
│   ├── commands.py           # Chat commands
│   └── chat_manager.py       # Chat management
└── database/                  # Database management
    ├── db_manager.py         # Database operations
    └── __init__.py
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

# Check what's running
ps aux | grep "python.*main.py"
```

### System Info
```bash
# Check system resources
htop
df -h
free -h

# Check bot process
ps aux | grep "python.*main.py"
```

---

## ✅ Deployment Checklist

- [x] Python dependencies installed
- [x] Discord bot token configured in .env
- [x] discord-bot.service created and enabled
- [x] Service auto-starts on boot
- [x] Bot online and responding to commands
- [x] Chat features functional

---

## 📝 Notes

- **Server Reboot Safe**: Service starts automatically after reboot
- **Log Rotation**: Systemd handles log rotation automatically
- **Restart Policy**: Service auto-restarts if it crashes
- **Last Updated**: November 10, 2025 - Removed music, move, and channel features

---

**🎉 Your Discord Bot is fully deployed and operational on VPS!**

For support or issues, check the logs first:
```bash
sudo journalctl -u discord-bot -f
```