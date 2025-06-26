FROM python:3.11-slim

WORKDIR /app

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

# Create a healthcheck script
RUN echo '#!/bin/sh\ncurl -f http://localhost:8888/health || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Expose the MCP server port
EXPOSE 8888

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD /healthcheck.sh

# Fix: Use mcpo command directly, not python -m mcpo
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8888", "--mode", "proxy", "--", "python", "mcp_server.py"]