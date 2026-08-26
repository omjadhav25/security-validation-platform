#!/usr/bin/env bash
# Run this ON the EC2 instance itself, over SSH, as the 'ubuntu' user.
# Usage: bash ec2-setup.sh YOUR-SSLIP-HOSTNAME
# Example: bash ec2-setup.sh 3-91-23-10.sslip.io

set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: bash ec2-setup.sh YOUR-SSLIP-HOSTNAME"
  echo "Example: bash ec2-setup.sh 3-91-23-10.sslip.io"
  exit 1
fi

SSLIP_HOST="$1"
REPO_URL="https://github.com/omjadhav25/security-validation-platform.git"
APP_DIR="/home/ubuntu/security-validation-platform"

echo "==> Updating system and installing dependencies"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx git

echo "==> Cloning the repo"
if [ -d "$APP_DIR" ]; then
  echo "Repo already exists, pulling latest instead"
  cd "$APP_DIR" && git pull
else
  git clone "$REPO_URL" "$APP_DIR"
fi

echo "==> Setting up Python virtual environment"
cd "$APP_DIR/backend"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "==> Writing .env (edit this afterwards with your real DB password!)"
if [ ! -f "$APP_DIR/backend/.env" ]; then
  cat > "$APP_DIR/backend/.env" <<EOF
DATABASE_URL=postgresql://svpadmin:CHANGE_ME@CHANGE_ME.rds.amazonaws.com:5432/securitydb
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
BACKEND_URL=https://${SSLIP_HOST}
FRONTEND_URL=https://your-app.vercel.app
EOF
  echo "!! Edit $APP_DIR/backend/.env now and set your real RDS connection string and Vercel URL."
else
  echo ".env already exists, leaving it as-is"
fi

echo "==> Installing systemd service"
sudo cp "$APP_DIR/deploy/aws/svp-backend.service" /etc/systemd/system/svp-backend.service
sudo systemctl daemon-reload
sudo systemctl enable svp-backend
sudo systemctl restart svp-backend

echo "==> Configuring Nginx"
sudo cp "$APP_DIR/deploy/aws/nginx-svp-backend.conf" /etc/nginx/sites-available/svp-backend
sudo sed -i "s/YOUR-SSLIP-HOSTNAME/${SSLIP_HOST}/" /etc/nginx/sites-available/svp-backend
sudo ln -sf /etc/nginx/sites-available/svp-backend /etc/nginx/sites-enabled/svp-backend
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "==> Requesting a free HTTPS certificate for ${SSLIP_HOST}"
sudo certbot --nginx -d "${SSLIP_HOST}" --non-interactive --agree-tos -m you@example.com --redirect

echo
echo "==> Done!"
echo "Backend should now be live at: https://${SSLIP_HOST}"
echo "Next steps:"
echo "  1. Edit $APP_DIR/backend/.env with your real RDS password, then: sudo systemctl restart svp-backend"
echo "  2. Set VITE_API_URL=https://${SSLIP_HOST} in Vercel and redeploy the frontend"
