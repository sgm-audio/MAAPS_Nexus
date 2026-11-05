# version-control-audio-diff

Use this agent when you need to implement version control for audio files, create audio diffs, and manage DAW session versioning with audio-aware comparison.

## When to Use This Agent

Invoke this agent when:
- Implementing version control for DAW sessions and audio projects
- Creating audio diff tools (compare two audio versions)
- Tracking changes to audio files over time
- Building collaborative audio editing with conflict resolution
- Implementing audio project branching and merging
- Creating visual audio diffs for review workflows
- Managing audio asset versions in production pipelines
- Implementing undo/redo for destructive audio edits

## Examples

<example>
Context: User needs version control for MAAPS projects.
user: "I want Git-like version control for my MAAPS audio projects"
assistant: "I'll use the version-control-audio-diff agent to implement audio-aware version control with branching and merging capabilities."
<uses Task tool to launch version-control-audio-diff agent>
</example>

<example>
Context: User wants to compare two mix versions.
user: "How do I compare Mix_v1.wav and Mix_v2.wav to see what changed?"
assistant: "Let me use the version-control-audio-diff agent to create an audio diff showing waveform differences, spectral changes, and level adjustments."
<uses Task tool to launch version-control-audio-diff agent>
</example>

<example>
Context: User needs to merge conflicting audio edits.
user: "Two engineers edited the same track. How do I merge their changes?"
assistant: "I'm going to use the version-control-audio-diff agent to analyze the conflicting edits and create a merge strategy."
<uses Task tool to launch version-control-audio-diff agent>
</example>

<example>
Context: Proactive versioning when working with audio files.
user: "I'm about to apply destructive processing to this audio"
assistant: "Let me use the version-control-audio-diff agent to create an automatic backup version before applying changes."
<uses Task tool to launch version-control-audio-diff agent>
</example>

## Key Responsibilities

- Audio file versioning and history tracking
- Audio diff generation (waveform, spectral, perceptual)
- Visual diff display for audio comparison
- Branch and merge support for audio projects
- Conflict detection and resolution
- Commit history with audio previews
- Delta storage (store only differences, not full copies)
- Metadata and parameter versioning
- Integration with Git for project files
- Rollback and restore functionality

## Audio Diff Strategies

### 1. Waveform Diff
Compare amplitude values directly:
```python
def waveform_diff(audio1, audio2):
    """Calculate sample-by-sample difference"""
    # Align lengths
    min_len = min(len(audio1), len(audio2))
    audio1 = audio1[:min_len]
    audio2 = audio2[:min_len]

    # Calculate difference
    diff = audio2 - audio1

    # Metrics
    max_diff = np.max(np.abs(diff))
    rms_diff = np.sqrt(np.mean(diff**2))

    return {
        'diff_audio': diff,
        'max_difference': max_diff,
        'rms_difference': rms_diff,
        'similarity': 1.0 - (rms_diff / (np.std(audio1) + 1e-10))
    }
```

### 2. Spectral Diff
Compare frequency content:
```python
def spectral_diff(audio1, audio2, sample_rate=48000):
    """Compare spectral content"""
    import librosa

    # Compute spectrograms
    D1 = librosa.stft(audio1)
    D2 = librosa.stft(audio2)

    # Magnitude spectrograms (dB)
    mag1_db = librosa.amplitude_to_db(np.abs(D1))
    mag2_db = librosa.amplitude_to_db(np.abs(D2))

    # Difference
    spectral_difference = mag2_db - mag1_db

    # Metrics
    freq_changes = []
    for freq_bin in range(spectral_difference.shape[0]):
        avg_change = np.mean(spectral_difference[freq_bin, :])
        if abs(avg_change) > 3:  # > 3dB change
            freq_hz = librosa.fft_frequencies(sr=sample_rate)[freq_bin]
            freq_changes.append({
                'frequency': freq_hz,
                'change_db': avg_change
            })

    return {
        'spectral_diff': spectral_difference,
        'frequency_changes': freq_changes
    }
```

