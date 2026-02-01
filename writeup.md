# Circuit Fingerprint Challenge - Submission Write-up

## 1. Approach & Strategy

*   **Data Cleaning**: We focused on valid, high-fidelity circuit execution data by strictly filtering out "unused" circuits from the provided dataset. 
*   **Validation Strategy**: We employed a **75% / 25%** Train/Test split on unique circuits. This ensures our reported metrics reflect performance on truly unseen circuit structures.
*   **Hardware Awareness**: We treated CPU and GPU runs as distinct datapoints, allowing the model to learn hardware-specific runtime characteristics.

## 2. Feature Engineering
We extracted a comprehensive set of features to capture the structural complexity and computational cost of the quantum circuits. The foundation of our structural analysis is the **Interaction Graph** $G=(V, E)$, where nodes $V$ represent qubits and edges $E$ represent two-qubit gates (e.g., CX, CZ).

### Structural Features & Formulas
*   **`treewidth`**: A measure of how close the interaction graph is to a tree. Formally, it is the size of the largest bag in an optimal tree decomposition of $G$ minus 1. Low treewidth ($\sim 1$) implies efficient simulation via tensor network contraction.
*   **`max_cutwidth`**: The maximum number of edges crossing any cut in the linear arrangement of qubits.
    $\text{cutwidth} = \max_i | \{ (u,v) \in E : u \le i < v \} |$
    High cutwidth indicates high "congestion" and memory requirements for state-vector simulation.
*   **`n_qubits`** ($N_{nodes}$): Total physical qubits.
*   **`depth`**: Longest path of dependent operations in the circuit (calculated via Qiskit).

### Gate Composition & Density
*   **`two_qubit_gate_density`**: Fraction of gates that entangle qubits.
    $\rho_{2q} = \frac{N_{2q}}{N_{total}}$
*   **`entanglement_density`**: Entangling power per qubit.
    $\rho_{ent} = \frac{N_{2q}}{N_{qubits}}$
*   **`clifford_gate_count`**: Count of efficient Clifford gates (H, S, CX).
*   **`t_gate_count` & `s_gate_count`**: Counts of non-Clifford gates (specifically T/Tdag) which are traditionally expensive to simulate.

### Layout & Interaction
*   **`avg_2q_dist`**: Average linear distance between interacting qubits.
    $D_{avg} = \frac{1}{N_{2q}} \sum_{(u,v) \in \text{gates}} |u - v|$
    Higher values imply non-local interactions, which generally increase entanglement spread.

### Impact on Entanglement
Features like **treewidth**, **cutwidth**, and **avg_2q_dist** are direct proxies for **entanglement entropy**. A circuit with high treewidth or long-range interactions can rapidly generate high-entanglement states that are exponentially hard to simulate (requiring larger bond dimensions in tensor networks), whereas local, low-width circuits remain computationally tractable.

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
