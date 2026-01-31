# iQuHACK 2026 Challenge Submission

## Approach
We treated the problem as two separate supervised learning tasks:
1.  **Threshold Prediction**: A classification problem to predict the minimum successful rung (1, 2, 4, ..., 256).
2.  **Runtime Prediction**: A regression problem to predict the wall-clock time for the forward run.

## Features
We used the team's custom feature extractor (`feature_ext.py`) which includes:
-   **Graph Analysis**: Treewidth and Interaction Graph structure.
-   **Gate Properties**: Max Gate Arity.
-   **Basic**: Number of Qubits, Circuit Depth, Gate Counts.
-   **Task Metadata**: `processor` and `precision`.

## Modeling
We used **Random Forest** models (`scikit-learn`):
-   **Classifier**: `RandomForestClassifier` for threshold.
-   **Regressor**: `RandomForestRegressor` for runtime.

## Dependencies
-   `scikit-learn`, `qiskit`, `networkx`, `pandas`, `joblib`.

-   **Public Data Split**: We used an 80/20 train/validation split on the 36 public circuits.
-   **Local Holdout**: We simulated a holdout set using `scripts/prepare_local_test.py` on a subset of the public data to verify the full pipeline.
-   **Local Score**: Our local validation achieved an overall score of **0.5731** (normalized).

## Run Command
```bash
python predict.py --tasks <TASKS_JSON> --circuits <CIRCUITS_DIR> --id-map <ID_MAP> --out predictions.json
```
