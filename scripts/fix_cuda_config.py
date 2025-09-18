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
        # No GPUs available - force CPU mode or single GPU emulation
        recommended_sp_size = 1
        print("WARNING: No GPUs detected. Setting sp_size=1 for CPU fallback.")
    elif gpu_count == 1:
        # Single GPU - no parallelism needed
        recommended_sp_size = 1
        print("Single GPU detected. Setting sp_size=1.")
    else:
        # Multiple GPUs - use available count but cap at reasonable limit
        recommended_sp_size = min(gpu_count, current_sp_size) if current_sp_size > 1 else 1
        print(f"Multiple GPUs detected. Setting sp_size={recommended_sp_size}.")

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

    # Force single device if only one GPU or no GPUs
    if gpu_count <= 1:
        os.environ['CUDA_VISIBLE_DEVICES'] = '0' if gpu_count == 1 else ''
        print(f"Set CUDA_VISIBLE_DEVICES={os.environ['CUDA_VISIBLE_DEVICES']}")

    # Enable debugging if needed
    if gpu_count == 0:
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
        print("Set CUDA_LAUNCH_BLOCKING=1 for debugging")

    # Disable distributed training for single GPU
    if gpu_count <= 1:
        os.environ['WORLD_SIZE'] = '1'
        os.environ['RANK'] = '0'
        os.environ['LOCAL_RANK'] = '0'
        print("Set distributed training variables for single GPU mode")


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