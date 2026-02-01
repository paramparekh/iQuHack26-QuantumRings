import json
from pathlib import Path

DATA_PATH = Path('data/hackathon_public.json')
# Recommended test split from docs/CIRCUITS.md
TEST_FILES = [
    "ae_indep_qiskit_130.qasm", "dj_indep_qiskit_30.qasm", "ghz_indep_qiskit_30.qasm", "ghz_indep_qiskit_130.qasm",
    "grover-noancilla_indep_qiskit_11.qasm", "grover-v-chain_indep_qiskit_17.qasm", "portfolioqaoa_indep_qiskit_17.qasm",
    "portfoliovqe_indep_qiskit_18.qasm", "qft_indep_qiskit_15.qasm", "qftentangled_indep_qiskit_30.qasm",
    "qpeexact_indep_qiskit_30.qasm", "wstate_indep_qiskit_130.qasm"
]

with open(DATA_PATH, 'r') as f:
    data = json.load(f)

test_tasks = []
id_map_entries = []

counter = 1
for row in data['results']:
    if row['file'] in TEST_FILES:
        t_id = f"VAL_{counter:03d}"
        
        task = {
            "id": t_id,
            "processor": row['backend'],
            "precision": row['precision']
        }
        test_tasks.append(task)
        
        entry = {
            "id": t_id,
            "qasm_file": row['file']
        }
        id_map_entries.append(entry)
        counter += 1

# Output as "holdout" structure
out_tasks = {'tasks': test_tasks}
with open('local_test_tasks.json', 'w') as f:
    json.dump(out_tasks, f, indent=2)

out_map = {'entries': id_map_entries}
with open('local_test_id_map.json', 'w') as f:
    json.dump(out_map, f, indent=2)

print(f"Prepared {len(test_tasks)} verification tasks keys.")
