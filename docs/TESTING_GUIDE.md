# User Testing Guide

Quick start for testing MAAPS Nexus locally.

## Setup
1. Copy `.env.example` to `.env`
2. Set `JWT_SECRET`, `AUTH_USERNAME`, `AUTH_PASSWORD_HASH`
3. Install: `pip install -r requirements.txt`

## Run
```bash
docker-compose up --build
# OR
python maaps_nexus_main.py --mode test
```

## Test Endpoints
- Health: `curl http://localhost:8000/health`
- Auth: `curl -X POST http://localhost:8000/auth/login -d '{"username":"...","password":"..."}'`
- Audio enhancement: `curl -X POST http://localhost:8000/api/v1/audio/enhance ...`

## Monitoring
- Metrics: `curl http://localhost:8000/metrics`
- Logs: `tail -f logs/system.log`

## Staging / Manual Deploy
```bash
# Local staging
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# Production-like (requires .env with secrets)
docker-compose -f docker-compose.production.yml up -d
```

## System Initialization Requirements
The MAAPS Nexus system requires:
- `numpy`, `librosa`, `scipy`, `torch`, `torchaudio`, `ray` (core runtime)
- `fastapi`, `uvicorn`, `pyjwt`, `python-dotenv` (API server)
- System libraries: `libsndfile1-dev`, `ffmpeg` (audio processing)
Install with: `pip install -r requirements.txt -r requirements-api.txt`
Note: Some plugin modes (`vst3`, `clap`, `ara`) require external SDK installation.
