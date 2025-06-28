# 🚀 InstaBids AI Hub - Complete Droplet Build Plan

## Overview
Transform the current DigitalOcean App Platform deployment into a persistent Droplet-based system with full server-side code storage capabilities.

## Current State Assessment

### ✅ What We Have:
1. **DigitalOcean Resources**:
   - App Platform: `instabids-ai-hub-v2` (currently running)
   - Redis Cluster: `instabids-redis-shared` (Valkey 8, online)
   - Existing connection string in your environment

2. **Supabase Project**: `instabids-ai-hub`
   - PostgreSQL ready for Open WebUI data
   - Connection details in your Supabase dashboard

3. **GitHub Repository**: `Insta-Bids-System/ai-hub-cloud`
   - Docker Compose configuration ready
   - MCP Server implementation complete
   - Nginx configuration prepared

### ❌ What's Missing:
- Persistent file storage for AI-generated code
- Connection to external databases
- Visual file management tools

## 🏗️ Build Plan

### Phase 1: Create DigitalOcean Droplet

#### Step 1.1: Create Droplet
```bash
# Via DigitalOcean Console or CLI:
doctl compute droplet create instabids-ai-hub-droplet \
  --size s-2vcpu-4gb \
  --image docker-20-04 \
  --region nyc3 \
  --ssh-keys YOUR_SSH_KEY_ID
```

**Specifications**:
- Size: 2 vCPU, 4GB RAM ($24/month)
- OS: Ubuntu 20.04 with Docker pre-installed
- Region: NYC3 (same as your Redis)
- Storage: 80GB SSD

#### Step 1.2: Point Domain
Update DNS for `aihub.instabids.ai` to point to new Droplet IP

### Phase 2: Setup Persistent Storage Structure

#### Step 2.1: SSH into Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

#### Step 2.2: Create Directory Structure
```bash
# Create persistent directories
mkdir -p /data/workspace          # AI-generated code lives here
mkdir -p /data/openwebui          # Open WebUI data (backup)
mkdir -p /data/nginx/ssl          # SSL certificates
mkdir -p /data/filebrowser        # FileBrowser database
mkdir -p /data/backups            # Automated backups

# Set permissions
chmod -R 755 /data
```

### Phase 3: Configure Services

#### Step 3.1: Clone Repository
```bash
cd /root
git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git
cd ai-hub-cloud
```

#### Step 3.2: Create Enhanced Docker Compose
```yaml
# /root/ai-hub-cloud/docker-compose.production.yml
version: '3.8'

networks:
  ai-hub-net:
    driver: bridge

services:
  # Open WebUI with Supabase PostgreSQL
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    environment:
      # Use Supabase PostgreSQL
      - DATABASE_URL=${SUPABASE_DATABASE_URL}
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
      - ENV=dev
      - ENABLE_API_KEY=true
      - DATA_DIR=/app/backend/data
      # Use DigitalOcean Redis
      - REDIS_URL=${DO_REDIS_URL}
    volumes:
      - /data/openwebui:/app/backend/data
      - /data/workspace:/app/workspace  # AI can access workspace
    networks:
      - ai-hub-net
    restart: unless-stopped

  # MCP Server with File System Access
  mcp-server:
    build: ./mcp-server
    container_name: mcp-server
    environment:
      - OPENWEBUI_URL=http://open-webui:8080
      - OPENWEBUI_API_KEY=${OPENWEBUI_API_KEY}
      - WORKSPACE_PATH=/app/workspace
      - REDIS_URL=${DO_REDIS_URL}
    volumes:
      - /data/workspace:/app/workspace  # Read/write AI code
    networks:
      - ai-hub-net
    restart: unless-stopped

  # FileBrowser - Visual File Management
  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    environment:
      - FB_DATABASE=/database/filebrowser.db
      - FB_ROOT=/srv
      - FB_LOG=stdout
      - FB_NOAUTH=false  # Enable authentication
    volumes:
      - /data/workspace:/srv  # Browse AI code
      - /data/filebrowser:/database
    networks:
      - ai-hub-net
    restart: unless-stopped

  # Code Server - VS Code in Browser
  code-server:
    image: lscr.io/linuxserver/code-server:latest
    container_name: code-server
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
      - DEFAULT_WORKSPACE=/config/workspace
    volumes:
      - /data/workspace:/config/workspace
      - /data/code-server:/config
    networks:
      - ai-hub-net
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/production.conf:/etc/nginx/conf.d/default.conf:ro
      - /data/nginx/ssl:/etc/nginx/ssl:ro
      - /data/workspace:/var/www/workspace:ro  # Direct file access
    networks:
      - ai-hub-net
    depends_on:
      - open-webui
      - mcp-server
      - filebrowser
      - code-server
    restart: unless-stopped
```

#### Step 3.3: Environment Configuration
```bash
# /root/ai-hub-cloud/.env.production
# Get these values from your Supabase and DigitalOcean dashboards
SUPABASE_DATABASE_URL=your-supabase-postgres-url-here
DO_REDIS_URL=your-digitalocean-redis-url-here

# Open WebUI
WEBUI_SECRET_KEY=generate-strong-secret-here

# Generated after Open WebUI setup
OPENWEBUI_API_KEY=will-be-added-after-setup

# FileBrowser
FB_USERNAME=admin
FB_PASSWORD=choose-secure-password

# Code Server
CODE_SERVER_PASSWORD=choose-secure-password
```

