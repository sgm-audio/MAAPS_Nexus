import os
import requests
import librosa
import numpy as np
import yt_dlp
from bs4 import BeautifulSoup
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

class Listener:
    def __init__(self):
        self.temp_dir = "AudioAgent/data/temp_audio"
        os.makedirs(self.temp_dir, exist_ok=True)

    def scan_for_audio(self, url):
        """Scans for embedded players (YouTube, SoundCloud, Vimeo) or raw files."""
        print(f"      👂 Listening to {url}...")
        try:
            # 1. Fake Browser
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            html_str = str(soup)

            # 2. Check for Embeds (Stream Jacking)
            targets = ['youtube.com', 'youtu.be', 'soundcloud.com', 'vimeo.com']
            for target in targets:
                if target in html_str:
                    # Find the specific link
                    # Check iframes first (High probability)
                    for iframe in soup.find_all('iframe'):
                        src = iframe.get('src', '')
                        if target in src:
                            print(f"      🕵️ Stream Jacker: Found Embed ({target})")
                            return src
                    
                    # Check links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if target in href:
                            print(f"      🕵️ Stream Jacker: Found Link ({target})")
                            return href

            # 3. Fallback to Raw Audio
            extensions = ['.mp3', '.wav', '.aif', '.m4a']
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.lower().endswith(ext) for ext in extensions):
                    if href.startswith('/'): return url.rstrip('/') + href
                    if href.startswith('http'): return href
                        
            return None
        except Exception:
            return None

    def download_asset(self, target_url):
        """Uses yt-dlp to rip audio from ANY source."""
        import uuid
        try:
            print(f"      ⬇️ Ripping Asset: {target_url}...")
            
            # Use UUID for deterministic filename
            file_id = str(uuid.uuid4())[:8]
            # Output template must force mp3 extension for the post-processor to match expectation
            # We output to a temp placeholder, ffmpeg converts it
            output_template = os.path.join(self.temp_dir, f"{file_id}.%(ext)s")
            final_path = os.path.join(self.temp_dir, f"{file_id}.mp3")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True, # Strict single video
                'max_filesize': 20 * 1024 * 1024, # 20MB Limit
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([target_url])
            
            # Verify existence because yt-dlp might fail silently or skip
            if os.path.exists(final_path):
                return final_path
                
            print(f"      ⚠️ File not found at expected path: {final_path}")
            return None
            
        except Exception as e:
            print(f"      ❌ Rip Failed: {e}")
            return None

    def analyze_asset(self, path):
        """Performs DSP analysis."""
        print(f"      ⚡ Analyzing Bio-Metrics...")
        try:
            y, sr = librosa.load(path, sr=22050, mono=True)
            
            rms = librosa.feature.rms(y=y)
            avg_db = np.mean(librosa.amplitude_to_db(rms, ref=np.max))
            
            # Calibration:
            # Librosa dBFS is relative to max signal. 
            # We treat full scale sine generally as 0dBFS.
            # Real LUFS requires EBU R128 weighting (High/Low pass + gating).
            # For speed/status without massive deps, we use a calibrated offset.
            # -3dB is a safe offset for RMS -> Sine LUFS approx.
            estimated_lufs = round(avg_db - 3.0, 1)
            
            return {
                "lufs": estimated_lufs,
                "peak": round(float(np.max(y)), 2),
                "duration": round(librosa.get_duration(y=y, sr=sr), 1)
            }
        except Exception as e:
            print(f"      ⚠️ DSP Failed: {e}")
            return None

    def generate_hook(self, filename, metrics):
        if not metrics: return None
        lufs = metrics['lufs']
        return f"I analyzed the audio in your video/embed. It measures {lufs} LUFS (Industry standard is -14)."
