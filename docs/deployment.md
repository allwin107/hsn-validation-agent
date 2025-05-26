# Deployment Guide

## Overview

This guide covers deployment strategies for the HSN Code Validation Agent across different environments, from development to production-scale deployments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Scaling Strategies](#scaling-strategies)
- [Security Configuration](#security-configuration)
- [Troubleshooting](#troubleshooting)
- [Backup & Recovery](#backup--recovery)
- [CI/CD Pipeline](#cicd-pipeline)
- [Cost Optimization](#cost-optimization)

---

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ cores recommended for production)
- **Memory**: 2GB RAM minimum (4GB+ recommended)
- **Storage**: 1GB available space
- **Network**: HTTP/HTTPS access for API endpoints

### Software Dependencies

- **Python**: 3.8 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 1.29+ (for multi-container setup)

### Required Files

- HSN Master Dataset (`HSN_SAC.xlsx`)
- Application source code
- Configuration files (`.env`, `docker-compose.yml`)

---

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/allwin107/hsn-validation-agent.git
cd hsn-validation-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run application
python app.py
```

### Development Configuration

Create `.env` file:
```env
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
DATASET_PATH=data/HSN_SAC.xlsx
MAX_BATCH_SIZE=100
CACHE_TIMEOUT=3600
CORS_ORIGINS=*
```

### Hot Reload Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
flask run --reload --debug
```

---

## Docker Deployment

### Single Container

#### Build Image

```bash
# Build Docker image
docker build -t hsn-validation-agent:latest .

# Run container
docker run -d \
  --name hsn-agent \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e FLASK_ENV=production \
  hsn-validation-agent:latest
```

#### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### Multi-Container with Docker Compose

#### docker-compose.yml

```yaml
version: '3.8'

services:
  hsn-agent:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - hsn-agent
    restart: unless-stopped

volumes:
  redis_data:
```

#### Production Deployment

```bash
# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f hsn-agent

# Scale application
docker-compose up --scale hsn-agent=3
```

---

## Cloud Deployment

### AWS Deployment

#### EC2 Instance

```bash
# Launch EC2 instance (Ubuntu 20.04)
# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose

# Clone and deploy
git clone https://github.com/allwin107/hsn-validation-agent.git
cd hsn-validation-agent
sudo docker-compose up -d
```

#### ECS Deployment

```json
{
  "family": "hsn-validation-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "hsn-agent",
      "image": "your-account.dkr.ecr.region.amazonaws.com/hsn-validation-agent:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/hsn-validation-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Lambda Deployment (Serverless)

```yaml
# serverless.yml
service: hsn-validation-agent

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  timeout: 30
  memorySize: 1024

functions:
  validate:
    handler: lambda_handler.validate
    events:
      - http:
          path: validate
          method: post
          cors: true
  
  validate_list:
    handler: lambda_handler.validate_list
    events:
      - http:
          path: validate_list
          method: post
          cors: true

plugins:
  - serverless-python-requirements
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/hsn-validation-agent

# Deploy to Cloud Run
gcloud run deploy hsn-validation-agent \
  --image gcr.io/PROJECT-ID/hsn-validation-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

#### Kubernetes Engine

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hsn-validation-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hsn-validation-agent
  template:
    metadata:
      labels:
        app: hsn-validation-agent
    spec:
      containers:
      - name: hsn-agent
        image: gcr.io/PROJECT-ID/hsn-validation-agent:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: hsn-validation-service
spec:
  selector:
    app: hsn-validation-agent
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### Azure Deployment

#### Container Instances

```bash
# Create resource group
az group create --name hsn-rg --location eastus

# Deploy container
az container create \
  --resource-group hsn-rg \
  --name hsn-validation-agent \
  --image your-registry/hsn-validation-agent:latest \
  --cpu 1 \
  --memory 2 \
  --ports 5000 \
  --environment-variables FLASK_ENV=production
```

#### App Service

```bash
# Create App Service plan
az appservice plan create \
  --name hsn-plan \
  --resource-group hsn-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group hsn-rg \
  --plan hsn-plan \
  --name hsn-validation-agent \
  --deployment-container-image-name your-registry/hsn-validation-agent:latest
```

---

## Production Configuration

### Environment Variables

```env
# Production settings
FLASK_ENV=production
LOG_LEVEL=WARNING
DEBUG=False

# Database
DATASET_PATH=/app/data/HSN_SAC.xlsx

# Performance
MAX_BATCH_SIZE=100
CACHE_TIMEOUT=3600
WORKER_PROCESSES=4

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-newrelic-key

# External Services
REDIS_URL=redis://redis-server:6379/0
```

### Web Server Configuration

#### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

#### Nginx Configuration

```nginx
upstream hsn_agent {
    server 127.0.0.1:5000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5002 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://hsn_agent;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://hsn_agent;
        access_log off;
    }
}
```

---

## Monitoring & Logging

### Application Logging

```python
# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        # File handler
        file_handler = RotatingFileHandler(
            'logs/hsn_agent.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        app.logger.addHandler(console_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('HSN Validation Agent startup')
```

### Health Monitoring

```python
# health_check.py
from flask import jsonify
import psutil
import time

@app.route('/health')
def health_check():
    start_time = time.time()
    
    # Check dataset status
    dataset_status = {
        'loaded': df is not None,
        'records': len(df) if df is not None else 0
    }
    
    # System metrics
    system_metrics = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }
    
    response_time = (time.time() - start_time) * 1000
    
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'dataset': dataset_status,
        'system': system_metrics,
        'response_time_ms': response_time
    })
```

### Metrics Collection

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hsn-validation-agent'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

---

## Scaling Strategies

### Horizontal Scaling

#### Load Balancer Configuration

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - hsn-agent

  hsn-agent:
    build: .
    environment:
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
    deploy:
      replicas: 3
```

```bash
# Scale application
docker-compose up --scale hsn-agent=5
```

#### Auto-scaling with Kubernetes

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hsn-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hsn-validation-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

#### Resource Optimization

```yaml
# Resource limits for containers
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### Database Scaling

For large datasets (>100K records):

```python
# database_config.py
DATABASE_CONFIG = {
    'postgresql': {
        'host': 'localhost',
        'port': 5432,
        'database': 'hsn_codes',
        'user': 'hsn_user',
        'password': 'password',
        'pool_size': 20,
        'max_overflow': 30
    }
}
```

---

## Security Configuration

### SSL/TLS Setup

```bash
# Generate self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Let's Encrypt (production)
certbot --nginx -d api.yourdomain.com
```

### Environment Security

```env
# Secure environment variables
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://user:$(openssl rand -hex 16)@host:5432/db
API_KEY=$(openssl rand -hex 24)
```

### Container Security

```dockerfile
# Security-hardened Dockerfile
FROM python:3.9-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set secure permissions
COPY --chown=appuser:appuser . /app
USER appuser

# Security labels
LABEL security.non-root=true
LABEL security.no-new-privileges=true
```

---

## Troubleshooting

### Common Issues

#### Dataset Loading Errors

```bash
# Check file permissions
ls -la data/HSN_SAC.xlsx

# Verify file format
python -c "import pandas as pd; print(pd.read_excel('data/HSN_SAC.xlsx').head())"

# Check logs
docker logs hsn-agent
```

#### Memory Issues

```bash
# Monitor memory usage
docker stats hsn-agent

# Increase memory limit
docker run --memory="2g" hsn-validation-agent
```

#### Performance Issues

```bash
# Check application metrics
curl http://localhost:5000/health

# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/validate

# Profile memory usage
docker exec hsn-agent python -m memory_profiler app.py
```

#### Connection Issues

```bash
# Test connectivity
curl -I http://localhost:5000/health

# Check port binding
netstat -tlnp | grep 5000

# Verify container networking
docker network ls
docker network inspect bridge
```

#### SSL/TLS Issues

```bash
# Test SSL certificate
openssl s_client -connect api.yourdomain.com:443

# Check certificate expiry
openssl x509 -in cert.pem -text -noout

# Verify Nginx configuration
nginx -t
```

### Debugging Commands

```bash
# Container debugging
docker exec -it hsn-agent /bin/bash
docker logs --tail 100 hsn-agent

# Application debugging
python -m pdb app.py
python -m cProfile -o profile.stats app.py

# Network debugging
nslookup api.yourdomain.com
traceroute api.yourdomain.com
```

### Log Analysis

```bash
# Real-time log monitoring
tail -f logs/hsn_agent.log

# Error pattern analysis
grep ERROR logs/hsn_agent.log | head -20

# Performance analysis
awk '/response_time/ {print $4}' logs/hsn_agent.log | sort -n
```

---

## Backup & Recovery

### Data Backup Strategy

```bash
#!/bin/bash
# backup_script.sh

BACKUP_DIR="/backups/hsn-agent"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup dataset
cp data/HSN_SAC.xlsx $BACKUP_DIR/HSN_SAC_$DATE.xlsx

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml nginx.conf

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.xlsx" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Database Backup (PostgreSQL)

```bash
# Create database backup
pg_dump -h localhost -U hsn_user -d hsn_codes > backup_$(date +%Y%m%d).sql

# Restore database
psql -h localhost -U hsn_user -d hsn_codes < backup_20250526.sql
```

### Container State Backup

```bash
# Save container image
docker save hsn-validation-agent:latest | gzip > hsn-agent-backup.tar.gz

# Load container image
gunzip -c hsn-agent-backup.tar.gz | docker load
```

### Automated Backup with Cron

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup_script.sh

# Weekly full system backup
0 3 * * 0 /path/to/full_backup_script.sh
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy HSN Validation Agent

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
        python -m flake8 app.py
        python -m safety check
    
    - name: Run security scan
      run: bandit -r . -f json

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to DockerHub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: yourusername/hsn-validation-agent:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/hsn-validation-agent
          docker-compose pull
          docker-compose up -d
          docker system prune -f
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

test:
  stage: test
  image: python:3.9
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - python -m pytest tests/ -v
    - python -m flake8 app.py
  only:
    - merge_requests
    - main

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main

deploy_production:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache openssh-client
    - ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST "
        cd /opt/hsn-validation-agent &&
        docker-compose pull &&
        docker-compose up -d"
  only:
    - main
  when: manual
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'hsn-validation-agent'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    python -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt -r requirements-dev.txt
                    python -m pytest tests/ -v
                    python -m flake8 app.py
                '''
            }
        }
        
        stage('Build') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}")
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        image.push()
                        image.push("latest")
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    ssh deploy@production-server "
                        cd /opt/hsn-validation-agent &&
                        docker-compose pull &&
                        docker-compose up -d
                    "
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        failure {
            emailext (
                subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build failed. Check console output at ${env.BUILD_URL}",
                to: "devops@company.com"
            )
        }
    }
}
```

---

## Cost Optimization

### Cloud Resource Optimization

#### AWS Cost Optimization

```bash
# Use Spot Instances for non-critical workloads
aws ec2 request-spot-instances \
  --spot-price "0.05" \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification file://spot-specification.json

# Auto Scaling based on metrics
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name hsn-agent-asg \
  --min-size 1 \
  --max-size 5 \
  --desired-capacity 2
```

#### Resource Right-sizing

```yaml
# Kubernetes resource optimization
resources:
  requests:
    memory: "256Mi"  # Reduced from 512Mi
    cpu: "100m"      # Reduced from 250m
  limits:
    memory: "512Mi"  # Reduced from 1Gi
    cpu: "200m"      # Reduced from 500m
```

### Container Optimization

```dockerfile
# Multi-stage build for smaller images
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Monitoring Cost Impact

```python
# cost_monitor.py
import boto3
import json
from datetime import datetime, timedelta

def get_monthly_costs():
    client = boto3.client('ce', region_name='us-east-1')
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['BlendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )
    
    return response
```

---

## Maintenance Schedule

### Regular Maintenance Tasks

```bash
#!/bin/bash
# maintenance.sh - Run weekly

echo "Starting maintenance tasks..."

# Update system packages
apt update && apt upgrade -y

# Clean Docker system
docker system prune -f
docker volume prune -f

# Rotate logs
logrotate /etc/logrotate.d/hsn-agent

# Check disk space
df -h
du -sh /var/log/*

# Test application health
curl -f http://localhost:5000/health || echo "Health check failed"

# Update SSL certificates
certbot renew --dry-run

echo "Maintenance completed: $(date)"
```

### Performance Tuning

```python
# performance_tuning.py
import pandas as pd
from functools import lru_cache

# Optimize DataFrame loading
@lru_cache(maxsize=1)
def load_hsn_dataset():
    return pd.read_excel('data/HSN_SAC.xlsx', dtype={
        'HSN_CODE': 'category',
        'DESCRIPTION': 'string'
    })

# Enable DataFrame query optimization
pd.set_option('mode.copy_on_write', True)
```