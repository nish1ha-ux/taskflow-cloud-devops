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

## 📦 Deployment & CI/CD Status

[![TaskFlow CI/CD](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/workflows/ci.yml)

### Production Endpoint
- **Live URL**: [https://13-233-154-188.nip.io](https://13-233-154-188.nip.io)
- **Health Check**: [https://13-233-154-188.nip.io/health](https://13-233-154-188.nip.io/health)

---

## 🔒 Why Immutable Commit-SHA Tags are Safer than `latest`

In production container delivery pipelines, tagging container images with the exact Git commit SHA (e.g. `ghcr.io/nish1ha-ux/taskflow:452f2721783df18e01c4363b0529ebbe91d3c4ef`) is substantially safer than relying on mutable tags such as `latest`:

1. **True Immutability & Determinism**:
   The `latest` tag is a mutable pointer that gets overwritten on every pipeline build. If two deployments pull `latest` at different times, or if a cluster node has cached an older version of `latest`, different nodes may run completely different application binaries under the same tag name. Commit-SHA tags are immutable and uniquely bound to a single source commit.

2. **Reliable Rollbacks**:
   If a production bug occurs, rolling back to a previous version using `latest` is impossible without rebuilding. With commit-SHA tags, rolling back is as simple as re-deploying the exact image tag of the last known healthy commit (e.g. `APP_IMAGE=ghcr.io/.../taskflow:0285019...`).

3. **Complete Auditability & Traceability**:
   Inspecting any running container immediately reveals its exact source code version, git commit history, and corresponding CI/CD test results.

4. **Cache Invalidation Safety**:
   Docker daemons frequently skip pulling `latest` if a local image tagged `latest` already exists unless explicitly forced. SHA-specific image tags eliminate ambiguous cache states.

---

## ⚙️ CI/CD Pipeline Architecture & Evidence

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

1. **Lint and Test**:
   - Sets up Python 3.11 environment.
   - Runs `flake8 app tests` for PEP 8 styling and line-length limits.
   - Runs `pytest -q` executing all 21 unit, integration, and route validation tests.
2. **Validate Compose**:
   - `needs: lint-and-test` — blocks downstream stages if lint or tests fail.
   - Runs `docker compose config --quiet` to validate syntax and volume mapping.
3. **Build and Push Docker Image**:
   - `needs: compose-check`
   - Authenticates to GitHub Container Registry (`ghcr.io`) using `GITHUB_TOKEN` with `packages: write` permissions.
   - Builds container image with multi-stage Buildx caching.
   - Pushes both `latest` and full Git commit SHA (`${{ github.sha }}`) tags.
4. **Deploy to EC2**:
   - `needs: build-and-push`
   - Secure SSH deployment to AWS EC2 instance.
   - Executes idempotent `deploy.sh` script, restarts containers with zero-downtime, and verifies `/health` endpoint over HTTPS.

### Genuine GitHub Actions Run Evidence

- **Successful Runs (Passed Validation & Deployed)**:
  - [Run #35 (Commit `452f272`)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/runs/37999730252) — CI/CD Pipeline Success (Lint, Test, Compose, Image Push, EC2 Deploy).
  - [Run #34 (Commit `0285019`)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/runs/37999024708) — System Overview Page Deployment.
  - [Run #33 (Commit `d0452c7`)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/runs/37997517600) — UI Polish & Task Editing Deployment.
- **Failed Runs (Captured CI Failure & Blocked Deployment)**:
  - [Run #25 (Commit `62ded92`)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/runs/37990164837) — SSH Host Authentication Failure.
  - [Run #24 (Commit `8de3913`)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/runs/37990006504) — Host Key Verification Failure.
  - [Run #22 (Commit `6194d6d`)](https://github.com/nish1ha-ux/taskflow-cloud-devops/actions/runs/37989319728) — Docker Login Permission Failure.

---

## 🌐 Application Routes

| Method | Path                | Description                                       | Requires DB |
|--------|---------------------|---------------------------------------------------|-------------|
| GET    | `/`                 | Main Tasks view (create, list, edit, filter)      | No (UI)     |
| GET    | `/dashboard`        | Dashboard metrics, analytics & recent tasks table | No (UI)     |
| GET    | `/settings`         | Workspace preferences & appearance settings       | No (UI)     |
| GET    | `/system-overview`  | Cloud & DevOps platform architecture & health     | No (UI)     |
| GET    | `/health`           | Health check (probes PostgreSQL connectivity)     | Yes         |
| GET    | `/tasks`            | List all tasks as JSON                            | Yes         |
| POST   | `/tasks`            | Create task (title, description, deadline)        | Yes         |
| PUT    | `/tasks/<id>`       | Update task details (title, desc, deadline)       | Yes         |
| DELETE | `/tasks/<id>`       | Delete task by ID                                 | Yes         |

### Environment Variables

| Variable       | Required | Description                                               |
|----------------|----------|-----------------------------------------------------------|
| `DATABASE_URL` | Yes      | PostgreSQL connection string (`postgresql://...`)         |
| `NGINX_CONF`   | No       | Nginx config file (`http.conf` or `https.conf`)           |
| `APP_IMAGE`    | No       | Specific container image tag to run (used in CD pipeline) |

---

## 🖥️ Local Development (without Docker)

You can run the test suite and linter on Windows or Linux without Docker or PostgreSQL:

### 1. Install dependencies

```bash
pip install -r app/requirements.txt
pip install flake8 pytest
```

### 2. Run the test suite

```bash
pytest -v
```

### 3. Run the linter

```bash
flake8 app tests
```

---

## 🛡️ Track A Verification & Security Standards

- **Ports**: Only **80** (HTTP) and **443** (HTTPS) exposed to public Internet. Database (`5432`) and Flask app (`8000`) are isolated in the internal Docker bridge network `taskflow_net`.
- **TLS / HTTPS**: Let's Encrypt automated certificate issued for `13-233-154-188.nip.io`.
- **HTTP Redirect**: Nginx automatically redirects all port 80 traffic to HTTPS with `301 Moved Permanently`.
- **Reverse Proxy Headers**: `X-Forwarded-For`, `X-Forwarded-Proto`, and `Host` headers configured; Werkzeug `ProxyFix` active in Flask app for real client IP logging.
- **Idempotency**: `scripts/deploy.sh` safely handles state transitions, restarts containers with `--force-recreate`, and checks health before exiting.

