import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error
from feature_extractor import extract_features

# --- Configuration ---
DATA_PATH = Path('data/hackathon_public.json')
CIRCUITS_DIR = Path('circuits')
MODELS_DIR = Path('models')
MODELS_DIR.mkdir(exist_ok=True)


# --- 1. Load and Prepare Data ---
print("Loading data...")
with open(DATA_PATH, 'r') as f:
    data = json.load(f)

print(f"Loaded {len(data['results'])} result rows.")

# Cache for features to avoid re-parsing
feature_cache = {}

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
    if filename not in feature_cache:
        fpath = CIRCUITS_DIR / filename
        feats = extract_features(fpath)
        if feats is None: return None
        feature_cache[filename] = feats
    
    feats = feature_cache[filename]
    
    # Combine
    datum = feats.copy()
    datum['backend_cpu'] = 1 if row['backend'] == 'CPU' else 0
    datum['precision_single'] = 1 if row['precision'] == 'single' else 0
    datum['target_threshold'] = true_threshold
    datum['target_runtime'] = forward_time
    datum['filename'] = filename
    
    return datum

print("Extracting features and targets...")
dataset = []
for row in data['results']:
    d = get_row_data(row)
    if d:
        dataset.append(d)

df = pd.DataFrame(dataset)
print(f"Processed dataframe shape: {df.shape}")

# User requested 80/20 split on entire dataset
unique_files = df['filename'].unique()
train_files, test_files = train_test_split(unique_files, test_size=0.2, random_state=42)

train_mask = df['filename'].isin(train_files)
test_mask = df['filename'].isin(test_files)

train_df = df[train_mask]
test_df = df[test_mask]

print(f"Train samples: {len(train_df)} (from {len(train_files)} circuits)")
print(f"Test samples: {len(test_df)} (from {len(test_files)} circuits)")

feature_cols = ['n_qubits', 'depth', 'n_gates', 'n_cx', 'n_cz', 'n_2q', 'backend_cpu', 'precision_single']
target_thresh = 'target_threshold'
target_time = 'target_runtime' # We will model log(time)

X_train = train_df[feature_cols]
y_train_thresh = train_df[target_thresh]
y_train_time = np.log(train_df[target_time] + 1e-6) # Log transform

X_test = test_df[feature_cols]
y_test_thresh = test_df[target_thresh]
y_test_time = test_df[target_time]

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

# Threshold Eval
y_pred_thresh = rf_thresh.predict(X_test)
acc = accuracy_score(y_test_thresh, y_pred_thresh)
print(f"Threshold Accuracy: {acc:.4f}")

# Runtime Eval
y_pred_log_time = rf_time.predict(X_test)
y_pred_time = np.exp(y_pred_log_time)
mae = mean_absolute_error(y_test_time, y_pred_time)
print(f"Runtime MAE (s): {mae:.4f}")

# Feature Importance
print("\nthreshold Feature Importances:")
for name, imp in zip(feature_cols, rf_thresh.feature_importances_):
    print(f"{name}: {imp:.4f}")

# --- 5. Save Models ---
print("Saving models...")
joblib.dump(rf_thresh, MODELS_DIR / 'rf_threshold.joblib')
joblib.dump(rf_time, MODELS_DIR / 'rf_runtime.joblib')
print("Done.")
