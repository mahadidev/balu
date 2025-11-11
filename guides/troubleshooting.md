# Troubleshooting Guide - Global Chat System

Complete troubleshooting guide for common issues with the Global Chat System.

## 🔧 Quick Diagnostic Commands

### Check Overall System Health
```bash
# Check all services status
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Check resource usage
docker stats

# Test admin panel
curl http://localhost:8000/api/status
```

### Check Individual Services
```bash
# Discord Bot
docker-compose logs discord_bot
docker-compose restart discord_bot

# Admin Panel
docker-compose logs admin_panel
docker-compose restart admin_panel

# Database
docker-compose logs postgres
docker-compose exec postgres pg_isready -U postgres

# Redis Cache
docker-compose logs redis
docker-compose exec redis redis-cli ping
```

---

## 🤖 Discord Bot Issues

### Issue: Bot Not Responding to Messages

**Symptoms:**
- Bot appears online but doesn't react to messages
- No messages appearing in other servers
- Bot logs show no activity

**Diagnosis:**
```bash
# Check bot logs
docker-compose logs discord_bot

# Check bot status
docker-compose ps discord_bot

# Check environment variables
cat .env | grep DISCORD_BOT_TOKEN
```

**Solutions:**

1. **Invalid Discord Token**
```bash
# Verify token format (should start with MTAx, Nzk, etc.)
echo $DISCORD_BOT_TOKEN | head -c 20

# Regenerate token at https://discord.com/developers/applications
# Update .env file
nano .env
docker-compose restart discord_bot
```

2. **Missing Permissions**
```bash
# Check bot permissions in Discord server:
# - Send Messages ✅
# - Read Message History ✅
# - Use Slash Commands ✅
# - Message Content Intent ✅ (in Developer Portal)
```

3. **Bot Not in Correct Channels**
```bash
# Check if channels are registered
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/servers/channels

# Register channels through admin panel
# Or use Discord commands: /register
```

### Issue: Bot Shows Offline

**Diagnosis:**
```bash
# Check if bot container is running
docker-compose ps discord_bot

# Check bot logs for connection errors
docker-compose logs discord_bot | grep -i error
```

**Solutions:**

1. **Container Not Running**
```bash
# Start bot container
docker-compose up -d discord_bot

# Check startup logs
docker-compose logs -f discord_bot
```

2. **Network Connection Issues**
```bash
# Test internet connectivity from container
docker-compose exec discord_bot ping 8.8.8.8

# Restart networking
docker-compose down
docker-compose up -d
```

### Issue: Bot Crashes on Startup

**Diagnosis:**
```bash
# Check crash logs
docker-compose logs discord_bot

# Check for Python errors
docker-compose logs discord_bot | grep -i "error\|exception\|traceback"
```

**Common Solutions:**

1. **Import Errors**
```bash
# Rebuild container
docker-compose build --no-cache discord_bot
docker-compose up -d discord_bot
```

2. **Database Connection Error**
```bash
# Ensure database is running first
docker-compose up -d postgres
sleep 30
docker-compose up -d discord_bot
```

---

## 🌐 Admin Panel Issues

### Issue: Admin Panel Not Accessible

**Symptoms:**
- Cannot reach http://localhost:8000
- "Connection refused" error
- 404 error on admin panel

**Diagnosis:**
```bash
# Check if admin panel is running
docker-compose ps admin_panel

# Check port binding
docker-compose port admin_panel 8000

# Test from localhost
curl http://localhost:8000/api/status
```

**Solutions:**

1. **Container Not Running**
```bash
# Start admin panel
docker-compose up -d admin_panel

# Check startup logs
docker-compose logs -f admin_panel
```

2. **Port Conflict**
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill conflicting process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

3. **Firewall Issues (VPS)**
```bash
# Check firewall status
sudo ufw status

# Allow port 8000
sudo ufw allow 8000/tcp

# Test from external IP
curl http://your-vps-ip:8000/api/status
```

### Issue: Admin Panel Loads but Shows Errors

