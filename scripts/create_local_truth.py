import json
from pathlib import Path

# Configuration
DATA_PATH = Path('data/hackathon_public.json')
LOCAL_TEST_TASKS_PATH = Path('local_test_tasks.json')
OUTPUT_TRUTH_PATH = Path('local_test_truth.json')

def main():
    print(f"Loading data from {DATA_PATH}...")
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)

    print(f"Loading local test tasks from {LOCAL_TEST_TASKS_PATH}...")
    with open(LOCAL_TEST_TASKS_PATH, 'r') as f:
        tasks_data = json.load(f)
        tasks = tasks_data['tasks']

    # Map filename -> result row for faster lookup
    file_to_row = {row['file']: row for row in data['results']}

    truth_entries = []
    
    print("Extracting truth values...")
    for task in tasks:
        task_id = task['id']
        # We need to look up which file corresponds to this task.
        # But wait, local_test_tasks.json doesn't have the filename directly in the 'task' object
        # typically, but prepare_local_test.py might have constructed it.
        # Let's check how prepare_local_test.py makes the ID map.
        # It creates 'local_test_id_map.json'. We should probably load that too 
        # to be robust, OR we can rely on the fact that we ran prepare_local_test.py
        # and we know the mapping logic.
        
        # However, to be safe and clean, let's load the ID map.
        pass

    # Re-loading ID map
    ID_MAP_PATH = Path('local_test_id_map.json')
    with open(ID_MAP_PATH, 'r') as f:
        id_map = json.load(f)
    
    id_to_file = {entry['id']: entry['qasm_file'] for entry in id_map['entries']}

    for task in tasks:
        task_id = task['id']
        filename = id_to_file.get(task_id)
        
        if not filename:
            print(f"Warning: No file found for task {task_id}")
            continue
            
        row = file_to_row.get(filename)
        if not row:
            print(f"Warning: No data found for file {filename}")
            continue

        # Extract Truths
        # 1. Min Threshold
        true_threshold = None
        # Sort by threshold to find the *min* that passes
        threshold_sweep = sorted(row['threshold_sweep'], key=lambda x: x['threshold'])
        for run in threshold_sweep:
            fid = run.get('sdk_get_fidelity')
            if fid is not None and fid >= 0.99:
                true_threshold = run['threshold']
                break
        
        if true_threshold is None:
            # Fallback if no threshold met fidelity
            # In training we saturated to 256. Let's consistency usage.
            true_threshold = 256
            
        # 2. Runtime
        forward_time = row.get('forward', {}).get('run_wall_s')
        if forward_time is None:
             # If missing in data, we can't score it properly. 
             # But for Hackathon public data, it should be there.
             forward_time = 0.0

        truth_entries.append({
            "id": task_id,
            "true_threshold_min": true_threshold,
            "true_forward_wall_s": forward_time
        })

    # Output Format matches holdout_truth.json expected by scorer
    truth_output = {
        "labels": truth_entries
    }
    
    print(f"Saving {len(truth_entries)} truth entries to {OUTPUT_TRUTH_PATH}...")
    with open(OUTPUT_TRUTH_PATH, 'w') as f:
        json.dump(truth_output, f, indent=2)

if __name__ == "__main__":
    main()