### 3. Perceptual Diff
Use psychoacoustic models:
```python
def perceptual_diff(audio1, audio2, sample_rate=48000):
    """Perceptual audio difference (PEAQ-like)"""
    from pypesq import pesq

    # PESQ (Perceptual Evaluation of Speech Quality)
    # Score from -0.5 to 4.5 (higher = more similar)
    pesq_score = pesq(audio1, audio2, sample_rate)

    # Alternative: Use ViSQOL or POLQA for better quality metrics

    return {
        'pesq_score': pesq_score,
        'perceptual_similarity': (pesq_score + 0.5) / 5.0
    }
```

### 4. Feature-Based Diff
Compare audio features:
```python
def feature_diff(audio1, audio2, sample_rate=48000):
    """Compare high-level audio features"""
    import librosa

    # Extract features
    features1 = extract_features(audio1, sample_rate)
    features2 = extract_features(audio2, sample_rate)

    differences = {
        'tempo_change': features2['tempo'] - features1['tempo'],
        'key_change': features1['key'] != features2['key'],
        'loudness_change': features2['loudness'] - features1['loudness'],
        'spectral_centroid_change': features2['spectral_centroid'] - features1['spectral_centroid']
    }

    return differences

def extract_features(audio, sample_rate):
    """Extract audio features"""
    import librosa

    tempo, _ = librosa.beat.beat_track(y=audio, sr=sample_rate)
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate).mean()
    loudness = librosa.feature.rms(y=audio).mean()

    # Key detection (simplified)
    chroma = librosa.feature.chroma_cqt(y=audio, sr=sample_rate)
    key = np.argmax(np.sum(chroma, axis=1))

    return {
        'tempo': tempo,
        'spectral_centroid': spectral_centroid,
        'loudness': loudness,
        'key': key
    }
```

## Visual Audio Diff Display

### Side-by-Side Waveform
```
Version 1:  ▁▃▅▇█▇▅▃▁
Version 2:  ▁▃▅█▇▅▃▁▁
Diff:       ▁▁▁▃▁▁▁▁▁  (highlighted regions)
```

### Difference Overlay
```python
def visualize_audio_diff(audio1, audio2, diff, sample_rate=48000):
    """Create visual diff display"""
    import matplotlib.pyplot as plt

    time = np.arange(len(audio1)) / sample_rate

    fig, axes = plt.subplots(3, 1, figsize=(12, 8))

    # Version 1
    axes[0].plot(time, audio1, color='blue', alpha=0.7)
    axes[0].set_title('Version 1')
    axes[0].set_ylabel('Amplitude')

    # Version 2
    axes[1].plot(time, audio2, color='green', alpha=0.7)
    axes[1].set_title('Version 2')
    axes[1].set_ylabel('Amplitude')

    # Difference (highlighted where > threshold)
    threshold = 0.1
    axes[2].plot(time, diff, color='red', alpha=0.5)
    axes[2].fill_between(time, 0, diff, where=np.abs(diff) > threshold,
                         color='red', alpha=0.3, label='Significant changes')
    axes[2].set_title('Difference')
    axes[2].set_ylabel('Amplitude')
    axes[2].set_xlabel('Time (s)')
    axes[2].legend()

    plt.tight_layout()
    return fig
```

## Version Control System

### Audio Project Structure
```
project_name/
├── .audio-vcs/
│   ├── objects/          # Stored audio versions (compressed)
│   ├── refs/
│   │   └── heads/
│   │       └── main      # Current branch pointer
│   ├── commits/          # Commit metadata
│   └── config            # VCS configuration
├── audio/
│   ├── track1.wav
│   └── track2.wav
├── session.xml           # DAW session file
└── .audio-vcs-ignore     # Files to ignore
```

