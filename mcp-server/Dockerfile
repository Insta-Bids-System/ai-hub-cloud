FROM python:3.11-slim

WORKDIR /app

# Cache invalidation comment - REBUILD: 2025-06-26-18:50 PST - Force fresh build for import fix
# This comment forces Docker to rebuild all subsequent layers and bypass cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    mcpo \
    mcp \
    aiohttp \
    redis \
    python-jose[cryptography]

# Copy requirements from correct path (build context is repo root)
COPY mcp-server/requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy the COMPLETE MCP server files (200+ tools) from correct paths
COPY mcp-server/open_webui_mcp_complete.py mcp_server.py
COPY mcp-server/auth_handler.py .

# Expose the MCP server port
EXPOSE 8888

# FIXED: Remove health check and use correct mcpo syntax
# mcpo will proxy the MCP server and provide the HTTP endpoints
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8888", "--", "python", "mcp_server.py"]