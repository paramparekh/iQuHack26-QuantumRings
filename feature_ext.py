import os
import json
import re
from itertools import combinations
from collections import defaultdict
from qiskit import QuantumCircuit
import networkx as nx
from pathlib import Path

# Config
DEFAULT_OUTPUT_PATH = "circuit_features.json"

def extract_features(qasm_path, circuit_info=None):
    """
    Extracts features from a single QASM file.
    """
    path = Path(qasm_path)
    if not path.exists():
        return None

    # regex to find qubit operands like q[0], qreg[12], reg_name[3]
    qubit_regex = re.compile(r'([A-Za-z_]\w*)\[(\d+)\]')
    skip_prefixes = ('//', 'OPENQASM', 'include', 'qreg', 'creg', 'barrier')

    fname = path.name
    
    # Attempt to infer qubit count from filename
    filename_parts = fname.split('_')
    qubits = None
    if len(filename_parts) >= 3 and filename_parts[-2].startswith('n'):
        try:
           qubits = int(filename_parts[-2][1:])
        except ValueError:
           pass
    elif len(filename_parts) > 0 and filename_parts[-1].startswith('k'): 
         try:
            qubits = int(filename_parts[-1][1:])
         except ValueError:
            pass
    
    gates = defaultdict(int)
    edges = defaultdict(int)
    max_index = -1
    max_gate_arity = 1 

    try:
        with open(path, 'r') as f:
            content = f.read()

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(skip_prefixes):
                continue

            m = re.match(r'([A-Za-z_]\w*)', line)
            if not m:
                continue
            gate_name = m.group(1)
            gates[gate_name] += 1

            qubit_matches = qubit_regex.findall(line)
            indices = [int(idx) for (_, idx) in qubit_matches]
            
            if indices:
                max_index = max(max_index, max(indices))
            
            gate_arity = len(indices)
            if gate_arity > 0:
                 max_gate_arity = max(max_gate_arity, gate_arity)
            
            if len(indices) >= 2:
                for a, b in combinations(sorted(indices), 2):
                    edges[(a, b)] += 1
        
        # Determine n_qubits
        computed_n_qubits = None
        if circuit_info and circuit_info.get('n_qubits'):
            computed_n_qubits = circuit_info['n_qubits']
        elif qubits is not None:
             computed_n_qubits = qubits
        else:
             computed_n_qubits = max_index + 1 if max_index >= 0 else 0

        # Load Qiskit for depth
        try:
            qc = QuantumCircuit.from_qasm_file(str(path))
            circuit_depth = qc.depth()
        except Exception:
            # print(f"Error loading {fname} with Qiskit: {e}")
            circuit_depth = 0 

        # Treewidth
        nodes = list(range(computed_n_qubits)) if computed_n_qubits > 0 else []
        edges_list = [[a, b, w] for (a, b), w in edges.items()]
        
        treewidth = 1 
        if nodes:
            G = nx.Graph()
            G.add_nodes_from(nodes)
            for a, b, w in edges_list:
                G.add_edge(a, b, weight=w)
            
            try:
                treewidth_decomp = nx.algorithms.approximation.treewidth_min_degree(G)
                treewidth = treewidth_decomp[0]
            except Exception:
                treewidth = 1
            G.clear()

        # Gate Count
        n_gates = sum(gates.values())
        
        # New Feature Logic Integration
        # Calculate two-qubit gate density
        total_gates = n_gates
        two_qubit_gates = sum(count for gate, count in gates.items() 
                            if any(gate.startswith(prefix) for prefix in ['cx', 'cz', 'ch', 'swap', 'cp', 'cu1', 'cu2', 'cu3', 'rxx', 'ryy', 'rzz', 'rzx']))
        
        two_qubit_density = two_qubit_gates / total_gates if total_gates > 0 else 0.0

        # Count specific important gates
        t_gate_count = gates.get('t', 0) + gates.get('tdg', 0)  # T and T-dagger gates
        s_gate_count = gates.get('s', 0) + gates.get('sdg', 0)  # S and S-dagger gates
        
        # Count Clifford gates
        clifford_gates = ['h', 'x', 'y', 'z', 's', 'sdg', 'cx', 'cz', 'swap', 'ch', 'cy', 'cz']
        clifford_gate_count = sum(gates.get(gate, 0) for gate in clifford_gates)

        return {
            'filename': fname,
            'gates': dict(gates),
            'num_qubits': computed_n_qubits,
            'depth': circuit_depth,
            'gate_count': n_gates,
            'treewidth': treewidth,
            'max_gate_arity': max_gate_arity,
            'two_qubit_gate_density': two_qubit_density,
            't_gate_count': t_gate_count,
            's_gate_count': s_gate_count,
            'clifford_gate_count': clifford_gate_count
        }

    except Exception as e:
        print(f"Error processing {fname}: {e}")
        return None

def main():
    # Paths relative to this script
    script_dir = Path(__file__).parent
    circuit_path = script_dir / "circuits"
    data_path = script_dir / "data/hackathon_public.json"
    output_path = script_dir / "circuit_features.json" 
    
    print(f"Reading circuits from {circuit_path}...")
    
    # Load metadata
    circuit_info = {}
    if data_path.exists():
        with open(data_path, 'r') as f:
            d = json.load(f)
            for row in d.get('results', []):
                circuit_info[row['file']] = {
                    'n_qubits': None 
                }
    
    features_map = {}
    if circuit_path.exists():
        for fname in os.listdir(circuit_path):
            if fname.endswith('.qasm'):
                fpath = circuit_path / fname
                feats = extract_features(fpath, circuit_info.get(fname))
                if feats:
                    features_map[fname] = feats
    
    print(f"Saving {len(features_map)} feature sets to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(features_map, f, indent=2)

if __name__ == "__main__":
    main()