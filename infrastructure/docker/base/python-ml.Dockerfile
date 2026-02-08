# NeuroSync AI – Base Python ML image
# Used by all agent services that need ML dependencies

FROM python:3.11-slim

# System deps for OpenCV, audio, scientific computing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    libgl1-mesa-glx libglib2.0-0 \
    libsm6 libxext6 libxrender-dev \
    libgomp1 libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Base Python deps shared across services
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    httpx==0.25.1 \
    python-dotenv==1.0.0 \
    loguru==0.7.2 \
    prometheus-client==0.19.0

WORKDIR /app
