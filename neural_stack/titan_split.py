import sys
import os
import torch
import torchaudio
from demucs.apply import apply_model
from demucs.pretrained import get_model
from reapy import reascript_api as RPR
import reapy

def neural_split_selected_item():
    reapy.connect()
    project = reapy.Project()
    
    # 1. Grab Selected Audio from Reaper
    if not project.selected_items:
        RPR.ShowConsoleMsg("No item selected for Neural Split.\n")
        return

    selected_item = project.selected_items[0]
    take = selected_item.active_take
    if not take:
        RPR.ShowConsoleMsg("Selected item has no active take.\n")
        return

    source = take.source
    filename = source.filename
    
    if not os.path.exists(filename):
        RPR.ShowConsoleMsg(f"File not found: {filename}\n")
        return

    # 2. Load SOTA Model (Meta's Hybrid Transformer)
    # 'htdemucs_ft' is the fine-tuned heavy hitter. 
    device = "cuda" if torch.cuda.is_available() else "cpu"
    RPR.ShowConsoleMsg(f"Engaging Neural Engine on: {device}\n")
    print(f"Engaging Neural Engine on: {device}")
    
    try:
        model = get_model(name='htdemucs_ft').to(device)
        model.eval()
    except Exception as e:
        RPR.ShowConsoleMsg(f"Error loading model: {str(e)}\n")
        return

    # 3. Load Audio Tensor
    try:
        wav, sr = torchaudio.load(filename)
        wav = wav.to(device)
    except Exception as e:
        RPR.ShowConsoleMsg(f"Error loading audio: {str(e)}\n")
        return
    
    # 4. Inference (The Heavy Lifting)
    # shifts=1 improves quality at cost of compute time
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    
    RPR.ShowConsoleMsg("Starting Inference...\n")
    try:
        with torch.no_grad():
            sources = apply_model(model, wav[None], shifts=1, split=True, overlap=0.25, progress=True)[0]
    except Exception as e:
        RPR.ShowConsoleMsg(f"Inference failed: {str(e)}\n")
        return
    
    # 5. Export Stems & Inject back to Reaper
    stem_names = ["drums", "bass", "other", "vocals"]
    base_dir = os.path.dirname(filename)
    
    RPR.ShowConsoleMsg("Exporting stems...\n")
    for i, stem in enumerate(sources):
        stem = stem * ref.std() + ref.mean() # De-normalize
        out_path = os.path.join(base_dir, f"NEURAL_{stem_names[i]}_{os.path.basename(filename)}")
        torchaudio.save(out_path, stem.cpu(), sr)
        
        # Insert into new track
        RPR.InsertMedia(out_path, 0)
    
    RPR.ShowConsoleMsg("Neural Split Complete.\n")

if __name__ == "__main__":
    neural_split_selected_item()
