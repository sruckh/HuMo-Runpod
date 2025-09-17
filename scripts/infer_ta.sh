#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

CONFIG_PATH=${CONFIG_PATH:-${PROJECT_ROOT}/configs/generate.yaml}
OUTPUT_DIR=${OUTPUT_DIR:-${PROJECT_ROOT}/output}
PYTHON_BIN=${PYTHON_BIN:-python}

PROMPT=""
AUDIO=""
NEG_PROMPT=""
VARIANT=""
HEIGHT=""
WIDTH=""
FRAMES=""
STEPS=""
SCALE_A=""
SCALE_T=""
SEED=""
SP_SIZE=""
FPS=""

print_usage() {
    cat <<USAGE
Usage: $0 --prompt "text" --audio /path/audio.[wav|mp3] [options]

Options:
  --negative-prompt TEXT    Negative prompt text
  --config PATH             Path to generate.yaml (default: ${CONFIG_PATH})
  --output PATH             Output directory (default: ${OUTPUT_DIR})
  --variant KEY             Model variant key (1.7B or 17B)
  --height N                Video height override
  --width N                 Video width override
  --frames N                Frame count override
  --steps N                 Sampling steps override
  --scale-a FLOAT           Audio guidance scale override
  --scale-t FLOAT           Text guidance scale override
  --seed N                  Random seed override
  --sp-size N               Sequence parallel size (dit.sp_size)
  --fps N                   Frames per second
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --audio)
            AUDIO="$2"
            shift 2
            ;;
        --negative-prompt)
            NEG_PROMPT="$2"
            shift 2
            ;;
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --variant)
            VARIANT="$2"
            shift 2
            ;;
        --height)
            HEIGHT="$2"
            shift 2
            ;;
        --width)
            WIDTH="$2"
            shift 2
            ;;
        --frames)
            FRAMES="$2"
            shift 2
            ;;
        --steps)
            STEPS="$2"
            shift 2
            ;;
        --scale-a)
            SCALE_A="$2"
            shift 2
            ;;
        --scale-t)
            SCALE_T="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --sp-size)
            SP_SIZE="$2"
            shift 2
            ;;
        --fps)
            FPS="$2"
            shift 2
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            print_usage
            exit 1
            ;;
    esac
done

if [[ -z "${PROMPT}" ]]; then
    echo "Error: --prompt is required" >&2
    exit 1
fi

if [[ -z "${AUDIO}" ]]; then
    echo "Error: --audio is required" >&2
    exit 1
fi

CMD=("${PYTHON_BIN}" "${SCRIPT_DIR}/run_inference.py" "--mode" "TA" "--prompt" "${PROMPT}" "--audio" "${AUDIO}" "--config" "${CONFIG_PATH}" "--output-dir" "${OUTPUT_DIR}")

if [[ -n "${NEG_PROMPT}" ]]; then
    CMD+=("--negative-prompt" "${NEG_PROMPT}")
fi
if [[ -n "${VARIANT}" ]]; then
    CMD+=("--variant" "${VARIANT}")
fi
if [[ -n "${HEIGHT}" ]]; then
    CMD+=("--height" "${HEIGHT}")
fi
if [[ -n "${WIDTH}" ]]; then
    CMD+=("--width" "${WIDTH}")
fi
if [[ -n "${FRAMES}" ]]; then
    CMD+=("--frames" "${FRAMES}")
fi
if [[ -n "${STEPS}" ]]; then
    CMD+=("--steps" "${STEPS}")
fi
if [[ -n "${SCALE_A}" ]]; then
    CMD+=("--scale-a" "${SCALE_A}")
fi
if [[ -n "${SCALE_T}" ]]; then
    CMD+=("--scale-t" "${SCALE_T}")
fi
if [[ -n "${SEED}" ]]; then
    CMD+=("--seed" "${SEED}")
fi
if [[ -n "${SP_SIZE}" ]]; then
    CMD+=("--sp-size" "${SP_SIZE}")
fi
if [[ -n "${FPS}" ]]; then
    CMD+=("--fps" "${FPS}")
fi

exec "${CMD[@]}"
