# Docker Setup Guide

## Prerequisites

- Docker Desktop installed and running
- Git installed

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/RathodRonakiiitv/E-commerce-review-analysis.git
cd E-commerce-review-analysis
```

### 2. Set Up Environment Variables

```bash
# Copy the example env file
cp backend/.env.example backend/.env

# Edit the .env file and add your Groq API key
# GROQ_API_KEY=your_actual_api_key_here
```

### 3. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 4. Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Useful Docker Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild a specific service
docker-compose up --build backend
docker-compose up --build frontend

# Remove all containers and volumes
docker-compose down -v

# Access backend container shell
docker-compose exec backend /bin/bash

# Access frontend container shell
docker-compose exec frontend /bin/sh
```

## Architecture

The Docker setup includes:

- **Backend**: FastAPI server with Python 3.12
- **Frontend**: React + Vite development server with Node.js 20
- **Volumes**: Persistent data storage for database

## Troubleshooting

### Port Conflicts

If ports 3001 or 8000 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000" # Change 8000 to 8001
  frontend:
    ports:
      - "3002:3001" # Change 3001 to 3002
```

### Build Errors

```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up
```

## Production Deployment

For production, modify the docker-compose.yml to:

1. Remove volume mounts for source code
2. Change frontend to build mode instead of dev mode
3. Add Nginx reverse proxy
4. Use environment-specific configuration files

## Environment Variables

Create a `.env` file in the backend directory:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///./reviews.db
CORS_ORIGINS=http://localhost:3001
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
```

## Notes

- First startup may take longer as it downloads ML models
- The backend uses UTF-8 encoding for Windows compatibility
- SQLite database is stored in a Docker volume for persistence
