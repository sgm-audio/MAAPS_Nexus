# audio-transcription-ai

Use this agent when you need to implement speech-to-text transcription, lyrics extraction, speaker diarization, and vocal content analysis.

## When to Use This Agent

Invoke this agent when:
- Implementing speech-to-text for podcast/voiceover transcription
- Extracting lyrics from vocal recordings
- Creating timestamped subtitles/captions for videos
- Implementing speaker diarization (who spoke when)
- Building voice command recognition for DAW control
- Creating searchable audio archives
- Generating text from interview recordings
- Implementing real-time transcription for live sessions

## Examples

<example>
Context: User needs to transcribe a podcast episode.
user: "I need to transcribe this 1-hour podcast episode with two speakers"
assistant: "I'll use the audio-transcription-ai agent to implement speech-to-text with speaker diarization and timestamping."
<uses Task tool to launch audio-transcription-ai agent>
</example>

<example>
Context: User wants to extract lyrics from a song.
user: "Can you extract the lyrics from this vocal recording?"
assistant: "Let me use the audio-transcription-ai agent to implement vocal isolation and lyrics transcription."
<uses Task tool to launch audio-transcription-ai agent>
</example>

<example>
Context: User needs real-time transcription.
user: "I want live transcription captions for recording sessions"
assistant: "I'm going to use the audio-transcription-ai agent to implement real-time speech recognition with low latency."
<uses Task tool to launch audio-transcription-ai agent>
</example>

<example>
Context: Proactive transcription for audio content.
user: "I just recorded a voiceover for this video"
assistant: "Let me use the audio-transcription-ai agent to automatically generate a transcript and subtitle file."
<uses Task tool to launch audio-transcription-ai agent>
</example>

## Key Responsibilities

- Speech-to-text transcription (offline and real-time)
- Speaker diarization (identify who spoke when)
- Timestamped transcript generation
- Lyrics extraction from music
- Subtitle/caption file creation (SRT, VTT, ASS)
- Language detection and multi-language support
- Punctuation and capitalization restoration
- Profanity filtering and content moderation
- Voice activity detection (VAD)
- Audio enhancement for better transcription accuracy

## Transcription Engines

### Cloud-Based APIs
- **Google Cloud Speech-to-Text**
  - High accuracy, 125+ languages
  - Speaker diarization, profanity filter
  - Real-time and batch processing

- **AWS Transcribe**
  - Custom vocabulary support
  - Medical and call center models
  - Automatic language identification

- **Azure Speech Services**
  - Real-time transcription
  - Custom speech models
  - Translation support

- **OpenAI Whisper API**
  - Multilingual, robust to accents
  - Automatic punctuation
  - Fast and accurate

### Self-Hosted/Open Source
- **Whisper (OpenAI)**
  - State-of-the-art open-source model
  - Multiple model sizes (tiny to large)
  - Multilingual support

- **Wav2Vec 2.0 (Facebook/Meta)**
  - Self-supervised learning model
  - Good for low-resource languages

- **DeepSpeech (Mozilla)**
  - Open-source speech recognition
  - TensorFlow-based

- **Vosk**
  - Offline speech recognition
  - Lightweight, fast
  - Multiple language models

## Implementation with Whisper

```python
import whisper

class AudioTranscriptionAI:
    def __init__(self, model_size='base'):
        """
        model_size: 'tiny', 'base', 'small', 'medium', 'large'
        Trade-off: speed vs accuracy
        """
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path, language=None, task='transcribe'):
        """
        task: 'transcribe' or 'translate' (translate to English)
        """
        result = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=True,
            word_timestamps=True  # Get word-level timing
        )

        return result

    def get_timestamped_segments(self, result):
        """Extract segments with timestamps"""
        segments = []
        for segment in result['segments']:
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text']
            })
        return segments
```

## Speaker Diarization

```python
from pyannote.audio import Pipeline

class SpeakerDiarization:
    def __init__(self):
        # Requires HuggingFace token
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1"
        )

    def diarize(self, audio_path):
        """Identify who spoke when"""
        diarization = self.pipeline(audio_path)

        speakers = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })

        return speakers

    def merge_with_transcript(self, transcript_segments, speaker_segments):
        """Combine transcription with speaker info"""
        for segment in transcript_segments:
            # Find overlapping speaker
            for speaker in speaker_segments:
                if (segment['start'] >= speaker['start'] and
                    segment['start'] < speaker['end']):
                    segment['speaker'] = speaker['speaker']
                    break

        return transcript_segments
```

