# MAAPS V3 Cloud GPU Deployment Guide

**Target Environment**: Ubuntu 20.04/22.04 LTS with Nvidia GPU (T4, A10, A100).

## ⚠️ Critical Prerequisites
- **Docker** and **Docker Compose** must be installed.
- **Nvidia Container Toolkit** (`nvidia-docker2`) is REQUIRED for GPU passthrough.

## 🚀 Deployment Sequence (4 Steps)

### 1. System Prep & Drivers
Install Docker and Nvidia drivers/toolkit.
```bash
# Update and install Docker
sudo apt-get update && sudo apt-get install -y docker.io docker-compose

# Install Nvidia Container Toolkit (Official)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
   && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
   && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. Configuration
Setup the environment variables.
```bash
cd MAAPS_V3_Deploy
cp .env.template .env
# EDIT THE PASSWORDS!
nano .env
```

### 3. Build Worker
Build the custom PyTorch worker image (this takes a few minutes).
```bash
docker-compose build audio_worker
```

### 4. Launch Net
Ignite the swarm.
```bash
docker-compose up -d
```

## 🔍 Verification
- **n8n**: `http://<IP>:5678`
- **Postgres**: Port `5432`
- **Selenium Grid**: `http://<IP>:4444`
- **Audio Worker Docs**: `http://<IP>:8000/docs`
- **Qdrant**: `http://<IP>:6333/dashboard`