#### Step 3.4: Nginx Configuration
```nginx
# /root/ai-hub-cloud/nginx/production.conf
server {
    listen 80;
    server_name aihub.instabids.ai;

    # Main Open WebUI
    location / {
        proxy_pass http://open-webui:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # MCP Server
    location /mcp/ {
        proxy_pass http://mcp-server:8888/;
        proxy_set_header Host $host;
    }

    # FileBrowser
    location /files/ {
        proxy_pass http://filebrowser:80/;
        proxy_set_header Host $host;
    }

    # VS Code Server
    location /code/ {
        proxy_pass http://code-server:8443/;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
    }

    # Direct workspace browsing
    location /workspace/ {
        alias /var/www/workspace/;
        autoindex on;
    }
}
```

### Phase 4: Enhanced MCP Tools

#### Step 4.1: Add File Management Tools to MCP
```python
# Add to mcp-server/main.py

@mcp_tool
async def create_project(name: str, description: str = ""):
    """Create new project directory with AI"""
    project_path = Path(f"/app/workspace/{name}")
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create project metadata
    metadata = {
        "name": name,
        "description": description,
        "created": datetime.now().isoformat(),
        "ai_managed": True
    }
    
    with open(project_path / "project.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    return {"status": "success", "path": str(project_path)}

@mcp_tool
async def write_code(project: str, filename: str, content: str):
    """AI writes code to workspace"""
    file_path = Path(f"/app/workspace/{project}/{filename}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    return {"status": "success", "path": str(file_path)}

@mcp_tool
async def read_code(project: str, filename: str):
    """AI reads code from workspace"""
    file_path = Path(f"/app/workspace/{project}/{filename}")
    
    if not file_path.exists():
        return {"status": "error", "message": "File not found"}
    
    with open(file_path, "r") as f:
        content = f.read()
    
    return {"status": "success", "content": content}

@mcp_tool
async def list_projects():
    """List all AI projects"""
    workspace = Path("/app/workspace")
    projects = []
    
    for item in workspace.iterdir():
        if item.is_dir() and (item / "project.json").exists():
            with open(item / "project.json", "r") as f:
                projects.append(json.load(f))
    
    return {"projects": projects}
```

### Phase 5: Deployment

#### Step 5.1: Deploy Services
```bash
cd /root/ai-hub-cloud
docker-compose -f docker-compose.production.yml up -d
```

#### Step 5.2: Initialize Open WebUI
1. Access: `http://YOUR_DROPLET_IP`
2. Create admin account
3. Generate API key
4. Update `.env.production` with API key

#### Step 5.3: Setup SSL
```bash
# Install Certbot
apt update && apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d aihub.instabids.ai
```

### Phase 6: Automated Backups

#### Step 6.1: Backup Script
```bash
#!/bin/bash
# /root/backup.sh

# Backup workspace to DigitalOcean Spaces
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /data/backups/workspace_$DATE.tar.gz /data/workspace

# Backup to GitHub (optional)
cd /data/workspace
git add -A
git commit -m "Auto backup $DATE"
git push origin main

# Clean old backups (keep 30 days)
find /data/backups -name "*.tar.gz" -mtime +30 -delete
```

#### Step 6.2: Cron Job
```bash
# Add to crontab
0 2 * * * /root/backup.sh  # Daily at 2 AM
```

## 🎯 Access Points

After deployment, you'll have:

1. **Open WebUI**: `https://aihub.instabids.ai`
   - Main AI interface
   - Chat with AI
   - API key management

2. **FileBrowser**: `https://aihub.instabids.ai/files`
   - Visual file manager
   - Upload/download files
   - Edit text files

3. **VS Code**: `https://aihub.instabids.ai/code`
   - Full IDE in browser
   - Edit AI-generated code
   - Git integration

4. **Direct Browse**: `https://aihub.instabids.ai/workspace`
   - Apache-style directory listing
   - Quick file access

5. **MCP Tools**: `https://aihub.instabids.ai/mcp`
   - API endpoints
   - AI self-modification tools

## 💰 Cost Summary

- **Droplet**: $24/month (2vCPU, 4GB RAM, 80GB SSD)
- **Supabase**: FREE tier (already have)
- **Redis**: Already paying for cluster
- **Total Additional**: $24/month

## 🚀 Migration Steps

1. **Backup current data** from App Platform
2. **Deploy Droplet** using this plan
3. **Test everything** works
4. **Update DNS** to point to Droplet
5. **Shutdown App Platform** deployment

## 📋 Checklist

- [ ] Create Droplet
- [ ] Setup directory structure
- [ ] Deploy Docker services
- [ ] Configure Supabase connection
- [ ] Configure Redis connection
- [ ] Setup FileBrowser auth
- [ ] Setup Code Server auth
- [ ] Configure SSL
- [ ] Test file persistence
- [ ] Setup automated backups
- [ ] Migrate from App Platform
- [ ] Update DNS

## 🎉 Result

A fully persistent, self-modifying AI system where:
- AI creates code directly on server
- You can browse/edit via web interfaces
- Everything persists forever
- Full backup capabilities
- Complete control over your AI ecosystem

## 🔐 Security Notes

Remember to:
1. Get your Supabase DATABASE_URL from your Supabase dashboard
2. Get your Redis connection string from DigitalOcean
3. Generate strong passwords for all services
4. Keep your `.env.production` file secure
5. Never commit sensitive credentials to Git
