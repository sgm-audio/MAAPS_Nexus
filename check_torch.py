
try:
    import torch
    print(f"Torch imported successfully. Version: {torch.__version__}")
except OSError as e:
    print(f"Failed to import torch: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
