#!/usr/bin/env bash
set -euo pipefail

log() {
    echo "[entrypoint][$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
}

CONDA_DIR=${CONDA_DIR:-/opt/conda}
CONDA_BIN="${CONDA_DIR}/bin/conda"
ENV_NAME=${CONDA_ENV_NAME:-humo}
WORKSPACE=${WORKDIR:-/workspace}
SETUP_MARKER=${WORKSPACE}/.runtime_setup_complete
RUNTIME_SCRIPT=${WORKSPACE}/docker/runtime_setup.sh

if [[ ! -f "${RUNTIME_SCRIPT}" ]]; then
    log "ERROR: runtime setup script missing at ${RUNTIME_SCRIPT}"
    exit 1
fi

if [[ "${FORCE_RUNTIME_SETUP:-0}" == "1" ]]; then
    log "FORCE_RUNTIME_SETUP enabled; re-running runtime setup"
    rm -f "${SETUP_MARKER}"
fi

if [[ ! -f "${SETUP_MARKER}" ]]; then
    log "Launching runtime setup"
    bash "${RUNTIME_SCRIPT}"
else
    log "Runtime setup already completed; skipping"
fi

if [[ ! -x "${CONDA_BIN}" ]]; then
    log "ERROR: conda binary not found at ${CONDA_BIN}"
    exit 1
fi

start_command() {
    if [[ "$#" -gt 0 ]]; then
        log "Executing container command: $*"
        exec "${CONDA_BIN}" run --no-capture-output -n "${ENV_NAME}" "$@"
    elif [[ -n "${STARTUP_COMMAND:-}" ]]; then
        log "Executing STARTUP_COMMAND via bash -lc"
        exec "${CONDA_BIN}" run --no-capture-output -n "${ENV_NAME}" bash -lc "${STARTUP_COMMAND}"
    else
        log "No command provided; opening interactive shell in ${ENV_NAME}"
        exec "${CONDA_BIN}" run --no-capture-output -n "${ENV_NAME}" bash
    fi
}

start_command "$@"