**Symptoms:**
- Page loads but shows "Error 500"
- API calls failing
- WebSocket not connecting

**Diagnosis:**
```bash
# Check backend logs
docker-compose logs admin_panel

# Check API health
curl http://localhost:8000/api/status

# Test database connection
curl http://localhost:8000/api/rooms
```

**Solutions:**

1. **Database Connection Issues**
```bash
# Check if postgres is healthy
docker-compose ps postgres

# Test database connection
docker-compose exec postgres pg_isready -U postgres

# Restart admin panel
docker-compose restart admin_panel
```

2. **Frontend Build Issues**
```bash
# Rebuild frontend
cd admin/frontend
npm run build
npm run copy-build

# Or rebuild entire container
docker-compose build --no-cache admin_panel
docker-compose up -d admin_panel
```

### Issue: Cannot Login to Admin Panel

**Symptoms:**
- "Invalid username or password" error
- Login form not responding

**Diagnosis:**
```bash
# Check authentication endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Check environment variables
cat .env | grep -E "ADMIN_USERNAME|ADMIN_PASSWORD"
```

**Solutions:**

1. **Wrong Credentials**
```bash
# Check .env file
cat .env | grep ADMIN

# Default credentials are:
# Username: admin
# Password: admin123

# Update if needed
nano .env
docker-compose restart admin_panel
```

2. **JWT Secret Key Issues**
```bash
# Ensure SECRET_KEY is set and long enough (32+ characters)
cat .env | grep SECRET_KEY

# Generate new secret key
openssl rand -hex 32

# Update .env and restart
nano .env
docker-compose restart admin_panel
```

---

## 🗄️ Database Issues

### Issue: Database Connection Failed

**Symptoms:**
- "Connection refused" errors
- "Database not found" errors
- Services can't start

**Diagnosis:**
```bash
# Check postgres status
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U postgres -d globalchat
```

**Solutions:**

1. **Postgres Not Running**
```bash
# Start postgres
docker-compose up -d postgres

# Wait for startup
sleep 30

# Check health
docker-compose exec postgres pg_isready -U postgres
```

2. **Database Not Initialized**
```bash
# Run database migration
python scripts/migrate.py

# Or recreate database
docker-compose down -v postgres
docker-compose up -d postgres
sleep 30
python scripts/migrate.py
```

3. **Wrong Database Credentials**
```bash
# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Should match POSTGRES_PASSWORD
cat .env | grep POSTGRES_PASSWORD

# Fix if needed
nano .env
docker-compose restart
```

### Issue: Database Performance Issues

**Symptoms:**
- Slow API responses
- High CPU usage from postgres
- Long query times

**Diagnosis:**
```bash
# Check postgres resource usage
docker stats | grep postgres

# Check active connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
docker-compose exec postgres psql -U postgres -c "SELECT query, query_start FROM pg_stat_activity WHERE state = 'active';"
```

**Solutions:**

1. **Increase Database Resources**
```yaml
# Edit docker-compose.yml
postgres:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

2. **Optimize Database**
```bash
# Vacuum database
docker-compose exec postgres psql -U postgres -d globalchat -c "VACUUM ANALYZE;"

# Restart postgres
docker-compose restart postgres
```

---

## ⚡ Redis Cache Issues

### Issue: Redis Connection Failed

**Symptoms:**
- "Redis connection error" in logs
- Slow admin panel responses
- Cache not working

**Diagnosis:**
```bash
# Check redis status
docker-compose ps redis

# Test redis connection
docker-compose exec redis redis-cli ping

# Check redis logs
docker-compose logs redis
```

**Solutions:**

1. **Redis Not Running**
```bash
# Start redis
docker-compose up -d redis

# Test connection
docker-compose exec redis redis-cli ping
# Should respond: PONG
```

2. **Memory Issues**
```bash
# Check redis memory usage
docker-compose exec redis redis-cli info memory

# Clear cache if needed
docker-compose exec redis redis-cli flushall

