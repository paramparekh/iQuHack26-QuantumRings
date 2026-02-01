# Circuit Fingerprint Challenge - Submission Write-up

## 1. Approach & Strategy

*   **Data Cleaning**: Strictly filtered "unused" circuits to ensure high-fidelity training data.
*   **Validation**: Used a **75% / 25%** Train/Test split on unique circuits to validate generalization to unseen structures.
*   **Hardware**: Distinct modeling for CPU vs. GPU to capture hardware-specific execution characteristics.


## 2. Feature Engineering
We extracted structural and interaction features to proxy circuit complexity and simulation cost (based on the **Interaction Graph** $G=(V, E)$).

### Feature Glossary
We extracted the following features to capture the structural and computational properties of each circuit.

*   **`treewidth`** ($tw(G) = \min \max |b| - 1$): Complexity of interaction tree decomposition.
    **Impact**: Higher treewidth $\implies$ exponentially harder tensor contraction $\implies$ lower threshold.
*   **`max_cutwidth`** ($cw = \max_i |\{(u,v) \in E : u \le i < v\}|$): Max edges crossing a linear partition.
    **Impact**: Higher cutwidth $\implies$ higher memory congestion/bottleneck $\implies$ increased runtime.
*   **`avg_2q_dist`** ($D_{avg} = \frac{1}{N_{2q}} \sum |u-v|$): Average distance of 2-qubit interactions.
    **Impact**: Larger distance $\implies$ faster entanglement spread $\implies$ harder simulation.
*   **`max_2q_dist`**: Maximum distance between interacting qubits.
    **Impact**: Presence of global operations $\implies$ requires full-state updates.
*   **`two_qubit_gate_density`** ($\rho_{2q} = N_{2q} / N_{total}$): Proportion of entangling gates.
    **Impact**: Higher density $\implies$ faster entanglement growth $\implies$ lower threshold.
*   **`entanglement_density`** ($\rho_{ent} = N_{2q} / N_{qubits}$): Entangling operations per qubit.
    **Impact**: Higher intensity $\implies$ more complex state vector.
*   **`clifford_gate_count`**: Count of stabilizer operations (H, S, CX).
    **Impact**: More Clifford gates $\implies$ easier simulation (Gottesman-Knill) $\implies$ higher threshold.
*   **`n_qubits`**: Total physical qubits.
    **Impact**: More qubits $\implies$ larger state space $\implies$ exponential cost (for full state-vector).
*   **`depth`**: Longest path of dependent operations.
    **Impact**: Greater depth $\implies$ more time for entanglement to accumulate.
*   **`n_gates`**: Total gate count.
    **Impact**: Linearly increases simulation time (assuming constant entanglement).

## 3. Modeling
We implemented a two-stage chained pipeline: **Circuit Hardness (Threshold) $\to$ Execution Time**.

### Methodology
We designed a **2-Stage Chained Pipeline** to leverage the causal relationship between a circuit's simulation difficulty ("hardness") and its runtime.

1.  **Stage 1: Hardness Prediction (RF Classifier)**
    *   **Goal**: Predict the "Circuit Hardness" (Threshold). Lower thresholds indicate "harder" circuits that require more resources.

2.  **Stage 2: Runtime Prediction (RF Regressor)**
    *   **Goal**: Predict `log(runtime)`.
    *   **Chained Input**: We feed the *predicted hardness* from Stage 1 as a direct feature into Stage 2. This explicit signal helps the regressor distinguish between "complex but small" vs "simple but large" circuits, improving accuracy by **~5s MAE**.

### Performance (Validation Set)
*   **Threshold Accuracy**: **66.67%** (Exact Match)
*   **Runtime MAE**: **~62s**
*   **Runtime Accuracy**: **84%** (within tolerance)

## 4. Limitations
*   **Basis Gate Generalization**: This model is optimized for the specific basis gates (Clifford+T, etc.) observed in the training set. Performance on circuits utilizing arbitrary unitary blocks or unseen native gate sets is unverified and would likely require retraining.
*   **System Contention**: The model predicts the inherent *execution time* of the circuit on the hardware. It does not account for stochastic delays caused by multi-tenant resource contention, scheduler latency, or queue times on public cloud backends.
