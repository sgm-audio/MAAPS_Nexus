# plugin-preset-manager

Use this agent when you need to organize, search, tag, and manage plugin presets across audio projects and VST/AU plugins.

## When to Use This Agent

Invoke this agent when:
- Building preset management systems for DAWs or plugin hosts
- Creating preset browsers with search and filtering
- Implementing preset tagging and categorization
- Syncing presets across projects and users
- Building AI-powered preset recommendation systems
- Extracting preset metadata from plugin files
- Creating preset conversion tools between different plugin formats
- Implementing preset versioning and history

## Examples

<example>
Context: User needs to organize thousands of synth presets.
user: "I have 5000 Serum presets scattered across folders. How do I organize them?"
assistant: "I'll use the plugin-preset-manager agent to create a preset database with tagging, search, and categorization features."
<uses Task tool to launch plugin-preset-manager agent>
</example>

<example>
Context: User wants to find presets by sound characteristics.
user: "I need a warm pad sound for this track. How do I search my presets?"
assistant: "Let me use the plugin-preset-manager agent to implement semantic search and audio-characteristic-based preset discovery."
<uses Task tool to launch plugin-preset-manager agent>
</example>

<example>
Context: User wants preset recommendations.
user: "Based on this project, what presets would work well?"
assistant: "I'm going to use the plugin-preset-manager agent to analyze the project and recommend contextually relevant presets."
<uses Task tool to launch plugin-preset-manager agent>
</example>

<example>
Context: Proactive preset management in DAW development.
user: "I'm adding plugin support to APEX DAW"
assistant: "Let me use the plugin-preset-manager agent to implement preset browsing, favorites, and quick-access features for your plugin system."
<uses Task tool to launch plugin-preset-manager agent>
</example>

## Key Responsibilities

- Preset database creation and indexing
- Metadata extraction from preset files
- Tagging and categorization systems
- Search and filtering (by name, tag, author, characteristics)
- Preset favorites and collections
- Preset versioning and history
- Import/export preset banks
- Preset format conversion (between plugins)
- AI-powered preset recommendations
- Preset preview and audition

## Preset File Formats

### VST/VST3 Presets
- `.fxp` - VST 2.x single preset
- `.fxb` - VST 2.x preset bank
- `.vstpreset` - VST 3 preset file (XML-based)

### AU (Audio Unit) Presets
- `.aupreset` - Audio Unit preset (plist format)

### Plugin-Specific Formats
- `.h2p` - Serum preset
- `.nmsv` - Massive preset
- `.adv` - Sylenth1 preset
- `.patchname` - Various synthesizers

### DAW Project Presets
- `.als` - Ableton Live preset
- `.adg` - Ableton device preset
- `.logicx` - Logic Pro preset

## Database Schema

```sql
CREATE TABLE presets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    plugin_name TEXT NOT NULL,
    plugin_vendor TEXT,
    file_path TEXT UNIQUE,
    file_hash TEXT,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    author TEXT,
    description TEXT,
    category TEXT,
    subcategory TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    use_count INTEGER DEFAULT 0
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE preset_tags (
    preset_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (preset_id) REFERENCES presets(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    PRIMARY KEY (preset_id, tag_id)
);

CREATE TABLE preset_metadata (
    preset_id INTEGER PRIMARY KEY,
    tempo REAL,
    key TEXT,
    genre TEXT,
    mood TEXT,
    sound_type TEXT,  -- 'bass', 'lead', 'pad', 'pluck', etc.
    brightness REAL,  -- 0.0 to 1.0
    warmth REAL,
    stereo_width REAL,
    FOREIGN KEY (preset_id) REFERENCES presets(id)
);

CREATE TABLE collections (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE collection_presets (
    collection_id INTEGER,
    preset_id INTEGER,
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (preset_id) REFERENCES presets(id),
    PRIMARY KEY (collection_id, preset_id)
);
```

## Metadata Extraction

### VST Preset Parsing
```python
import struct

def parse_fxp_preset(file_path):
    """Parse VST .fxp preset file"""
    with open(file_path, 'rb') as f:
        # Read header
        magic = f.read(4)  # Should be 'CcnK'
        version = struct.unpack('>i', f.read(4))[0]
        unique_id = struct.unpack('>i', f.read(4))[0]
        version_num = struct.unpack('>i', f.read(4))[0]

        # Read preset name (28 bytes)
        preset_name = f.read(28).decode('ascii', errors='ignore').strip('\x00')

        # Extract parameters...

        return {
            'name': preset_name,
            'plugin_id': unique_id,
            'version': version_num
        }
```

