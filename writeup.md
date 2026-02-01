# Circuit Fingerprint Challenge - Submission Write-up

## 1. Approach & Strategy
We focused on valid, high-fidelity circuit execution data by strictly filtering out "unused" circuits from the provided dataset. 
*   **Data Cleaning**: We excluded circuits that did not meet the `fidelity >= 0.75` threshold or had missing runtime data.
*   **Validation Strategy**: We employed a **75% / 25%** Train/Test split on unique circuits. This ensures our reported metrics reflect performance on truly unseen circuit structures.
*   **Hardware Awareness**: We treated CPU and GPU runs as distinct datapoints, allowing the model to learn hardware-specific runtime characteristics.

## 2. Feature Engineering
We extracted a comprehensive set of features, with a specific focus on circuit complexity and qubit interaction layouts:
*   **Long-Range Interactions**: `avg_2q_dist` and `max_2q_dist` (Average and Max distance between interacting qubits) were key features, improving prediction accuracy by ~5 seconds.
*   **Cutwidth**: `max_cutwidth` was implemented to capture the "congestion" of the circuit.
*   **Gate Densities**: Standard gate counts (`cx`, `cz`, `t`, `s`) and density metrics.
*   **Structural**: `treewidth`, `depth`, `n_qubits`.

## 3. Modeling
We benchmarked Gradient Boosting, Random Forest, XGBoost, and SVM.
*   **Threshold Prediction**: **Random Forest Classifier**. Achieved **66.67% Accuracy** (Exact Match) on validation set.
*   **Runtime Prediction**: **Random Forest Regressor**. Achieved **~63s MAE** and **84% Accuracy** (predictions within 60s of truth). We designed a chained pipeline where the *predicted threshold* is fed as an input feature to the runtime model, significantly improving runtime estimation.

## 4. Known Limitations
*   The model handles the provided 2-qubit gates well but may generalize less effectively to arbitrary custom gates not seen in training.
*   Runtime prediction varies significantly between CPU and GPU; while our model accounts for this, extreme outliers in cloud queue times (if any) are difficult to predict.
