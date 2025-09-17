
## Title

Containerize _HuMo_ for Runpod
https://github.com/Phantom-video/HuMo
https://huggingface.co/bytedance-research/HuMo

----------

## Purpose

Provide all tasks an Agentic Coder must complete to deliver a working Docker container for _HuMo_ (Phantom-video / bytedance-research), for deployment on Runpod.

----------

## Tasks

Each task should be committed, tested, and documented. Where relevant, include example outputs or logs.
Use serena mcp for documentation and context.
Use context7 mcp server to get up to date documentation
Use fetch mcp server to get information from web pages

----------

### 🛠 Task 1: Set up project repository

-   Ensure the target GitHub repository is `sruckh/HuMo-Runpod`.
    
-   Add placeholder files for secrets and config (e.g. `.env.example`) to avoid committing keys.
    
-   Ensure `.gitignore` ignores secrets, local state, model weights if not desired in repo.
    

----------

### Task 2: Write Dockerfile

-   Base image: `nvidia/cuda:12.5.1-cudnn-devel-ubuntu22.04`.
    
-   In Dockerfile, **do not** clone upstream or install everything during local build except minimal OS/dependencies; but ensure that container startup scripts perform the main installation.
    
-   Include minimal layers for OS tools, conda installer etc.
    
-   Set up an ENTRYPOINT or startup script so that when the container is run, it triggers the runtime setup (see Task 3).
    

----------

### Task 3: Runtime initialization script

-   Write a script (e.g. `entrypoint.sh` or `start.sh`) that runs when container starts, doing:
    
    1.  Install Miniconda (if not baked in already).
        
    2.  Create & activate `humo` conda environment (Python 3.11).
        
    3.  Install correct PyTorch / TorchAudio / TorchVision versions with CUDA support.
	     - pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
    4.  Clone `https://github.com/Phantom-video/HuMo.git`.
        
    5.  Change into the HuMo directory.
        
    6.  Install the `requirements.txt` from the cloned repo.
        
    7.  Install ffmpeg via conda-forge.
        
    8.  Install the flash-attention wheel (the exact URL / version).
		- https://huggingface.co/bytedance-research/HuMo
        
    9.  Download required models from Huggingface into certain local paths. (See Task 4.)
      
-   The script must check for already-downloaded models or existing installations, to avoid repeating work.
    

----------

### Task 4: Model download

-   At startup (or as part of initialization), download the following models using Huggingface APIs / `hf` / `huggingface-cli`:
    
    Model
    
    Local Dir
    
    `Wan-AI/Wan2.1-T2V-1.3B`
    
    `./weights/Wan2.1-T2V-1.3B`
    
    `bytedance-research/HuMo`
    
    `./weights/HuMo`
    
    `openai/whisper-large-v3`
    
    `./weights/whisper-large-v3`
    
    `huangjackson/Kim_Vocal_2`
    
    `./weights/audio_separator`
    
-   Ensure download is efficient (e.g. using normalized caching, retries, partial downloads).
    
-   Handle missing model or failed download gracefully (error messages, fallback?).
    

----------

### Task 5: Inference & Configuration

-   Ensure inference scripts are present:
    
    -   Text + Audio: `scripts/infer_ta.sh` + possibly the 1.7B version.
        
    -   Text + Image + Audio: `scripts/infer_tia.sh` + 1.7B version.
        
-   Expose a configuration file (`generate.yaml`) in the repo / container to allow users to modify parameters:
    
    -   `generation.frames`
        
    -   `scale_a`, `scale_t`
        
    -   `mode` (“TA” / “TIA” etc)
        
    -   `height`, `width`
        
    -   `dit.sp_size` (#GPUs or sequence parallel size)
        
    -   Diffusion / sampling timestep steps
        
-   Validate that inference works for both 480p and 720p modes.
    
-   Ensure that generating longer than 97 frames degrades appropriately or has a warning.
    

----------

### Task 6: Gradio interface

-   Build a Gradio app inside the container that provides UI for:
    
    -   Entering text prompt
        
    -   Uploading audio
        
    -   Optionally uploading a reference image (for TIA mode)
        
    -   Choosing config options: frames, mode, resolution, scale_a, scale_t, sampling steps
        
-   Launch the Gradio app on `0.0.0.0:7860` with `share=True` (if desired) so that public link visible.
    
-   Ensure it works inside the container when deployed on Runpod.
    

----------

### Task 7: GitHub Actions / CI/CD

-   Write a GitHub Action workflow that:
    
    -   On push to `main` (or tagged release), builds the Docker image.
        
    -   Logs into Dockerhub using secrets `DOCKER_USERNAME` / `DOCKER_PASSWORD`.
        
    -   Tags the image (e.g. `latest`, versioned tag).
        
    -   Pushes to Dockerhub under `gemneye/<imagename>`.
        
    -   Optionally verifies container run (could run a smoke test).
        
-   Add README or other documentation so container users know how to run it locally (on Runpod), what inputs are required, how to use the Gradio UI or inference scripts.
    

----------

### Task 8: Security & Secret Management

-   Ensure no API keys, secrets or passwords are in the code or committed files. Use placeholders / environment variables.
    
-   Confirm that any credentials required (Dockerhub credentials) are pulled from GitHub Secrets in CI, not stored in code.
    
-   Review all new files for accidental leakage of private credentials.
    

----------

### Task 9: Testing & Validation

-   Run a full end-to-end test on Runpod:
    
    -   Deploy the container image from Dockerhub.
        
    -   Start a Pod / Worker with required GPU(s).
        
    -   Execute inference via scripts (TA and TIA) and via Gradio interface.
        
-   Validate:
    
    -   Model downloads succeeded.
        
    -   Inference output (video) meets expected resolution and sync.
        
    -   Performance is acceptable (runtime, resource use).
        
    -   UI responds correctly.
        
-   Include logs and example output.
    

----------

### Task 10: Documentation & Examples

-   In README.md, include:
    
    -   How to start the container on Runpod (expected commands or Runpod UI steps).
        
    -   How to use the Gradio UI.
        
    -   How to use inference scripts.
        
    -   Example `test_case.json` or link to upstream example.
        
    -   Sample config file and explanation of all key parameters.
        
-   Add versioning / tag info for Docker images.
    

----------

## Deliverables

-   Dockerfile + entrypoint / startup script(s)
    
-   Model download logic
    
-   Working inference scripts and config
    
-   Gradio UI
    
-   GitHub Actions workflow file(s)
    
-   README.md with usage instructions & examples
    
-   Passing tests / example outputs
    
-   Docker image published to Dockerhub (`gemneye/<imagename>`), with tags
    

----------

## Dependencies / References

-   HuMo repo & its `requirements.txt` and documentation. [GitHub+2Hugging Face+2](https://github.com/Phantom-video/HuMo?utm_source=chatgpt.com)
    
-   Runpod docs: how to use custom containers, how to deploy Pods, etc. [Runpod Documentation+2Runpod Documentation+2](https://docs.runpod.io/pods/overview?utm_source=chatgpt.com)
    

----------

## Acceptance Criteria

-   All tasks executed correctly, tested, and documented.
    
-   Container image builds and runs _only_ in container / Runpod environment (no local/manual installs required).
    
-   Models downloaded properly & inference works in different modes.
    
-   Gradio UI accessible and usable.
    
-   No secret leakage.
    
-   Docker image published and usable via Runpod.
