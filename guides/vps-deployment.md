# VPS Deployment Guide - Global Chat System

Complete guide for deploying the Global Chat System on a Virtual Private Server (VPS) for production use.

## 🖥️ VPS Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: 2GB (4GB+ recommended for 50+ servers)
- **CPU**: 2 cores (4 cores recommended)
- **Storage**: 20GB SSD (50GB+ recommended)
- **Network**: Stable internet connection
- **Ports**: 22 (SSH), 8000 (Admin Panel)

### Recommended VPS Providers
- **DigitalOcean**: $12/month (2GB RAM, 2 vCPUs)
- **Linode**: $12/month (2GB RAM, 2 vCPUs)
- **Vultr**: $12/month (2GB RAM, 2 vCPUs)
- **AWS EC2**: t3.small instance
- **Google Cloud**: e2-small instance

---

## 🚀 Quick VPS Setup

### Step 1: Connect to Your VPS
```bash
# SSH into your VPS (replace with your details)
ssh root@your-vps-ip

# Or if using a specific user
ssh username@your-vps-ip

# Or with SSH key
ssh -i your-key.pem username@your-vps-ip
```

### Step 2: Quick Install Script
```bash
# Download and run the quick install script
curl -fsSL https://raw.githubusercontent.com/your-repo/unbot/main/scripts/vps-install.sh | bash

# Or manual installation (recommended)
# Follow the manual steps below
```

### Step 3: Upload Your Project
```bash
# Option 1: Using Git (Recommended)
git clone https://github.com/your-username/unbot.git
cd unbot

# Option 2: Upload via SCP from local machine
# Run this from your local machine:
# scp -r /Users/mahadihasan/Desktop/unbot username@your-vps-ip:~/
```

### Step 4: Configure and Deploy
```bash
# Configure environment
cp .env.example .env
nano .env  # Add your Discord token and secure passwords

# Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

---

## 🛠️ Manual VPS Setup (Detailed)

### Step 1: Update System
```bash
# For Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano

# For CentOS/RHEL
sudo yum update -y
sudo yum install -y curl wget git nano

# For newer CentOS/RHEL (dnf)
sudo dnf update -y
sudo dnf install -y curl wget git nano
```

### Step 2: Install Docker

#### Ubuntu/Debian Installation
```bash
# Remove old Docker versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### CentOS/RHEL Installation
```bash
# Remove old Docker versions
sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# Install dependencies
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# Add Docker repository
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### Alternative: Quick Docker Install (All Distributions)
```bash
# Universal Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add user to docker group (replace 'username' with your username)
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker
```

### Step 3: Install Docker Compose
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink (optional)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify installation
docker-compose --version
```

### Step 4: Configure Firewall

#### Ubuntu/Debian (ufw)
```bash
# Install ufw if not installed
sudo apt install -y ufw

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow Admin Panel
sudo ufw allow 8000/tcp

# Optional: Allow HTTP/HTTPS if using Nginx
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

#### CentOS/RHEL (firewalld)
```bash
# Start and enable firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow SSH
sudo firewall-cmd --permanent --add-service=ssh

# Allow Admin Panel
sudo firewall-cmd --permanent --add-port=8000/tcp

# Optional: Allow HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

### Step 5: Create Application User (Optional but Recommended)
```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash globalchat
sudo usermod -aG docker globalchat

# Switch to application user
sudo su - globalchat

# Set up SSH access for app user (if needed)
mkdir -p ~/.ssh
# Copy your SSH public key to ~/.ssh/authorized_keys
```

---

## 📦 Deploy Application on VPS

### Step 1: Get Application Code

#### Method 1: Clone from Git
```bash
# Clone repository
git clone https://github.com/your-username/unbot.git
cd unbot

# Or if using a specific branch
git clone -b main https://github.com/your-username/unbot.git
cd unbot
```

#### Method 2: Upload via SCP
```bash
# From your local machine, upload the project
scp -r /Users/mahadihasan/Desktop/unbot username@your-vps-ip:~/

# Then on VPS
cd ~/unbot
```

#### Method 3: Download Release Archive
```bash
# Download and extract release
wget https://github.com/your-username/unbot/archive/main.zip
unzip main.zip
mv unbot-main unbot
cd unbot
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file with production values
nano .env
```

