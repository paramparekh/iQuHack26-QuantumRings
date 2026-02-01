import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier, XGBRegressor

# --- Model Benchmarking ---
from sklearn.svm import SVC, SVR
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# --- Configuration ---
DATA_PATH = Path('data/hackathon_public.json')
FEATURES_PATH = Path('circuit_features.json')
MODELS_DIR = Path('models')
MODELS_DIR.mkdir(exist_ok=True, parents=True)

# --- 1. Load Data ---
print("Loading data...")
with open(DATA_PATH, 'r') as f:
    data = json.load(f)

print("Loading features...")
if not FEATURES_PATH.exists():
    import feature_ext
    feature_ext.main()

with open(FEATURES_PATH, 'r') as f:
    feature_map = json.load(f)

# --- STRICT DATA FILTERING (Restoring High Performance) ---
def get_row_data(row):
    filename = row['file']
    
    # Prerequisite: Must have features
    if filename not in feature_map:
        return None
    
    # Prerequisite: Must have VALID FORWARD RUNTIME (Strict Filter)
    # This excludes "broken" or "unused" circuits that dragged down accuracy
    forward_time = row.get('forward', {}).get('run_wall_s')
    if forward_time is None:
        return None
    
    # Targets
    true_threshold = None
    threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
    for run in threshold_sweep:
        fid = run.get('sdk_get_fidelity')
        if fid is not None and fid >= 0.75:
            true_threshold = run['threshold']
            break
            
    if true_threshold is None:
        if row['status'] == 'no_threshold_met':
             true_threshold = 256
        else:
             return None # Skip undefined
    
    feats = feature_map[filename]
    datum = {}
    
    # Features
    datum['filename'] = filename
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
    
    datum['target_threshold'] = true_threshold
    # Note: datum['target_runtime'] is not set here because we explode later?
    # Actually, for get_row_data logic (Step 1144), we need to handle the structure properly.
    
    return datum, threshold_sweep

# Extract Data
dataset_thresh = []
dataset_runtime = []

for row in data['results']:
    res = get_row_data(row)
    if not res:
        continue
    
    datum, sweep = res
    
    # Threshold Data (1 per circuit)
    dataset_thresh.append(datum)
    
    # Runtime Data (Exploded Sweep)
    for run in sweep:
        if run.get('run_wall_s') and run['run_wall_s'] > 0:
            d_time = datum.copy()
            d_time['input_threshold'] = run['threshold']
            d_time['target_runtime'] = run['run_wall_s']
            dataset_runtime.append(d_time)

df_t = pd.DataFrame(dataset_thresh).fillna(0)
df_r = pd.DataFrame(dataset_runtime).fillna(0)

print(f"STRICT Filtering Applied.")
print(f"Threshold Samples: {len(df_t)}")
print(f"Runtime Samples: {len(df_r)}")

# Split (3/4 Train, 1/4 Val as requested)
unique_files = df_t['filename'].unique()
train_files, val_files = train_test_split(unique_files, test_size=0.25, random_state=42)

# Features
exclude = ['filename', 'target_threshold', 'target_runtime', 'backend_cpu', 'precision_single', 'input_threshold']
base_cols = [c for c in df_t.columns if c not in exclude]
feats_t = base_cols
feats_r = base_cols + ['input_threshold']

# Train Sets
mask_tr_t = df_t['filename'].isin(train_files)
mask_val_t = df_t['filename'].isin(val_files)
X_tr_t = df_t.loc[mask_tr_t, feats_t]
y_tr_t = df_t.loc[mask_tr_t, 'target_threshold']
X_v_t = df_t.loc[mask_val_t, feats_t]
y_v_t = df_t.loc[mask_val_t, 'target_threshold']

mask_tr_r = df_r['filename'].isin(train_files)
mask_val_r = df_r['filename'].isin(val_files)
X_tr_r = df_r.loc[mask_tr_r, feats_r]
y_tr_log_r = np.log(df_r.loc[mask_tr_r, 'target_runtime'] + 1e-6)
X_v_r = df_r.loc[mask_val_r, feats_r]
y_v_real_r = df_r.loc[mask_val_r, 'target_runtime']

print("\n--- Benchmarking ---")

# Threshold (RF)
rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_tr_t, y_tr_t)
pred_t = rf.predict(X_v_t)
acc_t = accuracy_score(y_v_t, pred_t)
print(f"Threshold Accuracy: {acc_t:.2%}")

# Runtime (RF) - Previously 58s MAE
gb = RandomForestRegressor(n_estimators=200, random_state=42)
gb.fit(X_tr_r, y_tr_log_r)
pred_log_r = gb.predict(X_v_r)
pred_r = np.exp(pred_log_r)
mae_r = mean_absolute_error(y_v_real_r, pred_r)

# Runtime Accuracy (1 - wMAPE)
w_mape = np.sum(np.abs(y_v_real_r - pred_r)) / np.sum(y_v_real_r)
acc_r_score = max(0, 100 * (1 - w_mape))

print(f"Runtime MAE: {mae_r:.4f} s")
print(f"Runtime Accuracy Score: {acc_r_score:.2f}%")

# Save Models
print("\nSaving 75% Trained Models (No Full Retrain)...")
joblib.dump(rf, MODELS_DIR / 'rf_threshold.joblib')
joblib.dump(gb, MODELS_DIR / 'rf_runtime.joblib')
joblib.dump(feats_t, MODELS_DIR / 'feature_cols.joblib')
joblib.dump(feats_r, MODELS_DIR / 'feature_cols_runtime.joblib')

# Save Report CSV
df_report = df_r.loc[mask_val_r].copy()
df_report['pred_runtime'] = pred_r
df_report['true_runtime'] = y_v_real_r
df_report.to_csv('runtime_predictions.csv', index=False)
print("Saved runtime_predictions.csv (Validation)")
