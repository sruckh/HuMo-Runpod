# syntax=docker/dockerfile:1.6
FROM nvidia/cuda:12.5.1-cudnn-devel-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install core system dependencies only. Runtime setup installs the rest.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        git \
        curl \
        wget \
        ca-certificates \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Set up workspace
ENV WORKDIR=/workspace
WORKDIR ${WORKDIR}

# Copy project files into the image
COPY . ${WORKDIR}

# Create directories for weights and outputs used at runtime
RUN mkdir -p ${WORKDIR}/weights ${WORKDIR}/output

# Ensure entrypoint scripts are executable
RUN chmod +x ${WORKDIR}/docker/entrypoint.sh ${WORKDIR}/docker/runtime_setup.sh

# Expose default Gradio port
EXPOSE 7860

# Default environment hints for runtime setup script
ENV CONDA_DIR=/opt/conda \
    CONDA_ENV_NAME=humo \
    MODEL_CACHE_DIR=${WORKDIR}/weights \
    OUTPUT_DIR=${WORKDIR}/output \
    HUGGINGFACE_CACHE=${WORKDIR}/weights/.cache \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    PYTHONUNBUFFERED=1 \
    GRADIO_SHARE=true \
    STARTUP_COMMAND="python /workspace/app/gradio_app.py"

# Use Tini as init to handle signal forwarding and zombie reaping
ENTRYPOINT ["/usr/bin/tini", "--", "bash", "/workspace/docker/entrypoint.sh"]
