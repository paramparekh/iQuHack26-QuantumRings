import os
import json

circuit_path = "../2026-Quantum-Rings/circuits/"
training_data_path = "../2026-Quantum-Rings/data/hackathon_public.json"
output_path = "circuit_features.json"
circuit_details = {}

# Load training data
with open(training_data_path, 'r') as f:
    training_data = json.load(f)

# Create a mapping from filename to circuit info
circuit_info = {}
for circuit in training_data['circuits']:
    circuit_info[circuit['file']] = {
        'family': circuit['family'],
        'n_qubits': circuit['n_qubits']
    }

# Create a mapping from filename to results (taking the best result per file)
# results_info = {}
# for result in training_data['results']:
#     file = result['file']
#     if file not in results_info or result['selection']['selected_mirror_metric_value'] > results_info[file].get('fidelity', 0):
#         results_info[file] = {
#             'backend': result['backend'],
#             'precision': result['precision'],
#             'status': result['status'],
#             'selected_threshold': result['selection']['selected_threshold'],
#             'fidelity': result['selection']['selected_mirror_metric_value']
#         }

for circuits in os.listdir(circuit_path):
    if not circuits.endswith('.qasm'):
        continue
    full_path = os.path.join(circuit_path, circuits)
    # Extract number of qubits from filename (handle patterns like '130' or 'n30_k6')
    filename_parts = circuits.split('_')
    if len(filename_parts) >= 3 and filename_parts[-2].startswith('n'):
        qubits = int(filename_parts[-2][1:])  # Remove 'n' prefix from the part before last
    elif filename_parts[-1].startswith('k'):
        qubits = int(filename_parts[-1][1:])  # Remove 'k' prefix from last part
    else:
        qubits = int(filename_parts[-1].split('.')[0])
    gates = {}
    with open(full_path, 'r') as f:
        circuit = f.read()
    for line in circuit.split('\n'):
        parts = line.split(' ')
        if len(parts) >= 2 and parts[0] not in ['//', '', 'OPENQASM', 'include', 'qreg', 'creg', 'barrier']:
            gate_name = parts[0].split('(')[0]
            if gate_name not in gates:
                gates[gate_name] = 1
            else:
                gates[gate_name] += 1
    # Combine all information
    circuit_data = {
        'gates': gates,
        'family': circuit_info.get(circuits, {}).get('family', 'Unknown'),
        'num_qubits': circuit_info.get(circuits, {}).get('n_qubits', qubits)
    }
    circuit_details[circuits] = circuit_data

# Save to JSON file
with open(output_path, 'w') as f:
    json.dump(circuit_details, f, indent=2)

print(f"Circuit features saved to {output_path}")
print(f"Processed {len(circuit_details)} circuit files")