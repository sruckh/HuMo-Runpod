#!/usr/bin/env python3
"""
Model download script for HuMo video generation system.
Downloads required models from Hugging Face and validates them.
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional




@dataclass(frozen=True)
class ModelSpec:
    """Declarative configuration for a Hugging Face repository download."""

    key: str
    repo_id: str
    description: str
    local_subdir: str
    required: bool = True
    allow_patterns: Optional[Iterable[str]] = None
    ignore_patterns: Optional[Iterable[str]] = None
    files_to_validate: Optional[Iterable[str]] = None


class ModelDownloader:
    """Downloads and manages AI models for video generation."""

    REQUIRED_MODELS = (
        ModelSpec(
            key="wan_t2v",
            repo_id="Wan-AI/Wan2.1-T2V-1.3B",
            description="Wan 1.3B text-to-video base model",
            local_subdir="Wan2.1-T2V-1.3B",
            files_to_validate=("config.json",),
        ),
        ModelSpec(
            key="wan_t2v_14b",
            repo_id="Wan-AI/Wan2.1-T2V-14B",
            description="Wan 14B high-capacity model",
            local_subdir="Wan2.1-T2V-14B",
            required=False,
            files_to_validate=("config.json",),
        ),
        ModelSpec(
            key="humo",
            repo_id="bytedance-research/HuMo",
            description="HuMo motion generation resources",
            local_subdir="HuMo",
            files_to_validate=("config.json",),
        ),
        ModelSpec(
            key="whisper",
            repo_id="openai/whisper-large-v3",
            description="Whisper ASR model",
            local_subdir="whisper-large-v3",
            files_to_validate=("config.json", "model.safetensors"),
        ),
        ModelSpec(
            key="audio_separator",
            repo_id="huangjackson/Kim_Vocal_2",
            description="Kim Vocal 2 source separation model",
            local_subdir="audio_separator",
            files_to_validate=("Kim_Vocal_2.onnx",),
        ),
    )

    def __init__(self, weights_dir: Optional[str] = None):
        """Initialize model downloader."""
        resolved_dir = weights_dir or os.getenv("MODEL_CACHE_DIR") or "./weights/"
        self.weights_dir = Path(resolved_dir)
        self.weights_dir.mkdir(parents=True, exist_ok=True)

        # Check for Hugging Face token
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not self.hf_token:
            print("Warning: HUGGINGFACE_TOKEN not set. Some models may not be accessible.")

        self.manifest_path = self.weights_dir / "download_manifest.json"

    def _target_dir(self, spec: ModelSpec) -> Path:
        return self.weights_dir / spec.local_subdir

    def download_model(self, spec: ModelSpec) -> bool:
        """Download a specific model repository snapshot."""
        target_dir = self._target_dir(spec)
        try:
            print(f"Downloading {spec.repo_id} -> {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

            if spec.key == "audio_separator":
                url = "https://huggingface.co/seanghay/uvr_models/resolve/main/Kim_Vocal_2.onnx"
                command = ["wget", url, "-O", str(target_dir / "Kim_Vocal_2.onnx")]
            else:
                command = [
                    "hf",
                    "download",
                    spec.repo_id,
                    "--local-dir",
                    str(target_dir),
                ]
                if spec.allow_patterns:
                    command.extend(["--include", *spec.allow_patterns])
                if spec.ignore_patterns:
                    command.extend(["--exclude", *spec.ignore_patterns])

                if self.hf_token:
                    command.extend(["--token", self.hf_token])

            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"Successfully downloaded {spec.repo_id}")
                return True
            else:
                print(f"Error downloading {spec.repo_id}: {result.stderr}")
                return False

        except Exception as exc:
            print(f"Error downloading {spec.repo_id}: {exc}")
            return False

    def download_all_models(self) -> Dict[str, bool]:
        """Download all required models."""
        results = {}

        for spec in self.REQUIRED_MODELS:
            print(f"\nProcessing {spec.key} ({spec.description})...")
            success = self.download_model(spec)
            results[spec.key] = success

            if not success and spec.required:
                print(f"ERROR: Required model {spec.key} failed to download!")

        return results

    def validate_downloads(self) -> bool:
        """Validate that all required models are downloaded."""
        print("Validating model downloads...")

        all_valid = True
        for spec in self.REQUIRED_MODELS:
            if not spec.required:
                continue

            model_dir = self._target_dir(spec)

            if not model_dir.exists():
                print(f"ERROR: Model directory missing: {model_dir}")
                all_valid = False
                continue

            if spec.files_to_validate:
                for filename in spec.files_to_validate:
                    file_path = model_dir / filename
                    if not file_path.exists():
                        print(f"WARNING: Required file missing for {spec.key}: {file_path}")
                        all_valid = False

        return all_valid

    def check_disk_space(self) -> bool:
        """Check if there's enough disk space for models."""
        required_space = 50 * 1024**3  # 50GB estimate

        try:
            disk_usage = os.statvfs(self.weights_dir)
            free_space = disk_usage.f_frsize * disk_usage.f_bavail

            if free_space < required_space:
                print(f"ERROR: Insufficient disk space. Need {required_space/1024**3:.1f}GB, "
                      f"have {free_space/1024**3:.1f}GB")
                return False

            print(f"Disk space check passed: {free_space/1024**3:.1f}GB available")
            return True

        except Exception as e:
            print(f"Warning: Could not check disk space: {e}")
            return True  # Continue anyway

    def write_manifest(self, results: Dict[str, bool]) -> None:
        """Persist a manifest describing downloaded models."""
        manifest = {
            "weights_dir": str(self.weights_dir.resolve()),
            "models": [],
        }

        for spec in self.REQUIRED_MODELS:
            manifest["models"].append(
                {
                    "key": spec.key,
                    "repo_id": spec.repo_id,
                    "local_path": str(self._target_dir(spec)),
                    "required": spec.required,
                    "downloaded": bool(results.get(spec.key, False)),
                }
            )

        try:
            with self.manifest_path.open("w", encoding="utf-8") as handle:
                json.dump(manifest, handle, indent=2)
        except Exception as exc:
            print(f"Warning: Unable to write manifest {self.manifest_path}: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download required HuMo models and validate the installation."
    )
    parser.add_argument(
        "--weights-dir",
        dest="weights_dir",
        default=None,
        help="Path to store downloaded models (defaults to $MODEL_CACHE_DIR or ./weights)."
    )
    parser.add_argument(
        "--skip-validation",
        dest="skip_validation",
        action="store_true",
        help="Skip validation of downloaded models."
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    print("HuMo Model Downloader")
    print("====================")

    args = parse_args()

    # Initialize downloader
    downloader = ModelDownloader(weights_dir=args.weights_dir)

    # Check disk space
    if not downloader.check_disk_space():
        print("Please free up disk space and try again.")
        sys.exit(1)

    # Download models
    print("\nStarting model downloads...")
    results = downloader.download_all_models()

    # Validate downloads
    if args.skip_validation:
        print("\nSkipping validation step as requested.")
        is_valid = True
    else:
        print("\nValidating downloads...")
        is_valid = downloader.validate_downloads()

    # Summary
    print("\nDownload Summary:")
    print("================")

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    spec_lookup = {spec.key: spec for spec in downloader.REQUIRED_MODELS}
    for model_key, success in results.items():
        spec = spec_lookup[model_key]
        status = "✓" if success else "✗"
        print(f"{status} {model_key}: {spec.repo_id}")

    print(f"\nSuccess: {success_count}/{total_count} models downloaded")

    downloader.write_manifest(results)

    if not is_valid:
        print("ERROR: Some required models are missing or incomplete!")
        sys.exit(1)
    else:
        print("All required models downloaded successfully!")
        print("You can now start the HuMo video generation system.")


if __name__ == "__main__":
    main()
