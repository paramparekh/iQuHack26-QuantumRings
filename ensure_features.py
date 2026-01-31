import json
import sys
from pathlib import Path
# Add current directory to path so we can import feature_ext
sys.path.append(str(Path(__file__).parent))
from feature_ext import main as extract_main

# This script ensures that 'data/training_features.json' exists and is populated.
# It now uses feature_ext.py which writes to that file by default in its main()

if __name__ == "__main__":
    print("Running feature extraction...")
    extract_main()
    print("Done.")
