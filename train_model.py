import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error

# --- Configuration ---
DATA_PATH = Path('data/hackathon_public.json')
FEATURES_PATH = Path('data/training_features.json')
MODELS_DIR = Path('models')
MODELS_DIR.mkdir(exist_ok=True)


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
    # Find Min Threshold
    true_threshold = None
    threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
    for run in threshold_sweep:
        fid = run.get('sdk_get_fidelity')
        if fid is not None and fid >= 0.99:
            true_threshold = run['threshold']
            break
    
    # Identify failures
    if true_threshold is None:
        if row['status'] == 'no_threshold_met':
             true_threshold = 256 # Saturate max? Or exclude. Let's saturate for now.
        else:
             return None # Skip broken runs
    
    # Find Runtime
    # We want 'forward.run_wall_s'
    forward_time = row.get('forward', {}).get('run_wall_s')
    if forward_time is None:
        return None # Can't train runtime model without label

    # 2. Features
    if filename not in feature_map:
        return None
    
    feats = feature_map[filename]
    
    # Flatten features from new schema
    # Schema: {"gates": {...}, "num_qubits": N, "depth": D, "gate_count": G, "entanglement_density": ED}
    datum = {}
    datum['filename'] = filename
    datum['n_qubits'] = feats['num_qubits']
    datum['depth'] = feats['depth']
    datum['n_gates'] = feats['gate_count'] # User asked for 'gate count', we'll map to 'n_gates' or keep 'gate_count'
    # Current codebase uses 'n_gates' often, let's map to 'n_gates'.
    datum['entanglement_density'] = feats['entanglement_density']
    
    # Flatten gates
    gates = feats['gates']
    
    # Map 'cx' -> 'n_cx'
    for g_name, count in gates.items():
        datum[f'n_{g_name}'] = count
        
    # Derived features often used
    datum['n_2q'] = gates.get('cx', 0) + gates.get('cz', 0) 
    
    # We already have n_gates from the top level, no need to sum again unless we want to verify.
    # feats['gate_count'] should be accurate.
    
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

# User requested 80/20 split on entire dataset (Train / Validation)
unique_files = df['filename'].unique()
train_files, val_files = train_test_split(unique_files, test_size=0.2, random_state=42)

train_mask = df['filename'].isin(train_files)
val_mask = df['filename'].isin(val_files)

train_df = df[train_mask]
val_df = df[val_mask]

print(f"Train samples: {len(train_df)} (from {len(train_files)} circuits)")
print(f"Validation samples: {len(val_df)} (from {len(val_files)} circuits)")

print(f"Validation samples: {len(val_df)} (from {len(val_files)} circuits)")

# Determine feature columns dynamically based on what we found (plus standard ones)
# We want to exclude targets and filename
exclude_cols = ['filename', 'target_threshold', 'target_runtime', 'backend_cpu', 'precision_single']
potential_features = [c for c in df.columns if c not in exclude_cols]

# User might want specific ordering or specific set.
# Let's ensure our standard structural ones are there
base_features = ['n_qubits', 'n_gates', 'depth', 'n_2q', 'entanglement_density', 'backend_cpu', 'precision_single']
gate_features = [c for c in potential_features if c.startswith('n_') and c not in base_features]
feature_cols = base_features + gate_features

print(f"Features used: {feature_cols}")

# Fill NaNs with 0 (for gates not present in a file but present in others)
df[feature_cols] = df[feature_cols].fillna(0)

target_thresh = 'target_threshold'
target_time = 'target_runtime'

X_train = df.loc[train_mask, feature_cols]
y_train_thresh = df.loc[train_mask, target_thresh]
y_train_time = np.log(df.loc[train_mask, target_time] + 1e-6)

X_val = df.loc[val_mask, feature_cols]
y_val_thresh = df.loc[val_mask, target_thresh]
y_val_time = df.loc[val_mask, target_time]

# --- 3. Model Training ---

# A) Threshold Model (Classifier)
print("Training Threshold Classifier (RandomForest)...")
rf_thresh = RandomForestClassifier(n_estimators=100, random_state=42)
rf_thresh.fit(X_train, y_train_thresh)

# B) Runtime Model (Regressor)
print("Training Runtime Regressor (RandomForest)...")
rf_time = RandomForestRegressor(n_estimators=100, random_state=42)
rf_time.fit(X_train, y_train_time)

# --- 4. Evaluation ---

# A) Training Set Metrics
print("\n--- Training Metrics ---")
y_train_pred_thresh = rf_thresh.predict(X_train)
train_acc = accuracy_score(y_train_thresh, y_train_pred_thresh)
print(f"Training Threshold Accuracy: {train_acc:.4f}")

y_train_pred_log_time = rf_time.predict(X_train)
y_train_pred_time = np.exp(y_train_pred_log_time)
train_mae = mean_absolute_error(np.exp(y_train_time), y_train_pred_time)
print(f"Training Runtime MAE (s):   {train_mae:.4f}")

# B) Validation Set Metrics
print("\n--- Validation Metrics ---")
y_pred_thresh = rf_thresh.predict(X_val)
acc = accuracy_score(y_val_thresh, y_pred_thresh)
print(f"Validation Threshold Accuracy: {acc:.4f}")

# Runtime Eval
y_pred_log_time = rf_time.predict(X_val)
y_pred_time = np.exp(y_pred_log_time)
mae = mean_absolute_error(y_val_time, y_pred_time)
print(f"Validation Runtime MAE (s):   {mae:.4f}")

# Feature Importance
print("\nFeature Importances:")
importances = rf_thresh.feature_importances_
indices = np.argsort(importances)[::-1]
for i in range(min(20, len(indices))):
    print(f"{feature_cols[indices[i]]}: {importances[indices[i]]:.4f}")

# --- 5. Save Models ---
print("Saving models...")
joblib.dump(rf_thresh, MODELS_DIR / 'rf_threshold.joblib')
joblib.dump(rf_time, MODELS_DIR / 'rf_runtime.joblib')
# Also save the feature columns, as we need them for prediction!
joblib.dump(feature_cols, MODELS_DIR / 'feature_cols.joblib')
print("Done.")
