#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

CONFIG_PATH=${CONFIG_PATH:-${PROJECT_ROOT}/configs/generate.yaml}
OUTPUT_DIR=${OUTPUT_DIR:-${PROJECT_ROOT}/output}
PYTHON_BIN=${PYTHON_BIN:-python}

PROMPT=""
AUDIO=""
IMAGE=""
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
Usage: $0 --prompt "text" --audio /path/audio.wav --image /path/image.png [options]

Options mirror scripts/infer_ta.sh (including --sp-size and --fps).
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
        --image)
            IMAGE="$2"
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
if [[ -z "${IMAGE}" ]]; then
    echo "Error: --image is required" >&2
    exit 1
fi

CMD=("${PYTHON_BIN}" "${SCRIPT_DIR}/run_inference.py" "--mode" "TIA" "--prompt" "${PROMPT}" "--audio" "${AUDIO}" "--image" "${IMAGE}" "--config" "${CONFIG_PATH}" "--output-dir" "${OUTPUT_DIR}")

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
