import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import scipy.io.wavfile
import reapy
from reapy import reascript_api as RPR
import os

# Load Meta's MusicGen (Small is fast, Large is God-tier)
# We load strictly on demand for memory efficiency
def get_model():
    print("Loading MusicGen Model...")
    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    
    if torch.cuda.is_available():
        model = model.to("cuda")
        print("Model loaded on CUDA")
    else:
        print("Model loaded on CPU (Warning: Slow)")
        
    return processor, model

def generate_glitch_layer(prompt_text, duration_sec=5):
    reapy.connect()
    
    # Ensure output directory exists
    output_dir = "C:/Temp/ReaperAI"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        processor, model = get_model()
    except Exception as e:
        RPR.ShowConsoleMsg(f"Error loading model: {e}\n")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    RPR.ShowConsoleMsg(f"Generative Prompt: {prompt_text}\n")

    inputs = processor(
        text=[prompt_text],
        padding=True,
        return_tensors="pt",
    ).to(device)

    # Generate Audio Tokens
    RPR.ShowConsoleMsg("Generating audio tokens...\n")
    try:
        # Approx token/sec calculation adjustment might be needed depending on model
        audio_values = model.generate(**inputs, max_new_tokens=int(duration_sec * 50)) 
    except Exception as e:
        RPR.ShowConsoleMsg(f"Generation failed: {e}\n")
        return
    
    # Save to disk
    sampling_rate = model.config.audio_encoder.sampling_rate
    output_path = os.path.join(output_dir, f"generated_{prompt_text.replace(' ', '_')}.wav")
    
    try:
        scipy.io.wavfile.write(
            output_path, 
            rate=sampling_rate, 
            data=audio_values[0, 0].cpu().numpy()
        )
    except Exception as e:
        RPR.ShowConsoleMsg(f"Error saving wav: {e}\n")
        return
    
    # Send to Reaper
    RPR.InsertMedia(output_path, 0)
    RPR.ShowConsoleMsg(f"Inserted: {output_path}\n")

if __name__ == "__main__":
    # Example usage - in a real reaper action you'd probably pop a dialog to get the prompt
    # For now, we default or take args
    import sys
    prompt = "industrial metallic server crash mechanical failure 150bpm"
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    
    generate_glitch_layer(prompt)
