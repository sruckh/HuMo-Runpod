# Build Guide

## Prerequisites
- Docker 24+
- NVIDIA Container Toolkit (for GPU testing)
- Access to Docker Hub (for pushing images)

## Build Commands

### Local build
```bash
docker build -t gemneye/humo-runpod:local .
```

### Build with cache busting
```bash
docker build --no-cache -t gemneye/humo-runpod:local .
```

### Publish manually
```bash
docker tag gemneye/humo-runpod:local gemneye/humo-runpod:latest
docker push gemneye/humo-runpod:latest
```

## Running Locally
```bash
docker run \
  --gpus all \
  -p 7860:7860 \
  -e HUGGINGFACE_TOKEN=hf_xxx \
  -e GRADIO_SHARE=false \
  gemneye/humo-runpod:local
```

Set `FORCE_RUNTIME_SETUP=1` to rerun the bootstrap process, or `SKIP_MODEL_DOWNLOAD=1` to bypass weight downloads when testing startup logic.

## Continuous Integration
GitHub Actions workflow `.github/workflows/docker.yml` triggers on pushes to `main` or `v*` tags. It logs into Docker Hub using repository secrets and publishes multi-tag images (`latest`, tag-based, and `sha`). Use the **Run workflow** button in the Actions tab for manual releases (`workflow_dispatch`).
