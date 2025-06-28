FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for FastAPI
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY mcp-server/requirements.txt* ./
RUN pip install --no-cache-dir fastapi uvicorn httpx

# Copy the REVOLUTIONARY COMPLETE MCP server (200+ tools)
COPY mcp-server/revolutionary_complete.py mcp_server.py

# Expose the MCP server port
EXPOSE 8888

# Run the FastAPI server with uvicorn
CMD ["python", "mcp_server.py"]
