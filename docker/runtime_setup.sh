#!/usr/bin/env bash
set -euo pipefail

log() {
    echo "[runtime][$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
}

CONDA_DIR=${CONDA_DIR:-/opt/conda}
CONDA_BIN="${CONDA_DIR}/bin/conda"
ENV_NAME=${CONDA_ENV_NAME:-humo}
WORKSPACE=${WORKDIR:-/workspace}
HUMO_REPO_URL=${HUMO_REPO_URL:-https://github.com/Phantom-video/HuMo.git}
HUMO_SOURCE_DIR=${HUMO_SOURCE_DIR:-${WORKSPACE}/HuMo}
MODEL_CACHE_DIR=${MODEL_CACHE_DIR:-${WORKSPACE}/weights}
OUTPUT_DIR=${OUTPUT_DIR:-${WORKSPACE}/output}
SETUP_MARKER=${WORKSPACE}/.runtime_setup_complete
SKIP_MODEL_DOWNLOAD=${SKIP_MODEL_DOWNLOAD:-0}
FLASH_ATTENTION_WHEEL_URL=${FLASH_ATTENTION_WHEEL_URL:-}

ensure_directories() {
    log "Ensuring workspace directories exist"
    mkdir -p "${MODEL_CACHE_DIR}" "${OUTPUT_DIR}" "${WORKSPACE}/logs"
}

install_miniconda() {
    if [[ -x "${CONDA_BIN}" ]]; then
        log "Miniconda already installed"
        return
    fi

    log "Installing Miniconda into ${CONDA_DIR}"
    tmpdir=$(mktemp -d)
    installer_path="${tmpdir}/miniconda.sh"
    curl -fsSL "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" -o "${installer_path}"
    bash "${installer_path}" -b -p "${CONDA_DIR}"
    rm -rf "${tmpdir}"

    export PATH="${CONDA_DIR}/bin:${PATH}"
    log "Miniconda installation complete"
}

ensure_conda_env() {
    export PATH="${CONDA_DIR}/bin:${PATH}"

    if [[ ! -x "${CONDA_BIN}" ]]; then
        log "ERROR: conda binary not found after installation"
        exit 1
    fi

    if [[ ! -d "${CONDA_DIR}/envs/${ENV_NAME}" ]]; then
        log "Creating conda environment ${ENV_NAME} with Python 3.11"
        "${CONDA_BIN}" create -y -n "${ENV_NAME}" python=3.11
    else
        log "Conda environment ${ENV_NAME} already exists"
    fi
}

conda_run() {
    "${CONDA_BIN}" run --no-capture-output -n "${ENV_NAME}" "$@"
}

install_pytorch_stack() {
    log "Installing PyTorch stack inside ${ENV_NAME}"
    conda_run python -m pip install --upgrade pip
    conda_run pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu124 \
        torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
}

install_project_requirements() {
    if [[ -f "${WORKSPACE}/requirements.txt" ]]; then
        log "Installing base project requirements"
        conda_run pip install --no-cache-dir -r "${WORKSPACE}/requirements.txt"
    else
        log "No base requirements.txt found at ${WORKSPACE}/requirements.txt"
    fi

    if [[ -f "${HUMO_SOURCE_DIR}/requirements.txt" ]]; then
        log "Installing HuMo repository requirements"
        conda_run pip install --no-cache-dir -r "${HUMO_SOURCE_DIR}/requirements.txt"
    else
        log "HuMo repository requirements.txt not found; skipping"
    fi
}

install_ffmpeg() {
    log "Installing ffmpeg via conda-forge"
    "${CONDA_BIN}" install -y -n "${ENV_NAME}" -c conda-forge ffmpeg
}

install_flash_attention() {
    if [[ -z "${FLASH_ATTENTION_WHEEL_URL}" ]]; then
        log "FLASH_ATTENTION_WHEEL_URL not provided; skipping flash-attention install"
        return
    fi

    log "Installing flash-attention from ${FLASH_ATTENTION_WHEEL_URL}"
    conda_run pip install --no-cache-dir "${FLASH_ATTENTION_WHEEL_URL}"
}

clone_humo_repo() {
    if [[ -d "${HUMO_SOURCE_DIR}/.git" ]]; then
        log "HuMo repository already cloned; pulling latest changes"
        git -C "${HUMO_SOURCE_DIR}" pull --ff-only || log "Warning: git pull failed, continuing with existing clone"
    else
        log "Cloning HuMo repository from ${HUMO_REPO_URL}"
        git clone "${HUMO_REPO_URL}" "${HUMO_SOURCE_DIR}"
    fi
}

download_models() {
    if [[ "${SKIP_MODEL_DOWNLOAD}" == "1" ]]; then
        log "SKIP_MODEL_DOWNLOAD=1 set; skipping model downloads"
        return
    fi

    local marker="${MODEL_CACHE_DIR}/.models-download-complete"
    if [[ -f "${marker}" ]]; then
        log "Model download marker found; skipping new downloads"
        return
    fi

    log "Starting model downloads"
    pushd "${WORKSPACE}" >/dev/null
    if conda_run python scripts/download_models.py --weights-dir "${MODEL_CACHE_DIR}"; then
        log "Model downloads completed"
        touch "${marker}"
    else
        log "Warning: model download script reported errors"
    fi
    popd >/dev/null
}

main() {
    ensure_directories
    install_miniconda
    ensure_conda_env
    clone_humo_repo
    install_pytorch_stack
    install_project_requirements
    install_ffmpeg
    install_flash_attention
    download_models

    touch "${SETUP_MARKER}"
    log "Runtime setup complete"
}

main "$@"
