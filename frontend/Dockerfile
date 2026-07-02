# Use the lightweight Nginx Alpine image as the base
FROM nginx:alpine

# Remove default Nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy the static assets from the frontend folder to the Nginx public folder
COPY . /usr/share/nginx/html

# Expose port 80 for web traffic
EXPOSE 80

# Run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
