# iQuHACK 2026 Challenge Submission

## Approach
We treated the problem as two separate supervised learning tasks:
1.  **Threshold Prediction**: A classification problem to predict the minimum successful rung (1, 2, 4, ..., 256).
2.  **Runtime Prediction**: A regression problem to predict the wall-clock time for the forward run.

## Features
We extracted structural features from the QASM files using `qiskit`:
-   **Basic**: Number of Qubits, Circuit Depth, Gate Count.
-   **Gate Composition**: Counts of specific gates (e.g., `h`, `cx`, `u3`).
-   **Connectivity**: Entanglement Density (ratio of 2-qubit gates to qubits).
-   **Task Metadata**: `processor` (CPU/GPU) and `precision` (single/double) were encoded as binary features.

## Modeling
We used **Random Forest** models from `scikit-learn`:
-   **Classifier**: `RandomForestClassifier` for the threshold.
-   **Regressor**: `RandomForestRegressor` for the runtime (predicting log-transformed time to handle scale differences).

## Validation
-   **Public Data Split**: We used an 80/20 train/validation split on the 36 public circuits.
-   **Local Holdout**: We simulated a holdout set using `scripts/prepare_local_test.py` on a subset of the public data to verify the full pipeline.
-   **Local Score**: Our local validation achieved an overall score of **0.5731** (normalized).

## Run Command
```bash
python predict.py --tasks <TASKS_JSON> --circuits <CIRCUITS_DIR> --id-map <ID_MAP> --out predictions.json
```
