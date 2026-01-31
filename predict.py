import argparse
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from feature_extractor import extract_features

def main():
    parser = argparse.ArgumentParser(description="Circuit Fingerprint Predictor")
    parser.add_argument("--tasks", required=True, help="Path to holdout tasks JSON")
    parser.add_argument("--circuits", required=True, help="Directory containing QASM files")
    parser.add_argument("--id-map", required=True, help="Path to ID map JSON")
    parser.add_argument("--out", required=True, help="Output path for predictions JSON")
    args = parser.parse_args()

    # 1. Load Resources
    print("Loading models...")
    # Assume models are in a 'models' directory relative to this script
    script_dir = Path(__file__).parent
    rf_thresh = joblib.load(script_dir / 'models' / 'rf_threshold.joblib')
    rf_time = joblib.load(script_dir / 'models' / 'rf_runtime.joblib')

    # 2. Load Inputs
    print("Loading inputs...")
    with open(args.tasks, 'r') as f:
        tasks_input = json.load(f)
        if isinstance(tasks_input, dict) and 'tasks' in tasks_input:
            tasks = tasks_input['tasks']
        else:
            tasks = tasks_input
    
    with open(args.id_map, 'r') as f:
        id_map_data = json.load(f)
    
    # Create dict for faster lookup: task_id -> qasm_filename
    # ID Map format: {"entries": [{"id": "H001", "qasm_file": "foo.qasm"}, ...]}
    id_to_file = {entry['id']: entry['qasm_file'] for entry in id_map_data['entries']}
    
    predictions = []
    
    print(f"Processing {len(tasks)} tasks...")
    
    # Load feature columns used in training
    feature_cols = joblib.load(script_dir / 'models' / 'feature_cols.joblib')
    print(f"Using {len(feature_cols)} features.")

    # 4. Process each task
    task_data = [] # List of dicts
    
    for i, task in enumerate(tasks):
        task_id = task['id']
        filename = id_to_file.get(task_id)
        
        if not filename:
            continue
            
        qasm_path = Path(args.circuits) / filename
        feats = extract_features(qasm_path)
        
        if feats is None:
            continue
            
        # PROCESSS NESTED SCHEMA
        # Schema: {"gates": {...}, "num_qubits": N, "depth": D, "gate_count": G, "entanglement_density": ED}
        row = {}
        row['n_qubits'] = feats['num_qubits']
        row['depth'] = feats['depth']
        row['n_gates'] = feats['gate_count']
        row['entanglement_density'] = feats['entanglement_density']
        
        gates = feats.get('gates', {})
        for g_name, count in gates.items():
            row[f'n_{g_name}'] = count
        
        # Derived
        row['n_2q'] = gates.get('cx', 0) + gates.get('cz', 0)
        
        row['backend_cpu'] = 1 if task['processor'] == 'CPU' else 0
        row['precision_single'] = 1 if task['precision'] == 'single' else 0
        row['task_id'] = task_id
        
        task_data.append(row)

    if not task_data:
        print("No valid tasks found!")
        return

    df = pd.DataFrame(task_data)
    
    # Ensure all columns exist
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
            
    # Reorder to match training
    X = df[feature_cols].fillna(0)
    
    pred_thresh = rf_thresh.predict(X)
    pred_log_time = rf_time.predict(X)
    pred_time = np.exp(pred_log_time)
    
    # 5. Format Output
    results = []
    for i in range(len(df)):
        t_id = df.iloc[i]['task_id']
        p_thresh = int(pred_thresh[i])
        p_time = float(pred_time[i])
        
        results.append({
            "id": t_id,
            "predicted_threshold_min": p_thresh,
            "predicted_forward_wall_s": p_time
        })
        
    # 6. Save
    # Submissions allow list or wrapper. Let's use List as per example A.
    # Actually example B "Wrapper" might be safer? The doc says "Accepted JSON shapes: List... Wrapper".
    # Let's use List.
    print(f"Saving {len(results)} predictions to {args.out}")
    with open(args.out, 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
