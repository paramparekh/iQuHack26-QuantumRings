import os
import json
import re
from itertools import combinations
from collections import defaultdict
from qiskit import QuantumCircuit

circuit_path = "../2026-Quantum-Rings/circuits/"
training_data_path = "../2026-Quantum-Rings/data/hackathon_public.json"
output_path = "circuit_features.json"
circuit_details = {}

# Load training data (if available)
try:
    with open(training_data_path, 'r') as f:
        training_data = json.load(f)
except FileNotFoundError:
    training_data = {'circuits': []}

# Create a mapping from filename to circuit info
circuit_info = {}
for circuit in training_data.get('circuits', []):
    circuit_info[circuit['file']] = {
        'family': circuit.get('family', 'Unknown'),
        'n_qubits': circuit.get('n_qubits')
    }

# regex to find qubit operands like q[0], qreg[12], reg_name[3]
qubit_regex = re.compile(r'([A-Za-z_]\w*)\[(\d+)\]')

skip_prefixes = ('//', 'OPENQASM', 'include', 'qreg', 'creg', 'barrier')

for fname in os.listdir(circuit_path):
    if not fname.endswith('.qasm'):
        continue
    full_path = os.path.join(circuit_path, fname)

    # Attempt to infer qubit count from filename if available
    filename_parts = fname.split('_')
    qubits = None
    if len(filename_parts) >= 3 and filename_parts[-2].startswith('n'):
        try:
            qubits = int(filename_parts[-2][1:])
        except ValueError:
            qubits = None
    elif filename_parts[-1].startswith('k'):
        try:
            qubits = int(filename_parts[-1][1:])
        except ValueError:
            qubits = None
    else:
        try:
            qubits = int(filename_parts[-1].split('.')[0])
        except ValueError:
            qubits = None

    gates = defaultdict(int)
    edges = defaultdict(int)
    max_index = -1

    with open(full_path, 'r') as f:
        circuit = f.read()

    for line in circuit.splitlines():
        line = line.strip()
        if not line or line.startswith(skip_prefixes):
            continue

        # gate name is first token before whitespace or '('
        m = re.match(r'([A-Za-z_]\w*)', line)
        if not m:
            continue
        gate_name = m.group(1)
        gates[gate_name] += 1

        # find all qubit indices used on this line
        qubit_matches = qubit_regex.findall(line)
        if not qubit_matches:
            continue
        indices = [int(idx) for (_, idx) in qubit_matches]
        if indices:
            max_index = max(max_index, max(indices))
        # for interaction graph, count every pair appearing together
        if len(indices) >= 2:
            for a, b in combinations(sorted(indices), 2):
                edges[(a, b)] += 1

    # Determine number of qubits
    computed_n_qubits = None
    if circuit_info.get(fname, {}).get('n_qubits') is not None:
        computed_n_qubits = circuit_info[fname]['n_qubits']
    elif qubits is not None:
        computed_n_qubits = qubits
    else:
        computed_n_qubits = max_index + 1 if max_index >= 0 else 0

    # Load QASM circuit and calculate depth
    try:
        qc = QuantumCircuit.from_qasm_file(full_path)
        circuit_depth = qc.depth()
    except Exception as e:
        print(f"Error loading {fname}: {e}")
        circuit_depth = None

    # Build interaction graph structure
    nodes = list(range(computed_n_qubits))
    edges_list = [[a, b, w] for (a, b), w in edges.items()]

    circuit_data = {
        'gates': dict(gates),
        'family': circuit_info.get(fname, {}).get('family', 'Unknown'),
        'num_qubits': computed_n_qubits,
        'depth': circuit_depth,
        'interaction_graph': {
            'nodes': nodes,
            'edges': edges_list  # each edge: [qubit_a, qubit_b, weight]
        }
    }
    circuit_details[fname] = circuit_data

# Save to JSON file
with open(output_path, 'w') as f:
    json.dump(circuit_details, f, indent=2)

print(f"Circuit features (with interaction graphs) saved to {output_path}")
print(f"Processed {len(circuit_details)} circuit files")