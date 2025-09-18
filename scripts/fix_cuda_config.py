#!/usr/bin/env python3
"""
CUDA configuration fix for HuMo inference.

Detects available GPUs and modifies the HuMo configuration to match the runtime environment.
This fixes the "CUDA error: invalid device ordinal" issue when the upstream HuMo code
assumes more GPUs than are actually available.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def detect_gpu_count() -> int:
    """Detect the number of available CUDA GPUs."""
    if not TORCH_AVAILABLE:
        print("WARNING: PyTorch not available, assuming 0 GPUs")
        return 0

    if not torch.cuda.is_available():
        print("WARNING: CUDA not available, assuming 0 GPUs")
        return 0

    gpu_count = torch.cuda.device_count()
    print(f"Detected {gpu_count} CUDA GPU(s)")

    # Print GPU details
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        memory_gb = torch.cuda.get_device_properties(i).total_memory / (1024**3)
        print(f"  GPU {i}: {gpu_name} ({memory_gb:.1f}GB)")

    return gpu_count


def fix_config_file(config_path: Path, gpu_count: int) -> bool:
    """
    Fix the generate.yaml configuration to match available GPU count.

    Args:
        config_path: Path to the generate.yaml file
        gpu_count: Number of available GPUs

    Returns:
        True if config was modified, False otherwise
    """
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        return False

    try:
        with config_path.open('r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config file: {e}")
        return False

    # Ensure dit section exists
    dit_section = config.setdefault('dit', {})

    # Current sp_size setting
    current_sp_size = dit_section.get('sp_size', 1)

    # Determine appropriate sp_size
    if gpu_count == 0:
        recommended_sp_size = 1
        print("WARNING: No GPUs detected. Setting sp_size=1 for CPU fallback.")
    elif gpu_count == 1:
        recommended_sp_size = 1
        print("Single GPU detected. Setting sp_size=1.")
    else:
        if current_sp_size <= 1:
            recommended_sp_size = gpu_count
            print(
                f"Multiple GPUs detected. sp_size not configured, defaulting to {recommended_sp_size}."
            )
        else:
            recommended_sp_size = min(current_sp_size, gpu_count)
            if recommended_sp_size != current_sp_size:
                print(
                    f"Multiple GPUs detected. Clamping configured sp_size={current_sp_size} "
                    f"to available GPUs ({recommended_sp_size})."
                )
            else:
                print(
                    f"Multiple GPUs detected. Using configured sp_size={current_sp_size}."
                )

    # Update configuration if needed
    config_modified = False
    if dit_section.get('sp_size') != recommended_sp_size:
        dit_section['sp_size'] = recommended_sp_size
        config_modified = True
        print(f"Updated sp_size: {current_sp_size} -> {recommended_sp_size}")

    # Write back if modified
    if config_modified:
        try:
            with config_path.open('w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"Configuration updated: {config_path}")
        except Exception as e:
            print(f"ERROR: Failed to write config file: {e}")
            return False
    else:
        print("Configuration already optimal, no changes needed.")

    return True


def set_environment_variables(gpu_count: int) -> None:
    """Set environment variables to help with CUDA issues."""

    def apply_var(name: str, value: str, *, force: bool = False) -> None:
        if force or os.environ.get(name) != value:
            os.environ[name] = value
            print(f"Set {name}={value}")

    # Provide sensible rendezvous defaults when not already configured
    if 'MASTER_ADDR' not in os.environ:
        apply_var('MASTER_ADDR', '127.0.0.1')
    if 'MASTER_PORT' not in os.environ:
        apply_var('MASTER_PORT', '29500')

    # Force single-device execution semantics when GPUs are limited
    if gpu_count <= 1:
        apply_var('CUDA_VISIBLE_DEVICES', '0' if gpu_count == 1 else '', force=True)
        apply_var('WORLD_SIZE', '1', force=True)
        apply_var('RANK', '0', force=True)
        apply_var('LOCAL_RANK', '0', force=True)

    if gpu_count == 0:
        apply_var('CUDA_LAUNCH_BLOCKING', '1', force=True)


def main():
    """Main function to detect and fix CUDA configuration."""
    print("HuMo CUDA Configuration Fix")
    print("=" * 40)

    # Detect available GPUs
    gpu_count = detect_gpu_count()

    # Find configuration file
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "generate.yaml"

    # Fix configuration
    if fix_config_file(config_path, gpu_count):
        print("✅ Configuration fix completed successfully")
    else:
        print("❌ Configuration fix failed")
        return 1

    # Set helpful environment variables
    set_environment_variables(gpu_count)

    print("\nRecommendations:")
    if gpu_count == 0:
        print("- Running without GPU support may be very slow")
        print("- Consider using a GPU-enabled environment")
    elif gpu_count == 1:
        print("- Single GPU configuration is optimal for most use cases")
        print("- Distributed training disabled automatically")
    else:
        print(f"- Multi-GPU setup detected ({gpu_count} GPUs)")
        print("- Ensure all GPUs have sufficient memory for the model")

    return 0


if __name__ == "__main__":
    sys.exit(main())
