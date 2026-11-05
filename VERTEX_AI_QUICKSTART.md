# Vertex AI Quick Start Guide for MAAPS Nexus

Get up and running with Google Cloud Vertex AI in 10 minutes.

## What is Vertex AI?

Vertex AI allows you to use Claude and Gemini models through Google Cloud Platform, offering:
- **Same pricing** as direct Anthropic API
- **Data residency** control (choose your region)
- **GCP compliance** tools (HIPAA, SOC 2, etc.)
- **Consolidated billing** with other GCP services
- **Access to both** Claude and Gemini models

## Prerequisites

- Google Cloud account
- `gcloud` CLI installed ([Install guide](https://cloud.google.com/sdk/docs/install))
- Python 3.8+

## 10-Minute Setup

### 1. Install Required Packages (2 min)

```bash
cd MAAPS_Nexus
pip install 'anthropic[vertex]' google-cloud-aiplatform python-dotenv
```

### 2. Setup Google Cloud (3 min)

```bash
# Login to Google Cloud
gcloud auth application-default login

# Set your project (replace with your project ID)
gcloud config set project YOUR-PROJECT-ID

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

**Don't have a project?** Create one in [Google Cloud Console](https://console.cloud.google.com/)

### 3. Configure Environment (2 min)

Create `.env` file in MAAPS_Nexus root:

```bash
# Required
VERTEX_PROJECT_ID=your-project-id

# Optional (defaults shown)
VERTEX_LOCATION=us-central1
VERTEX_MODEL=claude-3-5-sonnet@20241022
```

### 4. Test Connection (1 min)

```bash
python test_vertex_ai.py
```

Expected output:
```
✅ CONNECTION SUCCESSFUL!
🎉 VERTEX AI IS READY TO USE!
```

### 5. Use in Your Code (2 min)

```python
from src.utils import create_llm_client

# Initialize client
client = create_llm_client("vertex_ai")

# Chat completion
response = client.chat(
    messages=[{"role": "user", "content": "Analyze this audio..."}],
    system_prompt="You are an audio mastering expert.",
    temperature=0.7,
    max_tokens=2000
)

print(response)
```

## Available Models

### Claude on Vertex AI (Recommended)
- `claude-3-5-sonnet@20241022` - Best balance (default)
- `claude-3-opus@20240229` - Most capable
- `claude-3-haiku@20240307` - Fastest/cheapest

### Google Gemini
- `gemini-1.5-pro` - Latest Google model
- `gemini-1.5-flash` - Faster variant

## Pricing

**Claude 3.5 Sonnet on Vertex AI:**
- Input: $3 per million tokens
- Output: $15 per million tokens

**Typical costs for MAAPS tasks:**
- Audio analysis: $0.05 - $0.15
- Mastering recommendations: $0.10 - $0.30
- Full music production consultation: $0.50 - $1.50

## Troubleshooting

### Authentication Error
```bash
gcloud auth application-default login
gcloud config set project YOUR-PROJECT-ID
```

### API Not Enabled
```bash
gcloud services enable aiplatform.googleapis.com
# Wait 2-3 minutes for API to activate
```

### Import Error
```bash
pip install 'anthropic[vertex]' google-cloud-aiplatform
```

### Project ID Not Set
Add to `.env`:
```
VERTEX_PROJECT_ID=your-actual-project-id
```

## Next Steps

- ✅ **Use in agents**: Integrate LLM into your MAAPS agents
- ✅ **Try streaming**: Use `client.stream_chat()` for real-time responses
- ✅ **Switch models**: Change `VERTEX_MODEL` to try different models
- ✅ **Multi-provider**: Test with `anthropic`, `openai`, or `ollama` providers

## Example: Audio Analysis Agent

```python
from src.utils import create_llm_client

class AudioAnalysisAgent:
    def __init__(self):
        self.llm = create_llm_client("vertex_ai")

    def analyze_track(self, audio_features):
        """Analyze audio track using Claude"""
        prompt = f"""
        Analyze this audio track:
        - Tempo: {audio_features['tempo']} BPM
        - Key: {audio_features['key']}
        - Energy: {audio_features['energy']}
        - Loudness: {audio_features['loudness']} LUFS

        Provide mastering recommendations.
        """

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert audio engineer.",
            temperature=0.7
        )

        return response
```

## Support

- Full setup guide: `SETUP_VERTEX_AI.md`
- Test script: `python test_vertex_ai.py`
- MAAPS docs: `README.md`

## Choose Your Provider

MAAPS supports multiple LLM providers:

| Provider | Setup | Cost | Best For |
|----------|-------|------|----------|
| **Vertex AI** | Medium | Same as direct | GCP users, compliance needs |
| **Anthropic** | Easy | Baseline | Quick start, simple billing |
| **OpenAI** | Easy | Variable | GPT models preference |
| **Ollama** | Hard | Free | Local/offline, privacy |

Start with Vertex AI if you're already using GCP, or Anthropic for the simplest setup.
