FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for FastAPI and agent deployment
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install PM2 globally for agent process management
RUN npm install -g pm2

# Copy requirements and install dependencies
COPY mcp-server/requirements.txt* ./
RUN pip install --no-cache-dir fastapi uvicorn httpx

# Copy the REVOLUTIONARY COMPLETE MCP server (200+ tools)
COPY mcp-server/revolutionary_complete.py mcp_server.py

# Create workspaces directory for agents
RUN mkdir -p /app/workspaces

# Configure nginx for agent routing (will be configured at runtime)
RUN mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

# Expose the MCP server port
EXPOSE 8888

# Run the FastAPI server with uvicorn
CMD ["python", "mcp_server.py"]
