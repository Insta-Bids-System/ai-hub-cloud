# 🚀 Quick Droplet Deployment Guide

## Prerequisites
- DigitalOcean account
- Domain pointing to Droplet (aihub.instabids.ai)
- Supabase project for PostgreSQL
- Redis connection string (you already have this)

## Step 1: Create Droplet
1. Go to DigitalOcean Console
2. Create Droplet with:
   - **Image**: Docker 20.04 (from Marketplace)
   - **Size**: Basic → Regular → $24/month (2 vCPU, 4GB RAM)
   - **Region**: NYC3
   - **Authentication**: SSH Key (recommended)
   - **Hostname**: instabids-ai-hub-droplet

## Step 2: Initial Setup
```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Download and run setup script
wget https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/setup-droplet.sh
chmod +x setup-droplet.sh
./setup-droplet.sh
```

## Step 3: Configure Environment
```bash
cd /root/ai-hub-cloud
nano .env.production
```

Add your actual values:
- Supabase PostgreSQL URL
- Redis connection string (from your existing cluster)
- Generate secure passwords

## Step 4: Deploy Services
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

## Step 5: Initialize Open WebUI
1. Access: http://YOUR_DROPLET_IP
2. Create admin account
3. Go to Settings → Account → API Keys
4. Generate new API key
5. Copy the key

## Step 6: Update MCP Configuration
```bash
# Add API key to environment
nano .env.production
# Add: OPENWEBUI_API_KEY=your-generated-key

# Restart MCP server
docker-compose -f docker-compose.production.yml restart mcp-server
```

## Step 7: Setup SSL
```bash
# Point domain to Droplet IP first!
certbot --nginx -d aihub.instabids.ai
```

## Step 8: Test Everything
- **Open WebUI**: https://aihub.instabids.ai
- **FileBrowser**: https://aihub.instabids.ai/files
- **VS Code**: https://aihub.instabids.ai/code
- **Direct Browse**: https://aihub.instabids.ai/workspace
- **MCP Tools**: https://aihub.instabids.ai/mcp/tools

## Persistent Directories
- `/data/workspace/` - All AI-generated code lives here
- `/data/openwebui/` - Open WebUI data (backup)
- `/data/backups/` - Daily automated backups

## Daily Maintenance
Backups run automatically at 2 AM. Check with:
```bash
ls -la /data/backups/
```

## Troubleshooting
```bash
# Check all logs
docker-compose -f docker-compose.production.yml logs

# Restart all services
docker-compose -f docker-compose.production.yml restart

# Stop everything
docker-compose -f docker-compose.production.yml down

# Start fresh
docker-compose -f docker-compose.production.yml up -d
```

## 🎉 Success Indicators
- All containers show as "Up" in docker ps
- Can access all web interfaces
- Files created by AI persist in /data/workspace
- No data loss on container restart
