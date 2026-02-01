# 🐛 Hugs for Bugs - AI Document Classification System

An intelligent document classification system powered by AI with memory capabilities. Upload documents and get automatic classification using Azure OpenAI and vector-based semantic memory.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start (Docker)](#-quick-start-docker)
- [Environment Setup](#-environment-setup)
- [Running the Project](#-running-the-project)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

## ✨ Features

- 📄 **Document Processing** - Extract text from PDFs, images, and various document formats
- 🤖 **AI Classification** - Intelligent document classification using Azure OpenAI GPT models
- 🧠 **Memory Layer** - Vector-based semantic memory using Qdrant and mem0
- ⚡ **Async Processing** - Background task processing with Celery and Redis
- 🎨 **Modern UI** - React frontend with real-time updates via WebSocket

## 🏗️ Architecture

| Service | Description | Port |
|---------|-------------|------|
| **Backend (FastAPI)** | Main API server | 8000 |
| **Celery Worker** | Async task processing | - |
| **Redis** | Message broker & cache | 6379 |
| **Qdrant** | Vector database for memory | 6333, 6334 |
| **Frontend (React)** | Web UI | 3000 (prod) / 5173 (dev) |

## 📦 Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- Git

**For local development without Docker:**
- Python 3.10+
- Node.js 20+
- pnpm (`npm install -g pnpm`)
- Redis server
- Qdrant server

## 🚀 Quick Start (Docker)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd IB_Hackathon_Hugs_for_Bugs
```

### 2. Set Up Environment Variables

```bash
# Backend - copy example and edit with your API keys
cp backend/.env.example backend/.env

# Frontend - copy example
cp frontend/.env.example frontend/.env
```

### 3. Start All Services

```bash
# Build and start all containers
docker compose up -d

# View logs
docker compose logs -f
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |

## ⚙️ Environment Setup

### Backend Environment Variables

Create `backend/.env` with the following:

```env
# ===================
# Azure OpenAI Configuration
# ===================
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-5-chat
AZURE_OPENAI_DEPLOYMENT_EMBEDDINGS=text-embedding-3-small

# ===================
# OpenAI Configuration (for GraphBit/mem0)
# ===================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_LLM_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ===================
# mem0 Memory Layer
# ===================
MEM0_USER_ID=classifier_agent
MEM0_AGENT_ID=document_classifier

# ===================
# Database Configuration
# ===================
DATABASE_URL=sqlite:///./sql_app.db

# ===================
# Redis Configuration (Docker)
# ===================
REDIS_URL=redis://redis:6379/0

# ===================
# Qdrant Configuration (Docker)
# ===================
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

> **Note:** For local development without Docker, use `localhost` instead of `redis` and `qdrant` for the host values.

### Frontend Environment Variables

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SOCKET_URL=ws://localhost:8000/ws/1
```

## 🏃 Running the Project

### Option 1: Docker (Recommended)

```bash
# Production mode
docker compose up -d

# Development mode (with hot-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop all services
docker compose down

# Stop and remove volumes (clean start)
docker compose down -v

# View logs for specific service
docker compose logs -f backend
docker compose logs -f celery
```

### Option 2: Local Development (Without Docker)

#### Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# In a separate terminal, start Celery worker
celery -A app.celery_worker:celery_app worker --loglevel=info --pool=solo
```

#### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

## 📚 API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Development

### Docker Commands

```bash
# Rebuild specific service
docker compose build backend
docker compose up -d backend

# Access backend container shell
docker compose exec backend bash

# Access Redis CLI
docker compose exec redis redis-cli

# Run database migrations
docker compose exec backend alembic upgrade head

# Scale Celery workers
docker compose up -d --scale celery=3
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 📁 Project Structure

```
IB_Hackathon_Hugs_for_Bugs/
├── backend/
│   ├── Dockerfile
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic/              # Database migrations
│   └── app/
│       ├── main.py           # FastAPI application
│       ├── celery_worker.py  # Celery configuration
│       ├── tasks.py          # Celery tasks
│       ├── api/              # API routes
│       ├── agent/            # AI classification agent
│       ├── core/             # Core configurations
│       ├── data_process/     # Document extraction
│       ├── models/           # Database models
│       ├── services/         # Business logic
│       └── schemas/          # Pydantic schemas
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── nginx.conf
│   ├── .env.example
│   ├── package.json
│   └── src/
├── docker-compose.yml        # Main compose file
├── docker-compose.dev.yml    # Development overrides
└── README.md
```

## 🔍 Troubleshooting

### Common Issues

**1. Docker containers fail to start**
```bash
# Check logs for errors
docker compose logs

# Ensure ports are not in use
lsof -i :8000
lsof -i :6379
```

**2. Backend cannot connect to Redis/Qdrant**
- Ensure you're using `redis` and `qdrant` as hostnames in Docker
- For local development, use `localhost`

**3. API key errors**
- Verify your Azure OpenAI and OpenAI API keys in `backend/.env`
- Check that the deployment names match your Azure resources

**4. Frontend build fails (nginx.conf not found)**
- Ensure `frontend/nginx.conf` exists for production builds

**5. Database migration issues**
```bash
# Reset database (removes all data)
docker compose exec backend rm sql_app.db
docker compose exec backend alembic upgrade head
```

## 📄 License

This project was created for the Hugs for Bugs Hackathon.

## 👥 Team

Built by InfinitiBit team for the Hackathon.