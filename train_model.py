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

# --- 1. Load and Prepare Data ---
print("Loading data...")
with open(DATA_PATH, 'r') as f:
    data = json.load(f)

print("Loading pre-computed features...")
if not FEATURES_PATH.exists():
    import feature_ext
    feature_ext.main()

with open(FEATURES_PATH, 'r') as f:
    feature_map = json.load(f)

print(f"Loaded {len(data['results'])} result rows and {len(feature_map)} feature sets.")

def get_base_features(row):
    filename = row['file']
    if filename not in feature_map:
        return None
    
    feats = feature_map[filename]
    datum = {}
    
    # Copy features
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
    
    return datum

print("Extracting features and targets...")
dataset_thresh = []
dataset_runtime = []

for row in data['results']:
    base = get_base_features(row)
    if not base:
        continue
        
    # --- Threshold Data (One per circuit) ---
    true_threshold = None
    threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
    for run in threshold_sweep:
        fid = run.get('sdk_get_fidelity')
        # FIDELITY 0.75 RULE
        if fid is not None and fid >= 0.75:
            true_threshold = run['threshold']
            break
            
    if true_threshold is None:
        if row['status'] == 'no_threshold_met':
             true_threshold = 256
        else:
             true_threshold = None # Skip invalid
             
    if true_threshold is not None:
        d_thresh = base.copy()
        d_thresh['target_threshold'] = true_threshold
        dataset_thresh.append(d_thresh)
        
    # --- Runtime Data (Many per circuit: Explode Sweep) ---
    # We want to learn: Time = f(Circuit, Input_Threshold)
    for run in threshold_sweep:
        if run['run_wall_s'] is not None and run['run_wall_s'] > 0:
            d_time = base.copy()
            d_time['input_threshold'] = run['threshold']
            d_time['target_runtime'] = run['run_wall_s']
            dataset_runtime.append(d_time)

df_thresh = pd.DataFrame(dataset_thresh)
df_thresh = df_thresh.fillna(0)
df_runtime = pd.DataFrame(dataset_runtime)
df_runtime = df_runtime.fillna(0)

print(f"Threshold Samples: {len(df_thresh)} (1 per circuit)")
print(f"Runtime Samples: {len(df_runtime)} (Exploded sweep)")

# Split (Stratified by file for thresh, Grouped by file for runtime to avoid leakage)
unique_files = df_thresh['filename'].unique()
train_files, val_files = train_test_split(unique_files, test_size=0.2, random_state=42)

# Masks
train_mask_t = df_thresh['filename'].isin(train_files)
val_mask_t = df_thresh['filename'].isin(val_files)

train_mask_r = df_runtime['filename'].isin(train_files)
val_mask_r = df_runtime['filename'].isin(val_files)

# Feature Columns
exclude = ['filename', 'target_threshold', 'target_runtime', 'backend_cpu', 'precision_single', 'input_threshold']
potential = [c for c in df_thresh.columns if c not in exclude]
base_cols = ['n_qubits', 'n_gates', 'depth', 'n_2q', 'entanglement_density', 'treewidth', 'max_gate_arity', 'two_qubit_gate_density', 't_gate_count', 's_gate_count', 'clifford_gate_count', 'avg_2q_dist', 'max_2q_dist', 'max_cutwidth', 'q_depth', 'q_gates', 'backend_cpu', 'precision_single']
gate_cols = [c for c in potential if c.startswith('n_') and c not in base_cols]

feature_cols_thresh = base_cols + gate_cols
# Runtime model NEEDS input_threshold
feature_cols_runtime = base_cols + gate_cols + ['input_threshold']

print(f"Features (Thresh): {len(feature_cols_thresh)}")
print(f"Features (Runtime): {len(feature_cols_runtime)}")

# Training Data
X_train_t = df_thresh.loc[train_mask_t, feature_cols_thresh]
y_train_t = df_thresh.loc[train_mask_t, 'target_threshold']
X_val_t = df_thresh.loc[val_mask_t, feature_cols_thresh]
y_val_t = df_thresh.loc[val_mask_t, 'target_threshold']

X_train_r = df_runtime.loc[train_mask_r, feature_cols_runtime]
y_train_r = np.log(df_runtime.loc[train_mask_r, 'target_runtime'] + 1e-6)
X_val_r = df_runtime.loc[val_mask_r, feature_cols_runtime]
y_val_r = df_runtime.loc[val_mask_r, 'target_runtime']

# Define models dynamically
n_features_r = X_train_r.shape[1]

models_thresh = {
    'rf': RandomForestClassifier(n_estimators=200, random_state=42),
    'gb': GradientBoostingClassifier(n_estimators=200, random_state=42),
    'xgb': XGBClassifier(n_estimators=200, eval_metric='logloss', random_state=42),
    'svm': Pipeline([('scaler', StandardScaler()), ('clf', SVC(random_state=42))]),
    'lr': Pipeline([('scaler', StandardScaler()), ('clf', LogisticRegression(random_state=42, max_iter=1000))])
}

