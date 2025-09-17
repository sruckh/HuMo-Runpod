# ARCHITECTURE.md

## Tech Stack
- **Primary Language**: Python 3.11
- **Deep Learning Framework**: PyTorch 2.5.1 with CUDA 12.4 support
- **Web Framework**: Gradio (user interface)
- **Video Processing**: FFmpeg (via conda-forge)
- **Container Runtime**: Docker with NVIDIA CUDA support
- **Infrastructure**: RunPod GPU cloud platform
- **Build Tools**: Conda, pip, Docker
- **Model Hub**: Hugging Face for AI model downloads

## Directory Structure
```
/opt/docker/HuMo/
├── Dockerfile              # Container specification
├── generate.yaml           # Model configuration parameters
├── .env                    # Environment variables (Docker Hub credentials)
├── scripts/                # Inference and utility scripts
│   ├── infer_ta.sh         # Text+Audio mode inference
│   └── infer_tia.sh        # Text+Image+Audio mode inference
├── weights/                # Local model weights storage
├── CLAUDE.md              # AI development guidance
├── CONDUCTOR.md           # Project documentation framework
├── ARCHITECTURE.md        # System architecture (this file)
├── BUILD.md               # Build and deployment instructions
├── CONFIG.md              # Runtime configuration
├── TEST.md                # Testing strategies
├── GOALS.md               # Project goals and objectives
├── JOURNAL.md             # Development journal
└── .github/               # CI/CD workflows
    └── workflows/
        └── docker-build.yml
```

## Key Architectural Decisions

### Container-Based Deployment
**Context**: Need for portable GPU-accelerated AI model deployment
**Decision**: Use Docker with NVIDIA CUDA runtime instead of bare-metal
**Rationale**: Ensures consistency across development and production environments
**Consequences**: Larger image size but improved portability and reproducibility

### Model Download at Runtime
**Context**: Large model weights (multi-GB) not suitable for git storage
**Decision**: Download models from Hugging Face at container startup
**Rationale**: Keeps git repository small, ensures latest model versions
**Consequences**: Longer startup time, requires internet access during deployment

### Gradio Web Interface
**Context**: Need for user-friendly interface without complex frontend development
**Decision**: Use Gradio instead of custom web application
**Rationale**: Rapid development, built-in file handling, good for AI demos
**Consequences**: Limited customization, but faster time-to-market

## Component Architecture

### Docker Container Structure <!-- #docker-structure -->
```dockerfile
# Dockerfile (lines 1-60)
FROM nvidia/cuda:12.5.1-cudnn-devel-ubuntu22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git curl wget ca-certificates tini && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY . /workspace
RUN mkdir -p /workspace/weights /workspace/output \
    && chmod +x /workspace/docker/entrypoint.sh /workspace/docker/runtime_setup.sh
ENV CONDA_DIR=/opt/conda \
    CONDA_ENV_NAME=humo \
    MODEL_CACHE_DIR=/workspace/weights \
    OUTPUT_DIR=/workspace/output \
    HUGGINGFACE_CACHE=/workspace/weights/.cache \
    STARTUP_COMMAND="python /workspace/app/gradio_app.py"
ENTRYPOINT ["/usr/bin/tini", "--", "bash", "/workspace/docker/entrypoint.sh"]
```

### Inference Scripts Structure <!-- #inference-scripts -->
```bash
# scripts/infer_ta.sh (lines 1-120)
#!/usr/bin/env bash
python scripts/run_inference.py \
  --mode TA \
  --prompt "A dancer performs energetic hip hop moves" \
  --audio /data/track.wav \
  --config configs/generate.yaml \
  --output-dir /workspace/output/run1 \
  --variant 1.7B
```

### Model Configuration Structure <!-- #model-config -->
```yaml
# generate.yaml (lines 1-40)
model:
  variant: "1.7B"

inputs:
  prompt: ""
  audio_path: ""
  image_path: ""

generation:
  mode: "TA"
  frames: 64
  scale_a: 1.0
  scale_t: 7.5
  height: 720
  width: 1280
  fps: 24

dit:
  sp_size: 1

diffusion:
  timesteps:
    sampling:
      steps: 25
```

## System Flow Diagram
```
[User] -> [Gradio Web UI] -> [Inference Scripts] -> [PyTorch Models]
   |            |                 |                   |
   v            v                 v                   v
[Browser] <- [Video Output] <- [FFmpeg Processing] <- [Hugging Face Hub]
                                                    |
                                                    v
                                               [Local Weights/]
```

## Model Integration Architecture
```
Hugging Face Hub
    ↓ (download at runtime)
Local Storage (./weights/)
    ↓ (load into memory)
PyTorch Model Cache
    ↓ (inference)
Text/Audio Input → Model Forward Pass → Video Output
    ↓
FFmpeg Post-processing → Final Video File
```

## Common Patterns

### Model Download Pattern
**When to use**: Container startup or first-time model access
**Implementation**: Check local weights directory, download if missing
**Example**: `scripts/download_models.py:lines 20-50`

### Inference Parameter Pattern
**When to use**: All model inference calls
**Implementation**: Load from generate.yaml, validate, pass to model
**Example**: `scripts/inference_base.py:lines 100-150`

### Video Processing Pipeline
**When to use**: Post-processing of model outputs
**Implementation**: Model frames → FFmpeg processing → Format conversion
**Example**: `scripts/video_utils.py:lines 200-250`

## Keywords <!-- #keywords -->
- AI video generation
- PyTorch CUDA
- Docker containers
- Gradio interface
- Hugging Face models
- RunPod deployment
- Text-to-video
- Human motion generation
- FFmpeg processing
- Model downloading
- GPU acceleration
- Container orchestration
