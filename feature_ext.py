import os

data_path = "../2026-Quantum-Rings/circuits/"
# circuit_1 = os.path.join(data_path, "ae_indep_qiskit_130.qasm")

circuit_details = {}
gates = {}

for circuits in os.listdir(data_path):
    if not circuits.endswith('.qasm'):
        continue
    full_path = os.path.join(data_path, circuits)
    with open(full_path, 'r') as f:
        circuit = f.read()
    for line in circuit.split('\n'):
        parts = line.split(' ')
        if len(parts) >= 2 and parts[0] not in ['//', '', 'OPENQASM', 'include', 'qreg', 'creg', 'barrier']:
            gate_name = parts[0].split('(')[0]  # Get only the gate name without parameters
            if gate_name not in gates:
                gates[gate_name] = 1
            else:
                gates[gate_name] += 1
    circuit_details[circuits] = gates

print(circuit_details)