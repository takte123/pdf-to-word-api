# PDF to Word Converter API

A production-ready REST API for converting PDF files to Word (DOCX) format using FastAPI and open-source tools.

## Features

- PDF to DOCX conversion using `pdf2docx` (primary) and LibreOffice (fallback)
- Async file processing with background tasks
- API key authentication
- Rate limiting
- File validation and security
- Auto-cleanup of old files
- Health check endpoint
- Docker support for easy deployment

## Tech Stack

- Python 3.11+
- FastAPI
- pdf2docx
- LibreOffice (headless)
- Redis (optional, for rate limiting)
- Docker

## Quick Start

### Using Docker

```bash
docker-compose up --build
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install LibreOffice:
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y libreoffice

# macOS
brew install --cask libreoffice
```

3. Run the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### POST /convert/pdf-to-word
Convert a PDF file to DOCX format.

**Headers:**
- `X-API-Key`: Your API key (default: `dev-api-key-change-in-production`)

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file, max 20MB)

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Body: DOCX file download

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `dev-api-key-change-in-production` |
| `MAX_FILE_SIZE` | Maximum upload size in bytes | `20971520` (20MB) |
| `FILE_RETENTION_MINUTES` | Auto-delete files after X minutes | `30` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Deployment

### AWS ECS/Fargate

1. Build and push Docker image to ECR
2. Create ECS cluster and task definition
3. Configure ALB with health checks

### Render

1. Create new Web Service
2. Connect your repository
3. Set environment variables
4. Deploy

### Railway

1. Create new project
2. Add Redis plugin (optional)
3. Deploy from GitHub

### VPS (Ubuntu)

```bash
# Clone repository
git clone <your-repo>
cd pdf-to-word-api

# Install Docker
curl -fsSL https://get.docker.com | sh

# Run
docker-compose up -d
```

## License

MIT
