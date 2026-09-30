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
