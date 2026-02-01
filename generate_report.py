import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import feature_ext
from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error

def main():
    # 1. Load Data
    with open('data/hackathon_public.json', 'r') as f:
        data = json.load(f)
        
    print("Loading models...")
    models_dir = Path('models')
    # Load the best runtime model (saved as rf_runtime.joblib by train_model.py)
    model = joblib.load(models_dir / 'rf_runtime.joblib')
    feature_cols = joblib.load(models_dir / 'feature_cols_runtime.joblib')
    
    # Load feature cache
    if Path('circuit_features.json').exists():
        with open('circuit_features.json', 'r') as f:
            feature_map = json.load(f)
    else:
        print("Feature cache not found, run train_model.py first or extraction.")
        return

    records = []
    
    print("Generating predictions...")
    
    for row in data['results']:
        filename = row['file']
        if filename not in feature_map:
            continue
            
        feats = feature_map[filename]
        
        # Base Features
        datum = {}
        datum['n_qubits'] = feats['num_qubits']
        datum['depth'] = feats['depth']
        datum['n_gates'] = feats['gate_count'] 
        datum['treewidth'] = feats.get('treewidth', 1)
        datum['max_gate_arity'] = feats.get('max_gate_arity', 1)
        datum['two_qubit_gate_density'] = feats.get('two_qubit_gate_density', 0)
        datum['t_gate_count'] = feats.get('t_gate_count', 0)
        datum['s_gate_count'] = feats.get('s_gate_count', 0)
        datum['clifford_gate_count'] = feats.get('clifford_gate_count', 0)
        datum['avg_2q_dist'] = feats.get('avg_2q_dist', 0)
        datum['max_2q_dist'] = feats.get('max_2q_dist', 0)
        datum['max_cutwidth'] = feats.get('max_cutwidth', 0)
        
        gates = feats['gates']
        n_2q = gates.get('cx', 0) + gates.get('cz', 0) + gates.get('cp', 0)
        datum['entanglement_density'] = n_2q / feats['num_qubits'] if feats['num_qubits'] > 0 else 0
        datum['q_depth'] = datum['n_qubits'] * datum['depth']
        datum['q_gates'] = datum['n_qubits'] * datum['n_gates']
        datum['n_2q'] = n_2q
        
        for g_name, count in gates.items():
            datum[f'n_{g_name}'] = count
            
        datum['backend_cpu'] = 1 if row['backend'] == 'CPU' else 0
        datum['precision_single'] = 1 if row['precision'] == 'single' else 0
        
        # Iterate Sweep
        threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
        for run in threshold_sweep:
            runtime = run.get('run_wall_s')
            if runtime is not None and runtime > 0:
                # Prepare Input
                d_in = datum.copy()
                d_in['input_threshold'] = run['threshold']
                
                # Predict
                df_in = pd.DataFrame([d_in])
                # Ensure cols
                for c in feature_cols:
                    if c not in df_in.columns:
                        df_in[c] = 0
                X = df_in[feature_cols]
                
                # Prediction (Log Space)
                pred_log = model.predict(X)[0]
                pred_val = float(np.exp(pred_log))
                
                records.append({
                    'filename': filename,
                    'threshold': run['threshold'],
                    'true_runtime': runtime,
                    'pred_runtime': pred_val,
                    'abs_error': abs(runtime - pred_val),
                    'pct_error': abs(runtime - pred_val) / runtime * 100
                })

    # Save CSV
    df_res = pd.DataFrame(records)
    print(f"Computed {len(df_res)} predictions.")
    
    csv_path = 'runtime_predictions.csv'
    df_res.to_csv(csv_path, index=False)
    print(f"Saved detailed report to {csv_path}")
    
    # Calculate Metrics
    mae = mean_absolute_error(df_res['true_runtime'], df_res['pred_runtime'])
    mape = mean_absolute_percentage_error(df_res['true_runtime'], df_res['pred_runtime'])
    r2 = r2_score(df_res['true_runtime'], df_res['pred_runtime'])
    
    print("\n--- Summary Metrics (All Data) ---")
    print(f"MAE:  {mae:.4f} s")
    print(f"MAPE: {mape:.2%} (Percentage Error)")
    print(f"R2:   {r2:.4f} (Fit Quality)")
    print("----------------------------------")

if __name__ == "__main__":
    main()