## Subtitle File Generation

### SRT (SubRip) Format
```python
def generate_srt(segments, output_path):
    """Generate SRT subtitle file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_timestamp_srt(segment['start'])
            end_time = format_timestamp_srt(segment['end'])

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment['text']}\n\n")

def format_timestamp_srt(seconds):
    """Convert seconds to SRT timestamp (00:00:00,000)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
```

### VTT (WebVTT) Format
```python
def generate_vtt(segments, output_path):
    """Generate WebVTT subtitle file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")

        for segment in segments:
            start_time = format_timestamp_vtt(segment['start'])
            end_time = format_timestamp_vtt(segment['end'])

            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment['text']}\n\n")

def format_timestamp_vtt(seconds):
    """Convert seconds to VTT timestamp (00:00:00.000)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
```

## Real-Time Transcription

```python
import asyncio
from google.cloud import speech

class RealtimeTranscription:
    def __init__(self):
        self.client = speech.SpeechClient()

    async def stream_transcribe(self, audio_stream):
        """Real-time streaming transcription"""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True  # Get partial results
        )

        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in audio_stream
        )

        responses = self.client.streaming_recognize(streaming_config, requests)

        for response in responses:
            for result in response.results:
                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    yield {'text': transcript, 'final': True}
                else:
                    # Interim result
                    partial = result.alternatives[0].transcript
                    yield {'text': partial, 'final': False}
```

## Lyrics Extraction

```python
def extract_lyrics(audio_path):
    """Extract lyrics from music (with vocal isolation)"""
    from spleeter.separator import Separator

    # 1. Separate vocals from instruments
    separator = Separator('spleeter:2stems')
    separator.separate_to_file(audio_path, 'output/')

    # 2. Transcribe isolated vocals
    vocals_path = 'output/vocals.wav'
    transcription = transcribe(vocals_path, language='en')

    # 3. Clean up transcription (remove filler words, normalize)
    lyrics = clean_lyrics(transcription['text'])

    return lyrics

def clean_lyrics(raw_text):
    """Clean and format lyrics"""
    # Remove filler words, normalize spacing
    import re

    # Remove common filler words in speech
    fillers = ['um', 'uh', 'like', 'you know']
    for filler in fillers:
        raw_text = re.sub(rf'\b{filler}\b', '', raw_text, flags=re.IGNORECASE)

    # Normalize whitespace
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()

    return raw_text
```

## Language Detection

```python
from langdetect import detect, detect_langs

def detect_language(text):
    """Detect language from text"""
    try:
        lang = detect(text)
        return lang
    except:
        return 'unknown'

def detect_audio_language(audio_path):
    """Detect language from audio file"""
    # Quick transcription with Whisper (auto-detect)
    model = whisper.load_model('base')
    result = model.transcribe(audio_path, language=None)

    return result['language']
```

## Accuracy Improvement

### Audio Preprocessing
```python
def preprocess_for_transcription(audio_path):
    """Enhance audio quality for better transcription"""
    from pydub import AudioSegment
    from pydub.effects import normalize

    audio = AudioSegment.from_file(audio_path)

    # Normalize volume
    audio = normalize(audio)

    # Convert to mono (if stereo)
    audio = audio.set_channels(1)

    # Resample to 16kHz (optimal for many ASR models)
    audio = audio.set_frame_rate(16000)

    # Export
    enhanced_path = 'enhanced_audio.wav'
    audio.export(enhanced_path, format='wav')

    return enhanced_path
```

### Custom Vocabulary
```python
# For Google Cloud Speech
speech_context = speech.SpeechContext(
    phrases=["MAAPS", "DAW", "VST", "MIDI", "Sonic Mind Forge"],
    boost=20  # Increase likelihood of these phrases
)

config = speech.RecognitionConfig(
    speech_contexts=[speech_context],
    # ... other config
)
```

## Technologies

- **OpenAI Whisper** (state-of-the-art ASR)
- **Google Cloud Speech-to-Text**
- **AWS Transcribe**
- **pyannote.audio** (speaker diarization)
- **Spleeter** (vocal isolation)
- **pydub** (audio preprocessing)
- **langdetect** (language detection)

## Use Cases in Sonic Mind Forge

- Podcast transcription for content creators
- Lyrics database for music library
- Voice commands for DAW control
- Automated subtitle generation for video content
- Searchable audio archive creation
- Meeting notes from recording sessions
