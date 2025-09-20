# Torchrun Single-GPU Safeguards (2025-09-19)

- Added `render_humo_config` pipeline that hydrates HuMo's upstream `humo/configs/inference/generate.yaml` template with our request metadata.
- We now author a per-request positive prompt dataset and sync the rendered YAML to `HuMo/generate.runtime.yaml`, avoiding clobbering the upstream config.
- The `torchrun` wrapper intercepts YAML paths (`HUMO_GENERATE_CONFIG`) and injects `dit.sp_size=1`/`generation.sequence_parallel=1` in single GPU mode before directly invoking `main.py`.
- Goal: ensure HuMo always sees coherent configs in single-GPU environments without requiring repeated container restarts.
