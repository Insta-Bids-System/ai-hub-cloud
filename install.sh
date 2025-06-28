#!/bin/bash
# One-liner installer for InstaBids AI Hub
# Just run: curl -sSL https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/install.sh | bash

echo "🚀 InstaBids AI Hub - One-Click Installer"
echo "========================================"

# Download and run the setup script
wget -q https://raw.githubusercontent.com/Insta-Bids-System/ai-hub-cloud/main/setup-droplet.sh
chmod +x setup-droplet.sh
./setup-droplet.sh

# Get Supabase connection info
echo ""
echo "📋 Configuration Required:"
echo "========================="
echo ""
echo "You need to add your credentials to: /root/ai-hub-cloud/.env.production"
echo ""
echo "1. Supabase PostgreSQL URL:"
echo "   - Go to: https://supabase.com/dashboard/project/ybxiqfyzexwfqyvmzypa/settings/database"
echo "   - Copy the 'Connection string' (URI format)"
echo ""
echo "2. Your existing Redis URL from DigitalOcean"
echo ""
echo "3. Generate secure passwords for:"
echo "   - WEBUI_SECRET_KEY"
echo "   - FB_PASSWORD"
echo "   - CODE_SERVER_PASSWORD"
echo ""
echo "After adding credentials, run:"
echo "  cd /root/ai-hub-cloud"
echo "  docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "Then access http://$(curl -s ifconfig.me) to set up Open WebUI!"
