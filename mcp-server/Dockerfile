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
    python-jose[cryptography] \
    asyncio

# Copy requirements if we have more dependencies
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy the COMPLETE MCP server files (200+ tools)
COPY open_webui_mcp_complete.py mcp_server.py
COPY auth_handler.py .

# Create a healthcheck script
RUN echo '#!/bin/sh\ncurl -f http://localhost:8888/health || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Expose the MCP server port
EXPOSE 8888

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD /healthcheck.sh

# Run with mcpo proxy mode for remote access
CMD ["python", "-m", "mcpo", "--host", "0.0.0.0", "--port", "8888", "--mode", "proxy", "--", "python", "mcp_server.py"]