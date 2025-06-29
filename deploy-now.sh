#!/bin/bash
# COMPLETE DEPLOYMENT IN ONE COMMAND

# Install Docker
curl -fsSL https://get.docker.com | sh
apt-get update && apt-get install -y docker-compose

# Create directories
mkdir -p /data/{workspace,openwebui/backend,nginx/ssl,filebrowser,redis,backups,mcp-configs}

# Get files
cd /root
rm -rf ai-hub-cloud
git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git
cd ai-hub-cloud

# Create config
echo 'WEBUI_SECRET_KEY='$(openssl rand -hex 32) > .env
echo 'FB_USERNAME=admin' >> .env
echo 'FB_PASSWORD='$(openssl rand -base64 16) >> .env

# Deploy
docker-compose up -d

echo "DONE! Access at http://159.65.36.162"
