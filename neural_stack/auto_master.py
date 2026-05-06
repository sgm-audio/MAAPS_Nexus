from pedalboard import Pedalboard, Compressor, Limiter, HighpassFilter
from pedalboard.io import AudioFile
import sys
import os
import reapy
from reapy import reascript_api as RPR

def neural_master_selected_item():
    reapy.connect()
    project = reapy.Project()
    
    # 1. Grab Selected Audio from Reaper
    if not project.selected_items:
        RPR.ShowConsoleMsg("No item selected for Neural Master.\n")
        return

    selected_item = project.selected_items[0]
    take = selected_item.active_take
    if not take:
        RPR.ShowConsoleMsg("Selected item has no active take.\n")
        return

    input_filename = take.source.filename
    
    if not os.path.exists(input_filename):
        RPR.ShowConsoleMsg(f"File not found: {input_filename}\n")
        return

    # Define the "Titan" Chain in pure code
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=30), # Clean sub-rumble
        Compressor(threshold_db=-10, ratio=4, attack_ms=10, release_ms=50), # Glue
        Limiter(threshold_db=-1.0), # Brickwall
    ])

    base_dir = os.path.dirname(input_filename)
    output_filename = os.path.join(base_dir, f"MASTERED_PY_{os.path.basename(input_filename)}")

    RPR.ShowConsoleMsg(f"Mastering: {input_filename}...\n")

    try:
        # Process the file offline (Faster than Real-time)
        with AudioFile(input_filename) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate

        # Run the Board
        effected = board(audio, samplerate)

        # Save
        with AudioFile(output_filename, 'w', samplerate, effected.shape[0]) as f:
            f.write(effected)
            
        # Insert into new track
        RPR.InsertMedia(output_filename, 0)
        RPR.ShowConsoleMsg(f"Mastering Complete. Saved to {output_filename}\n")
        
    except Exception as e:
        RPR.ShowConsoleMsg(f"Mastering failed: {str(e)}\n")

if __name__ == "__main__":
    neural_master_selected_item()
