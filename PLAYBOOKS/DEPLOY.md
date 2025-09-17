# DEPLOY.md

## Deployment Playbook

### Overview
This playbook provides step-by-step procedures for deploying the HuMo video generation system to RunPod GPU cloud platform.

## Pre-Deployment Checklist

### Environment Preparation
- [ ] Docker Hub account with push access
- [ ] Hugging Face account with model access tokens
- [ ] RunPod account with API key
- [ ] NVIDIA GPU drivers installed locally
- [ ] Docker with NVIDIA runtime configured
- [ ] Git repository access and write permissions

### Security Verification
- [ ] No hardcoded credentials in codebase
- [ ] .gitignore properly configured
- [ ] Environment variables documented
- [ ] Container security scan completed
- [ ] Model access permissions verified

### Build Validation
- [ ] Local Docker build successful
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Model download and loading verified
- [ ] GPU acceleration functional

## Deployment Options

### Option 1: Automated Deployment (Recommended)
```bash
# 1. Set environment variables
export DOCKERHUB_USERNAME="your_username"
export DOCKERHUB_TOKEN="your_token"
export HUGGINGFACE_TOKEN="your_hf_token"
export RUNPOD_API_KEY="your_runpod_key"

# 2. Build and push Docker image
docker build -t gemneye/seedvr-runpod:latest .
docker push gemneye/seedvr-runpod:latest

# 3. Deploy to RunPod using API
python scripts/deploy_to_runpod.py
```

### Option 2: Manual Deployment via RunPod Web UI
```bash
# 1. Build Docker image locally
docker build -t gemneye/seedvr-runpod:latest .

# 2. Save image for upload
docker save -o humo-docker-image.tar gemneye/seedvr-runpod:latest

# 3. Upload to RunPod Web Template
#    - Go to RunPod Web UI
#    - Create new template
#    - Upload the Docker image
#    - Configure GPU settings
#    - Set environment variables
#    - Configure networking
```

### Option 3: GitHub Actions CI/CD Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to RunPod

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t gemneye/seedvr-runpod:latest .

      - name: Push to Docker Hub
        run: |
          echo ${{ secrets.DOCKERHUB_TOKEN }} | docker login -u ${{ secrets.DOCKERHUB_USERNAME }} --password-stdin
          docker push gemneye/seedvr-runpod:latest

      - name: Deploy to RunPod
        run: |
          python scripts/deploy_to_runpod.py
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
```

## Deployment Steps

### Step 1: Image Build and Push
```bash
# Clone repository
git clone https://github.com/your-username/HuMo.git
cd HuMo

# Build Docker image
docker build -t gemneye/seedvr-runpod:latest .

# Test image locally
docker run --gpus all -p 7860:7860 gemneye/seedvr-runpod:latest

# Push to registry
echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin
docker push gemneye/seedvr-runpod:latest
```

### Step 2: RunPod Configuration
```yaml
# RunPod Template Configuration
name: HuMo Video Generation
image: gemneye/seedvr-runpod:latest

# GPU Settings
gpu_count: 1
gpu_type: "RTX 4090"  # or "A100", "A4000", etc.
gpu_memory: "24GB"

# Container Settings
ports:
  - "7860:7860"  # Gradio interface
  - "8080:8080"  # Health check

# Environment Variables
env:
  - "GRADIO_SHARE=false"
  - "HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}"
  - "MODEL_CACHE_DIR=/app/weights"
  - "OUTPUT_DIR=/app/outputs"

# Volume Mounting
volume_mounts:
  - source: "humo-weights"
    destination: "/app/weights"
    size: "50GB"
  - source: "humo-outputs"
    destination: "/app/outputs"
    size: "100GB"

# Health Checks
health_check:
  enabled: true
  interval: 30
  timeout: 10
  retries: 3
```

### Step 3: Deployment Script
```python
# scripts/deploy_to_runpod.py
import os
import requests
import json
from datetime import datetime

def deploy_to_runpod():
    """Deploy HuMo to RunPod using API"""

    # Configuration
    api_key = os.getenv('RUNPOD_API_KEY')
    image_name = 'gemneye/seedvr-runpod:latest'

    # RunPod API endpoints
    base_url = 'https://api.runpod.io/v2'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Create template
    template_data = {
        'name': 'HuMo Video Generation',
        'imageName': image_name,
        'gpuCount': 1,
        'gpuTypeId': 'NVIDIA GeForce RTX 4090',  # Adjust as needed
        'containerDiskInGb': 50,
        'volumeInGb': 100,
        'ports': '7860/http,8080/http',
        'env': [
            {'key': 'GRADIO_SHARE', 'value': 'false'},
            {'key': 'HUGGINGFACE_TOKEN', 'value': os.getenv('HUGGINGFACE_TOKEN')}
        ]
    }

    # Create template
    response = requests.post(
        f'{base_url}/templates',
        headers=headers,
        json=template_data
    )

    if response.status_code == 200:
        template_id = response.json()['id']
        print(f'Template created with ID: {template_id}')

        # Deploy endpoint
        deploy_data = {
            'templateId': template_id,
            'name': f'HuMo-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
        }

        deploy_response = requests.post(
            f'{base_url}/endpoints',
            headers=headers,
            json=deploy_data
        )

        if deploy_response.status_code == 200:
            endpoint = deploy_response.json()
            print(f'Endpoint deployed: {endpoint["url"]}')
            return endpoint
        else:
            print(f'Deployment failed: {deploy_response.text}')
            return None
    else:
        print(f'Template creation failed: {response.text}')
        return None

