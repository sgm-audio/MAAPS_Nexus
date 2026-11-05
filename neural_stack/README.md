# High-Fidelity Neural Stack ("Titan")

## Architecture: "Reaper as the GUI, Python as the Engine"

This stack bypasses standard DSP plugins, utilizing Reaper's Python API (`reapy`) to send audio to a local Python environment (or Vertex AI), process it through State-of-the-Art (SOTA) Transformer models, and inject the results back onto the timeline.

### 1. The Environment Setup

**Do not use the standard Plugin Folder.** You need a dedicated Conda environment.

Run `setup_neural_env.bat` to automatically create the `neural_audio` environment with all dependencies.

**Manual Setup:**
```bash
conda create -n neural_audio python=3.9
conda activate neural_audio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install reapy-boost demucs fairseq audiolm-pytorch transformers pedalboard scipy
```

**Reaper Configuration:**
Ensure your Reaper is configured to use the Python executable from this new environment.
`Options -> Preferences -> Plug-ins -> ReaScript`

### 2. The "Neural Splitter" (Meta's HT Demucs)

**Script:** `titan_split.py`

Uses `htdemucs_ft` (Hybrid Transformer Fine-Tuned) to split audio into 4 stems: Drums, Bass, Vocals, Other. This preserves phase coherence better than standard EQ-based splitters.

**Usage:**
1. Select an audio item in Reaper.
2. Run `titan_split.py`.
3. Stems will be generated and inserted as new tracks.

### 3. The "Glitch" Generator (MusicGen)

**Script:** `hallucinate_texture.py`

Uses Meta's `MusicGen` to hallucinate new audio textures based on text prompts.

**Usage:**
1. Run the script (you may need to modify the prompt in the code or wrap it in a ReaScript GUI to accept input).
2. Default prompt: "industrial metallic server crash mechanical failure 150bpm"
3. The generated audio is saved to `C:/Temp/ReaperAI/` and inserted into the project.

### 4. The "Vocal Deepfake" (SVC / RVC)

*Currently a Strategy / Placeholder*

**Goal:** Transform vocal timbre using Retrieval-based Voice Conversion (RVC) while keeping performance phrasing.

**Workflow:**
1. **Training:** Train a `.pth` model on target voice data (e.g., "Demon" or specific vocalist) externally or via Vertex AI.
2. **Inference:** Use a local script (e.g., `infer_batch_rvc.py`) to process exported vocal tracks.
   - Input: Dry vocal track.
   - Model: Custom `.pth`.
   - Output: Resynthesized vocal.

### 5. The "Mastering" Agent (Spotify Pedalboard)

**Script:** `auto_master.py`

Uses Spotify's `pedalboard` library for high-speed offline mastering.

**Chain:**
- Highpass Filter (30Hz)
- Compressor (Ratio 4:1)
- Limiter (-1.0dB)

**Usage:**
1. Select the pre-master mix item.
2. Run `auto_master.py`.
3. Mastered version is imported to a new track.

### 6. The "Vertex AI" Bridge

If local GPU VRAM is insufficient for large models, offload to Google Cloud Vertex AI:

1. **Containerize:** Wrap scripts in Docker.
2. **Upload:** Push to Google Artifact Registry.
3. **Trigger:** modifying the Reaper script to upload the WAV to GCS, trigger a Vertex AI job, and poll for the result.
