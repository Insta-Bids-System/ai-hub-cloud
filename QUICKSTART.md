# 🚀 Quick Start Guide - InstaBids AI Hub Persistent Setup

## Your Droplet is Ready! Here's what to do:

### 1️⃣ Connect to Your Droplet

**Option A: Use DigitalOcean Web Console (Easiest)**
1. Go to [DigitalOcean Dashboard](https://cloud.digitalocean.com/droplets)
2. Click on `ai-hub-persistent` (159.65.36.162)
3. Click "Access" → "Launch Droplet Console"
4. Login as `root` with your password

**Option B: SSH (if you have key setup)**
```bash
ssh root@159.65.36.162
```

### 2️⃣ Run the Automated Setup Script

Once connected, run this single command:

```bash
curl -sSL https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/setup-persistent.sh | bash
```

This script will:
- ✅ Create all persistent directories
- ✅ Install Docker and required tools
- ✅ Clone your repository
- ✅ Set up automated backups
- ✅ Create configuration templates

### 3️⃣ Configure Your Credentials

After the script completes, edit the environment file:

```bash
cd /root/ai-hub-cloud
nano .env.production
```

Add these values:
1. **Supabase Keys** - Get from [Supabase Dashboard](https://app.supabase.com/project/ybxiqfyzexwfqyvmzypa/settings/api)
2. **Redis Connection** - Your DigitalOcean Redis cluster connection string
3. **Passwords** - Change the default passwords for FileBrowser and Code Server

### 4️⃣ Deploy All Services

```bash
# Deploy everything
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose ps

# View logs if needed
docker-compose logs -f
```

### 5️⃣ Initialize Open WebUI

1. Open browser to: http://159.65.36.162
2. Create your admin account
3. Go to Settings → Account → API Keys
4. Generate an API key
5. Add it to `.env.production` as `OPENWEBUI_API_KEY=your-key-here`
6. Restart services: `docker-compose restart`

### 6️⃣ Access Your Services

- **Open WebUI**: http://159.65.36.162
- **FileBrowser**: http://159.65.36.162/files (login with credentials from .env)
- **Workspace Browser**: http://159.65.36.162/workspace
- **MCP Server**: http://159.65.36.162/mcp
- **VS Code** (optional): http://159.65.36.162/code

### 7️⃣ Test Persistence

1. Create a chat in Open WebUI
2. Have AI create a file using MCP tools
3. Check FileBrowser to see the file
4. Restart everything: `docker-compose restart`
5. Verify chat and files still exist ✅

### 8️⃣ Setup SSL (Optional but Recommended)

After DNS is pointed to your droplet:

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d aihub.instabids.ai

# Auto-renewal is configured automatically
```

## 📊 What You Get

1. **100% Data Persistence**
   - Open WebUI data in `/data/openwebui`
   - AI-created files in `/data/workspace`
   - Automated daily backups in `/data/backups`

2. **Triple Redundancy**
   - Local storage on droplet
   - Optional Supabase database backup
   - Automated GitHub repository backups

3. **Visual Access**
   - FileBrowser for easy file management
   - Direct workspace browsing
   - Optional VS Code in browser

## 🆘 Troubleshooting

**Services not starting?**
```bash
docker-compose logs open-webui
docker-compose logs mcp-server
```

**Need to restart everything?**
```bash
docker-compose down
docker-compose up -d
```

**Check disk space:**
```bash
df -h
```

**View running containers:**
```bash
docker ps
```

## 🎉 Success Indicators

- ✅ All containers show "Up" status
- ✅ Can access Open WebUI and create account
- ✅ Files created by AI appear in FileBrowser
- ✅ Data persists after container restarts
- ✅ Backups created daily in `/data/backups`

## 📞 Next Steps

1. Point DNS to your droplet IP
2. Setup SSL certificate
3. Configure automated monitoring
4. Start building with your bulletproof AI system!

---

**Remember:** This setup ensures you NEVER lose data again. Everything is persisted in three places with automated backups!
