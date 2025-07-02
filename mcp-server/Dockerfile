FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix: Use correct path for requirements.txt
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fix: Use correct path for main.py
COPY mcp-server/main.py .

EXPOSE 8888

CMD ["python", "main.py"]