# HuMo RunPod Container

Dockerized runtime for the [HuMo](https://github.com/Phantom-video/HuMo) human motion video generation system targeting GPU workers on RunPod. The container bootstraps the upstream repository, configures a CUDA-enabled Python environment, downloads Hugging Face model weights, and exposes both CLI scripts and a Gradio UI for inference.

## Features
- **CUDA 12.5 / PyTorch 2.5** runtime provisioned dynamically through Miniconda
- Idempotent startup script that clones the upstream HuMo repo and installs dependencies on container launch
- Automated Hugging Face weight downloads (`scripts/download_models.py`) with manifest tracking
- Text+Audio (`scripts/infer_ta.sh`) and Text+Image+Audio (`scripts/infer_tia.sh`) command-line pipelines backed by `configs/generate.yaml`
- Automatic routing to HuMo’s 1.7B/17B upstream scripts based on Gradio or CLI selections
- Gradio web UI (`app/gradio_app.py`) listening on port `7860` with adjustable generation parameters
- GitHub Actions workflow that builds and publishes images to Docker Hub (`gemneye/humo-runpod`)

## Repository Layout
```
.
├── Dockerfile
├── app/
│   └── gradio_app.py
├── configs/
│   └── generate.yaml
├── docker/
│   ├── entrypoint.sh
│   └── runtime_setup.sh
├── scripts/
│   ├── download_models.py
│   ├── infer_ta.sh
│   ├── infer_tia.sh
│   └── run_inference.py
└── .github/workflows/docker.yml
```

## Prerequisites
- Docker with NVIDIA Container Toolkit for GPU passthrough
- Hugging Face access token (if the models require authentication)
- Docker Hub credentials stored as secrets when using CI (`DOCKER_USERNAME`, `DOCKER_PASSWORD`)

## Building the Image
```bash
# Clone this repository and change into it
cd HuMo-Runpod

# Build the container
docker build -t gemneye/humo-runpod:local .
```

## Running the Container Locally
```bash
# Ensure NVIDIA runtime is available and pass any required env vars
docker run \
  --gpus all \
  -p 7860:7860 \
  -e HUGGINGFACE_TOKEN=hf_xxx \
  -e GRADIO_SHARE=false \
  gemneye/humo-runpod:local
```

The first startup installs Miniconda, creates the `humo` environment, clones the upstream HuMo repo, installs requirements, and downloads model weights into `/workspace/weights`. Subsequent starts reuse cached resources.

To force a rebuild of the runtime environment (for upgrades) pass `-e FORCE_RUNTIME_SETUP=1`.

## Runtime Environment Variables
Set these via `.env` (copy from `.env.example`) or `docker run -e` flags.

| Variable | Purpose |
| --- | --- |
| `HUGGINGFACE_TOKEN` | Authentication for private model downloads |
| `MODEL_CACHE_DIR` | Override weight storage directory (default `/workspace/weights`) |
| `OUTPUT_DIR` | Override inference output directory (default `/workspace/output`) |
| `GRADIO_SHARE` | Set to `true` to request a public Gradio link |
| `GRADIO_PORT` | Custom port for the Gradio server (default `7860`) |
| `FLASH_ATTENTION_WHEEL_URL` | Optional URL for flash-attention wheels |
| `SKIP_MODEL_DOWNLOAD` | Set to `1` to skip automatic weight downloads |

## CLI Inference Workflows
Text + Audio mode (Wan 1.7B by default):
```bash
./scripts/infer_ta.sh \
  --prompt "A dancer performs energetic hip hop moves" \
  --audio /data/track.wav \
  --variant 1.7B \
  --output /workspace/output/run1
```

Text + Image + Audio mode:
```bash
./scripts/infer_tia.sh \
  --prompt "A surfer riding a huge wave" \
  --audio /data/wave.wav \
  --image /data/reference.png \
  --frames 96 \
  --steps 30
```

Both scripts generate a `request_manifest.json` for reproducibility and automatically call the appropriate HuMo upstream script based on the selected mode and model size.

## Gradio Web Interface
The container entrypoint launches `python /workspace/app/gradio_app.py`. Access the UI at `http://localhost:7860`. Upload audio (and optionally an image), tweak parameters, and click **Generate Video**. The UI reuses the CLI pipeline and surfaces logs plus the manifest file.

## Model Downloads
`scripts/download_models.py` pulls the required Hugging Face assets into `./weights`. Use it directly for pre-warming caches:
```bash
python scripts/download_models.py --weights-dir /workspace/weights
```

A manifest file (`download_manifest.json`) lists the download status. Optional Wan 1.7B weights are attempted but do not block success if unavailable.

## Continuous Integration
`.github/workflows/docker.yml` builds and pushes the Docker image whenever `main` or a version tag is updated. Ensure the following GitHub repository secrets exist:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

## Deployment on RunPod
1. Push the built image to Docker Hub (CI handles this for `gemneye/humo-runpod`).
2. In RunPod, create a custom container deployment pointing to the published image.
3. Supply environment variables (`HUGGINGFACE_TOKEN`, `GRADIO_SHARE`, etc.) and mount persistent storage for `/workspace/weights` and `/workspace/output`.
4. Expose port `7860` for the Gradio interface.
5. After the pod starts, wait for logs indicating `Runtime setup complete` before opening the UI.

## Testing & Validation
- **Manifest/log inspection**: `python scripts/run_inference.py --prompt "Test" --audio /data/sample.wav --mode TA --variant 1.7B`
- **Model validation**: `python scripts/download_models.py --skip-validation` (or without the flag for a full check)
- **CI Workflow**: Trigger `workflow_dispatch` to verify Docker builds succeed

GPU-based end-to-end testing must occur on RunPod once models and commands are available. Capture logs and generated artifacts for documentation.

## Security Notes
- Secrets must be stored outside of the repository (`.env` is ignored).
- Docker Hub credentials are sourced from GitHub secrets in CI.
- Model downloads honor `HUGGINGFACE_TOKEN`; no credentials are written to disk.

## License
This repository packages third-party HuMo assets. Review upstream licensing before distributing images.
