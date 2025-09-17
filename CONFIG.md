# CONFIG.md

Configuration reference for the HuMo RunPod container.

## Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `HUGGINGFACE_TOKEN` | ✅ | `null` | Token used by `scripts/download_models.py` and the runtime bootstrap to access Hugging Face models. |
| `MODEL_CACHE_DIR` | ❌ | `/workspace/weights` | Directory where model weights are stored. Persist this volume between runs. |
| `OUTPUT_DIR` | ❌ | `/workspace/output` | Directory used for inference artifacts and Gradio exports. |
| `HUGGINGFACE_CACHE` | ❌ | `/workspace/weights/.cache` | Custom Hugging Face cache directory inside the container. |
| `HUMO_REPO_URL` | ❌ | `https://github.com/Phantom-video/HuMo.git` | Upstream repository cloned during runtime setup. |
| `FLASH_ATTENTION_WHEEL_URL` | ❌ | _unset_ | When provided, `docker/runtime_setup.sh` installs the specified flash-attention wheel. |
| `SKIP_MODEL_DOWNLOAD` | ❌ | `0` | Set to `1` to skip automatic model downloads on startup. |
| `FORCE_RUNTIME_SETUP` | ❌ | `0` | Set to `1` to force the bootstrap script to reinstall dependencies on next container start. |
| `GRADIO_SHARE` | ❌ | `false` | When `true`, Gradio attempts to create a public share link. |
| `GRADIO_PORT` | ❌ | `7860` | Port exposed by the Gradio app. |

### Secrets Template
Copy `.env.example` to `.env` and populate secrets before launching the container.

```
HUGGINGFACE_TOKEN=
DOCKER_USERNAME=
DOCKER_PASSWORD=
RUNPOD_API_KEY=
```

## Generation Configuration (`configs/generate.yaml`)

Key sections:

```yaml
model:
  variant: "1.7B"            # Choose between "1.7B" and "17B"

inputs:
  prompt: ""
  negative_prompt: ""
  audio_path: ""
  image_path: ""

outputs:
  directory: "${OUTPUT_DIR:-/workspace/output}"
  video_filename: "humo_output.mp4"
  audio_filename: "humo_audio.wav"
  metadata_filename: "metadata.json"

generation:
  frames: 64
  scale_a: 1.0
  scale_t: 7.5
  mode: "TA"
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

Override these values using CLI flags in `scripts/run_inference.py`, via the Gradio UI, or by editing `generate.yaml` before building the image.

### Output Definitions
`outputs` defines default filenames created during inference (`humo_output.mp4`, `humo_audio.wav`, `metadata.json`). Update when integrating with the upstream HuMo pipeline.

## Inference Scripts

`scripts/run_inference.py` consumes the configuration and creates a `request_manifest.json` per run. Execution flow:
1. Read base config (`configs/generate.yaml`).
2. Merge CLI overrides (frames, resolution, variant, etc.).
3. Write the resolved config and manifest into the chosen output directory.
4. Sync the resolved config to `HuMo/generate.yaml` inside the cloned repository.
5. Select the appropriate upstream script (TA/TIA × 1.7B/17B) and execute it from the HuMo repo.

`scripts/infer_ta.sh` and `scripts/infer_tia.sh` wrap this Python utility for TA and TIA modes respectively.

## Gradio UI

`app/gradio_app.py` loads defaults from `configs/generate.yaml` and exposes them in the UI. Submitted jobs call `scripts/run_inference.py`; the manifest path is returned for reproducibility. Configure `GRADIO_SHARE` and `GRADIO_PORT` to match your deployment needs.

## CI/CD Configuration

`.github/workflows/docker.yml` builds and pushes the Docker image. Configure GitHub repository secrets:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

Optional environment overrides for the workflow can be stored as GitHub variables (e.g., alternate registry names).

## Security Considerations
- `.gitignore` excludes weights, outputs, and `.env` to avoid leaking credentials or large artifacts.
- Runtime scripts never print secret values; Hugging Face token is only passed to the Hugging Face SDK.
- Provide secrets through environment variables or orchestration tooling (RunPod, GitHub Actions, etc.).

## Persistence Recommendations
- Mount `/workspace/weights` to retain downloaded models across pod restarts.
- Mount `/workspace/output` if you need to archive generated videos.
- Monitor `/workspace/logs` for runtime and inference logs.
