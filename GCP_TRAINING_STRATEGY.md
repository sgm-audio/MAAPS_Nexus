# MAAPS Nexus: Critic Agent GCP Training Strategy

**Target:** Google Cloud Platform (Vertex AI)
**Objective:** Train a robust Critic Agent capable of evaluating audio quality ("Warmth", "Clarity", "Punch") to guide the RL agents.

## 1. Architecture Overview

We will utilize **Vertex AI** for the training pipeline. Since the MAAPS Nexus architecture is built on **Ray**, we will leverage **Ray on Vertex AI** to scale the feature extraction and training process seamlessly.

```mermaid
graph LR
    A[Raw Audio (GCS)] --> B[Ray Cluster (Vertex AI)]
    B -->|Feature Extraction (CPU)| C[Processed Datasets (GCS)]
    C -->|Training (GPU)| D[Vertex AI Training Job]
    D -->|Model Artifacts| E[Vertex AI Model Registry]
    E -->|Download| F[Local VST3/DAW]
```

## 2. Data Strategy: The "Golden Ear" Dataset

 The Critic needs **paired data**: Audio + Semantic Labels. Since manual labeling is slow, we will use **Synthetic Degradation**.

### A. Source Data (GCS Bucket: `gs://maaps-audio-raw`)
1.  **High-Fidelity Corpus**: Upload 100GB+ of high-quality, mixed stems (FMA dataset, stems from stems-separation challenges).
    *   *Assumption*: These are "Reference" quality (Score: 1.0).

### B. Synthetic Generation (The "Teacher")
We will write a Ray processing script that takes "Good" audio and intentionally ruins it to create "Bad" examples with known labels.

| Transformation | Target Attribute | Label Value |
| :--- | :--- | :--- |
| **None** | All | **1.0 (Reference)** |
| Low-pass filter (200Hz) | Clarity / Brightness | 0.1 |
| Boost 250Hz (+12dB) | Mud | 0.9 (High Mud) |
| Bitcrush / Clip | Distortion | 0.9 |
| Remove Transients | Punch | 0.1 |

## 3. Implementation Steps

### Step 1: Containerization
We need a Docker image that mimics the local environment but runs on Vertex AI.

**File:** `MAAPS_Nexus/Dockerfile.training`
```dockerfile
FROM us-docker.pkg.dev/vertex-ai/training/pytorch-gpu.2-0:latest

WORKDIR /app

# Install system dependencies for audio (libsndfile)
RUN apt-get update && apt-get install -y libsndfile1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install google-cloud-storage google-cloud-aiplatform[ray]

# Copy source code
COPY src/ src/
```

### Step 2: Distributed Data Processing (Ray on Vertex)
We will submit a Ray Job to Vertex AI that:
1.  Reads audio files from GCS.
2.  Applies the **Synthetic Degradation** logic (using `torchaudio` or `pedalboard`).
3.  Extracts features (Spectrograms/Embeddings) using the `CriticAgent`'s feature extractor.
4.  Saves the features + labels to `gs://maaps-data-processed/train.parquet`.

### Step 3: Training Job
Submit a `CustomJob` to Vertex AI using NVIDIA T4 GPUs.

*   **Machine Type**: `n1-standard-8` (Data loading)
*   **Accelerator**: `NVIDIA_TESLA_T4` (1 or 4 count)
*   **Hyperparameters**:
    *   `batch_size`: 64
    *   `learning_rate`: 1e-4
    *   `dropout`: 0.3

## 4. Continuous Improvement (The Flywheel)

Once the model is deployed locally in the DAW:
1.  **Implicit Feedback**: If the user *bypasses* the MAAPS plugin or *undoes* an EQ move suggested by the RL agent, that is a **Negative Reward**.
2.  **Telemetry**: The VST3 plugin (via `StreamingPluginCommunicator`) should optionally log these "rejected" audio states to a local buffer.
3.  **Upload**: Periodically upload these "hard negatives" to GCS to retrain the Critic, making it smarter about what users actually dislike.

## 5. Cost Estimation (Est. for 100 hours training)

*   **Vertex AI Training (T4 GPU)**: ~$0.35/hour * 100 = $35.00
*   **Cloud Storage**: ~$0.02/GB/month.
*   **Dataflow/Ray**: Variable based on dataset size.

## 6. Execution Command

```bash
# 1. Build & Push Image
gcloud builds submit -t us-central1-docker.pkg.dev/PROJECT_ID/maaps-repo/critic-train:v1 -f Dockerfile.training .

# 2. Submit Job (using the script below)
python src/infrastructure/submit_vertex_job.py --bucket gs://maaps-data --epochs 50
```
