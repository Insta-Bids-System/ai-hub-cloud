FROM filebrowser/filebrowser:latest

# Set up the file browser with default configuration
COPY --chown=root:root filebrowser/filebrowser.json /.filebrowser.json

# Create directory for files
RUN mkdir -p /srv

# Expose port
EXPOSE 80

# Run filebrowser (without the leading slash)
CMD [ "filebrowser" ]
