# Complete Vertex AI Setup Guide for MAAPS Nexus

This guide provides comprehensive instructions for integrating Google Cloud Vertex AI with MAAPS Nexus.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Authentication Methods](#authentication-methods)
- [Configuration](#configuration)
- [Testing](#testing)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

### What is Vertex AI?

Vertex AI is Google Cloud's unified ML platform that provides access to:
- **Anthropic Claude models** (3.5 Sonnet, Opus, Haiku)
- **Google Gemini models** (1.5 Pro, Flash)

### Why Use Vertex AI?

**Choose Vertex AI if:**
- ✅ You already use Google Cloud Platform
- ✅ You need specific data residency (EU, Asia, etc.)
- ✅ You want GCP compliance tools (HIPAA, SOC 2)
- ✅ You prefer consolidated GCP billing
- ✅ You want both Claude AND Gemini access

**Choose Direct API if:**
- ✅ You want the simplest setup
- ✅ You're not using other GCP services
- ✅ You don't need data residency control

### Pricing

Claude pricing on Vertex AI is **identical** to direct Anthropic API:

| Model | Input | Output |
|-------|-------|--------|
| Claude 3.5 Sonnet | $3/M tokens | $15/M tokens |
| Claude 3 Opus | $15/M tokens | $75/M tokens |
| Claude 3 Haiku | $0.25/M tokens | $1.25/M tokens |

## Prerequisites

### Required
- Google Cloud account ([Create one](https://cloud.google.com/))
- GCP project with billing enabled
- Python 3.8 or higher
- MAAPS Nexus installed

### Optional but Recommended
- `gcloud` CLI ([Install guide](https://cloud.google.com/sdk/docs/install))
- Git for version control
- Virtual environment (venv, conda)

## Installation

### 1. Install Python Packages

```bash
cd MAAPS_Nexus

# Install Vertex AI packages
pip install 'anthropic[vertex]' google-cloud-aiplatform

# Install environment variable support
pip install python-dotenv

# Or install all at once from requirements.txt
pip install -r requirements.txt
```

**Package versions:**
- `anthropic[vertex]` >= 0.40.0
- `google-cloud-aiplatform` >= 1.71.1
- `python-dotenv` >= 1.0.0

### 2. Install gcloud CLI (Recommended)

**macOS:**
```bash
brew install google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
Download installer from [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

### 3. Verify Installation

```bash
gcloud --version
python --version
pip list | grep anthropic
```

## Authentication Methods

You can authenticate with Vertex AI using either method:

### Method 1: Application Default Credentials (Recommended)

**Easiest for development.** Uses your personal Google account.

```bash
# Login with your Google account
gcloud auth application-default login

# Set your project
gcloud config set project YOUR-PROJECT-ID

# Verify
gcloud auth application-default print-access-token
```

**Pros:**
- ✅ Quick setup for development
- ✅ No key management
- ✅ Works across all Google Cloud tools

**Cons:**
- ❌ Requires gcloud CLI
- ❌ Personal account (not for production)

### Method 2: Service Account Key

**Best for production.** Uses a service account.

#### Create Service Account

```bash
# Set your project
export PROJECT_ID=your-project-id

# Create service account
gcloud iam service-accounts create maaps-vertex-ai \
    --display-name="MAAPS Vertex AI Service Account" \
    --project=$PROJECT_ID

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:maaps-vertex-ai@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create ~/maaps-vertex-key.json \
    --iam-account=maaps-vertex-ai@$PROJECT_ID.iam.gserviceaccount.com
```

#### Use Service Account

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/maaps-vertex-key.json
```

Or add to `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/maaps-vertex-key.json
```

**Pros:**
- ✅ Production-ready
- ✅ Fine-grained permissions
- ✅ No personal account needed

**Cons:**
- ❌ More setup
- ❌ Key management required
- ❌ Must keep key secure

## Configuration

### 1. Enable Vertex AI API

```bash
# Enable the API
gcloud services enable aiplatform.googleapis.com --project=YOUR-PROJECT-ID

# Verify it's enabled
gcloud services list --enabled | grep aiplatform
```

**Note:** API activation can take 2-3 minutes.

### 2. Create Environment File

Create `.env` in MAAPS_Nexus root:

```bash
# Required: Your GCP project ID
VERTEX_PROJECT_ID=your-project-id

# Optional: Region (default: us-central1)
# Available: us-central1, us-east5, europe-west1, asia-southeast1
VERTEX_LOCATION=us-central1

# Optional: Model (default: claude-3-5-sonnet@20241022)
VERTEX_MODEL=claude-3-5-sonnet@20241022

# Optional: Service account key path (if not using ADC)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### 3. Available Regions

Choose a region close to your users:

| Region | Location | Use Case |
|--------|----------|----------|
| `us-central1` | Iowa, USA | Default, lowest latency for US |
| `us-east5` | Virginia, USA | US East Coast |
| `europe-west1` | Belgium | EU data residency |
| `europe-west4` | Netherlands | EU alternative |
| `asia-southeast1` | Singapore | Asia Pacific |

### 4. Available Models

**Claude Models:**
```python
VERTEX_MODEL=claude-3-5-sonnet@20241022  # Best balance (default)
VERTEX_MODEL=claude-3-opus@20240229      # Most capable
VERTEX_MODEL=claude-3-haiku@20240307     # Fastest/cheapest
```

**Gemini Models:**
```python
VERTEX_MODEL=gemini-1.5-pro    # Latest Google model
VERTEX_MODEL=gemini-1.5-flash  # Faster variant
```

## Testing

### 1. Run Test Script

```bash
python test_vertex_ai.py
```

**Expected output:**
```
============================================================
MAAPS Nexus - Vertex AI Connection Test
============================================================

1. Checking environment variables...
✅ VERTEX_PROJECT_ID: your-project-id
✅ VERTEX_LOCATION: us-central1
✅ VERTEX_MODEL: claude-3-5-sonnet@20241022

2. Checking authentication...
✅ Using Application Default Credentials

3. Testing package imports...
✅ Successfully imported VertexAIClient

4. Initializing Vertex AI client...
✅ Client initialized successfully

5. Testing API connection...
✅ CONNECTION SUCCESSFUL!
   Model: claude-3-5-sonnet@20241022
   Location: us-central1
   Response: connected

============================================================
🎉 VERTEX AI IS READY TO USE!
============================================================

Testing Unified LLM Integration Layer
✅ Unified LLM client works!

✅ ALL TESTS PASSED
```

### 2. Manual Test

```python
from src.utils import create_llm_client

# Create client
client = create_llm_client("vertex_ai")

# Test chat
response = client.chat(
    messages=[
        {"role": "user", "content": "Say hello"}
    ],
    temperature=0.7,
    max_tokens=100
)

print(response)
```

## Usage Examples

### Basic Chat

```python
from src.utils import create_llm_client

client = create_llm_client("vertex_ai")

response = client.chat(
    messages=[
        {"role": "user", "content": "Explain audio mastering in 3 sentences."}
    ],
    system_prompt="You are an expert audio engineer.",
    temperature=0.7,
    max_tokens=200
)

print(response)
```

### Conversation with History

```python
from src.utils import create_llm_client

client = create_llm_client("vertex_ai")

messages = [
    {"role": "user", "content": "What's the ideal loudness for streaming?"},
    {"role": "assistant", "content": "For streaming platforms, -14 LUFS is the standard..."},
    {"role": "user", "content": "What about for club playback?"}
]

response = client.chat(
    messages=messages,
    system_prompt="You are an expert audio engineer.",
    temperature=0.7
)

print(response)
```

### Streaming Response

```python
from src.utils import create_llm_client

client = create_llm_client("vertex_ai")

print("Response: ", end="", flush=True)

for chunk in client.stream_chat(
    messages=[{"role": "user", "content": "Analyze this audio track..."}],
    system_prompt="You are an audio mastering expert.",
    temperature=0.7
):
    print(chunk, end="", flush=True)

print()
```

### Audio Analysis Agent

```python
from src.utils import create_llm_client
import librosa

class AudioAnalysisAgent:
    def __init__(self):
        self.llm = create_llm_client("vertex_ai")

    def analyze_audio_file(self, audio_path):
        """Analyze audio file and get recommendations"""
        # Load audio
        y, sr = librosa.load(audio_path)

        # Extract features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
        rms = librosa.feature.rms(y=y).mean()

        # Get LLM analysis
        prompt = f"""
        Analyze this audio track:

        Technical Specs:
        - Tempo: {tempo:.1f} BPM
        - Spectral Centroid: {spectral_centroid:.1f} Hz
        - RMS Energy: {rms:.4f}

        Provide:
        1. Genre classification
        2. Mix quality assessment
        3. Mastering recommendations
        4. EQ suggestions
        """

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert audio engineer and mastering specialist.",
            temperature=0.7,
            max_tokens=1000
        )

        return response

# Usage
agent = AudioAnalysisAgent()
analysis = agent.analyze_audio_file("track.wav")
print(analysis)
```

### Multi-Provider Support

```python
from src.utils import create_llm_client

# Vertex AI (Claude via GCP)
vertex_client = create_llm_client("vertex_ai")

# Direct Anthropic API
anthropic_client = create_llm_client("anthropic", api_key="your-key")

# OpenAI
openai_client = create_llm_client("openai", api_key="your-key")

# Ollama (local)
ollama_client = create_llm_client("ollama", base_url="http://localhost:11434")

# All use the same interface
for client in [vertex_client, anthropic_client, openai_client, ollama_client]:
    response = client.chat(
        messages=[{"role": "user", "content": "Hello!"}],
        temperature=0.7
    )
    print(response)
```

## Troubleshooting

### Common Issues

#### 1. "VERTEX_PROJECT_ID not set"

**Solution:**
```bash
# Add to .env
echo "VERTEX_PROJECT_ID=your-project-id" >> .env

# Or export
export VERTEX_PROJECT_ID=your-project-id
```

#### 2. "Permission denied" or "403 Forbidden"

**Solution:**
```bash
# Re-authenticate
gcloud auth application-default login

# Grant yourself Vertex AI User role
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="user:your-email@gmail.com" \
    --role="roles/aiplatform.user"
```

#### 3. "API not enabled"

**Solution:**
```bash
# Enable API
gcloud services enable aiplatform.googleapis.com

# Wait 2-3 minutes
sleep 180

# Verify
gcloud services list --enabled | grep aiplatform
```

#### 4. "Import error: No module named anthropic"

**Solution:**
```bash
pip install 'anthropic[vertex]' google-cloud-aiplatform
```

#### 5. "Could not automatically determine credentials"

**Solution:**
```bash
# Method 1: Use ADC
gcloud auth application-default login

# Method 2: Use service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.utils import create_llm_client
client = create_llm_client("vertex_ai")
```

## Best Practices

### Security

1. **Never commit keys**
   ```bash
   echo ".env" >> .gitignore
   echo "*.json" >> .gitignore
   ```

2. **Use service accounts in production**
   - Create dedicated service account
   - Grant minimum required permissions
   - Rotate keys regularly

3. **Restrict API access**
   ```bash
   # Create firewall rules if needed
   # Use VPC Service Controls for additional security
   ```

### Cost Optimization

1. **Use appropriate models**
   - Haiku for simple tasks ($0.25/$1.25 per M tokens)
   - Sonnet for balanced performance ($3/$15 per M tokens)
   - Opus only when maximum capability needed ($15/$75 per M tokens)

2. **Set max_tokens wisely**
   ```python
   # Don't use max_tokens=8000 if you only need 500
   response = client.chat(..., max_tokens=500)
   ```

3. **Cache prompts when possible**
   - Reuse system prompts
   - Store common responses

4. **Monitor usage**
   - Check GCP billing dashboard
   - Set up budget alerts

### Performance

1. **Choose nearest region**
   ```python
   # US users
   VERTEX_LOCATION=us-central1

   # EU users
   VERTEX_LOCATION=europe-west1

   # Asia users
   VERTEX_LOCATION=asia-southeast1
   ```

2. **Use streaming for long responses**
   ```python
   for chunk in client.stream_chat(...):
       process(chunk)  # Process as you receive
   ```

3. **Batch requests when possible**
   - Group similar requests
   - Process multiple tracks together

## Additional Resources

- [Google Cloud Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)
- [Anthropic Vertex AI Guide](https://docs.anthropic.com/claude/docs/vertex-ai)
- [Claude Model Documentation](https://docs.anthropic.com/claude/docs/models-overview)
- [MAAPS Nexus README](README.md)

## Support

If you encounter issues:

1. Run `python test_vertex_ai.py` for diagnostics
2. Check [Troubleshooting](#troubleshooting) section
3. Review GCP logs: https://console.cloud.google.com/logs
4. Check Vertex AI status: https://status.cloud.google.com/

## Next Steps

Now that Vertex AI is set up:

1. ✅ Integrate into MAAPS agents
2. ✅ Build audio analysis workflows
3. ✅ Create music production assistants
4. ✅ Experiment with different models
5. ✅ Monitor costs and optimize

Ready to build? Check out the [examples](#usage-examples) above!
