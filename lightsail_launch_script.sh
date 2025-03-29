#!/bin/bash
# Log everything to a file in /tmp first for simplicity
exec > /tmp/userdata-output.log 2>&1

echo "--- Starting User Data Script Execution $(date) ---"

# Wait for network to be ready
echo "Waiting for network..."
sleep 10

# Update & Install essential packages
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y git python3-pip python3.10-venv nginx screen

# Define user and home directory
APP_USER="ubuntu"
APP_HOME="/home/$APP_USER"
APP_DIR="$APP_HOME/polish_plots"

# Clone the repository as the ubuntu user
echo "Cloning repository into $APP_DIR..."
cd $APP_HOME
sudo -u $APP_USER git clone https://github.com/naglemi/polish_plots.git

# Check if clone was successful
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Failed to clone repository into $APP_DIR" >&2
    exit 1
fi
cd $APP_DIR

# Navigate to app directory and install dependencies
cd $APP_DIR || exit 1
# Create venv as the ubuntu user
sudo -u $APP_USER python3 -m venv venv
# Install dependencies as the ubuntu user
sudo -u $APP_USER /bin/bash -c "source $APP_DIR/venv/bin/activate && pip install --upgrade pip && pip install -r $APP_DIR/requirements.txt"

# --- Application Service Setup (using Systemd) ---
echo "Setting up systemd service for the chat app..."

cat << EOF > /etc/systemd/system/agntcy-chat.service
[Unit]
Description=AGNTCY Chat Application (FastAPI)
After=network.target

[Service]
User=$APP_USER
# Group=ubuntu # Default to user's primary group (Commented out based on previous fix)
WorkingDirectory=$APP_DIR/app
Environment="PATH=$APP_DIR/venv/bin"
# Point ExecStart to the ASGI app object (main:asgi_app) for Socket.IO
ExecStart=$APP_DIR/venv/bin/uvicorn main:asgi_app --host 0.0.0.0 --port 8081
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
systemctl daemon-reload
systemctl enable agntcy-chat.service
systemctl start agntcy-chat.service

# --- Nginx Setup (Reverse Proxy) ---
# Optional but recommended: Use Nginx to serve on port 80 and handle static files
echo "Setting up Nginx reverse proxy..."

cat << EOF > /etc/nginx/sites-available/agntcy-chat
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias $APP_DIR/static;
        expires 1d;
    }
}
EOF

# Enable the site and restart Nginx
ln -s /etc/nginx/sites-available/agntcy-chat /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default # Remove default Nginx site
systemctl restart nginx

# Open firewall ports (redundant if already done via AWS CLI, but safe)
# ufw allow 22/tcp
# ufw allow 80/tcp
# ufw allow 443/tcp # For future HTTPS
# ufw allow 8081/tcp # May not be needed if only accessing via Nginx on port 80
# ufw --force enable

echo "Setup complete. Application should be running and accessible via Nginx on port 80."
