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
        n_gates = sum(ops.values())
        n_cx = ops.get('cx', 0)
        n_cz = ops.get('cz', 0)
        n_measure = ops.get('measure', 0)
        n_2q = n_cx + n_cz  # Approximate mostly CX/CZ
        n_1q = n_gates - n_2q - n_measure
        
        # 4. Advanced Structure (Interaction Graph Width rough proxy)
        # We can look at the number of active qubits in 2Q gates
        # Or just use the density of 2Q gates
        entanglement_density = n_2q / n_qubits if n_qubits > 0 else 0
        
        # 5. Regex / Raw Text Fallbacks (if needed or for speed)
        # (Already handled well by Qiskit generally, but let's stick to Qiskit for robust stats)

        features = {
            "n_qubits": n_qubits,
            "depth": depth,
            "n_gates": n_gates,
            "n_cx": n_cx,
            "n_cz": n_cz,
            "n_2q": n_2q,
            "n_1q": n_1q,
            "n_measure": n_measure,
            "entanglement_density": entanglement_density,
            "avg_gates_per_qubit": n_gates / n_qubits if n_qubits > 0 else 0
        }
        
        return features

    except Exception as e:
        print(f"Error processing {qasm_path}: {e}")
        # Fallback to regex if Qiskit fails (e.g., custom gates not defined)
        return extract_features_regex(path)

def extract_features_regex(path):
    """Fallback feature extraction using Regex."""
    text = path.read_text(encoding='utf-8')
    n_lines = len(text.splitlines())
    n_cx = len(re.findall(r'\bcx\b', text))
    n_cz = len(re.findall(r'\bcz\b', text))
    n_measure = len(re.findall(r'\bmeasure\b', text))
    # Approximation
    return {
        "n_qubits": 0, # Hard to parse reliably without parser
        "depth": 0,
        "n_gates": n_lines, # Very rough
        "n_cx": n_cx,
        "n_cz": n_cz,
        "n_2q": n_cx + n_cz,
        "n_1q": 0,
        "n_measure": n_measure,
        "entanglement_density": 0,
        "avg_gates_per_qubit": 0
    }

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
