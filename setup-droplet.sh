#!/bin/bash
# Setup script for InstaBids AI Hub on Droplet

echo "🚀 InstaBids AI Hub - Droplet Setup Script"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt install -y docker.io docker-compose git certbot python3-certbot-nginx

# Enable Docker
systemctl enable docker
systemctl start docker

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p /data/workspace
mkdir -p /data/openwebui
mkdir -p /data/nginx/ssl
mkdir -p /data/filebrowser
mkdir -p /data/code-server
mkdir -p /data/backups

# Set permissions
chmod -R 755 /data

# Clone repository
echo "📥 Cloning repository..."
cd /root
if [ -d "ai-hub-cloud" ]; then
    cd ai-hub-cloud
    git pull
else
    git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git
    cd ai-hub-cloud
fi

# Copy environment template
if [ ! -f ".env.production" ]; then
    cp .env.production.template .env.production
    echo "⚠️  Please edit .env.production with your actual credentials!"
    echo "   Required: Supabase PostgreSQL URL, Redis URL, and passwords"
fi

# Create backup script
cat > /root/backup.sh << 'EOF'
#!/bin/bash
# Daily backup script for AI workspace

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/data/backups"

# Create backup
echo "Creating backup at $DATE..."
tar -czf $BACKUP_DIR/workspace_$DATE.tar.gz /data/workspace

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed!"
EOF

chmod +x /root/backup.sh

# Setup cron for daily backups
echo "0 2 * * * /root/backup.sh" | crontab -

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /root/ai-hub-cloud/.env.production with your credentials"
echo "2. Run: cd /root/ai-hub-cloud"
echo "3. Run: docker-compose -f docker-compose.production.yml up -d"
echo "4. Access Open WebUI at http://YOUR_IP and create admin account"
echo "5. Generate API key and update .env.production"
echo "6. Run: docker-compose -f docker-compose.production.yml restart mcp-server"
echo "7. Setup SSL: certbot --nginx -d aihub.instabids.ai"
echo ""
echo "📍 Services will be available at:"
echo "   - Open WebUI: https://aihub.instabids.ai"
echo "   - FileBrowser: https://aihub.instabids.ai/files"
echo "   - VS Code: https://aihub.instabids.ai/code"
echo "   - Direct Browse: https://aihub.instabids.ai/workspace"
