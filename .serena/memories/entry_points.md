# HuMo Project Entry Points

## Primary Entry Points

### Model Downloader Script
**File**: `scripts/download_models.py`
**Function**: `main()`
**Purpose**: Download and validate required AI models
**Usage**: `python scripts/download_models.py`

### ModelDownloader Class
**File**: `scripts/download_models.py`
**Class**: `ModelDownloader`
**Purpose**: Core model management functionality
**Key Methods**:
- `download_model()`: Download individual models
- `download_all_models()`: Download all required models
- `validate_downloads()`: Verify model integrity
- `check_disk_space()`: Verify sufficient disk space

## Configuration Entry Points

### Environment Variables
**File**: Runtime environment
**Purpose**: Configure application behavior
**Key Variables**:
- `HUGGINGFACE_TOKEN`: Hugging Face API access
- `GRADIO_SHARE`: Gradio sharing mode
- `MODEL_CACHE_DIR`: Model storage location
- `OUTPUT_DIR`: Output video directory

### Configuration Files
**File**: `generate.yaml` (to be implemented)
**Purpose**: Generation parameters and settings
**Location**: Project root directory

## Application Entry Points

### Gradio Web Interface
**File**: To be implemented
**Port**: 7860
**Purpose**: User-facing web interface for video generation
**Access**: `http://localhost:7860` or RunPod endpoint

### Inference Scripts
**Files**: To be implemented
- `scripts/infer_ta.sh`: Text + Audio inference
- `scripts/infer_tia.sh`: Text + Image + Audio inference
**Purpose**: Command-line video generation

### Docker Container
**Image**: `gemneye/humo-runpod:latest`
**Purpose**: Containerized deployment for RunPod
**Entry Point**: Container startup script (to be implemented)

## Testing Entry Points

### Unit Tests
**Directory**: `tests/` (to be implemented)
**Purpose**: Test individual components and functions

### Integration Tests
**Directory**: `tests/integration/` (to be implemented)
**Purpose**: Test system workflows and model integration

### E2E Tests
**Directory**: `tests/e2e/` (to be implemented)
**Purpose**: End-to-end functionality testing

## Development Entry Points

### Build System
**File**: `Dockerfile` (to be implemented)
**Purpose**: Container build process

### CI/CD Pipeline
**File**: `.github/workflows/deploy.yml` (to be implemented)
**Purpose**: Automated building and deployment

### Documentation
**File**: Various `.md` files
**Purpose**: Project documentation and guidance