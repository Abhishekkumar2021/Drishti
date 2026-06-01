# Drishti Deployment Guide

This guide covers deploying Drishti to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker Compose)](#quick-start-docker-compose)
3. [Environment Configuration](#environment-configuration)
4. [Cloud Deployment](#cloud-deployment)
5. [Scaling](#scaling)
6. [Monitoring](#monitoring)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 50 GB SSD | 100+ GB SSD |
| Docker | 24.0+ | Latest |
| Docker Compose | 2.20+ | Latest |

### Required API Keys

At minimum, you need ONE of the following LLM providers:

- **Anthropic API Key** (recommended): [console.anthropic.com](https://console.anthropic.com)
- **OpenAI API Key**: [platform.openai.com](https://platform.openai.com)

For local-only deployment, you can use **Ollama** instead (no API key required).

---

## Quick Start (Docker Compose)

### 1. Clone the Repository

```bash
git clone https://github.com/Abhishekkumar2021/Drishti.git
cd Drishti
```

### 2. Create Environment File

```bash
cp .env.example .env.prod
```

Edit `.env.prod` with your configuration:

```bash
# Required: Database password
POSTGRES_PASSWORD=your-secure-password-here

# Required: Object storage credentials
MINIO_ROOT_USER=drishti
MINIO_ROOT_PASSWORD=your-secure-password-here

# Required: Graph database password
NEO4J_PASSWORD=your-secure-password-here

# Required: JWT secret for authentication
JWT_SECRET_KEY=$(openssl rand -hex 32)

# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...

# Optional: API token for authentication
API_TOKEN=your-api-token
```

### 3. Start Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Verify Deployment

```bash
# Check service health
docker compose -f docker-compose.prod.yml ps

# Check API health
curl http://localhost:8000/health/ready

# Run demo seeding (optional)
python scripts/seed_demo.py
```

### 5. Access the Application

- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Environment Configuration

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_HOST` | API bind address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |

### Database

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `DATABASE_POOL_SIZE` | Connection pool size | No (5) |

### Vector Database (Qdrant)

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_HOST` | Qdrant hostname | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `QDRANT_COLLECTION_NAME` | Collection name | `drishti_chunks` |

### Cache (Redis)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CACHE_ENABLED` | Enable caching | `true` |
| `CACHE_TTL_SECONDS` | Cache TTL | `3600` |

### Object Storage (MinIO)

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_MINIO` | Enable MinIO | `false` |
| `MINIO_ENDPOINT` | MinIO endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | Access key | Required |
| `MINIO_SECRET_KEY` | Secret key | Required |
| `MINIO_BUCKET` | Bucket name | `drishti-artifacts` |

### Graph Database (Neo4j)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_ENABLED` | Enable Neo4j | `false` |
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Username | `neo4j` |
| `NEO4J_PASSWORD` | Password | Required |

### LLM Providers

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | Provider: `anthropic`, `openai`, `ollama` |
| `LLM_MODEL` | Model name (e.g., `claude-sonnet-4-20250514`) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |

### Embedding Providers

| Variable | Description |
|----------|-------------|
| `EMBEDDING_PROVIDER` | Provider: `openai`, `cohere`, `ollama` |
| `EMBEDDING_MODEL` | Model name |
| `EMBEDDING_DIMENSIONS` | Vector dimensions |

### Authentication

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | JWT signing key (required) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret |

### Observability

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_ENABLED` | Enable OpenTelemetry | `false` |
| `STRUCTURED_LOGGING` | JSON logging | `true` |

---

## Cloud Deployment

### AWS (ECS/Fargate)

1. Push images to ECR:
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag drishti-api:latest <account>.dkr.ecr.<region>.amazonaws.com/drishti-api:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/drishti-api:latest
```

2. Create ECS task definitions for each service
3. Configure ALB for routing
4. Use RDS for PostgreSQL, ElastiCache for Redis
5. Use S3 instead of MinIO (configure `MINIO_ENDPOINT` to S3)

### Google Cloud (Cloud Run)

1. Push to Artifact Registry:
```bash
gcloud auth configure-docker <region>-docker.pkg.dev
docker tag drishti-api:latest <region>-docker.pkg.dev/<project>/drishti/api:latest
docker push <region>-docker.pkg.dev/<project>/drishti/api:latest
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy drishti-api \
  --image=<region>-docker.pkg.dev/<project>/drishti/api:latest \
  --platform=managed \
  --region=<region> \
  --allow-unauthenticated
```

3. Use Cloud SQL for PostgreSQL, Memorystore for Redis

### Kubernetes (Helm)

A Helm chart is planned for future releases. For now, convert the Docker Compose to Kubernetes manifests:

```bash
kompose convert -f docker-compose.prod.yml
kubectl apply -f .
```

---

## Scaling

### Horizontal Scaling

The API service can be horizontally scaled:

```yaml
# docker-compose.prod.yml
services:
  drishti-api:
    deploy:
      replicas: 3
```

### Database Scaling

- **PostgreSQL**: Use read replicas for read-heavy workloads
- **Qdrant**: Configure sharding for large vector collections
- **Redis**: Use Redis Cluster for high availability

### Resource Limits

Adjust resource limits based on workload:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

---

## Monitoring

### Health Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health/live` | Liveness probe |
| `/health/ready` | Readiness probe (checks dependencies) |

### Logging

Logs are output in JSON format by default. Configure your log aggregator to collect from stdout.

Example Loki/Promtail configuration:
```yaml
scrape_configs:
  - job_name: drishti
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: [__meta_docker_container_name]
        target_label: container
```

### Metrics (OpenTelemetry)

Enable OTEL for distributed tracing:

```bash
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

---

## Backup & Recovery

### PostgreSQL

```bash
# Backup
docker exec drishti-postgres pg_dump -U drishti drishti > backup.sql

# Restore
docker exec -i drishti-postgres psql -U drishti drishti < backup.sql
```

### Qdrant

Qdrant data is stored in `/qdrant/storage`. Back up the volume:

```bash
docker run --rm -v drishti_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant-backup.tar.gz /data
```

### MinIO

```bash
# Using mc (MinIO Client)
mc mirror drishti-minio/drishti-artifacts ./backup/minio/
```

---

## Troubleshooting

### Common Issues

**API not starting:**
```bash
# Check logs
docker logs drishti-api

# Common causes:
# - Missing environment variables
# - Database not ready
# - Invalid API keys
```

**Database connection issues:**
```bash
# Check PostgreSQL is running
docker exec drishti-postgres pg_isready -U drishti

# Check connection string
docker exec drishti-api env | grep DATABASE_URL
```

**Qdrant not responding:**
```bash
# Check Qdrant health
curl http://localhost:6333/healthz

# Check collection exists
curl http://localhost:6333/collections
```

**Out of memory:**
```bash
# Increase memory limits in docker-compose.prod.yml
# or scale horizontally
```

### Getting Help

- GitHub Issues: [github.com/Abhishekkumar2021/Drishti/issues](https://github.com/Abhishekkumar2021/Drishti/issues)
- Documentation: [docs/](../README.md)

---

## Security Checklist

- [ ] Use strong, unique passwords for all services
- [ ] Enable TLS/HTTPS in production
- [ ] Set up firewall rules to restrict access
- [ ] Use secrets management (e.g., HashiCorp Vault, AWS Secrets Manager)
- [ ] Enable authentication (`API_TOKEN` or OIDC)
- [ ] Regular security updates for base images
- [ ] Audit logs enabled
- [ ] Rate limiting configured
