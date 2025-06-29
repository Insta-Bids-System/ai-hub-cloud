#!/bin/bash
# Quick Install Script - Run this directly on your droplet

echo "Installing Docker if not present..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
fi

if ! command -v docker-compose &> /dev/null; then
    apt-get update && apt-get install -y docker-compose
fi

echo "Docker is ready!"
echo ""
echo "Now run:"
echo "  cd /root"
echo "  git clone https://github.com/Insta-Bids-System/ai-hub-cloud.git"
echo "  cd ai-hub-cloud"
echo "  bash rapid-deploy.sh"
