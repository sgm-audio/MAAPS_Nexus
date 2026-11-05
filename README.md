# MAAPS Nexus

[![CI](https://github.com/sgm-audio/MAAPS_Nexus/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/sgm-audio/MAAPS_Nexus/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Multi-Agent Audio Processing System** — an AI-powered audio engine where competing reinforcement-learning agents collaborate through a shared ontology to make real-time mixing and mastering decisions, integrated directly into your DAW via VST3, CLAP, or ARA.

---

**Multi-Agent Audio Processing System** - Professional-grade audio production automation

## Deployment (API)

1. Copy `.env.example` to `.env` and set `JWT_SECRET`, `AUTH_USERNAME`, and either `AUTH_PASSWORD_HASH` (preferred, bcrypt) or `AUTH_PASSWORD`. Update `ALLOWED_ORIGINS`.
2. Build and run:
   ```bash
   docker build --pull -t maaps-api .
   docker run --env-file .env -p 8000:8000 maaps-api
   ```
3. Health: `GET /health` (returns 200 when initialized). Auth: `POST /auth/login` to obtain a bearer token for protected endpoints.
