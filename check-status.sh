#!/bin/bash
# InstaBids AI Hub - Status Check Script

echo "🔍 InstaBids AI Hub - System Status Check"
echo "========================================"
echo ""

# Check if Docker is running
if systemctl is-active --quiet docker; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running"
    exit 1
fi

# Check containers
echo ""
echo "📦 Container Status:"
cd /root/ai-hub-cloud 2>/dev/null || { echo "❌ Deployment directory not found"; exit 1; }

# Check each service
services=("open-webui" "mcp-server" "filebrowser" "nginx")
all_running=true

for service in "${services[@]}"; do
    if docker ps | grep -q "$service"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        all_running=false
    fi
done

# Check data persistence
echo ""
echo "💾 Data Persistence Check:"
directories=("/data/workspace" "/data/openwebui" "/data/backups" "/data/filebrowser")

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "✅ $dir exists (Size: $size)"
    else
        echo "❌ $dir is missing"
    fi
done

# Check web endpoints
echo ""
echo "🌐 Service Endpoints:"
endpoints=(
    "http://localhost:80|Open WebUI"
    "http://localhost:80/mcp|MCP Server"
    "http://localhost:80/files|FileBrowser"
)

for endpoint in "${endpoints[@]}"; do
    url=$(echo "$endpoint" | cut -d'|' -f1)
    name=$(echo "$endpoint" | cut -d'|' -f2)
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302\|301"; then
        echo "✅ $name is accessible"
    else
        echo "❌ $name is not accessible"
    fi
done

# Check backup cron
echo ""
echo "🕒 Backup Schedule:"
if crontab -l 2>/dev/null | grep -q "backup-ai-hub"; then
    echo "✅ Automated backups are scheduled"
    crontab -l | grep backup-ai-hub
else
    echo "❌ Automated backups are not scheduled"
fi

# Summary
echo ""
echo "📊 Summary:"
if [ "$all_running" = true ]; then
    echo "✅ All services are running correctly!"
    echo ""
    echo "🎉 Your AI Hub is ready at:"
    echo "   http://159.65.36.162"
    echo ""
    echo "📁 Your data is persisted in:"
    echo "   /data/workspace   - AI files"
    echo "   /data/openwebui   - Chats & settings"
    echo "   /data/backups     - Daily backups"
else
    echo "⚠️  Some services need attention"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   docker-compose logs [service-name]"
    echo "   docker-compose restart [service-name]"
fi

echo ""
echo "Status check completed at $(date)"