**Production .env Configuration:**
```bash
# Discord Bot Token (REQUIRED)
DISCORD_BOT_TOKEN=your_actual_bot_token_here

# Secure Database Password (REQUIRED)
POSTGRES_PASSWORD=VerySecurePassword123!@#

# Strong Admin Panel Security (REQUIRED)
SECRET_KEY=your-super-secret-production-key-must-be-at-least-32-characters-long
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecureAdminPassword123!@#

# Production Settings
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration for your domain/IP
ALLOWED_ORIGINS=http://your-vps-ip:8000,https://yourdomain.com

# Optional: Custom database settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Optional: Redis settings
REDIS_MAX_CONNECTIONS=20

# Optional: Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Step 3: Deploy Application

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy in production mode
./scripts/deploy.sh production

# Or deploy with backup if you have existing data
./scripts/deploy.sh production true
```

### Step 4: Verify Deployment

```bash
# Check service status
docker-compose ps

# Expected output:
# globalchat_postgres   Up (healthy)
# globalchat_redis      Up (healthy)
# globalchat_bot        Up
# globalchat_admin      Up

# Check logs
docker-compose logs -f --tail=50

# Test admin panel
curl http://localhost:8000/api/status
```

---

## 🌐 Domain Setup (Optional)

### Step 1: Domain Configuration

If you have a domain name, you can set it up with your VPS:

```bash
# Point your domain A record to your VPS IP
# Example DNS settings:
# A record: yourdomain.com -> your-vps-ip
# A record: www.yourdomain.com -> your-vps-ip
```

### Step 2: Nginx Reverse Proxy Setup

```bash
# Create nginx configuration directory
mkdir -p nginx

# Create nginx configuration
nano nginx/nginx.conf
```

**Nginx Configuration:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server admin_panel:8000;
    }

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

### Step 3: Deploy with Nginx

```bash
# Deploy with nginx proxy
docker-compose --profile production up -d

# Or modify your .env to enable nginx
echo "USE_NGINX=true" >> .env
./scripts/deploy.sh production
```

### Step 4: SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Update nginx config to use SSL
nano nginx/nginx.conf
```

---

## 🔧 Production Optimization

### Step 1: System Optimization

```bash
# Increase file limits
echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Step 2: Docker Resource Limits

Edit `docker-compose.yml` to add resource limits:

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  admin_panel:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  discord_bot:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Step 3: Monitoring Setup

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor in real-time
htop                    # CPU and memory usage
docker stats           # Container resource usage
docker-compose logs -f # Application logs
```

---

## 💾 Backup and Maintenance

### Step 1: Automated Backup Script

```bash
# Create backup script
nano ~/backup-globalchat.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/home/backup/globalchat"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

cd ~/unbot

# Backup database
docker-compose exec -T postgres pg_dump -U postgres globalchat > $BACKUP_DIR/database_$DATE.sql

# Backup volumes
docker run --rm -v unbot_postgres_data:/data -v $BACKUP_DIR:/backup busybox tar czf /backup/postgres_data_$DATE.tar.gz -C /data .
docker run --rm -v unbot_redis_data:/data -v $BACKUP_DIR:/backup busybox tar czf /backup/redis_data_$DATE.tar.gz -C /data .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make script executable
chmod +x ~/backup-globalchat.sh

# Test backup
~/backup-globalchat.sh

# Schedule daily backup (crontab)
crontab -e
# Add this line for daily backup at 2 AM:
# 0 2 * * * /home/username/backup-globalchat.sh
```

### Step 2: Update Script

```bash
# Create update script
nano ~/update-globalchat.sh
```

**Update Script:**
```bash
#!/bin/bash
cd ~/unbot

echo "Stopping services..."
docker-compose down

echo "Backing up current version..."
cp .env .env.backup
~/backup-globalchat.sh

echo "Pulling latest code..."
git pull origin main

echo "Rebuilding and starting services..."
docker-compose build --no-cache
docker-compose up -d

echo "Checking service status..."
sleep 10
docker-compose ps

echo "Update completed!"
```

```bash
# Make script executable
chmod +x ~/update-globalchat.sh
```

---

## 📊 Monitoring and Alerts

### Step 1: Service Health Monitoring

```bash
# Create health check script
nano ~/check-services.sh
```

**Health Check Script:**
```bash
#!/bin/bash
cd ~/unbot

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "ERROR: Some services are not running!"
    docker-compose ps
    exit 1
