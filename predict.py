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
    is_xgb = 'XGBClassifier' in str(type(rf_thresh))
    rf_time = joblib.load(model_dir / 'rf_runtime.joblib')
    feature_cols = joblib.load(model_dir / 'feature_cols.joblib')
    try:
        feature_cols_runtime = joblib.load(model_dir / 'feature_cols_runtime.joblib')
    except:
        feature_cols_runtime = feature_cols + ['input_threshold'] # Fallback

    
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
            print(f"Warning: Features failed for {t_id}, using defaults.")
            feats = {
                'num_qubits': 0, 'depth': 0, 'gate_count': 0, 'treewidth': 1, 'max_gate_arity': 1,
                'two_qubit_gate_density': 0, 't_gate_count': 0, 's_gate_count': 0, 'clifford_gate_count': 0,
                'avg_2q_dist': 0, 'max_2q_dist': 0, 'max_cutwidth': 0, 'gates': {}
            }
            
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

        # Read Hardware/Precision from task
        # Keys might be 'processor'/'backend' or 'precision'
        proc = task.get('processor') or task.get('backend') or 'CPU'
        prec = task.get('precision', 'single')
        
        row['backend_cpu'] = 1 if str(proc).upper() == 'CPU' else 0
        row['precision_single'] = 1 if str(prec).lower() == 'single' else 0 
        
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
    
    # Predict Threshold
    pred_thresh_raw = rf_thresh.predict(X)
    
    # We must predict Runtime row-by-row or vectorized?
    # Vectorized is faster but we need to decode threshold first.
    
    # Decode Thresholds
    if le and is_xgb:
        pred_thresh_val = le.inverse_transform(pred_thresh_raw.astype(int))
    else:
        pred_thresh_val = pred_thresh_raw.astype(int)
        
    # Prepare Runtime Input
    # Runtime model needs 'input_threshold'. Even if feature_cols says it's there?
    # Wait, X was built from feature_cols. If feature_cols didn't have input_threshold, X doesn't.
    # We need separate feature cols?
    # In train_model.py we might have saved DIFFERENT feature_cols for runtime?
    # Yes: joblib.dump(feats_r, MODELS_DIR / 'feature_cols_runtime.joblib')
    # predict.py loads 'feature_cols.joblib' at line 26.
    # It SHOULD load 'feature_cols_runtime.joblib' too.
    
    # Let's fix imports first!
    pass

    # We need to load the runtime feature columns at the start of main
    # Then here:
    X_runtime = X.copy()
    X_runtime['input_threshold'] = pred_thresh_val
    
    # Ensure column order matches training
    # Align columns
    for c in feature_cols_runtime:
        if c not in X_runtime.columns:
            X_runtime[c] = 0
    X_runtime = X_runtime[feature_cols_runtime]
    
    pred_log_time = rf_time.predict(X_runtime)
    pred_time = np.exp(pred_log_time)
    
    # Construct Results
    results = []
    for i, t_id in enumerate(task_ids):
        p_val = int(pred_thresh_val[i])
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
