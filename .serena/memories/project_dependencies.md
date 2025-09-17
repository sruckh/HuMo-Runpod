# HuMo Project Dependencies

## Core Python Dependencies

### AI/ML Framework
- **torch>=2.5.1**: Core deep learning framework with CUDA 12.4 support
- **torchvision>=0.20.1**: Computer vision utilities for PyTorch
- **torchaudio>=2.5.1**: Audio processing utilities for PyTorch
- **transformers>=4.35.0**: Hugging Face transformers for model loading
- **huggingface-hub>=0.17.0**: Hugging Face model hub integration

### Web Interface
- **gradio>=3.50.0**: Web interface framework for AI applications

### Video/Audio Processing
- **ffmpeg-python>=0.2.0**: Python bindings for FFmpeg
- **librosa>=0.10.0**: Audio analysis and processing
- **soundfile>=0.12.0**: Audio file I/O operations

### Image Processing
- **Pillow>=10.0.0**: Image processing library
- **opencv-python>=4.8.0**: Computer vision operations

### Utilities
- **numpy>=1.24.0**: Numerical computing foundation
- **pandas>=2.0.0**: Data manipulation and analysis
- **requests>=2.31.0**: HTTP library for API calls
- **pyyaml>=6.0.1**: YAML configuration file parsing
- **tqdm>=4.66.0**: Progress bar utilities

### GPU/CUDA Support
- **nvidia-cuda-runtime>=12.4.0**: CUDA runtime (via conda)

## Development Dependencies (Optional)

### Testing
- **pytest>=7.4.0**: Unit testing framework
- **pytest-cov>=4.1.0**: Coverage reporting

### Code Quality
- **black>=23.7.0**: Code formatting
- **flake8>=6.0.0**: Linting and style checking
- **mypy>=1.5.0**: Static type checking

## Model Dependencies

### Required Models
- **Wan-AI/Wan2.1-T2V-1.3B**: Text-to-video generation model
- **bytedance-research/HuMo**: Human motion generation model
- **openai/whisper-large-v3**: Speech recognition model
- **huangjackson/Kim_Vocal_2**: Audio separation model

### Model Storage
- **Local Directory**: `./weights/`
- **Estimated Space**: 50GB for all models
- **Format**: Hugging Face model format (config.json, model.safetensors)

## System Dependencies

### Container Runtime
- **Docker**: Containerization platform
- **NVIDIA Container Toolkit**: GPU support in containers
- **CUDA 12.4**: GPU compute platform

### Build Tools
- **Git**: Version control
- **Buildx**: Docker buildx for multi-architecture builds

### Deployment Platform
- **RunPod**: GPU cloud computing platform
- **Docker Hub**: Container registry

## Configuration Dependencies

### Environment Variables
- **HUGGINGFACE_TOKEN**: Model access authentication
- **DOCKER_USERNAME**: Docker registry access
- **DOCKER_PASSWORD**: Docker registry authentication
- **RUNPOD_API_KEY**: RunPod API access

### Configuration Files
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container build configuration
- **generate.yaml**: Generation parameters (to be implemented)

## Security Dependencies

### Secret Management
- **Environment Variables**: Runtime secret injection
- **GitHub Secrets**: CI/CD secret management
- **.gitignore**: Secret exclusion from version control

### Network Security
- **HTTPS**: Secure communication
- **Firewall**: Network access control
- **Authentication**: Model and API access control