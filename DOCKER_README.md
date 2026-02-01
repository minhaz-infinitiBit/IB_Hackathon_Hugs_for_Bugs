# Hugs for Bugs - Document Classification System

A full-stack document classification system using AI-powered extraction and classification with memory capabilities.

## 🏗️ Architecture

| Service | Description | Port |
|---------|-------------|------|
| **Backend (FastAPI)** | Main API server | 8000 |
| **Celery Worker** | Async task processing | - |
| **Celery Beat** | Task scheduler | - |
| **Redis** | Message broker & cache | 6379 |
| **Qdrant** | Vector database for memory | 6333, 6334 |
| **Frontend (React)** | Web UI | 3000 |
| **Flower** | Celery monitoring dashboard | 5555 |

## 📋 Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd IB_Hackathon_Hugs_for_Bugs
```

### 2. Configure Environment Variables

#### Backend Configuration

```bash
# Copy the example environment file
cp backend/.env.example backend/.env

# Edit with your API keys
nano backend/.env
```

Required environment variables:

```env
# Azure OpenAI (for document classification)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-5-chat

# OpenAI (for embeddings/memory)
OPENAI_API_KEY=your_openai_api_key
OPENAI_LLM_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### Frontend Configuration

```bash
# Create frontend environment file
echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env
```

### 3. Build and Run with Docker Compose

#### Production Mode

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Development Mode (with hot-reload)

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Flower Dashboard** | http://localhost:5555 |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |

## 🐳 Docker Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (clean start)
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# View logs for a specific service
docker-compose logs -f backend
docker-compose logs -f celery

# Restart a specific service
docker-compose restart backend
```

### Scaling Celery Workers

```bash
# Scale to 3 celery workers
docker-compose up -d --scale celery=3
```

### Shell Access

```bash
# Access backend container
docker-compose exec backend bash

# Access Redis CLI
docker-compose exec redis redis-cli

# Run database migrations
docker-compose exec backend alembic upgrade head
```

## 📁 Project Structure

```
IB_Hackathon_Hugs_for_Bugs/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
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
│   ├── .dockerignore
│   ├── nginx.conf
│   ├── package.json
│   └── src/
├── docker-compose.yml        # Main compose file
├── docker-compose.dev.yml    # Development overrides
├── .dockerignore
└── DOCKER_README.md
```

## 🔧 Configuration

### Environment Variables Reference

#### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./sql_app.db` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `QDRANT_HOST` | Qdrant server host | `qdrant` |
| `QDRANT_PORT` | Qdrant server port | `6333` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | - |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-5-chat` |
| `OPENAI_API_KEY` | OpenAI API key (for embeddings) | - |

#### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

## 🛠️ Development

### Running Without Docker

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in another terminal)
celery -A app.celery_worker.celery_app worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A app.celery_worker.celery_app beat --loglevel=info
```

#### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Running Services Individually with Docker

```bash
# Start only infrastructure services
docker-compose up -d redis qdrant

# Run backend locally connecting to Docker services
REDIS_URL=redis://localhost:6379/0 QDRANT_HOST=localhost uvicorn app.main:app --reload
```

## 🔍 Monitoring & Debugging

### View Service Status

```bash
docker-compose ps
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/

# Check Redis
docker-compose exec redis redis-cli ping

# Check Qdrant
curl http://localhost:6333/
```

### View Resource Usage

```bash
docker stats
```

## 🧹 Cleanup

```bash
# Stop all containers
docker-compose down

# Remove all containers, networks, and volumes
docker-compose down -v --remove-orphans

# Remove all images
docker-compose down --rmi all

# Clean Docker system (careful - removes all unused Docker resources)
docker system prune -af
```

## 🐛 Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

**2. Container fails to start**
```bash
# Check logs
docker-compose logs <service-name>

# Rebuild the container
docker-compose build --no-cache <service-name>
```

**3. Redis connection refused**
```bash
# Ensure Redis is running
docker-compose up -d redis
docker-compose logs redis
```

**4. Qdrant memory issues**
```bash
# Increase Docker memory limit or add to Qdrant service:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

**5. Frontend can't connect to backend**
- Ensure `VITE_API_BASE_URL` is set correctly
- Check CORS settings in backend

## 📝 License

[Your License Here]

## 👥 Contributors

- Hugs for Bugs Team
