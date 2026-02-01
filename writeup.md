# Circuit Fingerprint Challenge - Submission Write-up

## 1. Approach & Strategy

*   **Data Cleaning**: We focused on valid, high-fidelity circuit execution data by strictly filtering out "unused" circuits from the provided dataset. 
*   **Validation Strategy**: We employed a **75% / 25%** Train/Test split on unique circuits. This ensures our reported metrics reflect performance on truly unseen circuit structures.
*   **Hardware Awareness**: We treated CPU and GPU runs as distinct datapoints, allowing the model to learn hardware-specific runtime characteristics.

## 2. Feature Engineering
We extracted a comprehensive set of features to capture the structural complexity and computational cost of the quantum circuits.

### Structural Features
*   **`treewidth`**: Graph-theoretic measure of how "tree-like" the circuit's interaction graph is. Lower treewidth suggests easier contraction/simulation.
*   **`max_cutwidth`**: Measures the maximum number of hyperedges (gates) crossing any point in a linear ordering of qubits. This proxies the "congestion" or memory overhead required for simulation.
*   **`n_qubits`**: Total number of qubits used.
*   **`depth`**: The longest path of dependent operations in the circuit (calculated via Qiskit).
*   **`n_gates`**: Total number of quantum gates.

### Gate Composition & Density
*   **`two_qubit_gate_density`**: Ratio of 2-qubit gates (e.g., `cx`, `cz`) to total gates. Higher density implies more complex variable interactions.
*   **`entanglement_density`**: Number of 2-qubit gates normalized by the number of qubits.
*   **`clifford_gate_count`**: Count of gates belonging to the Clifford group (e.g., H, S, CX). These are computationally cheaper to simulate (stabilizer formalism).

### Layout & Interaction
*   **`avg_2q_dist`**: Average distance between qubits interacting in 2-qubit gates. Higher distance implies non-local interactions which can be harder for certain hardware topologies or simulator optimizations.
*   **`max_2q_dist`**: The maximum distance between interacting qubits.

## 3. Modeling
We developed a two-stage pipeline to robustly predict runtime, leveraging the strong correlation between circuit "hardness" (valid execution threshold) and execution time.

### Methodology
1.  **Threshold Prediction (Classifier)**: We train a **Random Forest Classifier** (`n_estimators=200`) to predict the minimum successful "threshold" (a proxy for circuit difficulty).
2.  **Runtime Prediction (Regressor)**: We train a **Random Forest Regressor** (`n_estimators=200`) to predict the execution time.
    *   **Chained Input**: The *predicted threshold* from Stage 1 is fed as an input feature into Stage 2. This explicit dependency significantly improves runtime accuracy (MAE reduced by ~5s).
    *   **Log-Space Target**: We predict `log(runtime)` rather than raw runtime to handle the wide dynamic range of execution times and ensure positive predictions.

### Validation
*   We utilized a **75% / 25% Train/Test split** on unique circuit files (not just random rows) to prevent data leakage.
*   **Performance**:
    *   Threshold Accuracy: **66.67%** (Exact Match)
    *   Runtime MAE: **~63s**
    *   Runtime Accuracy (within labeled tolerance): **84%**

## 4. Known Limitations
*   The model handles the provided 2-qubit gates well but may generalize less effectively to arbitrary custom gates not seen in training.
*   Runtime prediction varies significantly between CPU and GPU; while our model accounts for this, extreme outliers in cloud queue times (if any) are difficult to predict.
