# Circuit Fingerprint Challenge - Submission Write-up

## 1. Approach & Strategy
*   **Data Cleaning**: Strictly filtered "unused" circuits to ensure high-fidelity training data.
*   **Validation**: Used a **75% / 25%** Train/Test split on unique circuits to validate generalization to unseen structures.
*   **Hardware**: Distinct modeling for CPU vs. GPU to capture hardware-specific execution characteristics.

## 2. Feature Engineering
We extracted structural and interaction features to proxy circuit complexity and simulation cost (based on the **Interaction Graph** $G=(V, E)$).

### Key Features
*   **`treewidth`**: Size of the largest bag in optimal tree decomposition - 1. Low treewidth ($\sim 1$) implies efficient tensor contraction.
*   **`max_cutwidth`**: Max edges crossing any linear partition. Proxies simulation memory overhead.
    $\text{cutwidth} = \max_i | \{ (u,v) \in E : u \le i < v \} |$
*   **`avg_2q_dist`**: Avg linear distance between interacting qubits. High values signal non-local interactions.
    $D_{avg} = \frac{1}{N_{2q}} \sum_{(u,v) \in \text{gates}} |u - v|$
*   **Densities**: Entangling power per gate ($\rho_{2q}$) and per qubit ($\rho_{ent}$).
    $\rho_{2q} = \frac{N_{2q}}{N_{total}}, \quad \rho_{ent} = \frac{N_{2q}}{N_{qubits}}$

**Impact**: High `treewidth`, `cutwidth`, and `avg_2q_dist` correlate directly with high entanglement entropy, making simulation exponentially harder.

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
