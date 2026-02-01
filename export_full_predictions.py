import pandas as pd
import joblib
import numpy as np
from pathlib import Path
import json

def main():
    # Load Data (Full)
    with open('data/hackathon_public.json', 'r') as f:
        data = json.load(f)
        
    # Load Models
    rf_thresh = joblib.load('models/rf_threshold.joblib')
    rf_time = joblib.load('models/rf_runtime.joblib')
    feature_cols = joblib.load('models/feature_cols.joblib')
    feature_cols_r = joblib.load('models/feature_cols_runtime.joblib')
    
    # Load Features
    with open('circuit_features.json', 'r') as f:
        feat_map = json.load(f)

    rows = []
    
    # Process All Rows
    for row in data['results']:
        fname = row['file']
        if fname not in feat_map: continue
        
        # Get True Runtime (if any)
        true_time = row.get('forward', {}).get('run_wall_s', 0)
        
        # Get True Threshold
        true_thresh = 256
        for r in row['threshold_sweep']:
            fid = r.get('sdk_get_fidelity')
            if fid is not None and fid >= 0.75:
                true_thresh = r['threshold']
                break
                
        # Build Feature Vector
        feats = feat_map[fname]
        vec = {k: v for k, v in feats.items() if k in feature_cols}
        
        # Add missing columns
        for c in feature_cols:
            if c not in vec: vec[c] = 0
            
        # Add Structural
        n_2q = feats['gates'].get('cx',0) + feats['gates'].get('cz',0) + feats['gates'].get('cp',0)
        vec['n_2q'] = n_2q
        vec['q_depth'] = feats['num_qubits'] * feats['depth']
        vec['q_gates'] = feats['num_qubits'] * feats['gate_count']
        vec['backend_cpu'] = 1 if row['backend'] == 'CPU' else 0
        vec['precision_single'] = 1 if row['precision'] == 'single' else 0
        
        # Predict Threshold
        df_vec = pd.DataFrame([vec])[feature_cols]
        pred_t_raw = rf_thresh.predict(df_vec)[0]
        pred_t = int(pred_t_raw)
        
        # Predict Runtime (using predicted threshold)
        vec_r = vec.copy()
        vec_r['input_threshold'] = pred_t
        df_vec_r = pd.DataFrame([vec_r])[feature_cols_r]
        pred_log_time = rf_time.predict(df_vec_r)[0]
        pred_time = np.exp(pred_log_time)
        
        rows.append({
            "filename": fname,
            "backend": row['backend'],
            "precision": row['precision'],
            "pred_threshold": pred_t,
            "true_threshold": true_thresh,
            "pred_runtime": pred_time,
            "true_runtime": true_time
        })
        
    # Valid Split Knowledge (Hardcoded from train_model.py seed=42)
    # We can't easily reproduce the random split here without re-running split logic.
    # But the user just wants the list.
    
    df = pd.DataFrame(rows)
    df['runtime_error'] = np.abs(df['true_runtime'] - df['pred_runtime'])
    
    txt_path = 'all_runtime_predictions.txt'
    with open(txt_path, 'w') as f:
        f.write(f"{'Circuit':<30} | {'Backend':<5} | {'Pred Thresh':<12} | {'True Thresh':<12} | {'Pred Time':<10} | {'True Time':<10} | {'Error':<10}\n")
        f.write("-" * 110 + "\n")
        for _, r in df.iterrows():
            f.write(f"{r['filename']:<30} | {r['backend']:<5} | {r['pred_threshold']:<12} | {r['true_threshold']:<12} | {r['pred_runtime']:<10.2f} | {r['true_runtime']:<10.2f} | {r['runtime_error']:<10.2f}\n")
            
    print(f"Exported all predictions to {txt_path}")

if __name__ == "__main__":
    main()