### Audio Characteristic Analysis
```python
def analyze_preset_audio(audio_sample, sample_rate=48000):
    """Analyze audio characteristics for preset metadata"""
    import librosa

    # Spectral features
    spectral_centroid = librosa.feature.spectral_centroid(y=audio_sample, sr=sample_rate)[0].mean()
    spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_sample, sr=sample_rate)[0].mean()

    # Brightness (normalized spectral centroid)
    brightness = min(spectral_centroid / (sample_rate / 2), 1.0)

    # Stereo width (if stereo)
    if len(audio_sample.shape) > 1:
        mid = (audio_sample[0] + audio_sample[1]) / 2
        side = (audio_sample[0] - audio_sample[1]) / 2
        stereo_width = np.std(side) / (np.std(mid) + 1e-10)
    else:
        stereo_width = 0.0

    # Warmth (low frequency content)
    low_freq_energy = np.sum(np.abs(librosa.stft(audio_sample)[:100, :]))
    total_energy = np.sum(np.abs(librosa.stft(audio_sample)))
    warmth = low_freq_energy / (total_energy + 1e-10)

    return {
        'brightness': brightness,
        'stereo_width': stereo_width,
        'warmth': warmth
    }
```

## Search and Filtering

### Text Search
```python
def search_presets(query, database):
    """Full-text search across preset names, tags, descriptions"""
    results = database.execute("""
        SELECT DISTINCT p.* FROM presets p
        LEFT JOIN preset_tags pt ON p.id = pt.preset_id
        LEFT JOIN tags t ON pt.tag_id = t.id
        WHERE
            p.name LIKE ? OR
            p.description LIKE ? OR
            t.name LIKE ?
        ORDER BY p.use_count DESC
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))

    return results.fetchall()
```

### Characteristic-Based Search
```python
def find_similar_presets(target_characteristics, database, limit=10):
    """Find presets with similar audio characteristics"""
    presets = database.execute("SELECT * FROM preset_metadata").fetchall()

    # Calculate similarity scores
    scores = []
    for preset in presets:
        score = 0
        score += abs(preset['brightness'] - target_characteristics['brightness'])
        score += abs(preset['warmth'] - target_characteristics['warmth'])
        score += abs(preset['stereo_width'] - target_characteristics['stereo_width'])

        scores.append((preset['preset_id'], score))

    # Sort by similarity (lower score = more similar)
    scores.sort(key=lambda x: x[1])

    return scores[:limit]
```

## Tagging System

### Auto-Tagging
```python
def auto_tag_preset(preset_name, audio_characteristics):
    """Generate automatic tags based on name and characteristics"""
    tags = []

    # Name-based tags
    name_lower = preset_name.lower()
    sound_types = ['bass', 'lead', 'pad', 'pluck', 'arp', 'fx', 'drum']
    for sound_type in sound_types:
        if sound_type in name_lower:
            tags.append(sound_type)

    # Characteristic-based tags
    if audio_characteristics['brightness'] > 0.7:
        tags.append('bright')
    elif audio_characteristics['brightness'] < 0.3:
        tags.append('dark')

    if audio_characteristics['warmth'] > 0.6:
        tags.append('warm')

    if audio_characteristics['stereo_width'] > 0.5:
        tags.append('wide')

    return tags
```

### Tag Suggestions
- Genre tags: electronic, rock, hip-hop, ambient, etc.
- Mood tags: aggressive, mellow, uplifting, dark, etc.
- Sound type: bass, lead, pad, pluck, arp, fx, percussion
- Characteristics: bright, warm, wide, mono, resonant, etc.

## AI-Powered Recommendations

### Context-Aware Recommendations
```python
def recommend_presets(project_context, user_history, database):
    """Recommend presets based on project and user behavior"""

    # Extract project context
    project_genre = project_context.get('genre')
    project_tempo = project_context.get('tempo')
    existing_sounds = project_context.get('used_presets', [])

    # Find complementary sounds
    # (e.g., if project has heavy bass, suggest leads/pads)

    # Consider user history
    frequently_used = get_frequent_tags(user_history)

    # Query database with combined criteria
    recommendations = database.execute("""
        SELECT p.* FROM presets p
        JOIN preset_tags pt ON p.id = pt.preset_id
        JOIN tags t ON pt.tag_id = t.id
        JOIN preset_metadata m ON p.id = m.preset_id
        WHERE
            m.genre = ? AND
            ABS(m.tempo - ?) < 20 AND
            t.name IN (?)
        ORDER BY p.use_count DESC
        LIMIT 20
    """, (project_genre, project_tempo, tuple(frequently_used)))

    return recommendations.fetchall()
```

## Preset Preview

### Audition System
- Load preset into plugin instance
- Play test MIDI note (e.g., C4)
- Render short audio sample
- Cache audio for quick playback
- Allow comparison of multiple presets

## Integration Points

- APEX DAW preset browser
- MAAPS plugin parameter automation
- sonic-mind-forge-platform sound library
- ai-mixing-mastering-engine preset suggestions
- Real-time preset preview in web UIs

## Technologies

- **SQLite** (preset database)
- **Whoosh** (full-text search)
- **scikit-learn** (similarity matching)
- **librosa** (audio analysis)
- **VST SDK** (preset format parsing)
- Custom parsers for plugin-specific formats
