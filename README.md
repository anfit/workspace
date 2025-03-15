# Workspace – REST API Interface for File-Based Storage for Custom GPTs

**Workspace** is a lightweight, standalone REST API service that acts as a bridge between a custom GPT (or any other HTTP client) and a sandboxed section of the deployment server’s **filesystem workspace folder**. It enables programmatic listing, creation, reading, and updating of files, allowing GPT-based document automation or bot integrations without needing a database or third-party system.

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- REST API secured via a pre-shared GPT secret (`X-GPT-Secret` header)
- Operations scoped to a defined directory on the local filesystem
- Fully compatible with Custom GPTs via OpenAPI tool definition
- Minimal, self-contained Flask app with no external database
- OpenAPI schema served from `/openapi.json`
- Systemd and Nginx deployment-ready

## 📚 Use Case

Designed to integrate with a **Custom GPT Operator Tool**, this API allows a GPT to:
- **List** files and subfolders in a root directory
- **Read** content of a file by name
- **Create** a new file under the root directory
- **Update** existing file content by name

This provides a clean and safe interface for document automation in a sandboxed file environment.

## 🏗 Architecture Overview

Workspace follows a minimal architecture for simplicity and portability:

```
Client (Custom GPT / HTTP client)
        │
        ▼
   [Nginx Reverse Proxy] ──▶ [Gunicorn WSGI Server] ──▶ [Flask App (workspace.py)]
                                               │
                                               ▼
                                  [Local Filesystem Workspace Folder]
```

Deployment is managed via Systemd and served through Nginx (HTTP/HTTPS). SSL certificates can be provisioned via Let's Encrypt.

## 📂 Project Structure

```
workspace/
├── workspace.py                    # Flask application implementing the API
├── openapi.json                    # OpenAPI 3.1 schema describing the API interface (update servers.url before use)
├── workspace.properties.example   # Example configuration file
├── deployment/
│   ├── workspace.http             # Nginx config for initial HTTP deployment
│   ├── workspace.ssl              # Nginx config for HTTPS/SSL deployment
│   └── workspace.service          # Systemd unit file for Gunicorn deployment
```

## ⚙️ Setup & Deployment

For full setup and deployment instructions, including HTTP → HTTPS transition, see: [SETUP.md](./SETUP.md)

## 🔐 Security Model

All protected operations require a pre-shared secret header:
```
X-GPT-Secret: your_gpt_secret
```
GPT tool calls must include this to access or modify file contents. The secret should be embedded in your Custom GPT configuration.

## 📑 API Endpoints (summary)

| Method | Path                | Description                            | Auth required |
|--------|---------------------|----------------------------------------|----------------|
| GET    | `/files`            | List all files in root directory       | ✅ Yes          |
| GET    | `/files/{filename}` | Read a file by name                    | ✅ Yes          |
| POST   | `/files`            | Create a new file                      | ✅ Yes          |
| PUT    | `/files/{filename}` | Update a file by name                  | ✅ Yes          |
| GET    | `/openapi.json`     | Get OpenAPI schema (for GPT integration) | ❌ No        |
| GET    | `/health`           | Health check                           | ❌ No           |

## 🤖 GPT Integration Guide

To integrate this API with a Custom GPT:
1. Upload or import `openapi.json` into the GPT tool definition. **Before doing so, make sure you edit the file and replace the `servers.url` field (currently set to a placeholder) with the actual domain or IP address where your API is hosted.**
2. Configure the `X-GPT-Secret` header in your GPT setup.
3. Ensure the API server is reachable over HTTPS at the declared domain.
4. Your GPT will now be able to list, read, create, and update files in the sandboxed directory.

## 📄 License

MIT License.

## 🙌 Credits

Developed by Jan Chimiak.

---

For questions, improvements or ideas — feel free to open an issue or PR.
