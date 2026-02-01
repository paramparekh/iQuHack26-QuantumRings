import argparse
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from feature_ext import extract_features

def main():
    parser = argparse.ArgumentParser(description="Circuit Fingerprint Predictor")
    parser.add_argument("--tasks", required=True, help="Path to holdout tasks JSON")
    parser.add_argument("--circuits", required=True, help="Directory containing QASM files")
    parser.add_argument("--id-map", required=True, help="Path to ID map JSON (Optional, legacy)")
    parser.add_argument("--out", required=True, help="Output path for predictions JSON")
    args = parser.parse_args()

    # 1. Load Resources
    print("Loading models...")
    # Assume models are in a 'models' directory relative to this script
    script_dir = Path(__file__).parent
    model_dir = script_dir / 'models'
    
    rf_thresh = joblib.load(model_dir / 'rf_threshold.joblib')
    rf_time = joblib.load(model_dir / 'rf_runtime.joblib')
    feature_cols = joblib.load(model_dir / 'feature_cols.joblib')
    
    le = None
    le_path = model_dir / 'label_encoder.joblib'
    if le_path.exists():
        le = joblib.load(le_path)
        print("Loaded LabelEncoder for XGBoost support.")

    # 2. Load Inputs
    print("Loading inputs...")
    tasks_path = Path(args.tasks)
    circuits_path = Path(args.circuits)
    
    with open(tasks_path, 'r') as f:
        tasks_data = json.load(f)

    # Load ID Map
    id_map = {}
    if args.id_map:
        try:
            with open(args.id_map, 'r') as f:
                 id_map_data = json.load(f)
                 # Format: {"entries": [{"id": "...", "qasm_file": "..."}, ...]}
                 if 'entries' in id_map_data:
                     for entry in id_map_data['entries']:
                         id_map[entry['id']] = entry.get('qasm_file')
        except Exception as e:
            print(f"Warning: Could not load ID map: {e}")
            
    # Support both list-of-dicts and dict-of-task-ids formats
    tasks_list = []
    if isinstance(tasks_data, dict) and 'tasks' in tasks_data:
        tasks_list = tasks_data['tasks']
    elif isinstance(tasks_data, list):
        tasks_list = tasks_data
        
    print(f"Processing {len(tasks_list)} tasks...")
    
    rows = []
    task_ids = []

    for task in tasks_list:
        if isinstance(task, dict):
             t_id = task.get('id')
             # Try to find filename from task dict first, then ID map
             qasm_filename = task.get('filename') or task.get('qasm_file')
             if not qasm_filename and t_id in id_map:
                 qasm_filename = id_map[t_id]
        else:
             # If task is just ID string (unlikely for this format but possible)
             t_id = task
             qasm_filename = id_map.get(t_id)

        if not qasm_filename:
            print(f"Warning: No filename found for task {t_id}")
            continue
            
        qasm_path = circuits_path / qasm_filename
        if not qasm_path.exists():
             print(f"Warning: {qasm_path} not found")
             continue
             
        feats = extract_features(qasm_path)
        
        if feats is None:
            continue
            
        row = {}
        row['n_qubits'] = feats['num_qubits']
        row['depth'] = feats['depth']
        row['n_gates'] = feats['gate_count']
        row['treewidth'] = feats.get('treewidth', 1)
        row['max_gate_arity'] = feats.get('max_gate_arity', 1)
        
        # New features
        row['two_qubit_gate_density'] = feats.get('two_qubit_gate_density', 0)
        row['t_gate_count'] = feats.get('t_gate_count', 0)
        row['s_gate_count'] = feats.get('s_gate_count', 0)
        row['clifford_gate_count'] = feats.get('clifford_gate_count', 0)
        
        gates = feats.get('gates', {})
        n_2q = gates.get('cx', 0) + gates.get('cz', 0) + gates.get('cp', 0)
        row['entanglement_density'] = n_2q / feats['num_qubits'] if feats['num_qubits'] > 0 else 0
        
        # Structural features
        row['q_depth'] = row['n_qubits'] * row['depth']
        row['q_gates'] = row['n_qubits'] * row['n_gates']

        row['backend_cpu'] = 1 
        row['precision_single'] = 1 
        
        for g_name, count in gates.items():
            row[f'n_{g_name}'] = count
            
        row['n_2q'] = n_2q
        
        rows.append(row)
        task_ids.append(t_id)

    if not rows:
        print("No valid tasks processed.")
        with open(args.out, 'w') as f:
            json.dump([], f)
        return

    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure all columns exist and fill NaNs
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    
    # Select columns in correct order
    X = df[feature_cols].fillna(0)
    
    # Predict
    pred_thresh_raw = rf_thresh.predict(X)
    pred_log_time = rf_time.predict(X)
    pred_time = np.exp(pred_log_time)
    
    # Construct Results
    results = []
    for i, t_id in enumerate(task_ids):
        p_raw = pred_thresh_raw[i]
        
        if le:
            # Decode label
            # XGBoost/LabelEncoder outputs 0..N-1, we need 1, 2, 4...
            # inverse_transform expects array-like
            p_val = int(le.inverse_transform([int(p_raw)])[0])
        else:
            p_val = int(p_raw)
            
        p_t = float(pred_time[i])
        
        results.append({
            "id": t_id,
            "predicted_threshold_min": p_val,
            "predicted_forward_wall_s": p_t
        })
        
    print(f"Saving {len(results)} predictions to {args.out}")
    with open(args.out, 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