# Restart redis
docker-compose restart redis
```

### Issue: Cache Not Working

**Diagnosis:**
```bash
# Test cache operations
docker-compose exec redis redis-cli
> set test_key "test_value"
> get test_key
> keys *
> exit
```

**Solutions:**

1. **Clear Cache**
```bash
# Clear all cache
docker-compose exec redis redis-cli flushall

# Restart services to rebuild cache
docker-compose restart admin_panel discord_bot
```

---

## 🌐 Network and Connectivity Issues

### Issue: Services Can't Communicate

**Symptoms:**
- "Connection refused" between containers
- Database connection timeouts
- Redis connection failures

**Diagnosis:**
```bash
# Check docker network
docker network ls

# Inspect network
docker network inspect unbot_globalchat_network

# Check container connectivity
docker-compose exec admin_panel ping postgres
docker-compose exec admin_panel ping redis
```

**Solutions:**

1. **Network Issues**
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

2. **Service Discovery Issues**
```bash
# Check service names in docker-compose.yml
# Containers should use service names (postgres, redis) not localhost

# Restart all services
docker-compose restart
```

### Issue: External Access Problems (VPS)

**Symptoms:**
- Cannot access admin panel from internet
- "Connection timeout" from external IP
- Works locally but not externally

**Diagnosis:**
```bash
# Test from VPS itself
curl http://localhost:8000/api/status

# Test from external
curl http://your-vps-ip:8000/api/status

# Check firewall
sudo ufw status
```

**Solutions:**

1. **Firewall Configuration**
```bash
# Allow admin panel port
sudo ufw allow 8000/tcp

# Check iptables rules
sudo iptables -L

# For cloud providers, check security groups
```

2. **Binding Issues**
```bash
# Ensure admin panel binds to all interfaces (0.0.0.0)
# Check docker-compose.yml ports configuration:
# ports:
#   - "8000:8000"  # Correct
# Not:
#   - "127.0.0.1:8000:8000"  # Only localhost
```

---

## 🚀 Performance Issues

### Issue: High Resource Usage

**Symptoms:**
- VPS running out of memory
- High CPU usage
- Slow responses

**Diagnosis:**
```bash
# Check overall system resources
htop
free -h
df -h

# Check container resources
docker stats

# Check service logs for errors
docker-compose logs --tail=100 | grep -i error
```

**Solutions:**

1. **Optimize Resource Limits**
```yaml
# Edit docker-compose.yml
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
```

2. **Clear Logs and Data**
```bash
# Clear old logs
docker-compose logs --tail=0

# Clean docker system
docker system prune

# Clear cache
docker-compose exec redis redis-cli flushall
```

### Issue: Memory Leaks

**Symptoms:**
- Memory usage continuously growing
- Services getting killed by OOM killer
- System becomes unresponsive

**Diagnosis:**
```bash
# Monitor memory over time
watch -n 5 'docker stats --no-stream'

# Check system memory
cat /proc/meminfo

# Check for OOM kills
dmesg | grep -i "killed process"
```

**Solutions:**

1. **Add Swap Space**
```bash
# Create swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

2. **Restart Services Regularly**
```bash
# Add to crontab for nightly restart
crontab -e
# Add: 0 3 * * * cd /path/to/unbot && docker-compose restart
```

---

## 🔐 Security Issues

### Issue: Unauthorized Access Attempts

**Symptoms:**
- Failed login attempts in logs
- Unknown IP addresses in access logs
- Suspicious activity

**Diagnosis:**
```bash
# Check admin panel logs for failed logins
docker-compose logs admin_panel | grep -i "login\|auth"

# Check system auth logs
sudo tail -f /var/log/auth.log

# Check network connections
sudo netstat -tulpn | grep :8000
```

**Solutions:**

1. **Enable Fail2Ban**
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure for admin panel
sudo nano /etc/fail2ban/jail.local
# Add custom rule to monitor admin panel logs
```

2. **Change Default Credentials**
```bash
# Update admin credentials in .env
nano .env
# Change ADMIN_USERNAME and ADMIN_PASSWORD

