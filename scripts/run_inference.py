#!/usr/bin/env python3
"""HuMo inference orchestrator.

Loads `configs/generate.yaml`, applies CLI or UI overrides, writes a request
manifest plus resolved configuration, and dispatches the correct upstream HuMo
shell script (TA/TIA, 1.7B/17B) automatically.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DEFAULT = PROJECT_ROOT / "configs" / "generate.yaml"
HUMO_SOURCE_DIR = Path(os.getenv("HUMO_SOURCE_DIR", PROJECT_ROOT / "HuMo"))
HUMO_SCRIPTS_DIR = HUMO_SOURCE_DIR / "scripts"
HUMO_BASE_INFERENCE_CONFIG = HUMO_SOURCE_DIR / "humo" / "configs" / "inference" / "generate.yaml"

SCRIPT_MATRIX = {
    ("TA", "1.3B"): "infer_ta.sh",
    ("TA", "14B"): "infer_ta.sh",
    ("TIA", "1.3B"): "infer_tia.sh",
    ("TIA", "14B"): "infer_tia.sh",
}


def expand_env_vars(text: str) -> str:
    # This is a simple expansion, might need a more robust solution for complex cases
    # For now, it handles ${VAR:-default}
    def replace_var(match):
        var_name = match.group(1)
        default_value = match.group(2)
        return os.getenv(var_name, default_value)

    # Use fullmatch to ensure the entire string matches the pattern
    match = re.fullmatch(r'\$\{(\w+):-(.*?)\}', text)
    if match:
        return replace_var(match)
    else:
        # If it doesn't match the pattern, return the original text
        return text




def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HuMo inference launcher")
    parser.add_argument("--mode", choices=["TA", "TIA"], default=None, help="Generation mode override")
    parser.add_argument("--prompt", help="Text prompt for generation")
    parser.add_argument("--prompt-file", help="Path to file containing the text prompt")
    parser.add_argument("--negative-prompt", help="Negative prompt to steer generation")
    parser.add_argument("--audio", required=True, help="Path to conditioning audio file")
    parser.add_argument("--image", help="Optional reference image (TIA mode)")
    parser.add_argument("--config", default=str(CONFIG_DEFAULT), help="Path to generate.yaml")
    parser.add_argument(
        "--output-dir",
        default=str(Path(os.getenv("OUTPUT_DIR", "./output")).resolve()),
        help="Directory for outputs"
    )
    parser.add_argument("--frames", type=int, help="Number of frames to generate")
    parser.add_argument("--height", type=int, help="Video height")
    parser.add_argument("--width", type=int, help="Video width")
    parser.add_argument("--steps", type=int, help="Sampling steps")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--scale-a", type=float, help="Audio guidance scale")
    parser.add_argument("--scale-t", type=float, help="Text guidance scale")
    parser.add_argument("--seed", type=int, help="Random seed override")
    parser.add_argument(
        "--variant",
        default=None,
        choices=["1.3B", "14B"],
        help="Model variant selection (maps to upstream 1.3B/14B scripts)",
    )
    parser.add_argument("--sp-size", type=int, help="Sequence parallel size (dit.sp_size)")
    parser.add_argument("--metadata", default=None, help="Optional metadata json to merge into request")
    return parser.parse_args()


def resolve_prompt(args: argparse.Namespace) -> str:
    prompt_source = args.prompt_file
    if prompt_source:
        path = Path(prompt_source)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_source}")
        return path.read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt
    raise ValueError("A prompt must be supplied via --prompt or --prompt-file")


def merge_metadata(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    cfg = copy.deepcopy(config)

    inputs = cfg.setdefault("inputs", {})
    generation = cfg.setdefault("generation", {})
    dit = cfg.setdefault("dit", {})
    diffusion = cfg.setdefault("diffusion", {}).setdefault("timesteps", {}).setdefault("sampling", {})
    outputs = cfg.setdefault("outputs", {})
    model = cfg.setdefault("model", {})

    inputs["prompt"] = resolve_prompt(args)
    if args.negative_prompt:
        inputs["negative_prompt"] = args.negative_prompt

    inputs["audio_path"] = str(Path(args.audio).resolve())
    if args.image:
        inputs["image_path"] = str(Path(args.image).resolve())
    elif inputs.get("image_path") and (args.mode or generation.get("mode")) == "TIA":
        # Clear stale image path if switching back to TA
        inputs.pop("image_path", None)

    if args.mode:
        generation["mode"] = args.mode
    generation["mode"] = generation.get("mode", "TA").upper()

    if args.frames is not None:
        generation["frames"] = args.frames
    if args.height is not None:
        generation["height"] = args.height
    if args.width is not None:
        generation["width"] = args.width
    if args.fps is not None:
        generation["fps"] = args.fps
    if args.scale_a is not None:
        generation["scale_a"] = args.scale_a
    if args.scale_t is not None:
        generation["scale_t"] = args.scale_t
    if args.seed is not None:
        generation["seed"] = args.seed

    if args.steps is not None:
        diffusion["steps"] = args.steps

    if args.sp_size is not None:
        dit["sp_size"] = args.sp_size

    if args.variant:
        model["variant"] = args.variant

    outputs.setdefault("directory", str(Path(os.getenv("OUTPUT_DIR", "./output")).resolve()))

    if args.metadata:
        metadata_path = Path(args.metadata)
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata override file not found: {metadata_path}")
        extra = json.loads(metadata_path.read_text(encoding="utf-8"))
        cfg.setdefault("extra", {}).update(extra)

    return cfg


def write_request_manifest(cfg: Dict[str, Any], script_name: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "request_manifest.json"
    payload = {
        "config": cfg,
        "script": script_name,
    }
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return manifest_path


def normalise_variant(value: Optional[str]) -> str:
    if not value:
        return "1.3B" # Default to 1.3B

    compact = value.replace("_", "").replace("-", "").replace(" ", "").lower()

    if "1.3" in compact or "1.3b" in compact:
        return "1.3B"
    if "14" in compact or "14b" in compact:
        return "14B"

    # Fallback if no match, perhaps raise an error or return a default
    # For now, let's return 1.3B as a safe default
    return "1.3B"


def select_upstream_script(mode: str, variant: str) -> Path:
    key = (mode.upper(), normalise_variant(variant))
    script_name = SCRIPT_MATRIX.get(key)
    if not script_name:
        raise ValueError(f"Unsupported mode/variant combination: {key}")
    script_path = HUMO_SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"HuMo script not found: {script_path}")
    return script_path


def write_resolved_config(cfg: Dict[str, Any], output_dir: Path) -> Path:
    resolved_path = output_dir / "generate_resolved.yaml"
    with resolved_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(cfg, handle, sort_keys=False)
    return resolved_path


def load_base_humo_config() -> Dict[str, Any]:
    if not HUMO_BASE_INFERENCE_CONFIG.exists():
        raise FileNotFoundError(
            f"Base HuMo inference config not found at {HUMO_BASE_INFERENCE_CONFIG}"
        )
    with HUMO_BASE_INFERENCE_CONFIG.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def build_positive_prompt_dataset(inputs: Dict[str, Any], output_dir: Path) -> Tuple[Path, str]:
    prompt = inputs.get("prompt", "")
    if not prompt:
        raise ValueError("Prompt is required to build HuMo dataset")

    itemname = f"request_{uuid.uuid4().hex[:8]}"
    dataset = {
        itemname: {
            "prompt": prompt,
            "audio_path": inputs.get("audio_path", ""),
            "img_paths": [inputs["image_path"]] if inputs.get("image_path") else [],
        }
    }

    dataset_path = output_dir / "positive_prompt.json"
    with dataset_path.open("w", encoding="utf-8") as handle:
        json.dump(dataset, handle, indent=2)

    return dataset_path, itemname


def render_humo_config(merged: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    base_cfg = load_base_humo_config()
    cfg = copy.deepcopy(base_cfg)

    generation = merged.setdefault("generation", {})
    dit = merged.setdefault("dit", {})
    diffusion = merged.setdefault("diffusion", {})
    inputs = merged.setdefault("inputs", {})

    dataset_path, itemname = build_positive_prompt_dataset(inputs, output_dir)
    cfg.setdefault("generation", {})["positive_prompt"] = str(dataset_path)
    cfg["generation"].setdefault("output", {})["dir"] = str(output_dir)

    for key in ("mode", "frames", "height", "width", "fps", "seed", "scale_a", "scale_t"):
        value = generation.get(key)
        if value is not None:
            cfg["generation"][key] = value

    neg_prompt = inputs.get("negative_prompt")
    if neg_prompt:
        cfg["generation"]["sample_neg_prompt"] = neg_prompt

    steps = diffusion.get("steps")
    if steps is not None:
        cfg.setdefault("diffusion", {}).setdefault("timesteps", {}).setdefault("sampling", {})["steps"] = steps

    sp_size = dit.get("sp_size")
    if sp_size is not None:
        cfg.setdefault("dit", {})["sp_size"] = sp_size
        cfg["generation"]["sequence_parallel"] = sp_size

    # Track the generated item for debugging/logging purposes
    cfg.setdefault("generation", {})["_request_itemname"] = itemname

    inputs_dataset_note = {
        "dataset": str(dataset_path),
        "itemname": itemname,
    }
    cfg.setdefault("runtime_metadata", {}).update(inputs_dataset_note)

    return cfg


def sync_config_to_humo(resolved_config: Path) -> list[Path]:
    """Copy the resolved config into locations the upstream HuMo code expects."""

    if not HUMO_SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"HuMo repository not found at {HUMO_SOURCE_DIR}. Ensure runtime_setup.sh cloned it."
        )

    payload = resolved_config.read_text(encoding="utf-8")

    candidate_paths = [
        HUMO_SOURCE_DIR / "generate.runtime.yaml",
        HUMO_SOURCE_DIR / "configs" / "generate.runtime.yaml",
    ]

    written_targets: list[Path] = []
    for target in candidate_paths:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
        written_targets.append(target)

    if not written_targets:
        raise FileNotFoundError(
            f"Unable to locate a writable generate.yaml within {HUMO_SOURCE_DIR}"
        )

    return written_targets


def main() -> int:
    args = parse_args()

    # Fix CUDA configuration before proceeding
    cuda_env_overrides = {}
    fix_script = Path(__file__).parent / "fix_cuda_config.py"
    if fix_script.exists():
        print("Running CUDA configuration fix...")
        fix_result = subprocess.run([sys.executable, str(fix_script)], capture_output=True, text=True)
        if fix_result.returncode != 0:
            print(f"CUDA fix failed: {fix_result.stderr}")
            print("Continuing anyway, but inference may fail...")
        else:
            print("CUDA configuration check completed")
            # Extract environment recommendations from fix script output
            for line in fix_result.stdout.split('\n'):
                match = re.match(r"Set ([A-Z0-9_]+)=(.*)", line.strip())
                if match:
                    key, value = match.group(1), match.group(2)
                    cuda_env_overrides[key] = value

    config_path = Path(args.config).resolve()
    try:
        config = load_yaml(config_path)
    except Exception as exc:
        print(f"Failed to load config {config_path}: {exc}")
        return 1

    # Expand environment variables in the config
    if "outputs" in config and "directory" in config["outputs"]:
        config["outputs"]["directory"] = expand_env_vars(config["outputs"]["directory"])

    audio_path = Path(args.audio).resolve()
    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}")
        return 1
    args.audio = str(audio_path)

    if args.image:
        image_path = Path(args.image).resolve()
        if not image_path.exists():
            print(f"Image file not found: {image_path}")
            return 1
        args.image = str(image_path)

    try:
        merged = merge_metadata(config, args)
    except Exception as exc:
        print(f"Failed to build request payload: {exc}")
        return 1

    # Ensure dit.sp_size does not exceed the effective world size
    effective_world_size = 1
    ws_source = cuda_env_overrides.get("WORLD_SIZE") or os.environ.get("WORLD_SIZE")
    if ws_source:
        try:
            effective_world_size = max(1, int(ws_source))
        except ValueError:
            print(f"Warning: Invalid WORLD_SIZE value '{ws_source}', defaulting to 1")
            effective_world_size = 1

    dit_section = merged.setdefault("dit", {})
    raw_sp_size = dit_section.get("sp_size", 1)
    try:
        sp_size = max(1, int(raw_sp_size))
    except (TypeError, ValueError):
        print(f"Warning: Invalid dit.sp_size '{raw_sp_size}', forcing to 1")
        sp_size = 1

    if effective_world_size % sp_size != 0:
        adjusted_sp_size = 1
        if effective_world_size > 1:
            for candidate in range(min(sp_size, effective_world_size), 0, -1):
                if effective_world_size % candidate == 0:
                    adjusted_sp_size = candidate
                    break
        if adjusted_sp_size != sp_size:
            print(
                f"Adjusted dit.sp_size from {sp_size} to {adjusted_sp_size} to align with WORLD_SIZE={effective_world_size}"
            )
        dit_section["sp_size"] = adjusted_sp_size

    print(
        f"Resolved distributed settings -> WORLD_SIZE={effective_world_size}, dit.sp_size={dit_section['sp_size']}"
    )

    generation_section = merged.setdefault("generation", {})
    if generation_section.get("sequence_parallel") != dit_section["sp_size"]:
        print(
            f"Propagating sequence_parallel from {generation_section.get('sequence_parallel')} "
            f"to {dit_section['sp_size']}"
        )
        generation_section["sequence_parallel"] = dit_section["sp_size"]

    generation_mode = merged.setdefault("generation", {}).get("mode", "TA").upper()
    merged["generation"]["mode"] = generation_mode

    variant_value = normalise_variant(merged.setdefault("model", {}).get("variant"))
    merged["model"]["variant"] = variant_value

    if generation_mode == "TIA" and not merged.get("inputs", {}).get("image_path"):
        print("TIA mode selected but no image provided. Supply --image or switch to TA mode.")
        return 1

    output_dir = Path(merged.setdefault("outputs", {}).get("directory", args.output_dir)).resolve()
    merged["outputs"]["directory"] = str(output_dir)

    try:
        humo_ready_config = render_humo_config(merged, output_dir)
    except Exception as exc:
        print(f"Failed to translate request into HuMo config: {exc}")
        return 1

    try:
        script_path = select_upstream_script(generation_mode, variant_value)
    except Exception as exc:
        print(f"Failed to select HuMo script: {exc}")
        return 1

    resolved_config_path = write_resolved_config(humo_ready_config, output_dir)

    try:
        synced_paths = sync_config_to_humo(resolved_config_path)
    except Exception as exc:
        print(f"Unable to sync configuration into HuMo repo: {exc}")
        return 1
    else:
        print("Synced resolved config to:")
        for path in synced_paths:
            print(f"  - {path}")

    manifest_path = write_request_manifest(merged, script_path.name, output_dir)
    print(f"Wrote request manifest to {manifest_path}")

    env = os.environ.copy()
    env.setdefault("OUTPUT_DIR", str(output_dir))
    env.setdefault("HUMO_GENERATE_CONFIG", str(resolved_config_path))
    env.setdefault("PYTHONUNBUFFERED", "1")

    # Apply CUDA environment overrides for upstream HuMo scripts
    env.update(cuda_env_overrides)
    if cuda_env_overrides:
        print(f"Applied CUDA environment overrides: {cuda_env_overrides}")

    # Add our scripts directory to PATH to intercept torchrun calls
    scripts_dir = str(Path(__file__).parent.resolve())
    current_path = env.get('PATH', '')
    env['PATH'] = f"{scripts_dir}:{current_path}"
    print(f"Added {scripts_dir} to PATH for torchrun interception")

    output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["bash", str(script_path)],
        cwd=str(HUMO_SOURCE_DIR),
        capture_output=True,
        text=True,
        env=env,
    )

    log_path = output_dir / "inference.log"
    log_path.write_text((completed.stdout or "") + "\n" + (completed.stderr or ""), encoding="utf-8")
    print(f"Inference logs written to {log_path}")

    if completed.returncode != 0:
        print(f"HuMo script exited with code {completed.returncode}")
        return completed.returncode

    print("HuMo inference completed successfully")

    video_filename = merged.get("outputs", {}).get("video_filename", "humo_output.mp4")
    video_path = output_dir / video_filename

    if not video_path.exists():
        fallback = HUMO_SOURCE_DIR / "outputs" / video_filename
        if fallback.exists():
            import shutil

            shutil.copy2(fallback, video_path)

    if video_path.exists():
        print(f"Generated video available at {video_path}")
    else:
        print("Warning: Expected video file not found. Check HuMo logs for details.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
