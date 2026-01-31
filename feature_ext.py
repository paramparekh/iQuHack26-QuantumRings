# Circuit Feature Extraction with Graph Analysis
# 
# This script extracts various features from quantum circuits in QASM format:
#
# Features extracted:
# 1. Gate counts: Number of each type of quantum gate (u2, u3, cx, h, etc.)
# 2. Number of qubits: Total qubits used in the circuit
# 3. Circuit depth: Number of time steps needed to execute the circuit sequentially
# 4. Treewidth: Measures how "tree-like" the circuit's connectivity is
#    - Low treewidth (1-2): Circuit connectivity is simple, like a tree
#    - High treewidth: Circuit has complex connectivity, like a dense mesh
#    - Important for: Simulation complexity, optimization potential, hardware mapping
# 5. Max gate arity: Maximum number of qubits a single gate operates on
#    - Low arity (1-2): Simple single and two-qubit gates
#    - High arity: Complex multi-qubit gates, harder to implement on hardware
# 6. Interaction graph: Graph showing which qubits interact with each other
#    - Nodes: Qubits
#    - Edges: Multi-qubit gates connecting qubits
#    - Edge weights: Number of interactions between qubit pairs

import os
import json
import re
from itertools import combinations
from collections import defaultdict
from qiskit import QuantumCircuit
import networkx as nx

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

    # Extract gate counts and build interaction graph
    gates = defaultdict(int)  # Count each gate type
    edges = defaultdict(int)   # Count qubit interactions
    max_index = -1             # Track highest qubit index
    max_gate_arity = 1         # Track maximum number of qubits per gate

    with open(full_path, 'r') as f:
        circuit = f.read()

    # Parse each line of the QASM file
    for line in circuit.splitlines():
        line = line.strip()
        # Skip comments, headers, and declarations
        if not line or line.startswith(skip_prefixes):
            continue

        # Extract gate name (first token before whitespace or '(')
        m = re.match(r'([A-Za-z_]\w*)', line)
        if not m:
            continue
        gate_name = m.group(1)
        gates[gate_name] += 1

        # Find all qubit indices used in this gate
        qubit_matches = qubit_regex.findall(line)
        if not qubit_matches:
            continue
        indices = [int(idx) for (_, idx) in qubit_matches]
        if indices:
            max_index = max(max_index, max(indices))
        
        # Update max gate arity (number of qubits this gate operates on)
        gate_arity = len(indices)
        max_gate_arity = max(max_gate_arity, gate_arity)
        
        # Build interaction graph: count qubit pairs that appear together
        if len(indices) >= 2:
            for a, b in combinations(sorted(indices), 2):
                edges[(a, b)] += 1

    # Determine number of qubits (priority: JSON metadata > filename > max index)
    computed_n_qubits = None
    if circuit_info.get(fname, {}).get('n_qubits') is not None:
        computed_n_qubits = circuit_info[fname]['n_qubits']  # From JSON metadata
    elif qubits is not None:
        computed_n_qubits = qubits  # From filename parsing
    else:
        computed_n_qubits = max_index + 1 if max_index >= 0 else 0  # From circuit content

    # Load QASM circuit and calculate depth using Qiskit
    try:
        qc = QuantumCircuit.from_qasm_file(full_path)
        circuit_depth = qc.depth()  # Number of time steps for sequential execution
    except Exception as e:
        print(f"Error loading {fname}: {e}")
        circuit_depth = None

    # Build interaction graph and calculate treewidth
    nodes = list(range(computed_n_qubits))
    edges_list = [[a, b, w] for (a, b), w in edges.items()]
    
    # Create NetworkX graph for treewidth calculation
    G = nx.Graph()
    G.add_nodes_from(nodes)  # Qubits as nodes
    for a, b, w in edges_list:
        G.add_edge(a, b, weight=w)  # Multi-qubit gates as weighted edges
    
    # Calculate treewidth: measures how "tree-like" the circuit connectivity is
    try:
        # Use minimum degree heuristic for treewidth approximation
        # Lower treewidth = more tree-like, easier to simulate/optimize
        # Higher treewidth = more complex connectivity, harder to simulate
        treewidth_decomp = nx.algorithms.approximation.treewidth_min_degree(G)
        treewidth = treewidth_decomp[0]  # Extract treewidth value
        print(treewidth)  # Debug output
    except Exception as e:
        print(f"Error calculating treewidth for {fname}: {e}")
        treewidth = None
    
    # Clean up NetworkX objects to prevent JSON serialization errors
    G.clear()
    del G

    circuit_data = {
        'gates': dict(gates),
        'family': circuit_info.get(fname, {}).get('family', 'Unknown'),
        'num_qubits': computed_n_qubits,
        'depth': circuit_depth,
        'treewidth': treewidth,
        'max_gate_arity': max_gate_arity,
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