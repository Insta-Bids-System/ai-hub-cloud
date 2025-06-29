#!/bin/bash
# One-command installer - Just run this!

set -e

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    apt-get update -qq && apt-get install -y docker-compose
fi

# Create all directories
echo "Creating persistent directories..."
mkdir -p /data/{workspace,openwebui/backend,nginx/ssl,filebrowser,redis,backups,mcp-configs}
chmod -R 755 /data

# Clone repo
echo "Getting deployment files..."
cd /root
rm -rf ai-hub-cloud
git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git
cd ai-hub-cloud

# Create .env
echo "Setting up configuration..."
cat > .env << 'EOF'
DOMAIN_NAME=aihub.instabids.ai
SUPABASE_URL=https://ybxiqfyzexwfqyvmzypa.supabase.co
SUPABASE_ANON_KEY=YOUR_KEY
SUPABASE_SERVICE_KEY=YOUR_KEY
WEBUI_SECRET_KEY=$(openssl rand -hex 32)
REDIS_URL=rediss://default:YOUR_REDIS_PASSWORD@instabids-redis-shared-do-user-23190909-0.i.db.ondigitalocean.com:25061/0
FB_USERNAME=admin
FB_PASSWORD=$(openssl rand -base64 16)
OPENWEBUI_API_KEY=
EOF

# Start everything
echo "Starting services..."
docker-compose up -d

# Show status
echo ""
echo "====================================="
echo "DEPLOYMENT COMPLETE!"
echo "====================================="
echo "Access your services at:"
echo "  Open WebUI: http://$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)"
echo "  Files: http://$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)/files"
echo ""
echo "Next: Create admin account in Open WebUI"
echo "====================================="
