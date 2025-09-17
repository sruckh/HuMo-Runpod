# TEST.md

Testing guidance for the HuMo RunPod container.

## Test Matrix

| Area | Objective | How to Run |
| --- | --- | --- |
| Bootstrap smoke | Ensure runtime scripts execute without reinstalling unexpectedly | `docker run --rm --entrypoint /bin/bash gemneye/humo-runpod:local -lc 'ls /workspace'` |
| Model downloader | Validate Hugging Face assets download and manifest output | `python scripts/download_models.py --weights-dir /tmp/humo-weights --skip-validation` |
| Manifest integrity | Confirm resolved config + manifest generation | `python scripts/run_inference.py --prompt "Test" --audio /data/sample.wav --mode TA --variant 1.7B --steps 25` |
| CLI scripts | Exercise TA/TIA wrappers for argument parsing | `./scripts/infer_ta.sh --prompt "Test" --audio /data/sample.wav --steps 25` |
| Gradio UI | Manual GPU test of UI-driven workflow | Launch container, open `http://pod-ip:7860`, submit job, verify manifest/logs/video |
| RunPod E2E | Validate real hardware run with weights cached | Follow README deployment steps and capture produced video/logs |

## Local Quick Checks

1. **Download script**
   ```bash
   python scripts/download_models.py --weights-dir /tmp/humo-weights --skip-validation
   ```
   Inspect `/tmp/humo-weights/download_manifest.json` for success flags.

2. **Inference manifest / config**
   ```bash
   python scripts/run_inference.py \
     --prompt "Quick check" \
     --audio /path/to/audio.wav \
     --mode TA \
     --variant 1.7B \
     --steps 20
   ```
   Inspect the generated `generate_resolved.yaml`, `request_manifest.json`, and `inference.log` under the specified output directory. The command will invoke the upstream HuMo script; on machines without models/GPU it may exit with an error after producing the manifest and log.

3. **Shell wrappers**
   ```bash
   ./scripts/infer_ta.sh --prompt "Quick check" --audio /path/to/audio.wav --steps 20
   ./scripts/infer_tia.sh --prompt "Quick check" --audio /path/to/audio.wav --image /path/to/img.png --steps 20
   ```
   These wrappers feed into `run_inference.py` and route to the appropriate HuMo script. Validate that argument parsing succeeds and manifests/logs are produced.

## RunPod Validation Checklist

- Mount persistent volumes for `/workspace/weights` and `/workspace/output`.
- Export `HUGGINGFACE_TOKEN` and optional `FLASH_ATTENTION_WHEEL_URL`.
- Allow initial startup to finish (`Runtime setup complete` in logs) before testing.
- Trigger model download via `python scripts/download_models.py --weights-dir /workspace/weights` if needed.
- Run both CLI scripts and the Gradio UI, capturing logs and generated assets.

## Automation Notes

- The GitHub Actions workflow builds the container on each push to `main` or version tags.
- GPU testing is not run automatically; RunPod validation must be performed manually and recorded in `JOURNAL.md`.
- Add targeted unit tests alongside new Python modules when functionality is extended beyond orchestration.
