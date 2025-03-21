# Workspace – REST API Interface for File-Based Storage for Custom GPTs

**Workspace** is a lightweight, standalone REST API service that acts as a bridge between a custom GPT (or any other HTTP client) and a sandboxed section of the deployment server’s **filesystem workspace folder**. It enables programmatic listing, creation, reading, updating, renaming, moving, deleting, and committing of files, allowing GPT-based document automation or bot integrations without needing a database or third-party system.

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- REST API secured via a Bearer token (`Authorization: Bearer <token>` header)
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
- **Update** existing file content by name (⚠️ Requires full file content — diffs or partial updates are not supported)
- **Rename** files
- **Move** files
- **Delete** files
- **Commit** changes to a Git repository

This provides a clean and safe interface for document automation in a sandboxed file environment.

## 🏗 Architecture Overview

Workspace follows a minimal architecture for simplicity and portability:

```
Client (Custom GPT / HTTP client)
        │
        ▼
   [Nginx Reverse Proxy] ▶ [Gunicorn WSGI Server] ▶ [Flask App (workspace.py)]
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

All protected operations require a Bearer token:
```
Authorization: Bearer your_secret_token
```
GPT tool calls must include this to access or modify file contents. The token should be embedded in your Custom GPT configuration.

## 📖 API Endpoints (summary)

| Method | Path                   | Description                                                                 | Auth required |
|--------|------------------------|------------------------------------------------------------------------------|----------------|
| GET    | `/files`               | List all files in root directory                                            | ✅ Yes          |
| GET    | `/files/{filename}`    | Read full content of a file                                                 | ✅ Yes          |
| POST   | `/files`               | Create a new file with optional initial content                             | ✅ Yes          |
| PUT    | `/files/{filename}`    | Replace content of an existing file (full content required, no diffs)       | ✅ Yes          |
| POST   | `/files/rename`        | Rename an existing file (atomic operation)                                  | ✅ Yes          |
| POST   | `/files/move`          | Move a file to another location                                             | ✅ Yes          |
| DELETE | `/files`               | Delete a file permanently                                                   | ✅ Yes          |
| POST   | `/commit`              | Commit all current changes to Git with a descriptive message                | ✅ Yes          |
| GET    | `/openapi.json`        | Get OpenAPI schema (for GPT tool integration)                               | ❌ No           |
| GET    | `/health`              | Check service health status                                                 | ❌ No           |

## 🤖 GPT Integration Guide

To integrate this API with a Custom GPT:
1. Upload or import `openapi.json` into the GPT tool definition. **Update the `servers.url` field to match your deployment domain/IP.**
2. Configure the `Authorization: Bearer <token>` header in your GPT setup.
3. Ensure the API server is reachable over HTTPS.
4. Your GPT will now be able to manage files and commit changes programmatically.

## 📄 License

MIT License.

## 🙌 Credits

Developed by Jan Chimiak.

---

For questions, improvements or ideas — feel free to open an issue or PR.