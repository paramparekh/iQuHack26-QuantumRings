import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
import joblib
from feature_extractor import extract_features

# --- Load Data & Config ---

DATA_PATH = Path('data/hackathon_public.json')
MODELS_DIR = Path('models')
CIRCUITS_DIR = Path('circuits')

# --- Split Logic removed from here (moved after prepare_dataframe) ---

# --- Helper: Load Models ---
rf_thresh = joblib.load(MODELS_DIR / 'rf_threshold.joblib')
rf_time = joblib.load(MODELS_DIR / 'rf_runtime.joblib')
feature_cols = ['n_qubits', 'depth', 'n_gates', 'n_cx', 'n_cz', 'n_2q', 'backend_cpu', 'precision_single']

# --- Helper: Extract Data ---
def prepare_dataframe():
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)

    dataset = []
    cache = {}

    for row in data['results']:
        filename = row['file']
        
        # Determine targets
        true_thresh = None
        for run in sorted(row['threshold_sweep'], key=lambda x: x['threshold']):
            fid = run.get('sdk_get_fidelity')
            if fid is not None and fid >= 0.99:
                true_thresh = run['threshold']
                break
        if true_thresh is None: continue # Skip if no threshold met (can't grade)

        true_time = row.get('forward', {}).get('run_wall_s')
        if true_time is None: continue

        # Features
        if filename not in cache:
            cache[filename] = extract_features(CIRCUITS_DIR / filename)
        if cache[filename] is None: continue

        datum = cache[filename].copy()
        datum['filename'] = filename
        datum['backend_cpu'] = 1 if row['backend'] == 'CPU' else 0
        datum['precision_single'] = 1 if row['precision'] == 'single' else 0
        datum['target_threshold'] = true_thresh
        datum['target_runtime'] = true_time
        dataset.append(datum)
    
    return pd.DataFrame(dataset)

# --- Scoring Logic (Approximate Challenge Grader) ---
def compute_challenge_score(y_true_thresh, y_pred_thresh, y_true_time, y_pred_time):
    """
    Computes a score resembling the official challenge logic.
    Note: Exact weights aren't public, but we know:
    1. Threshold < True => Score 0
    2. Threshold > True => Penalty
    3. Runtime Error => Penalty
    """
    scores = []
    
    for tt, pt, tr, pr in zip(y_true_thresh, y_pred_thresh, y_true_time, y_pred_time):
        # 1. Fidelity Constraint
        if pt < tt:
            scores.append(0.0)
            continue
            
        # 2. Threshold Penalty (e.g., exponentially decaying score as we go higher?)
        # Or simply, we assume perfect score = 1.0, and subtract.
        # Let's define a simple custom metric:
        # Base = 100
        # If PT > TT: Penalty proportional to steps (log2 difference)
        steps_diff = np.log2(pt) - np.log2(tt)
        thresh_score = max(0, 100 - (steps_diff * 10)) # Penalize 10 points per rung overshoot
        
        # 3. Runtime Accuracy
        # Symmetric log error seems best
        log_diff = abs(np.log(tr) - np.log(pr))
        # Perfect = 1.0. Error 1.0 (e.g. e^1 factor off) => 0.5?
        time_score = 100 * np.exp(-log_diff)
        
        # Combined
        final = 0.75 * thresh_score + 0.25 * time_score
        scores.append(final)
        
    return np.mean(scores)

# --- Execution ---
print("Preparing Data...")
df = pd.DataFrame()
try:
    df = prepare_dataframe()
except Exception as e:
    print(e)
    exit(1)

# --- Split Logic (Match Training) ---
print("Applying 80/20 Random Split (Seed 42)...")
unique_files = df['filename'].unique()
from sklearn.model_selection import train_test_split
train_files, test_files = train_test_split(unique_files, test_size=0.2, random_state=42)

train_df = df[df['filename'].isin(train_files)]
test_df = df[df['filename'].isin(test_files)]

print(f"Dataset Sizes -> Train: {len(train_df)}, Test: {len(test_df)}")

for name, dataset in [("TRAIN", train_df), ("TEST", test_df)]:
    if len(dataset) == 0: continue
    
    X = dataset[feature_cols]
    y_true_thresh = dataset['target_threshold']
    y_true_time = dataset['target_runtime']
    
    # Predict
    pred_thresh = rf_thresh.predict(X)
    pred_log_time = rf_time.predict(X)
    pred_time = np.exp(pred_log_time)
    
    # Metrics
    acc = accuracy_score(y_true_thresh, pred_thresh)
    mae = mean_absolute_error(y_true_time, pred_time)
    grade = compute_challenge_score(y_true_thresh, pred_thresh, y_true_time, pred_time)
    
    print(f"\n--- {name} METRICS ---")
    print(f"Accuracy (Threshold): {acc:.2%}")
    print(f"MAE (Runtime): {mae:.2f} s")
    print(f"Estimated Grade (0-100): {grade:.2f}")
