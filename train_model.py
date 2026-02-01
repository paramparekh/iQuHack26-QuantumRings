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
    raise FileNotFoundError(f"Features file {FEATURES_PATH} not found. Run ensure_features.py first.")

with open(FEATURES_PATH, 'r') as f:
    feature_map = json.load(f)

print(f"Loaded {len(data['results'])} result rows and {len(feature_map)} feature sets.")

def get_row_data(row):
    filename = row['file']
    
    # 1. Targets
    true_threshold = None
    threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
    for run in threshold_sweep:
        fid = run.get('sdk_get_fidelity')
        if fid is not None and fid >= 0.99:
            true_threshold = run['threshold']
            break
    
    if true_threshold is None:
        if row['status'] == 'no_threshold_met':
             true_threshold = 256
        else:
             return None
    
    forward_time = row.get('forward', {}).get('run_wall_s')
    if forward_time is None:
        return None

    if filename not in feature_map:
        return None
    
    feats = feature_map[filename]
    
    datum = {}
    datum['filename'] = filename
    datum['n_qubits'] = feats['num_qubits']
    datum['depth'] = feats['depth']
    datum['n_gates'] = feats['gate_count'] 
    
    datum['treewidth'] = feats.get('treewidth', 1)
    datum['max_gate_arity'] = feats.get('max_gate_arity', 1)
    
    # New features
    datum['two_qubit_gate_density'] = feats.get('two_qubit_gate_density', 0)
    datum['t_gate_count'] = feats.get('t_gate_count', 0)
    datum['s_gate_count'] = feats.get('s_gate_count', 0)
    datum['clifford_gate_count'] = feats.get('clifford_gate_count', 0)
    
    gates = feats['gates']
    n_2q = gates.get('cx', 0) + gates.get('cz', 0) + gates.get('cp', 0)
    datum['entanglement_density'] = n_2q / feats['num_qubits'] if feats['num_qubits'] > 0 else 0
    
    # Structural features
    datum['q_depth'] = datum['n_qubits'] * datum['depth']
    datum['q_gates'] = datum['n_qubits'] * datum['n_gates']

    for g_name, count in gates.items():
        datum[f'n_{g_name}'] = count
        
    datum['n_2q'] = n_2q
    
    datum['backend_cpu'] = 1 if row['backend'] == 'CPU' else 0
    datum['precision_single'] = 1 if row['precision'] == 'single' else 0
    datum['target_threshold'] = true_threshold
    datum['target_runtime'] = forward_time
    
    return datum

print("Extracting features and targets...")
dataset = []
for row in data['results']:
    d = get_row_data(row)
    if d:
        dataset.append(d)

df = pd.DataFrame(dataset)
print(f"Processed dataframe shape: {df.shape}")

unique_files = df['filename'].unique()
train_files, val_files = train_test_split(unique_files, test_size=0.2, random_state=42)

train_mask = df['filename'].isin(train_files)
val_mask = df['filename'].isin(val_files)

train_df = df[train_mask]
val_df = df[val_mask]

print(f"Train samples: {len(train_df)} (from {len(train_files)} circuits)")
print(f"Validation samples: {len(val_df)} (from {len(val_files)} circuits)")

exclude_cols = ['filename', 'target_threshold', 'target_runtime', 'backend_cpu', 'precision_single']
potential_features = [c for c in df.columns if c not in exclude_cols]

base_features = ['n_qubits', 'n_gates', 'depth', 'n_2q', 'entanglement_density', 'treewidth', 'max_gate_arity', 'two_qubit_gate_density', 't_gate_count', 's_gate_count', 'clifford_gate_count', 'q_depth', 'q_gates', 'backend_cpu', 'precision_single']
gate_features = [c for c in potential_features if c.startswith('n_') and c not in base_features]
feature_cols = base_features + gate_features

print(f"Features used ({len(feature_cols)}): {feature_cols}")

df[feature_cols] = df[feature_cols].fillna(0)

target_thresh = 'target_threshold'
target_time = 'target_runtime'

X_train = df.loc[train_mask, feature_cols]
y_train_thresh = df.loc[train_mask, target_thresh]
y_train_time = np.log(df.loc[train_mask, target_time] + 1e-6)

X_val = df.loc[val_mask, feature_cols]
y_val_thresh = df.loc[val_mask, target_thresh]
y_val_time = df.loc[val_mask, target_time]

# --- Model Benchmarking ---

results = []

from sklearn.svm import SVC, SVR
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

