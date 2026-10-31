# Base image of the audio-enhancement pilot: tools only. Model environments, model weights and
# vendored model code live in the Docker volume mounted at /opt/aep (see container/setup_envs.sh),
# research audio is only ever bind-mounted at run time and never becomes part of an image.
FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg git curl ca-certificates libsndfile1 build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.10.5

ENV UV_CACHE_DIR=/opt/aep/uv-cache \
    UV_LINK_MODE=copy \
    HF_HOME=/opt/aep/models/hf \
    TORCH_HOME=/opt/aep/models/torch \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
