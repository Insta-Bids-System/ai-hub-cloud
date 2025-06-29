#!/bin/bash
# Quick fix script to get everything running

echo "🔧 Fixing AI Hub Production Setup..."

# Stop everything first
cd /root/ai-hub-cloud
docker-compose down
docker stop $(docker ps -aq) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null

# Create required directories with proper permissions
mkdir -p /data/openwebui
mkdir -p /data/workspace
mkdir -p /data/filebrowser
mkdir -p /data/uploads
chmod -R 755 /data

# Create a working docker-compose
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
      - ENV=production
      - ENABLE_SIGNUP=false
      - DATA_DIR=/app/backend/data
    volumes:
      - /data/openwebui:/app/backend/data
    ports:
      - "8080:8080"
    restart: unless-stopped

  mcp-server:
    image: python:3.11-slim
    container_name: mcp-server
    working_dir: /app
    command: bash -c "pip install fastapi uvicorn httpx redis && python main.py"
    environment:
      - OPENWEBUI_URL=http://open-webui:8080
      - MCPO_PORT=8888
      - MCPO_HOST=0.0.0.0
    volumes:
      - ./mcp-server:/app
      - /data/workspace:/app/workspace
    ports:
      - "8888:8888"
    restart: unless-stopped

  filebrowser:
    image: filebrowser/filebrowser:s6
    container_name: filebrowser
    environment:
      - PUID=0
      - PGID=0
    volumes:
      - /data:/srv
      - /data/filebrowser/filebrowser.db:/database.db
      - /data/filebrowser/settings.json:/config/settings.json
    ports:
      - "8090:80"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/simple.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
EOF

# Create simple nginx config
mkdir -p nginx
cat > nginx/simple.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://open-webui:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    location /mcp/ {
        proxy_pass http://mcp-server:8888/;
        proxy_set_header Host $host;
    }
    
    location /files/ {
        proxy_pass http://filebrowser/;
        proxy_set_header Host $host;
    }
}
EOF

# Start everything with the production environment
docker-compose --env-file .env.production up -d

# Wait a bit
echo "⏳ Waiting for services to start..."
sleep 30

# Check status
echo "📊 Service Status:"
docker ps

echo "
✅ DONE! Your services should now be available at:
- Open WebUI: http://159.65.36.162
- MCP Server: http://159.65.36.162/mcp/
- FileBrowser: http://159.65.36.162/files/

🔍 To check logs:
- docker logs open-webui
- docker logs mcp-server
- docker logs filebrowser
"
