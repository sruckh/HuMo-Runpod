# HuMo Development Commands

## Python Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run model downloader
python scripts/download_models.py

# Check disk space for models
python -c "from scripts.download_models import ModelDownloader; ModelDownloader().check_disk_space()"
```

## Docker Development
```bash
# Build Docker image (to be implemented)
docker build -t gemneye/humo-runpod:latest .

# Test container locally (requires GPU)
docker run --gpus all -p 7860:7860 -e GRADIO_SHARE=false gemneye/humo-runpod:latest

# Save image for deployment
docker save -o humo-image.tar gemneye/humo-runpod:latest
```

## Model Management
```bash
# Validate model downloads
python -c "from scripts.download_models import ModelDownloader; downloader = ModelDownloader(); downloader.validate_downloads()"

# Download all models (requires HUGGINGFACE_TOKEN)
export HUGGINGFACE_TOKEN="your_token_here"
python scripts/download_models.py
```

## Testing Commands
```bash
# Run Python linting
flake8 scripts/

# Run type checking
mypy scripts/download_models.py

# Security scan (if implemented)
bandit -r scripts/
```

## Deployment Commands
```bash
# Push to Docker Hub
docker push gemneye/humo-runpod:latest

# Deploy to RunPod (via API or web UI)
# See PLAYBOOKS/DEPLOY.md for detailed procedures
```

## Environment Setup
```bash
# Required environment variables
export HUGGINGFACE_TOKEN="your_hf_token"
export DOCKER_USERNAME="your_docker_username"
export DOCKER_PASSWORD="your_docker_password"
export RUNPOD_API_KEY="your_runpod_key"
```

## Development Workflow
1. Set up environment variables
2. Install Python dependencies
3. Test model downloading functionality
4. Build and test Docker container locally
5. Deploy to RunPod for GPU testing
6. Validate inference and UI functionality