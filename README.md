<div align="center">

# 🛡️ AegisCloud

### AI-Driven Container Vulnerability & Runtime Threat Defense Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.4-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![AWS](https://img.shields.io/badge/AWS-EC2%20|%20SNS%20|%20IAM-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> **AegisCloud** is a production-grade, full-stack cloud security platform that combines **static container vulnerability scanning**, **real-time runtime threat detection**, and **multi-provider AI threat intelligence** into a single unified system — built for modern DevSecOps teams securing containerized cloud infrastructure.

<br/>

[Features](#-features) · [Architecture](#-system-architecture) · [Tech Stack](#-technology-stack) · [Quick Start](#-quick-start) · [Screenshots](#-screenshots) · [API Docs](#-api-documentation) · [Cloud Setup](#-cloud-deployment) · [License](#-license)

</div>

---

## 🎯 Problem Statement

Modern applications run inside **Docker containers** deployed on cloud servers. These containers are fast and portable — but they carry a hidden danger:

- 🔴 **Most container images ship with hundreds of known CVE vulnerabilities** — outdated libraries, weak configurations, and unpatched dependencies that attackers actively exploit.
- 🔴 **Traditional security tools are blind to runtime attacks** — they only scan infrastructure before deployment, missing real-time threats like reverse shells, privilege escalation, and data exfiltration happening inside live containers.
- 🔴 **Security teams lack AI-powered tools** that can automatically explain threats in plain English and generate specific, actionable remediation steps.

> **There is no unified, intelligent platform that combines pre-deployment scanning, live runtime defense, and AI-powered threat analysis in a single system.**

**AegisCloud was built to close this gap.**

---

## ✨ Features

### 🔍 Static Vulnerability Scanning
- Scans Docker container images using **Trivy** (trusted by Google, Red Hat, Aqua Security)
- Detects CVEs across 300+ OS packages and application dependencies
- Classifies findings into **CRITICAL**, **HIGH**, **MEDIUM**, and **LOW** severity tiers
- Stores complete scan history with timestamps for compliance auditing

### ⚡ Runtime Threat Detection
- Integrates **CNCF Falco** daemon for real-time Linux system call monitoring
- Detects live container attacks: shell spawning, credential theft, privilege escalation, filesystem tampering
- Receives Falco alerts via webhook and broadcasts them to the dashboard in real-time
- Automatically triggers AWS SNS notifications for high-severity runtime events

### 🤖 Multi-Provider AI Threat Intelligence
- Translates raw CVE codes into **plain-English security reports** with 3-part analysis:
  1. **What It Is** — Human-readable threat explanation
  2. **Attack Scenario** — How an attacker would exploit it in Docker
  3. **Remediation Steps** — Step-by-step fix instructions
- Supports **three AI providers** with seamless switching:

  | Provider | Type | Use Case |
  |---|---|---|
  | **Groq API** | ☁️ Cloud LLM (Llama-3) | Ultra-fast inference, free tier |
  | **GCP Google Gemini** | ☁️ Cloud LLM (Gemini 1.5 Flash) | Google Cloud Platform AI |
  | **Ollama** | 🏠 Local Offline LLM | Data privacy — sensitive CVE data never leaves your network |

### 📊 Full Observability Stack
- **Prometheus** scrapes security and performance metrics every 15 seconds
- **Grafana** dashboards visualize vulnerability trends, alert frequencies, and system health
- **Vue.js** dashboard provides an integrated security command center with real-time WebSocket updates

### 🔔 Instant Cloud Alerting
- **AWS SNS** dispatches SMS and email notifications within seconds of threat detection
- Configurable alert thresholds — only CRITICAL and HIGH severity events trigger notifications
- Complete notification history stored in MongoDB for audit compliance

### 🔐 Enterprise Security Controls
- **JWT** (JSON Web Token) stateless authentication
- **RBAC** (Role-Based Access Control) with three permission tiers: `ADMIN`, `ANALYST`, `VIEWER`
- Bcrypt password hashing, token expiry management, and CORS policy enforcement
- Complete audit trail of all user actions stored in MongoDB

---

## 🏗️ System Architecture

AegisCloud follows a **5-layer microservices architecture** where each layer has a single responsibility:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 1 — PRESENTATION                               │
│         Vue.js 3 + Vuetify Dashboard  ·  Grafana Panels                │
│         JWT-Secured Login  ·  Role-Based Views  ·  WebSocket           │
├─────────────────────────────────────────────────────────────────────────┤
│                    LAYER 2 — API GATEWAY                                │
│         FastAPI (Python)  ·  RESTful Endpoints  ·  WebSocket Alerts    │
│         Prometheus /metrics  ·  OAuth2 Token Validation                │
├─────────────────────────────────────────────────────────────────────────┤
│                    LAYER 3 — SECURITY ENGINE                            │
│         Trivy (Static CVE Scanner)  ·  Falco (Runtime Defense)         │
│         Groq API + Google Gemini + Ollama (AI Analysis)                │
├─────────────────────────────────────────────────────────────────────────┤
│                    LAYER 4 — DATA LAYER                                 │
│         MongoDB (Events, Alerts, Audit Logs)                           │
│         Prometheus (Time-Series Metrics)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                    LAYER 5 — CLOUD & NOTIFICATIONS                      │
│         AWS EC2 (Hosting)  ·  AWS CloudWatch (Logs)                    │
│         AWS IAM (Access Control)  ·  AWS SNS (SMS/Email Alerts)        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Category | Technology | Purpose |
|:---|:---|:---|
| **Frontend** | Vue.js 3 + Vuetify 3 | Reactive security dashboard with Material Design |
| **Backend** | FastAPI (Python 3.11) | High-performance async REST API server |
| **Database** | MongoDB 7.0 | Flexible document storage for security events |
| **Vulnerability Scanner** | Trivy | Docker image CVE detection (300+ package types) |
| **Runtime Security** | Falco (CNCF) | Real-time container system call monitoring |
| **AI Tool 1** | Groq API | Fast cloud-based LLM threat analysis |
| **AI Tool 2** | GCP Google Gemini | Google Cloud Platform AI integration |
| **AI Tool 3** | Ollama | Local offline LLM for data privacy |
| **AI Framework** | LangChain | Structured prompt engineering for security context |
| **Monitoring** | Prometheus | Time-series metrics collection (15s intervals) |
| **Visualization** | Grafana | Live security dashboards and graphs |
| **Authentication** | JWT + Bcrypt | Stateless token auth with password hashing |
| **Authorization** | RBAC | Admin / Analyst / Viewer permission tiers |
| **Containerization** | Docker + Docker Compose | Multi-service orchestration |
| **Cloud Compute** | AWS EC2 | Production Linux server hosting |
| **Cloud Logging** | AWS CloudWatch | Infrastructure-level log management |
| **Cloud Access** | AWS IAM | Least-privilege access control policies |
| **Cloud Alerts** | AWS SNS | Instant SMS and email threat notifications |
| **CI/CD** | GitHub Actions | Automated testing and deployment pipeline |

---

## 🚀 Quick Start

### Prerequisites

- [Python 3.11+](https://python.org)
- [Node.js 18+](https://nodejs.org)
- [MongoDB](https://mongodb.com/try/download/community) (local or Atlas cloud)
- [Docker](https://docker.com) (optional, for containerized deployment)
- [Trivy](https://github.com/aquasecurity/trivy) (for real vulnerability scanning)

### Option 1: Run Locally (Development)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/aegiscloud.git
cd aegiscloud

# Setup Backend
cd backend
cp .env.example .env          # Configure your API keys in .env
pip install -r requirements.txt
python main.py                 # Starts on http://localhost:8000

# Setup Frontend (new terminal)
cd frontend
npm install
npm run dev                    # Starts on http://localhost:5173
```

### Option 2: Run with Docker Compose (Production)

```bash
# Clone and configure
git clone https://github.com/YOUR_USERNAME/aegiscloud.git
cd aegiscloud
cp .env.example backend/.env   # Configure your API keys

# Launch all services with one command
docker-compose up --build -d

# Access the platform
# Frontend:  http://localhost:5173
# API Docs:  http://localhost:8000/docs
# Grafana:   http://localhost:3000
# Prometheus: http://localhost:9090
```

### Default Login Credentials

| Username | Password | Role |
|:---|:---|:---|
| `admin` | `admin123` | ADMIN (Full Access) |

---

## 📸 Screenshots

### Security Dashboard
> Real-time overview with risk score, vulnerability severity distribution, active runtime alerts, and quick action shortcuts.

### Container Vulnerability Scanner
> Submit any Docker image name to trigger a Trivy scan. View CVE findings with severity classification and detailed scan history.

### Falco Runtime Alerts
> Live feed of runtime security events detected by Falco — shell spawning, credential access, privilege escalation attempts — with one-click acknowledgement.

### AI Threat Intelligence
> Analyze any CVE vulnerability using Groq API, Google Gemini, or local Ollama. AI generates plain-English threat explanations with step-by-step remediation instructions.

---

## 📖 API Documentation

AegisCloud exposes a fully documented REST API via **FastAPI's interactive Swagger UI**:

```
http://localhost:8000/docs
```

### Core Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/auth/login` | Authenticate and receive JWT token |
| `POST` | `/auth/register` | Register new user account |
| `GET` | `/auth/me` | Get current user profile |
| `POST` | `/scan/image` | Trigger Trivy vulnerability scan |
| `GET` | `/scan/results` | List all scan results |
| `GET` | `/scan/results/{id}/vulnerabilities` | Get CVEs for a scan |
| `POST` | `/alerts/falco` | Falco webhook receiver |
| `GET` | `/alerts` | List runtime security alerts |
| `PUT` | `/alerts/{id}/acknowledge` | Acknowledge an alert |
| `POST` | `/ai/analyze/vulnerability` | AI analysis of a CVE |
| `POST` | `/ai/analyze/custom` | Custom AI security analysis |
| `GET` | `/dashboard/overview` | Dashboard summary metrics |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/metrics` | Prometheus metrics endpoint |

---

## ☁️ Cloud Deployment

### AWS Services Configuration

| Service | Role in AegisCloud |
|:---|:---|
| **EC2** | Hosts all Docker containers on Ubuntu Linux |
| **CloudWatch** | Captures application and infrastructure logs |
| **IAM** | Manages AWS resource access with least-privilege policies |
| **SNS** | Delivers instant SMS/email alerts on critical threats |

### GCP Services Configuration

| Service | Role in AegisCloud |
|:---|:---|
| **Google Gemini API** | AI-powered vulnerability analysis and threat explanation |

### Environment Variables

All configuration is managed through environment variables. Copy `.env.example` to `backend/.env` and configure:

```env
# AI Providers (get free keys)
GROQ_API_KEY=gsk_...              # https://console.groq.com/keys
GOOGLE_API_KEY=AI...              # https://aistudio.google.com

# AWS Services
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_SNS_TOPIC_ARN=arn:aws:sns:...

# Database
MONGODB_URL=mongodb://localhost:27017
```

---

## 📂 Project Structure

```
aegiscloud/
├── backend/                    # FastAPI Python Backend
│   ├── app/
│   │   ├── routes/             # API endpoint handlers
│   │   ├── models/             # Pydantic data schemas
│   │   ├── services/           # Business logic (Trivy, AI, SNS, Falco)
│   │   ├── middleware/         # JWT auth & RBAC authorization
│   │   └── utils/              # Helper functions
│   ├── main.py                 # Application entry point
│   ├── Dockerfile              # Backend container image
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # Vue.js 3 Frontend
│   ├── src/
│   │   ├── views/              # Page components
│   │   ├── components/         # Reusable UI components
│   │   ├── services/           # Axios API clients
│   │   ├── store/              # Pinia state management
│   │   └── router/             # Vue Router configuration
│   ├── Dockerfile              # Frontend container image
│   └── package.json            # Node.js dependencies
│
├── monitoring/                 # Observability stack
│   ├── prometheus/             # Metrics collection config
│   └── grafana/                # Dashboard definitions
│
├── falco/                      # Runtime security rules
│   ├── falco.yaml              # Falco daemon configuration
│   └── falco_rules.yaml        # Custom threat detection rules
│
├── docker-compose.yml          # Multi-service orchestration
└── README.md                   # Project documentation
```

---

## 🔮 Future Roadmap

- [ ] **Kubernetes Security** — Integrate kube-bench and kube-hunter for K8s cluster scanning
- [ ] **Multi-Cloud Expansion** — Add Microsoft Azure and Google Cloud Platform support
- [ ] **Auto-Remediation** — Automatically patch LOW severity vulnerabilities
- [ ] **Fine-Tuned Security AI** — Train a custom LLM on CVE and vulnerability datasets
- [ ] **SIEM Integration** — Export alerts to Splunk, Elastic SIEM, or IBM QRadar
- [ ] **Mobile Application** — Real-time alert monitoring on iOS and Android
- [ ] **Compliance Automation** — Generate CIS Benchmarks, PCI-DSS, and SOC2 reports
- [ ] **Slack / Teams Integration** — Team notifications via collaboration platforms

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### 🛡️ AegisCloud — Securing the Cloud, One Container at a Time.

Built with ❤️ for the Cloud Computing Department | Academic Year 2025-2026

</div>