models_thresh = {
    'rf': RandomForestClassifier(n_estimators=200, random_state=42),
    'gb': GradientBoostingClassifier(n_estimators=200, random_state=42),
    'xgb': XGBClassifier(n_estimators=200, eval_metric='logloss', random_state=42),
    'svm': Pipeline([('scaler', StandardScaler()), ('clf', SVC(random_state=42))]),
    'lr': Pipeline([('scaler', StandardScaler()), ('clf', LogisticRegression(random_state=42, max_iter=1000))])
}

models_time = {
    'rf': RandomForestRegressor(n_estimators=200, random_state=42),
    'gb': GradientBoostingRegressor(n_estimators=200, random_state=42),
    'xgb': XGBRegressor(n_estimators=200, objective='reg:absoluteerror', random_state=42),
    'svm': Pipeline([('scaler', StandardScaler()), ('reg', SVR())]),
    'lr': Pipeline([('scaler', StandardScaler()), ('reg', LinearRegression())])
}

best_thresh_model = None
best_thresh_acc = -1
best_time_model = None
best_time_mae = float('inf')

print("\n--- Model Benchmark Results ---")
print(f"{'Model':<10} | {'Type':<10} | {'Metric':<10} | {'Score':<10}")
print("-" * 50)

# Encode labels for XGBoost
le = LabelEncoder()
y_all_thresh = pd.concat([y_train_thresh, y_val_thresh])
le.fit(y_all_thresh)
y_train_thresh_enc = le.transform(y_train_thresh)
y_val_thresh_enc = le.transform(y_val_thresh)

for name, model in models_thresh.items():
    if name == 'xgb':
        model.fit(X_train, y_train_thresh_enc)
        y_pred_enc = model.predict(X_val)
        y_pred = le.inverse_transform(y_pred_enc)
    else:
        model.fit(X_train, y_train_thresh)
        y_pred = model.predict(X_val)
        
    acc = accuracy_score(y_val_thresh, y_pred)
    print(f"{name:<10} | {'Thresh':<10} | {'Accuracy':<10} | {acc:.4f}")
    
    if acc > best_thresh_acc:
        best_thresh_acc = acc
        best_thresh_model = model

# Runtime Benchmark
for name, model in models_time.items():
    model.fit(X_train, y_train_time)
    y_pred_log = model.predict(X_val)
    # Clip log predictions to avoid overflow (exp(15) ~ 3e6 seconds, which is plenty)
    y_pred_log = np.clip(y_pred_log, None, 15)
    y_pred = np.exp(y_pred_log)
    mae = mean_absolute_error(y_val_time, y_pred)
    print(f"{name:<10} | {'Runtime':<10} | {'MAE (s)':<10} | {mae:.4f}")
    
    if mae < best_time_mae:
        best_time_mae = mae
        best_time_model = model

print("-" * 50)
print(f"Best Threshold Model: {best_thresh_model.__class__.__name__} (Acc: {best_thresh_acc:.4f})")
print(f"Best Runtime Model:   {best_time_model.__class__.__name__} (MAE: {best_time_mae:.4f})")

# --- Save Best Models ---
print("\nSaving best models...")
joblib.dump(best_thresh_model, MODELS_DIR / 'rf_threshold.joblib') # Keeping filename same for compatibility
joblib.dump(best_time_model, MODELS_DIR / 'rf_runtime.joblib')     # Keeping filename same for compatibility
joblib.dump(feature_cols, MODELS_DIR / 'feature_cols.joblib')
if best_thresh_model.__class__.__name__ == 'XGBClassifier':
    joblib.dump(le, MODELS_DIR / 'label_encoder.joblib')
else:
    # If using RF, we might not need it, but good to clean up if exists
    le_path = MODELS_DIR / 'label_encoder.joblib'
    if le_path.exists():
        le_path.unlink()
print("Done.")

# --- Feature Importance Analysis ---
print("\n--- Feature Importance Analysis ---")
if hasattr(best_thresh_model, 'feature_importances_'):
    print(f"\nTop 10 Features for Threshold Model ({best_thresh_model.__class__.__name__}):")
    importances = best_thresh_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in range(min(10, len(indices))):
        print(f"{feature_cols[indices[i]]:<30} | {importances[indices[i]]:.4f}")

if hasattr(best_time_model, 'feature_importances_'):
    print(f"\nTop 10 Features for Runtime Model ({best_time_model.__class__.__name__}):")
    importances = best_time_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in range(min(10, len(indices))):
        print(f"{feature_cols[indices[i]]:<30} | {importances[indices[i]]:.4f}")