fi

# Check admin panel response
if ! curl -f http://localhost:8000/api/status > /dev/null 2>&1; then
    echo "ERROR: Admin panel not responding!"
    exit 1
fi

echo "All services healthy"
```

### Step 2: Log Monitoring

```bash
# Monitor error logs
docker-compose logs --tail=100 | grep -i error

# Monitor specific service
docker-compose logs -f discord_bot

# Check disk usage
df -h

# Check memory usage
free -h

# Check system load
uptime
```

---

## 🔐 Security Hardening

### Step 1: SSH Security

```bash
# Backup SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH configuration
sudo nano /etc/ssh/sshd_config
```

**SSH Security Settings:**
```
# Disable root login
PermitRootLogin no

# Use SSH keys only
PasswordAuthentication no
PubkeyAuthentication yes

# Change default port (optional)
Port 2222

# Limit users
AllowUsers your-username

# Disable X11 forwarding
X11Forwarding no
```

```bash
# Restart SSH service
sudo systemctl restart sshd

# Test connection with new settings before closing current session!
```

### Step 2: Fail2Ban Setup

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure fail2ban for SSH
sudo nano /etc/fail2ban/jail.local
```

**Fail2Ban Configuration:**
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
```

```bash
# Start and enable fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Check status
sudo fail2ban-client status
```

### Step 3: Environment Security

```bash
# Set secure permissions on environment file
chmod 600 .env

# Regular security updates
sudo apt update && sudo apt upgrade -y

# Remove unused packages
sudo apt autoremove -y
```

---

## 🚨 Troubleshooting

### Common VPS Issues

#### Issue: "Cannot connect to VPS"
```bash
# Check if SSH service is running
sudo systemctl status ssh

# Check firewall
sudo ufw status

# Check if port 22 is open
sudo netstat -tulpn | grep :22

# From local machine, test connection
ssh -v username@your-vps-ip
```

#### Issue: "Docker permission denied"
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker

# Test docker command
docker run hello-world
```

#### Issue: "Port 8000 not accessible"
```bash
# Check if admin panel is running
docker-compose ps admin_panel

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp

# Check if port is in use
sudo netstat -tulpn | grep :8000

# Check from VPS itself
curl http://localhost:8000/api/status
```

#### Issue: "Out of disk space"
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Remove old logs
docker-compose logs --tail=0

# Clear system logs
sudo journalctl --vacuum-size=100M
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage
free -h
docker stats

# Restart services
docker-compose restart

# Add swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### High CPU Usage
```bash
# Monitor processes
htop

# Check Docker containers
docker stats

# Scale down if needed
docker-compose scale discord_bot=1 admin_panel=1
```

---

## ✅ VPS Deployment Checklist

### Initial Setup
- [ ] VPS created and accessible via SSH
- [ ] System updated and secured
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured (ports 22, 8000)
- [ ] Application user created (optional)

### Application Deployment
- [ ] Project code uploaded/cloned
- [ ] .env file configured with secure values
- [ ] Deploy script executed successfully
- [ ] All services showing "Up" status
- [ ] Admin panel accessible from internet

### Security
- [ ] SSH keys configured, password auth disabled
- [ ] Firewall rules in place
- [ ] Strong passwords in .env file
- [ ] Regular security updates scheduled
- [ ] Fail2ban installed and configured

### Monitoring
- [ ] Backup script created and scheduled
- [ ] Update script created
- [ ] Health monitoring in place
- [ ] Log monitoring set up
- [ ] Resource monitoring configured

### Final Tests
- [ ] Admin panel loads from external IP
- [ ] Can login to admin panel
- [ ] Discord bot is online and responds
- [ ] Can create rooms and register channels
- [ ] Messages flow between Discord servers
- [ ] WebSocket updates work in admin panel

---

**🎉 Congratulations! Your Global Chat System is now running on a VPS!**

**Access your admin panel at: http://your-vps-ip:8000**
**Remember to change default passwords and keep your system updated!**

**Next Steps:**
1. Set up your Discord bot in servers
2. Create rooms in the admin panel
3. Register Discord channels to rooms
4. Monitor the system and enjoy cross-server chat!