# Restart admin panel
docker-compose restart admin_panel
```

3. **Restrict Access by IP (Optional)**
```bash
# Allow only specific IPs
sudo ufw delete allow 8000/tcp
sudo ufw allow from YOUR_IP to any port 8000
```

---

## 🧰 Emergency Recovery

### Complete System Reset (DANGER: Loses All Data)

**When to use:**
- System is completely broken
- Multiple critical errors
- Data corruption suspected

**Steps:**
```bash
# 1. Backup what you can
cp .env .env.backup
docker-compose exec postgres pg_dump -U postgres globalchat > emergency_backup.sql 2>/dev/null || true

# 2. Stop and remove everything
docker-compose down -v
docker system prune -a -f

# 3. Restart fresh
docker-compose up --build -d

# 4. Restore data if backup exists
if [ -f emergency_backup.sql ]; then
  sleep 30
  docker-compose exec -T postgres psql -U postgres globalchat < emergency_backup.sql
fi
```

### Partial Recovery

**Reset only specific service:**
```bash
# Reset just the bot
docker-compose stop discord_bot
docker-compose rm discord_bot
docker-compose up -d discord_bot

# Reset admin panel
docker-compose stop admin_panel
docker-compose rm admin_panel
docker-compose build --no-cache admin_panel
docker-compose up -d admin_panel

# Reset database (DANGER: Loses data)
docker-compose down postgres
docker volume rm unbot_postgres_data
docker-compose up -d postgres
sleep 30
python scripts/migrate.py
```

---

## 📞 Getting Help

### Collect Debug Information

Before asking for help, collect this information:

```bash
# Create debug report
echo "=== SYSTEM INFO ===" > debug_report.txt
uname -a >> debug_report.txt
docker --version >> debug_report.txt
docker-compose --version >> debug_report.txt

echo -e "\n=== SERVICE STATUS ===" >> debug_report.txt
docker-compose ps >> debug_report.txt

echo -e "\n=== RECENT LOGS ===" >> debug_report.txt
docker-compose logs --tail=50 >> debug_report.txt

echo -e "\n=== ENVIRONMENT (SANITIZED) ===" >> debug_report.txt
grep -v "TOKEN\|PASSWORD\|SECRET" .env >> debug_report.txt

echo -e "\n=== RESOURCE USAGE ===" >> debug_report.txt
docker stats --no-stream >> debug_report.txt
```

### Common Log Patterns

**Look for these patterns in logs:**

```bash
# Connection issues
docker-compose logs | grep -i "connection\|connect"

# Authentication issues
docker-compose logs | grep -i "auth\|login\|token"

# Database issues
docker-compose logs | grep -i "postgres\|database\|sql"

# Python/JavaScript errors
docker-compose logs | grep -i "error\|exception\|traceback"
```

---

## ✅ Health Check Checklist

Use this checklist to verify system health:

### Basic Health Check
- [ ] All services show "Up" in `docker-compose ps`
- [ ] Admin panel responds to http://localhost:8000/api/status
- [ ] Database accepts connections
- [ ] Redis responds to ping
- [ ] Discord bot shows as online

### Functional Health Check
- [ ] Can login to admin panel
- [ ] Can create a test room
- [ ] Can register a Discord channel
- [ ] Bot responds to messages in Discord
- [ ] Messages appear in other registered channels
- [ ] WebSocket updates work in admin panel

### Performance Health Check
- [ ] API responses < 1 second
- [ ] Memory usage < 80% of available
- [ ] Disk usage < 85% of available
- [ ] No error messages in logs
- [ ] CPU usage reasonable during normal operation

---

**🔧 Remember: Most issues can be solved by checking logs first!**

**Quick Fix Commands:**
```bash
# Restart everything
docker-compose restart

# View all logs
docker-compose logs -f

# Check status
docker-compose ps

# Emergency reset (loses data!)
docker-compose down -v && docker-compose up --build -d
```