# ARD Kernel: Constant * RBF(length_scale_vector) + Noise
kernel = ConstantKernel() * RBF(length_scale=np.ones(n_features_r), length_scale_bounds=(1e-2, 1e4)) + WhiteKernel(noise_level=1, noise_level_bounds=(1e-4, 1e2))

models_time = {
    'rf': RandomForestRegressor(n_estimators=200, random_state=42),
    'gb': GradientBoostingRegressor(n_estimators=200, random_state=42),
    'xgb': XGBRegressor(n_estimators=200, objective='reg:absoluteerror', random_state=42),
    'svm': Pipeline([('scaler', StandardScaler()), ('reg', SVR())]),
    'lr': Pipeline([('scaler', StandardScaler()), ('reg', LinearRegression())]),
    'gpr': Pipeline([('scaler', StandardScaler()), ('gpr', GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42))])
}

best_thresh_model = None
best_thresh_acc = -1
best_time_model = None
best_time_mae = float('inf')

print("\n--- Model Benchmark Results ---")
print(f"{'Model':<10} | {'Type':<10} | {'Metric':<10} | {'Score':<10}")
print("-" * 50)

# Encode labels for XGBoost fit-only
le = LabelEncoder()
le.fit(y_train_t)
y_train_thresh_enc = le.transform(y_train_t)

# Handle unseen labels in validation
y_val_thresh_enc = []
for label in y_val_t:
    if label in le.classes_:
        y_val_thresh_enc.append(le.transform([label])[0])
    else:
        y_val_thresh_enc.append(0)
y_val_thresh_enc = np.array(y_val_thresh_enc)

for name, model in models_thresh.items():
    if name == 'xgb':
        model.fit(X_train_t, y_train_thresh_enc)
        y_pred_enc = model.predict(X_val_t)
        y_pred = le.inverse_transform(y_pred_enc)
    else:
        model.fit(X_train_t, y_train_t)
        y_pred = model.predict(X_val_t)
        
    acc = accuracy_score(y_val_t, y_pred)
    print(f"{name:<10} | {'Thresh':<10} | {'Accuracy':<10} | {acc:.4f}")
    
    if acc > best_thresh_acc:
        best_thresh_acc = acc
        best_thresh_model = model

# Runtime Benchmark
for name, model in models_time.items():
    model.fit(X_train_r, y_train_r)
    y_pred_log = model.predict(X_val_r)
    # Clip log predictions to avoid overflow
    y_pred_log = np.clip(y_pred_log, None, 15)
    y_pred = np.exp(y_pred_log)
    mae = mean_absolute_error(y_val_r, y_pred)
    print(f"{name:<10} | {'Runtime':<10} | {'MAE (s)':<10} | {mae:.4f}")
    
    if mae < best_time_mae:
        best_time_mae = mae
        best_time_model = model

print("-" * 50)
print(f"Best Threshold Model: {best_thresh_model.__class__.__name__} (Acc: {best_thresh_acc:.4f})")
print(f"Best Runtime Model:   {best_time_model.__class__.__name__} (MAE: {best_time_mae:.4f})")

# --- Save All Models ---
print("\nSaving all models...")

# Threshold Models
for name, model in models_thresh.items():
    joblib.dump(model, MODELS_DIR / f'{name}_threshold.joblib')

# Runtime Models
for name, model in models_time.items():
    joblib.dump(model, MODELS_DIR / f'{name}_runtime.joblib')

# Save Best (Standard Names for Predict.py default usage)
joblib.dump(best_thresh_model, MODELS_DIR / 'rf_threshold.joblib')
joblib.dump(best_time_model, MODELS_DIR / 'rf_runtime.joblib')

joblib.dump(feature_cols_thresh, MODELS_DIR / 'feature_cols.joblib')
joblib.dump(feature_cols_runtime, MODELS_DIR / 'feature_cols_runtime.joblib')
joblib.dump(le, MODELS_DIR / 'label_encoder.joblib')
print("Done.")

# --- Feature Importance Analysis ---
print("\n--- Feature Importance Analysis ---")
if hasattr(best_thresh_model, 'feature_importances_'):
    print(f"\nTop 10 Features for Threshold Model ({best_thresh_model.__class__.__name__}):")
    importances = best_thresh_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in range(min(10, len(indices))):
        print(f"{feature_cols_thresh[indices[i]]:<30} | {importances[indices[i]]:.4f}")

if hasattr(best_time_model, 'feature_importances_'):
    print(f"\nTop 10 Features for Runtime Model ({best_time_model.__class__.__name__}):")
    importances = best_time_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in range(min(10, len(indices))):
        print(f"{feature_cols_runtime[indices[i]]:<30} | {importances[indices[i]]:.4f}")
