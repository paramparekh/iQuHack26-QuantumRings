# Circuit Fingerprint Challenge - Submission Write-up

## 1. Approach & Strategy
*   **Data Cleaning**: Strictly filtered "unused" circuits to ensure high-fidelity training data.
*   **Validation**: Used a **75% / 25%** Train/Test split on unique circuits to validate generalization to unseen structures.
*   **Hardware**: Distinct modeling for CPU vs. GPU to capture hardware-specific execution characteristics.

## 2. Feature Engineering
We extracted structural and interaction features to proxy circuit complexity and simulation cost (based on the **Interaction Graph** $G=(V, E)$).

### Feature Glossary
We extracted the following features to capture the structural and computational properties of each circuit.

| Feature | Description & Formula | Relation to Entanglement & Threshold |
| :--- | :--- | :--- |
| **`treewidth`** | Complexity of the interaction graph's tree decomposition. <br> $tw(G) = \min_{\mathcal{T}} \max_{b \in \mathcal{T}} |b| - 1$ | **High Impact**. Low treewidth implies the state vector can be compressed (MPS/Tensor Network). High treewidth $\implies$ high entanglement $\implies$ lower simulation threshold. |
| **`max_cutwidth`** | Max edges crossing any linear partition of qubits. <br> $cw = \max_i |\{(u,v) \in E : u \le i < v\}|$ | **High Impact**. Proxies the memory "bottleneck" during simulation. High cutwidth correlates with higher simulation cost and runtime. |
| **`avg_2q_dist`** | Average distance between qubits in 2-qubit gates. <br> $D_{avg} = \frac{1}{N_{2q}} \sum |u-v|$ | **High Impact**. Long-range interactions spread entanglement rapidly across the system, increasing the difficulty of simulation (higher runtime). |
| **`max_2q_dist`** | Maximum distance between interacting qubits. | **Moderate Impact**. Indicates the presence of at least one global operation, often necessitating full-state updates. |
| **`two_qubit_gate_density`** | Proportion of gates that are 2-qubit (entangling). <br> $\rho_{2q} = N_{2q} / N_{total}$ | **High Impact**. More entangling gates typically allow entanglement to grow faster, reducing the threshold for efficient simulation. |
| **`entanglement_density`** | Entangling gates per qubit. <br> $\rho_{ent} = N_{2q} / N_{qubits}$ | **High Impact**. Measures the "intensity" of entanglement operations relative to system size. |
| **`clifford_gate_count`** | Count of H, S, CX, Z, etc. (Stabilizer operations). | **High Impact**. Clifford circuits are efficiently simulatable (Gottesman-Knill). High proportion $\implies$ easier simulation $\implies$ higher threshold. |
| **`n_qubits`** | Total physical qubits used. | **Base Complexity**. runtime scales exponentially with qubits for full state-vector, but polynomially for some tensor methods (depending on treewidth). |
| **`depth`** | Longest path of dependent operations. | **Moderate Impact**. Deeper circuits allow more time for entanglement to build up and spread. |
| **`n_gates`** | Total gate count. | **Linear Impact**. Runtime generally scales linearly with gate count for a fixed state size, unless entanglement suggests otherwise. |
| **`max_gate_arity`** | Max qubits involved in a single gate (typically 2). | **Sanity Check**. Ensures no unexpected multi-qubit gates are present. |

## 3. Modeling
We implemented a two-stage chained pipeline: **Circuit Hardness (Threshold) $\to$ Execution Time**.

### Methodology
1.  **Threshold (RF Classifier)**: Predicts minimum successful threshold (proxy for difficulty).
2.  **Runtime (RF Regressor)**: Predicts `log(runtime)`.
    *   **Chained Input**: The *predicted threshold* from Stage 1 is an input to Stage 2, improving MAE by ~5s.

### Performance (Validation Set)
*   **Threshold Accuracy**: **66.67%** (Exact Match)
*   **Runtime MAE**: **~63s**
*   **Runtime Accuracy**: **84%** (within tolerance)

## 4. Limitations
*   **Generalization**: Performance on arbitrary custom gates not seen in training is unverified.
*   **Cloud Variance**: Minimum correlation with extreme cloud queue outliers.