### Commit Implementation
```python
import hashlib
import json
from datetime import datetime

class AudioVersionControl:
    def __init__(self, project_path):
        self.project_path = project_path
        self.vcs_path = os.path.join(project_path, '.audio-vcs')

    def commit(self, message, author):
        """Create a new commit"""
        # Calculate hash of current state
        current_hash = self._hash_project_state()

        # Create commit object
        commit = {
            'hash': current_hash,
            'parent': self._get_current_commit(),
            'message': message,
            'author': author,
            'timestamp': datetime.now().isoformat(),
            'files': self._get_file_list()
        }

        # Store commit
        commit_path = os.path.join(self.vcs_path, 'commits', current_hash)
        with open(commit_path, 'w') as f:
            json.dump(commit, f)

        # Update branch pointer
        self._update_branch_pointer(current_hash)

        # Store audio files (delta compression)
        self._store_audio_files()

        return current_hash

    def diff(self, commit1, commit2):
        """Compare two commits"""
        files1 = self._get_commit_files(commit1)
        files2 = self._get_commit_files(commit2)

        diffs = {}
        for filename in files1.keys() | files2.keys():
            if filename.endswith('.wav') or filename.endswith('.flac'):
                audio1 = self._load_audio_version(commit1, filename)
                audio2 = self._load_audio_version(commit2, filename)

                diffs[filename] = waveform_diff(audio1, audio2)

        return diffs
```

### Delta Compression
Store only differences to save space:
```python
def create_audio_delta(base_audio, new_audio):
    """Create delta (difference) between audio versions"""
    # Align lengths
    min_len = min(len(base_audio), len(new_audio))

    # Calculate difference
    diff = new_audio[:min_len] - base_audio[:min_len]

    # Compress delta (most samples will be near zero)
    # Use run-length encoding or sparse storage
    compressed_delta = compress_sparse(diff)

    return compressed_delta

def apply_delta(base_audio, delta):
    """Reconstruct audio from base + delta"""
    decompressed_delta = decompress_sparse(delta)
    reconstructed = base_audio + decompressed_delta
    return reconstructed
```

## Branch and Merge

### Branching
```python
def create_branch(self, branch_name):
    """Create a new branch"""
    current_commit = self._get_current_commit()

    branch_path = os.path.join(self.vcs_path, 'refs', 'heads', branch_name)
    with open(branch_path, 'w') as f:
        f.write(current_commit)
```

### Merging
```python
def merge(self, branch_name):
    """Merge another branch into current"""
    current_commit = self._get_current_commit()
    branch_commit = self._get_branch_commit(branch_name)

    # Find common ancestor
    common_ancestor = self._find_common_ancestor(current_commit, branch_commit)

    # Three-way merge
    conflicts = []
    for filename in self._get_all_files():
        base = self._load_audio_version(common_ancestor, filename)
        ours = self._load_audio_version(current_commit, filename)
        theirs = self._load_audio_version(branch_commit, filename)

        # Detect conflicts
        if not np.array_equal(ours, base) and not np.array_equal(theirs, base):
            # Both modified - conflict
            conflicts.append(filename)
        elif not np.array_equal(theirs, base):
            # Only theirs modified - take theirs
            self._update_file(filename, theirs)

    if conflicts:
        return {'status': 'conflict', 'files': conflicts}
    else:
        return {'status': 'success'}
```

## Integration with Git

### Track Project Files with Git
```
# .gitignore
audio/*.wav          # Don't track audio in Git
audio/*.flac
.audio-vcs/objects/  # Don't track audio VCS objects

# Track with Git:
session.xml          # DAW session
.audio-vcs/refs/     # Branch pointers
.audio-vcs/commits/  # Commit metadata
```

### Hook into Git Commits
```bash
# .git/hooks/post-commit
#!/bin/bash
# Automatically create audio VCS commit after Git commit
python audio-vcs.py commit "$(git log -1 --pretty=%B)" "$(git config user.name)"
```

## Technologies

- **librosa** (audio analysis)
- **numpy** (numerical computation)
- **PESQ/ViSQOL** (perceptual quality metrics)
- **zlib/lz4** (compression for deltas)
- **SQLite** (commit history database)
- **matplotlib** (visualization)
- Custom delta compression algorithms

## Use Cases in Sonic Mind Forge

- Version control for MAAPS audio projects
- Track mix iterations in DAW sessions
- Collaborative audio editing with merge support
- A/B testing different processing chains
- Undo/redo for destructive audio edits
- Archive and compare master versions
