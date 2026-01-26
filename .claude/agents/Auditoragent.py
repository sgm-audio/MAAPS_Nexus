import librosa
import numpy as np
import pyloudnorm as pyln
from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any
import json

@dataclass
class SonicSignature:
    """The immutable JSON schema passed to downstream Agents."""
    bpm: float
    key: str
    lufs_integrated: float
    spectral_centroid_hz: float
    is_clipping: bool
    status: str

class AuditorAgent:
    def __init__(self, target_sr: int = 44100, noise_floor_db: float = -40.0):
        self.target_sr = target_sr
        self.noise_floor_db = noise_floor_db
        
        # Major and Minor templates for Key Detection
        self.key_templates = self._generate_key_templates()
        self.keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def _generate_key_templates(self) -> np.ndarray:
        """Generates standard binary templates for Major/Minor key correlation."""
        maj = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
        min = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]
        templates = []
        for i in range(12):
            templates.append(np.roll(maj, i))
            templates.append(np.roll(min, i))
        return np.array(templates)

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Loads and normalizes audio to system spec."""
        # Mono load for structural analysis, standard SR.
        y, sr = librosa.load(file_path, sr=self.target_sr, mono=True)
        return y, sr

    def detect_key(self, y: np.ndarray, sr: int) -> str:
        """Extracts the exact musical key using Chromagram correlation."""
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Correlate against the 24 templates (12 Maj, 12 Min)
        correlations = [np.corrcoef(chroma_mean, t)[0, 1] for t in self.key_templates]
        best_match_idx = np.argmax(correlations)
        
        key_idx = best_match_idx // 2
        mode = "Major" if best_match_idx % 2 == 0 else "Minor"
        return f"{self.keys[key_idx]} {mode}"

    def get_lufs(self, y: np.ndarray, sr: int) -> float:
        """Calculates BS.1770 Integrated Loudness."""
        meter = pyln.Meter(sr) 
        return meter.integrated_loudness(y)

    def analyze(self, file_path: str) -> str:
        """
        The Core Method. 
        Ingests audio, extracts state, and returns the JSON Sonic Signature.
        """
        y, sr = self.load_audio(file_path)

        # 1. Check for Clipping / Noise Floor (The Gatekeeper)
        peak = np.max(np.abs(y))
        is_clipping = bool(peak >= 1.0)
        
        lufs = self.get_lufs(y, sr)
        if lufs < self.noise_floor_db:
            return json.dumps({"status": "REJECTED_TOO_QUIET"})

        # 2. Rhythmic Analysis
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)

        # 3. Harmonic & Spectral Analysis
        key = self.detect_key(y, sr)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_brightness = float(np.mean(spectral_centroids))

        # 4. Construct the Output
        signature = SonicSignature(
            bpm=round(bpm, 1),
            key=key,
            lufs_integrated=round(lufs, 2),
            spectral_centroid_hz=round(avg_brightness, 2),
            is_clipping=is_clipping,
            status="VALID" if not is_clipping else "WARNING_CLIPPING"
        )

        return json.dumps(asdict(signature), indent=4)

# --- EXECUTION (The Ray Worker Layer) ---
# if __name__ == "__main__":
#     auditor = AuditorAgent()
#     json_state = auditor.analyze("raw_guitar_riff.wav")
#     print(json_state)