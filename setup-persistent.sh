#!/bin/bash
# InstaBids AI Hub - Persistent Setup Script
# This script sets up complete data persistence on your droplet

set -e  # Exit on any error

echo "🚀 Starting InstaBids AI Hub Persistent Setup..."
echo "================================================"

# Step 1: Create directory structure
echo "📁 Creating persistent directory structure..."
mkdir -p /data/workspace
mkdir -p /data/openwebui/backend
mkdir -p /data/nginx/ssl
mkdir -p /data/filebrowser
mkdir -p /data/redis
mkdir -p /data/backups
mkdir -p /data/mcp-configs

# Set permissions
chmod -R 755 /data

echo "✅ Directory structure created"

# Step 2: Install required packages
echo "📦 Installing required packages..."
apt-get update
apt-get install -y git docker.io docker-compose certbot python3-certbot-nginx

# Enable Docker
systemctl enable docker
systemctl start docker

echo "✅ Packages installed"

# Step 3: Clone repository
echo "📥 Cloning repository..."
cd /root
if [ -d "ai-hub-cloud" ]; then
    cd ai-hub-cloud
    git pull
else
    git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git
    cd ai-hub-cloud
fi

echo "✅ Repository ready"

# Step 4: Create environment file template
echo "🔐 Creating environment configuration template..."
if [ ! -f ".env.production" ]; then
    cat > .env.production << 'EOF'
# Supabase Configuration (UPDATE THESE!)
SUPABASE_URL=https://ybxiqfyzexwfqyvmzypa.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY_HERE
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY_HERE
SUPABASE_DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Redis Configuration (Your existing cluster)
REDIS_URL=YOUR_REDIS_CONNECTION_STRING_HERE

# Open WebUI Security
WEBUI_SECRET_KEY=$(openssl rand -hex 32)

# FileBrowser Authentication
FB_USERNAME=admin
FB_PASSWORD=$(openssl rand -base64 16)

# Backup Configuration
GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE
BACKUP_ENCRYPTION_KEY=$(openssl rand -hex 32)

# API Key (generated after Open WebUI setup)
OPENWEBUI_API_KEY=
EOF
    echo ""
    echo "⚠️  IMPORTANT: Edit .env.production and add:"
    echo "   1. Your Supabase keys"
    echo "   2. Your Redis connection string"
    echo "   3. Your GitHub token for backups"
fi

echo "✅ Environment template created"

# Step 5: Show generated passwords
echo ""
echo "📝 Generated Credentials:"
echo "========================"
echo "FileBrowser Username: admin"
echo "FileBrowser Password: Check .env.production"
echo ""

# Step 6: Create backup script
echo "💾 Creating backup script..."
cat > /root/backup-ai-hub.sh << 'EOF'
#!/bin/bash
# Daily backup script for AI Hub

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/data/backups/ai_hub_backup_$TIMESTAMP.tar.gz"

# Create backup
tar -czf $BACKUP_FILE /data/workspace /data/openwebui /data/filebrowser

# Keep only last 30 days of backups
find /data/backups -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
EOF
chmod +x /root/backup-ai-hub.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup-ai-hub.sh") | crontab -

echo "✅ Backup system configured"

echo ""
echo "🎉 Initial setup complete!"
echo "=========================="
echo ""
echo "📋 Required manual steps:"
echo ""
echo "1. Edit environment file:"
echo "   nano /root/ai-hub-cloud/.env.production"
echo ""
echo "2. Add your credentials:"
echo "   - Supabase anon key"
echo "   - Supabase service key" 
echo "   - Redis connection string"
echo "   - GitHub token (optional)"
echo ""
echo "3. Deploy services:"
echo "   cd /root/ai-hub-cloud"
echo "   docker-compose up -d"
echo ""
echo "4. Access services:"
echo "   - Open WebUI: http://159.65.36.162"
echo "   - FileBrowser: http://159.65.36.162/files"
echo "   - MCP Server: http://159.65.36.162/mcp"
echo ""
echo "5. In Open WebUI:"
echo "   - Create admin account"
echo "   - Generate API key"
echo "   - Add key to .env.production"
echo "   - Restart: docker-compose restart"
echo ""
echo "📂 Persistent data locations:"
echo "- AI Code: /data/workspace"
echo "- Open WebUI: /data/openwebui"
echo "- Backups: /data/backups"
