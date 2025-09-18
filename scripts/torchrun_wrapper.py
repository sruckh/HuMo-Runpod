#!/usr/bin/env python3
"""
Torchrun wrapper that automatically adjusts distributed training parameters
based on available GPU hardware to prevent CUDA device ordinal errors.

This wrapper intercepts torchrun calls and modifies parameters to match
the runtime environment, preventing the upstream HuMo code from assuming
more GPUs are available than actually exist.
"""

import os
import sys
import subprocess
from pathlib import Path

def detect_gpu_count():
    """Detect available CUDA GPUs."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.device_count()
    except ImportError:
        pass
    return 0

def fix_torchrun_args(args, gpu_count):
    """
    Fix torchrun arguments based on available GPU count.

    Args:
        args: Original torchrun arguments
        gpu_count: Number of available GPUs

    Returns:
        Modified arguments list
    """
    fixed_args = []
    i = 0

    while i < len(args):
        arg = args[i]

        if arg == '--nproc_per_node' or arg == '--nproc-per-node':
            # Fix number of processes per node
            if i + 1 < len(args):
                original_nproc = args[i + 1]
                # Use minimum of requested processes and available GPUs
                new_nproc = min(int(original_nproc), max(1, gpu_count))
                fixed_args.extend([arg, str(new_nproc)])
                print(f"torchrun_wrapper: Adjusted nproc_per_node: {original_nproc} -> {new_nproc}")
                i += 2
            else:
                fixed_args.append(arg)
                i += 1

        elif arg == '--nnodes':
            # Keep nnodes as is, but ensure it's reasonable
            if i + 1 < len(args):
                fixed_args.extend([arg, args[i + 1]])
                i += 2
            else:
                fixed_args.append(arg)
                i += 1

        elif arg.startswith('--nproc_per_node=') or arg.startswith('--nproc-per-node='):
            # Handle combined form --nproc_per_node=N
            param, value = arg.split('=', 1)
            new_value = min(int(value), max(1, gpu_count))
            fixed_args.append(f"{param}={new_value}")
            print(f"torchrun_wrapper: Adjusted {param}: {value} -> {new_value}")
            i += 1

        else:
            fixed_args.append(arg)
            i += 1

    return fixed_args

def set_cuda_environment(gpu_count):
    """Set CUDA environment variables for single GPU/CPU mode."""
    env_vars = {}

    if gpu_count <= 1:
        # Single GPU or CPU mode
        env_vars['CUDA_VISIBLE_DEVICES'] = '0' if gpu_count == 1 else ''
        env_vars['WORLD_SIZE'] = '1'
        env_vars['RANK'] = '0'
        env_vars['LOCAL_RANK'] = '0'

        if gpu_count == 0:
            env_vars['CUDA_LAUNCH_BLOCKING'] = '1'

    # Apply environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"torchrun_wrapper: Set {key}={value}")

    return env_vars

def main():
    """Main wrapper function."""
    if len(sys.argv) < 2:
        print("Usage: torchrun_wrapper.py <torchrun_args...>")
        sys.exit(1)

    # Detect available GPUs
    gpu_count = detect_gpu_count()
    print(f"torchrun_wrapper: Detected {gpu_count} GPU(s)")

    # Set environment variables
    set_cuda_environment(gpu_count)

    # Get original torchrun arguments (skip script name)
    original_args = sys.argv[1:]

    # If no GPUs or single GPU, consider running without torchrun
    if gpu_count <= 1 and '--nproc_per_node' in ' '.join(original_args):
        print("torchrun_wrapper: Single GPU/CPU detected, attempting direct execution")

        # Find the python script in the arguments
        python_script = None
        script_args = []
        found_script = False

        for i, arg in enumerate(original_args):
            if not found_script and arg.endswith('.py'):
                python_script = arg
                script_args = original_args[i+1:]
                found_script = True
                break
            elif not found_script and not arg.startswith('-'):
                # Non-option argument that might be the script
                if Path(arg).exists() or arg.endswith('.py'):
                    python_script = arg
                    script_args = original_args[i+1:]
                    found_script = True
                    break

        if python_script:
            print(f"torchrun_wrapper: Executing directly: python {python_script}")
            # Try direct execution first
            try:
                result = subprocess.run([sys.executable, python_script] + script_args)
                sys.exit(result.returncode)
            except Exception as e:
                print(f"torchrun_wrapper: Direct execution failed: {e}")
                print("torchrun_wrapper: Falling back to modified torchrun")

    # Fix torchrun arguments based on available hardware
    fixed_args = fix_torchrun_args(original_args, gpu_count)

    # Execute torchrun with fixed arguments
    torchrun_cmd = ['torchrun'] + fixed_args
    print(f"torchrun_wrapper: Executing: {' '.join(torchrun_cmd)}")

    try:
        result = subprocess.run(torchrun_cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"torchrun_wrapper: Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()