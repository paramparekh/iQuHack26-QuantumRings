import json
from pathlib import Path
from feature_extractor import extract_features

# Configuration
DATA_PATH = Path('data/hackathon_public.json')
OUTPUT_PATH = Path('data/training_features.json')
CIRCUITS_DIR = Path('circuits')

def main():
    print(f"Reading data from {DATA_PATH}...")
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)

    # Get unique list of files
    unique_files = set()
    for row in data['results']:
        unique_files.add(row['file'])
    
    print(f"Found {len(unique_files)} unique circuits.")

    features_map = {}
    
    print("Extracting features...")
    for filename in unique_files:
        if filename in features_map:
            continue
            
        fpath = CIRCUITS_DIR / filename
        feats = extract_features(fpath)
        
        if feats is not None:
            features_map[filename] = feats
        else:
            print(f"Failed to extract features for {filename}")

    print(f"Saving {len(features_map)} feature sets to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(features_map, f, indent=2)
    
    print("Done.")

if __name__ == "__main__":
    main()
