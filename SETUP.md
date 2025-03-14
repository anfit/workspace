# SETUP.md — Deploying the Workspace Server (Gunicorn + Nginx + HTTPS)

This document describes how to install and deploy the `workspace` REST API server in production using **Gunicorn** behind **Nginx**, first via HTTP, then upgrading to HTTPS via **Let's Encrypt / Certbot**.

This setup exposes the `workspace` API (defined in `workspace.py`) under a public domain (e.g., `workspace.someplace.eu`) for integration with tools like **Custom GPTs**. It serves as a REST API interface to a **sandboxed local filesystem folder** instead of an external system like Confluence. This setup does not require any external storage systems – all data is managed in a directory on the local server.

---

## 📋 Requirements

- Ubuntu Linux server (tested on Ubuntu 22.04+)
- Python 3.10+ installed
- A **configured subdomain** (e.g., `workspace.someplace.eu`) already pointing to your server IP address (via DNS A record)
- Firewall open for **ports 80 (HTTP)** and **443 (HTTPS)**

---

# Part 1 — Initial HTTP Setup (No SSL)

## ⚙️ 1. Install Required System Packages
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx -y
```

## 🐍 2. Set Up Python Environment and Application
Navigate to your project directory and set up:
```bash
cd /home/ubuntu/projects/workspace
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn
```

## 📁 2b. Define the Filesystem Workspace Directory

Before starting the server, ensure that your intended root directory for file storage (the “workspace”) exists and is writable by the application process.

Example:
```bash
mkdir -p /srv/workspace-data
chown ubuntu:ubuntu /srv/workspace-data
```

Set the directory path in your `workspace.properties` file before running the service.

## 🔧 3. Configure Systemd Service (Gunicorn)
Use the systemd service file in `deployment/`:
```bash
sudo cp deployment/workspace.service /etc/systemd/system/workspace.service
sudo systemctl daemon-reload
sudo systemctl enable workspace
sudo systemctl start workspace
```
Check logs:
```bash
sudo journalctl -u workspace -n 50 --no-pager
```

## 🌐 4. Set Up Nginx Reverse Proxy (HTTP only)
Use the HTTP-only config file:
```bash
sudo cp deployment/workspace.http /etc/nginx/sites-available/workspace
sudo ln -s /etc/nginx/sites-available/workspace /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```
✅ Your API is now accessible at:
```
http://workspace.someplace.eu/
```
Confirm public access before proceeding to SSL setup.

---

# Part 2 — Upgrading to HTTPS (SSL/TLS)

## 🔐 5. Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

## 🔏 6. Obtain SSL Certificate (Let's Encrypt)
```bash
sudo certbot --nginx -d workspace.someplace.eu
```

## 🆗 7. Switch to SSL Nginx Configuration
Replace HTTP config with SSL-enabled one:
```bash
sudo cp deployment/workspace.ssl /etc/nginx/sites-available/workspace
sudo nginx -t
sudo systemctl reload nginx
```

## 🔁 8. Redirect HTTP to HTTPS (Optional)
Ensure the SSL config contains a redirect block for HTTP → HTTPS.

---

## 🔄 9. Auto-Renewal of SSL Certificates
Verify Certbot timer:
```bash
sudo systemctl list-timers | grep certbot
```
Test renewal:
```bash
sudo certbot renew --dry-run
```

---

## ✅ 10. Verify Deployment
Check your API health endpoint:
```
https://workspace.someplace.eu/health
```

---

## 📁 Additional Notes

- Configuration is sourced from `workspace.properties` (see `workspace.properties.example`)
- Files are created, read, updated, or deleted in a confined root directory on the server
- API schema available at `/openapi.json`
- Protect your GPT token at all times

---

## 📊 Summary
| Component   | Role                                |
|------------|-------------------------------------|
| Flask      | REST API for file access            |
| Gunicorn   | Production WSGI server              |
| Nginx      | TLS proxy and route manager         |
| Certbot    | SSL certificate automation          |
| Filesystem | Backend storage (sandboxed folder)  |

🔔 Remember to update the `servers.url` field in `openapi.json` to match your deployment domain.