#!/bin/bash
# InstaBids AI Hub - Rapid Persistent Deployment
# This script deploys everything with data persistence

set -e

echo "🚀 InstaBids AI Hub - Rapid Persistent Deployment"
echo "================================================"
echo "Starting deployment at $(date)"
echo ""

# Step 1: Quick prerequisites
echo "📦 Installing prerequisites..."
apt-get update -y > /dev/null 2>&1
apt-get install -y docker.io docker-compose git curl > /dev/null 2>&1
systemctl enable docker > /dev/null 2>&1
systemctl start docker > /dev/null 2>&1

# Step 2: Create persistent directories
echo "📁 Creating persistent storage directories..."
mkdir -p /data/{workspace,openwebui/backend,nginx/ssl,filebrowser,backups}
chmod -R 755 /data

# Step 3: Setup deployment directory
echo "📥 Setting up deployment..."
cd /root
rm -rf ai-hub-cloud
git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git > /dev/null 2>&1
cd ai-hub-cloud

# Step 4: Create optimized docker-compose.yml
echo "🐳 Creating Docker configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

networks:
  ai-hub-net:
    driver: bridge

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    volumes:
      - /data/openwebui:/app/backend/data
      - /data/workspace:/app/workspace
    environment:
      - ENV=dev
      - ENABLE_API_KEY=true
      - ENABLE_SIGNUP=true
      - DATA_DIR=/app/backend/data
      - WEBUI_AUTH=true
    networks:
      - ai-hub-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s

  mcp-server:
    build: ./mcp-server
    container_name: mcp-server
    volumes:
      - /data/workspace:/app/workspace
    environment:
      - OPENWEBUI_URL=http://open-webui:8080
      - WORKSPACE_PATH=/app/workspace
      - MCPO_PORT=8888
      - MCPO_HOST=0.0.0.0
    networks:
      - ai-hub-net
    restart: unless-stopped
    depends_on:
      - open-webui

  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    volumes:
      - /data/workspace:/srv
      - /data/filebrowser:/database
    environment:
      - FB_DATABASE=/database/filebrowser.db
      - FB_ROOT=/srv
      - FB_NOAUTH=true
    networks:
      - ai-hub-net
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /data/workspace:/var/www/workspace:ro
    networks:
      - ai-hub-net
    depends_on:
      - open-webui
      - mcp-server
      - filebrowser
    restart: unless-stopped
EOF

# Step 5: Create simplified Nginx config if missing
if [ ! -f "nginx/nginx.conf" ]; then
    mkdir -p nginx
    cat > nginx/nginx.conf << 'NGINX'
events {
    worker_connections 1024;
}

http {
    upstream open-webui { server open-webui:8080; }
    upstream mcp-server { server mcp-server:8888; }
    upstream filebrowser { server filebrowser:80; }

    server {
        listen 80;
        client_max_body_size 100M;
        
        location / {
            proxy_pass http://open-webui;
            proxy_set_header Host $host;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        location /mcp/ {
            proxy_pass http://mcp-server/;
            proxy_set_header Host $host;
        }
        
        location /files/ {
            proxy_pass http://filebrowser/;
            proxy_set_header Host $host;
        }
        
        location /workspace/ {
            alias /var/www/workspace/;
            autoindex on;
        }
    }
}
NGINX
fi

# Step 6: Deploy services
echo "🚀 Deploying services..."
docker-compose down > /dev/null 2>&1 || true
docker-compose up -d --build

# Step 7: Wait for services
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# Step 8: Setup automated backups
echo "💾 Setting up automated backups..."
cat > /root/backup-ai-hub.sh << 'BACKUP'
#!/bin/bash
BACKUP_FILE="/data/backups/ai_hub_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" /data/workspace /data/openwebui
find /data/backups -name "*.tar.gz" -mtime +30 -delete
BACKUP
chmod +x /root/backup-ai-hub.sh
(crontab -l 2>/dev/null | grep -v backup-ai-hub; echo "0 2 * * * /root/backup-ai-hub.sh") | crontab -

# Step 9: Show results
echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🌐 Your services are available at:"
echo ""
echo "  Open WebUI:    http://159.65.36.162"
echo "  FileBrowser:   http://159.65.36.162/files"
echo "  Workspace:     http://159.65.36.162/workspace"  
echo "  MCP Server:    http://159.65.36.162/mcp"
echo ""
echo "📋 Next Steps:"
echo "  1. Open http://159.65.36.162 in your browser"
echo "  2. Click 'Sign up' to create your admin account"
echo "  3. Start using your AI with 100% data persistence!"
echo ""
echo "💾 Your data is permanently stored in:"
echo "  • /data/workspace   - All AI-generated files"
echo "  • /data/openwebui   - All chats and settings"
echo "  • /data/backups     - Daily automated backups"
echo ""
echo "🔍 Useful commands:"
echo "  • Check status:  docker-compose ps"
echo "  • View logs:     docker-compose logs -f"
echo "  • Restart:       docker-compose restart"
echo ""

# Check if services are running
if docker ps | grep -q open-webui; then
    echo "✅ Open WebUI is running"
else
    echo "⚠️  Open WebUI is not running - check logs with: docker logs open-webui"
fi

if docker ps | grep -q mcp-server; then
    echo "✅ MCP Server is running"
else
    echo "⚠️  MCP Server is not running - check logs with: docker logs mcp-server"
fi

if docker ps | grep -q filebrowser; then
    echo "✅ FileBrowser is running"
else
    echo "⚠️  FileBrowser is not running - check logs with: docker logs filebrowser"
fi

echo ""
echo "Deployment completed at $(date)"
echo "Your AI Hub is ready with 100% persistent storage! 🎉"
