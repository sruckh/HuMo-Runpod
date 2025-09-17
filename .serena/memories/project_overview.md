# HuMo Project Overview

## Project Purpose
Containerize the HuMo AI video generation system for deployment on RunPod GPU cloud platform. The project enables human motion video generation from text, audio, and optional image inputs using state-of-the-art AI models.

## Key Components
- **AI Model**: bytedance-research/HuMo for human motion generation
- **Video Generation**: Wan-AI/Wan2.1-T2V-1.3B for text-to-video synthesis  
- **Audio Processing**: openai/whisper-large-v3 for speech recognition
- **Vocal Separation**: huangjackson/Kim_Vocal_2 for audio processing
- **Web Interface**: Gradio UI for user interaction
- **Container**: Docker deployment with GPU support for RunPod

## Technology Stack
- **Language**: Python 3.11
- **ML Framework**: PyTorch 2.5.1 with CUDA 12.4
- **Container**: Docker with NVIDIA CUDA runtime
- **UI**: Gradio web framework
- **Deployment**: RunPod GPU cloud platform
- **Model Hub**: Hugging Face integration

## Project Structure
```
/opt/docker/HuMo/
├── scripts/
│   └── download_models.py    # Model downloading utility
├── PLAYBOOKS/
│   └── DEPLOY.md            # Deployment procedures
├── .serena/                 # Project configuration
├── requirements.txt         # Python dependencies
├── CLAUDE.md               # Claude Code guidance
├── CONDUCTOR.md            # Project documentation index
├── ARCHITECTURE.md         # System architecture
├── CONFIG.md               # Configuration guide
├── BUILD.md                # Build procedures
├── TEST.md                 # Testing strategy
├── CONTRIBUTING.md         # Development guidelines
├── ERRORS.md               # Error tracking
└── GOALS.md                # Project objectives and tasks
```

## Development Focus
- Docker containerization for GPU cloud deployment
- Automated model downloading and validation
- Gradio web interface for video generation
- RunPod platform optimization
- Security best practices and secret management