FROM filebrowser/filebrowser:latest

# Set up the file browser with default configuration
COPY --chown=root:root filebrowser.json /.filebrowser.json

# Create directory for files
RUN mkdir -p /srv

# Expose port
EXPOSE 80

# Run filebrowser
CMD [ "/filebrowser" ]
