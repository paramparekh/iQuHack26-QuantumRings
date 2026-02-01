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

def get_base_features(row):
    filename = row['file']
    if filename not in feature_map:
        return None
    feats = feature_map[filename]
    datum = {}
    
    # Structural
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
    
    # The contentious features
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
    return datum

print("Extracting datasets...")
dataset_thresh = []
dataset_runtime = []

for row in data['results']:
    base = get_base_features(row)
    if not base: continue
    
    # Threshold Data
    true_threshold = None
    threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
    for run in threshold_sweep:
        fid = run.get('sdk_get_fidelity')
        if fid is not None and fid >= 0.75:
            true_threshold = run['threshold']
            break
    
    # Include 'failed' circuits as 256 threshold? Or drop? Use 256 logic.
    if true_threshold is None and row['status'] == 'no_threshold_met':
        true_threshold = 256
        
    if true_threshold is not None:
        d = base.copy()
        d['target_threshold'] = true_threshold
        dataset_thresh.append(d)
        
    # Runtime Data (Exploded)
    for run in threshold_sweep:
        if run.get('run_wall_s') and run['run_wall_s'] > 0:
            d = base.copy()
            d['input_threshold'] = run['threshold']
            d['target_runtime'] = run['run_wall_s']
            dataset_runtime.append(d)

df_t = pd.DataFrame(dataset_thresh).fillna(0)
df_r = pd.DataFrame(dataset_runtime).fillna(0)
print(f"Data: {len(df_t)} Threshold Samples, {len(df_r)} Runtime Samples.")

# --- Split Strategy ---
# Include "unused" circuits implies using everything available?
# We will do a 80/20 split based on Filenames to prevent leakage (Standard Practice)
unique_files = df_t['filename'].unique()
train_files, val_files = train_test_split(unique_files, test_size=0.2, random_state=42)

def get_xy(df, features, target_col, log_target=False):
    mask_train = df['filename'].isin(train_files)
    mask_val = df['filename'].isin(val_files)
    
    X_train = df.loc[mask_train, features]
    X_val = df.loc[mask_val, features]
    y_train = df.loc[mask_train, target_col]
    y_val = df.loc[mask_val, target_col]
    
    if log_target:
        y_train = np.log(y_train + 1e-6)
        # Keep y_val in real scale for MAE
        
    return X_train, y_train, X_val, y_val

# --- Feature Sets ---
exclude = ['filename', 'target_threshold', 'target_runtime', 'backend_cpu', 'precision_single', 'input_threshold', 'avg_2q_dist', 'max_2q_dist']
base_structural = [c for c in df_t.columns if c not in exclude and not c.startswith('n_')]
gate_counts = [c for c in df_t.columns if c.startswith('n_') and c not in ['n_qubits', 'n_gates', 'n_2q']]

# Base Features (No Distance)
feats_base = base_structural + gate_counts + ['n_qubits', 'n_gates', 'depth', 'n_2q', 'entanglement_density', 'backend_cpu', 'precision_single']
# Full Features (With Distance)
feats_dist = feats_base + ['avg_2q_dist', 'max_2q_dist']

# Note: Runtime models need 'input_threshold'
feats_base_r = feats_base + ['input_threshold']
feats_dist_r = feats_dist + ['input_threshold']

# --- Ablation Stuy ---
print("\n--- Ablation Study: Long Range Gates ---")
results = {}

for name, f_set_t, f_set_r in [("Without_Dist", feats_base, feats_base_r), ("With_Dist", feats_dist, feats_dist_r)]:
    print(f"\nTesting {name} ...")
    
    # Threshold
    X_tr, y_tr, X_v, y_v = get_xy(df_t, f_set_t, 'target_threshold')
    accs = []
    # Test RF (usually best)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_tr, y_tr)
    pred = rf.predict(X_v)
    acc = accuracy_score(y_v, pred)
    print(f"  Threshold (RF) Acc: {acc:.4f}")
    results[f"{name}_Thresh"] = acc
    
    # Runtime
    X_tr, y_tr_log, X_v, y_v_real = get_xy(df_r, f_set_r, 'target_runtime', log_target=True)
    # Test GB (usually best)
    gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb.fit(X_tr, y_tr_log)
    pred_log = gb.predict(X_v)
    pred = np.exp(pred_log)
    mae = mean_absolute_error(y_v_real, pred)
    print(f"  Runtime (GB) MAE: {mae:.4f}")
    results[f"{name}_Runtime"] = mae

# Decision
print("\n--- Decision ---")
best_feats_t = feats_dist
best_feats_r = feats_dist_r
use_dist = True

# Bias towards keeping unless significant drop, or user requested removing if increases score?
# User: "try removing... if that increases score"
# So if Without > With (Acc) or Without < With (MAE), switch.

if results["Without_Dist_Thresh"] > results["With_Dist_Thresh"]:
    print(f"Removing Distance Features improves Threshold: {results['Without_Dist_Thresh']} > {results['With_Dist_Thresh']}")
    best_feats_t = feats_base
    use_dist = False

if results["Without_Dist_Runtime"] < results["With_Dist_Runtime"]:
    print(f"Removing Distance Features improves Runtime: {results['Without_Dist_Runtime']} < {results['With_Dist_Runtime']}")
    best_feats_r = feats_base_r
    # We can split features per model, but simpler to align? No, predict.py calls separate models.
    # Let's optimize separately.

# Final Training
print("\n--- Training Final Models (With 80/20 Validation for Report) ---")
# Use the winning feature sets
X_full_t, y_full_t, X_val_t, y_val_t = get_xy(df_t, best_feats_t, 'target_threshold')
X_full_r, y_full_log_r, X_val_r, y_val_real_r = get_xy(df_r, best_feats_r, 'target_runtime', log_target=True)

# Train RF Threshold
rf_final = RandomForestClassifier(n_estimators=200, random_state=42)
rf_final.fit(X_full_t, y_full_t)
val_pred_t = rf_final.predict(X_val_t)
final_acc = accuracy_score(y_val_t, val_pred_t)

# Train GB Runtime
gb_final = GradientBoostingRegressor(n_estimators=200, random_state=42)
gb_final.fit(X_full_r, y_full_log_r)
val_pred_log_r = gb_final.predict(X_val_r)
val_pred_r = np.exp(val_pred_log_r)
final_mae = mean_absolute_error(y_val_real_r, val_pred_r)

print(f"Final Validation Accuracy: {final_acc:.4f}")
print(f"Final Validation MAE: {final_mae:.4f}")

# Save Models
print("Saving...")
joblib.dump(rf_final, MODELS_DIR / 'rf_threshold.joblib')
joblib.dump(gb_final, MODELS_DIR / 'rf_runtime.joblib') # Save GB as the 'rf_runtime' slot for predict.py compat
joblib.dump(best_feats_t, MODELS_DIR / 'feature_cols.joblib')
joblib.dump(best_feats_r, MODELS_DIR / 'feature_cols_runtime.joblib')

# Save Validation Predictions for Report
# We need to reconstruct the dataframe for the report
df_val_report = df_r.loc[df_r['filename'].isin(val_files)].copy()
df_val_report['pred_runtime'] = val_pred_r
df_val_report['true_runtime'] = y_val_real_r
df_val_report.to_csv('runtime_predictions.csv', index=False)

print("Saved runtime_predictions.csv (Validation Set Only)")
