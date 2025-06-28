FROM filebrowser/filebrowser:latest

# Set up the file browser with default configuration
COPY --chown=root:root filebrowser/filebrowser.json /.filebrowser.json

# Create directory for files
RUN mkdir -p /srv

# Expose port
EXPOSE 80

# Fix: Use proper command format for newer FileBrowser versions
CMD [ "/filebrowser", "--config", "/.filebrowser.json" ]
