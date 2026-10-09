<div align="center">

# 🚀 TaskFlow

### Simple Task Management Application

**GeeksforGeeks KIIT — Cloud & DevOps Domain**  
**Foundation Project — Task 01**

<br>

![Track](https://img.shields.io/badge/Track-A%20%7C%20Ship%20It-2ea44f?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

</div>

---

## 👩‍💻 Student

| Details | Information |
|---|---|
| **Name** | Nishtha Bhushan |
| **Roll No.** | 24155262 |
| **Domain** | Cloud & DevOps |
| **Project** | Foundation Project — Task 01 |
| **Track** | 🚀 Track A — Ship It |

---

## 📌 About the Project

**TaskFlow** is a lightweight task management web application developed
as part of the GeeksforGeeks KIIT Cloud & DevOps Foundation Project.

The application allows users to create and view tasks through a simple
web interface. The main focus of this project is not the complexity of
the application itself, but the complete Cloud & DevOps workflow used to
build, containerize, deploy, secure, and automate it.

The project will progress from a local Ubuntu Server environment to a
Dockerized multi-service application deployed on AWS EC2, followed by
continuous integration and image delivery using GitHub Actions.

---

## 🎯 Project Objectives

- 🐧 Configure and harden an Ubuntu Server
- 🔐 Implement SSH key-based authentication
- 🛡️ Configure firewall rules using UFW
- 🐳 Containerize the application using Docker
- 📦 Create a multi-service Docker Compose stack
- 🗄️ Use PostgreSQL for persistent data storage
- ☁️ Deploy the application on AWS EC2
- ⚙️ Build a CI pipeline using GitHub Actions
- 📦 Push container images to GitHub Container Registry
- 🌐 Configure Nginx as a reverse proxy
- 🔒 Enable HTTPS using Let's Encrypt
- 🚀 Create an automated deployment script

---

## 🏗️ Architecture

> Architecture diagram will be added after the infrastructure is completed.

```text
                         🌐 INTERNET
                              │
                              ▼
                     ┌─────────────────┐
                     │      NGINX      │
                     │    :80 / :443   │
                     └────────┬────────┘
                              │
                       Reverse Proxy
                              │
                              ▼
                     ┌─────────────────┐
                     │   TASKFLOW APP  │
                     │      :8000      │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   PostgreSQL    │
                     │      :5432      │
                     └────────┬────────┘
                              │
                              ▼
                       💾 Named Volume
```

---

## 📦 Deployment

[![CI](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions)

### Deploy locally


1. **Edit the Certbot e‑mail**
   Open `docker-compose.yml` and replace `--email __YOUR_EMAIL_HERE__` with your real e‑mail address in the `certbot` service.

2. **Make the script executable**
   ```bash
   chmod +x scripts/deploy.sh
   ```

3. **Run the deployment script**
   ```bash
   ./scripts/deploy.sh
   ```
   The script will:
   * Pull the latest code and rebuild the Flask image.
   * Start the stack on ports **80** and **443** (initially HTTP‑only).
   * Wait for the HTTP `/health` endpoint to become healthy.
   * If a Let’s Encrypt certificate already exists, it will switch Nginx to the HTTPS configuration and verify the HTTPS health endpoint.
   * If the certificate is missing, the script will **not** run Certbot automatically. Instead it prints the exact command you must run manually:
   ```bash
   docker compose run --rm certbot
   ```
   After running the above command, re‑run `./scripts/deploy.sh` to switch to HTTPS.

## Notes

* PostgreSQL data lives in the external Docker volume `taskflow-cloud-devops_postgres_data`; the deployment script never removes or recreates this volume.
* Nginx selects its configuration via the environment variable `NGINX_CONF` (defaults to `default-http.conf`). The deploy script handles the switch to `default-https.conf` automatically when a certificate is present.
* Flask now uses `werkzeug.middleware.proxy_fix.ProxyFix` to correctly interpret `X‑Forwarded‑For`, `X‑Forwarded‑Proto`, etc., so real client IPs are logged.

---

## 🖥️ Local Development (without Docker)

You can run the test suite and linter on Windows **without Docker or PostgreSQL**.

### 1. Create a virtual environment (PowerShell)

```powershell
cd taskflow-cloud-devops
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r app/requirements.txt
pip install flake8 pytest
```

### 3. Run the tests

```powershell
pytest -v
```

### 4. Run the linter

```powershell
flake8 app
```

### 5. Run the application locally (requires PostgreSQL)

```powershell
$env:DATABASE_URL = "postgresql://taskflow:taskflow@localhost:5432/taskflow"
python app/app.py
```

The app starts on `http://localhost:8000`. A running PostgreSQL server is
required for routes that access the database.

---

## 🌐 Application Routes

| Method | Path      | Description                      | Requires DB |
|--------|-----------|----------------------------------|-------------|
| GET    | `/`       | Web UI (renders `index.html`)    | No          |
| GET    | `/health` | Health check (probes database)   | Yes         |
| GET    | `/tasks`  | List all tasks as JSON           | Yes         |
| POST   | `/tasks`  | Create a task (`{"title": "…"}`) | Yes         |

### Environment Variables

| Variable       | Required | Description                          |
|----------------|----------|--------------------------------------|
| `DATABASE_URL` | Yes      | PostgreSQL connection string         |
| `NGINX_CONF`   | No       | Nginx config file (default: `default-http.conf`) |

---

## ⚙️ CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

1. **Lint and Test** — installs dependencies, runs `flake8 app` and `pytest -q`.
2. **Validate Compose** — validates `docker-compose.yml` syntax.
3. **Build and Push Docker Image** — builds and pushes the Docker image to GHCR with dual tags (`latest` and immutable commit SHA).
4. **Deploy to EC2** — automated CD over SSH to the AWS EC2 instance, deploying the latest container image, verifying database volume persistence, and activating HTTPS with Let's Encrypt certificates.

---