if __name__ == '__main__':
    deploy_to_runpod()
```

## Post-Deployment Verification

### Health Checks
```bash
# Check endpoint health
curl -f http://your-endpoint.runpod.net:8080/health || exit 1

# Check Gradio interface
curl -f http://your-endpoint.runpod.net:7860/ || exit 1

# Check model loading
curl -f http://your-endpoint.runpod.net:8080/models || exit 1
```

### Functional Testing
```bash
# Test model availability
curl -X POST http://your-endpoint.runpod.net:7860/api/test \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt"}'

# Test video generation workflow
curl -X POST http://your-endpoint.runpod.net:7860/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A person walking",
    "mode": "ta",
    "resolution": "480p"
  }'
```

### Performance Monitoring
```bash
# Monitor GPU usage
ssh your-endpoint.runpod.net
nvidia-smi

# Monitor container resources
docker stats humo-container

# Check logs
docker logs humo-container --tail 100 -f
```

## Rollback Procedures

### Emergency Rollback
```bash
# 1. Stop current deployment
curl -X DELETE https://api.runpod.io/v2/endpoints/{endpoint_id} \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}"

# 2. Deploy previous version
docker tag gemneye/seedvr-runpod:previous gemneye/seedvr-runpod:latest
docker push gemneye/seedvr-runpod:latest

# 3. Redeploy
python scripts/deploy_to_runpod.py
```

### Gradual Rollback
```bash
# 1. Deploy previous version alongside current
docker tag gemneye/seedvr-runpod:previous gemneye/seedvr-runpod:rollback
docker push gemneye/seedvr-runpod:rollback

# 2. Update RunPod template to use rollback image
# 3. Test rollback deployment
# 4. Switch traffic to rollback version
# 5. Monitor for issues
```

## Troubleshooting

### Common Issues

#### Container Fails to Start
```bash
# Check container logs
docker logs humo-container

# Common causes:
# - Missing environment variables
# - GPU driver issues
# - Model download failures
# - Port conflicts
```

#### Model Loading Issues
```bash
# Check model weights
ls -la /app/weights/

# Check GPU availability
nvidia-smi

# Check model access logs
grep "model" /app/logs/humo.log
```

#### Performance Issues
```bash
# Monitor GPU memory usage
watch -n 1 nvidia-smi

# Check inference times
grep "inference_time" /app/logs/humo.log

# Monitor system resources
htop
```

### Diagnostic Commands
```bash
# Full system diagnostics
python scripts/diagnostics.py

# Model validation
python scripts/validate_models.py

# Performance benchmark
python scripts/benchmark.py
```

## Monitoring and Alerting

### System Metrics
```yaml
# Key metrics to monitor
metrics:
  gpu_utilization:
    threshold: 80%
    alert: critical

  gpu_memory_usage:
    threshold: 90%
    alert: warning

  inference_time:
    threshold: 60s
    alert: warning

  error_rate:
    threshold: 5%
    alert: critical

  available_disk:
    threshold: 10GB
    alert: warning
```

### Log Monitoring
```bash
# Monitor key log patterns
tail -f /app/logs/humo.log | grep -E "(ERROR|CRITICAL|WARN)"

# Monitor model downloads
tail -f /app/logs/humo.log | grep "download"

# Monitor inference requests
tail -f /app/logs/humo.log | grep "inference"
```

### Health Check Endpoints
```python
# health_check.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    models_loaded: bool
    disk_space: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check GPU
        gpu_available = check_gpu_availability()

        # Check models
        models_loaded = check_model_status()

        # Check disk space
        disk_space = get_available_disk_space()

        return HealthResponse(
            status="healthy" if all([gpu_available, models_loaded, disk_space > 10_000_000_000]) else "unhealthy",
            gpu_available=gpu_available,
            models_loaded=models_loaded,
            disk_space=disk_space
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            gpu_available=False,
            models_loaded=False,
            disk_space=0
        )
```

## Keywords <!-- #keywords -->
- deployment playbook
- RunPod deployment
- Docker deployment
- GPU deployment
- cloud deployment
- CI/CD pipeline
- automated deployment
- container orchestration
- HuMo deployment
- video generation deployment
- PyTorch deployment
- model deployment
- monitoring
- health checks
- rollback procedures
- troubleshooting
- performance monitoring
- error handling
- infrastructure as code
- DevOps practices