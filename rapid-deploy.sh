#!/bin/bash
# 🚀 InstaBids AI Hub - Rapid Persistent Deployment Script
# This script sets up a 100% persistent AI system that NEVER loses data

set -e  # Exit on any error

echo "🚀 InstaBids AI Hub - Rapid Persistent Deployment"
echo "================================================"
echo "Starting deployment at $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root"
    exit 1
fi

print_status "Starting deployment process..."

# Update system
print_status "Updating system packages..."
apt-get update -y > /dev/null 2>&1

# Install prerequisites
print_status "Installing prerequisites..."
apt-get install -y git curl wget unzip > /dev/null 2>&1

# Create persistent directory structure
print_status "Creating persistent directory structure..."
mkdir -p /data/workspace
mkdir -p /data/openwebui/backend
mkdir -p /data/nginx/ssl
mkdir -p /data/filebrowser
mkdir -p /data/redis
mkdir -p /data/backups
mkdir -p /data/mcp-configs
chmod -R 755 /data

# Clone repository if it doesn't exist
if [ ! -d "/root/ai-hub-cloud" ]; then
    print_status "Cloning repository..."
    cd /root
    git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git
else
    print_status "Updating repository..."
    cd /root/ai-hub-cloud
    git pull
fi

cd /root/ai-hub-cloud

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment configuration..."
    cat > .env << 'EOF'
# Domain
DOMAIN_NAME=aihub.instabids.ai

# Supabase (Update these with your values)
SUPABASE_URL=https://ybxiqfyzexwfqyvmzypa.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY

# Open WebUI Security
WEBUI_SECRET_KEY=GENERATE_ME

# Redis (Your existing DigitalOcean Redis)
REDIS_URL=YOUR_REDIS_CONNECTION_STRING

# FileBrowser Authentication
FB_USERNAME=admin
FB_PASSWORD=GENERATE_ME

# Generated after Open WebUI setup
OPENWEBUI_API_KEY=
EOF
    
    # Generate random secrets
    WEBUI_KEY=$(openssl rand -hex 32)
    FB_PASS=$(openssl rand -base64 16)
    
    # Update the placeholders
    sed -i "s/GENERATE_ME/$WEBUI_KEY/" .env
    sed -i "s/GENERATE_ME/$FB_PASS/" .env
    
    print_warning "Please update the Supabase keys and Redis URL in .env file"
fi

# Create docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml" ]; then
    print_status "Creating Docker Compose configuration..."
    wget -q https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/docker-compose.yml
fi

# Create necessary directories for services
print_status "Setting up service directories..."
mkdir -p mcp-server
mkdir -p nginx
mkdir -p backup-service

# Download service configurations
print_status "Downloading service configurations..."
wget -q -O mcp-server/Dockerfile https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/mcp-server/Dockerfile || true
wget -q -O mcp-server/requirements.txt https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/mcp-server/requirements.txt || true
wget -q -O mcp-server/main.py https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/mcp-server/main.py || true
wget -q -O nginx/nginx.conf https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/nginx/nginx.conf || true

# Start Docker services
print_status "Starting Docker services..."
docker-compose down > /dev/null 2>&1 || true
docker-compose up -d

# Wait for services to start
print_status "Waiting for services to initialize..."
sleep 10

# Check service status
print_status "Checking service status..."
docker-compose ps

# Get container IPs
DROPLET_IP=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)

echo ""
echo "====================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "====================================="
echo ""
echo "📋 Access your services at:"
echo "   Open WebUI: http://$DROPLET_IP"
echo "   FileBrowser: http://$DROPLET_IP/files"
echo "   Workspace: http://$DROPLET_IP/workspace"
echo "   MCP Server: http://$DROPLET_IP/mcp"
echo ""
echo "📝 Next Steps:"
echo "1. Access Open WebUI and create an admin account"
echo "2. Generate an API key in Open WebUI settings"
echo "3. Update the .env file with your API key"
echo "4. Run: docker-compose restart mcp-server"
echo ""
echo "🛡️ Data Persistence:"
echo "   All data is stored in /data/*"
echo "   Survives all restarts and updates"
echo "   Daily backups to /data/backups"
echo ""
echo "For help, check: docker-compose logs -f"
echo "====================================="