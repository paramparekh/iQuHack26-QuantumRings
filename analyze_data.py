import json
import pandas as pd
import numpy as np

def analyze():
    with open('data/hackathon_public.json', 'r') as f:
        data = json.load(f)
    
    thresholds = []
    runtimes = []
    
    for row in data['results']:
        # Extract Threshold
        true_threshold = -1
        status = row.get('status', '')
        
        # Check sweep
        for run in row.get('threshold_sweep', []):
            fid = run.get('sdk_get_fidelity')
            if fid is not None and fid >= 0.99:
                true_threshold = run['threshold']
                break
        
        # If not found but status says no_threshold_met, assume 256
        if true_threshold == -1 and status == 'no_threshold_met':
            true_threshold = 256
            
        thresholds.append(true_threshold)
        
        # Extract Runtime
        fw = row.get('forward', {})
        rt = fw.get('run_wall_s')
        if rt is not None:
            runtimes.append(rt)

    df_t = pd.Series(thresholds)
    df_r = pd.Series(runtimes)
    
    print(f"Total Samples: {len(data['results'])}")
    print("\n--- Threshold Distribution ---")
    print(df_t.value_counts().sort_index())
    
    print("\n--- Runtime Statistics ---")
    print(df_r.describe())

if __name__ == "__main__":
    analyze()
