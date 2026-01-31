import re
from pathlib import Path
from qiskit import QuantumCircuit
import sys
import numpy as np

def extract_features(qasm_path):
    """
    Extracts features from a QASM file.
    """
    path = Path(qasm_path)
    if not path.exists():
        print(f"Warning: {path} does not exist.")
        return None

    try:
        # 1. Load Circuit using Qiskit
        qc = QuantumCircuit.from_qasm_file(str(path))
        
        # 2. Basic Stats
        n_qubits = qc.num_qubits
        depth = qc.depth()
        
        # 3. Gate Counts
        ops = qc.count_ops()
        
        # Filter unwanted gates if they exist (rx, ry, rz)
        # User requested to NOT include them.
        gates = dict(ops)
        for g in ['rx', 'ry', 'rz', 'barrier']:
            if g in gates:
                del gates[g]

        n_gates = sum(ops.values())
        
        # Calculate entanglement density (keep as requested)
        n_cx = ops.get('cx', 0)
        n_cz = ops.get('cz', 0)
        n_2q = n_cx + n_cz
        entanglement_density = n_2q / n_qubits if n_qubits > 0 else 0
        
        features = {
            "gates": gates,
            "num_qubits": n_qubits,
            "depth": depth,
            "gate_count": n_gates,
            "entanglement_density": entanglement_density
        }
        
        return features

    except Exception as e:
        print(f"Error processing {qasm_path}: {e}")
        return None


def extract_features_regex(path):
    print(f"Regex fallback not supported for schema requirements.")
    return None

if __name__ == "__main__":
    # Test on a file
    import sys
    if len(sys.argv) > 1:
        f = sys.argv[1]
        print(extract_features(f))
    else:
        # Default test
        test_file = Path("circuits/ae_indep_qiskit_20.qasm")
        if test_file.exists():
            print(f"Testing on {test_file}")
            print(extract_features(test_file))
