FROM codercom/code-server:latest

# Create workspace directory
RUN mkdir -p /home/coder/workspace

# Set environment variables
ENV PASSWORD=${PASSWORD:-changeme}
ENV PORT=8443

# Expose the port
EXPOSE 8443

# Run code-server
ENTRYPOINT ["/usr/bin/entrypoint.sh", "--bind-addr", "0.0.0.0:8443", "--auth", "password"]
