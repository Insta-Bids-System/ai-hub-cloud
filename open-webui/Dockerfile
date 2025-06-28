FROM ghcr.io/open-webui/open-webui:main

# Set working directory
WORKDIR /app

# Copy any custom configurations or documents
COPY company-docs /app/backend/data/docs
COPY project-prompts /app/backend/data/prompts

# Set proper permissions
RUN chmod -R 755 /app/backend/data

# Expose port
EXPOSE 8080

# Use the default Open WebUI entrypoint
CMD ["bash", "start.sh"]
