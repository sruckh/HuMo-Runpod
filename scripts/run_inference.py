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
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DEFAULT = PROJECT_ROOT / "configs" / "generate.yaml"
HUMO_SOURCE_DIR = Path(os.getenv("HUMO_SOURCE_DIR", PROJECT_ROOT / "HuMo"))
HUMO_SCRIPTS_DIR = HUMO_SOURCE_DIR / "scripts"

SCRIPT_MATRIX = {
    ("TA", "1.3B"): "infer_ta.sh",
    ("TA", "14B"): "infer_ta.sh",
    ("TIA", "1.3B"): "infer_tia.sh",
    ("TIA", "14B"): "infer_tia.sh",
}


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

    outputs.setdefault("directory", str(Path(args.output_dir).resolve()))

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
        return "1.7B"
    compact = value.replace("_", "").replace("-", "").replace(" ", "").lower()
    if "1.7" in compact or "17b" in compact and "1" in compact and "." in compact:
        return "1.7B"
    if "17b" in compact or compact == "17":
        return "17B"
    if "17" in compact and "1" not in compact:
        return "17B"
    return "1.7B" if "1" in compact else "17B"


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


def sync_config_to_humo(resolved_config: Path) -> Path:
    target = HUMO_SOURCE_DIR / "generate.yaml"
    if not target.parent.exists():
        raise FileNotFoundError(
            f"HuMo repository not found at {HUMO_SOURCE_DIR}. Ensure runtime_setup.sh cloned it."
        )
    target.write_text(resolved_config.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def main() -> int:
    args = parse_args()

    config_path = Path(args.config).resolve()
    try:
        config = load_yaml(config_path)
    except Exception as exc:
        print(f"Failed to load config {config_path}: {exc}")
        return 1

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
        script_path = select_upstream_script(generation_mode, variant_value)
    except Exception as exc:
        print(f"Failed to select HuMo script: {exc}")
        return 1

    resolved_config_path = write_resolved_config(merged, output_dir)

    try:
        sync_config_to_humo(resolved_config_path)
    except Exception as exc:
        print(f"Unable to sync configuration into HuMo repo: {exc}")
        return 1

    manifest_path = write_request_manifest(merged, script_path.name, output_dir)
    print(f"Wrote request manifest to {manifest_path}")

    env = os.environ.copy()
    env.setdefault("OUTPUT_DIR", str(output_dir))
    env.setdefault("HUMO_GENERATE_CONFIG", str(resolved_config_path))
    env.setdefault("PYTHONUNBUFFERED", "1")

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
