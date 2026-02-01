# 📊 Runtime Model Performance Report

## Summary
| Metric | Value | Description |
| :--- | :--- | :--- |
| **Accuracy Score** | **77.48%** | % Predictions with error < 60s |
| **MAE** | **62.80 s** | Average prediction error in seconds |
| **Total Samples** | 111 | Circuit/Threshold Configurations |

## 🎯 Best Predictions (Top 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.38 | 0.36 | 0.02 |
| `ghz_indep_qiskit_15.qasm` | 1 | 0.24 | 0.27 | 0.03 |
| `ghz_indep_qiskit_15.qasm` | 2 | 0.25 | 0.28 | 0.03 |
| `ghz_indep_qiskit_15.qasm` | 2 | 0.25 | 0.28 | 0.03 |
| `ghz_indep_qiskit_15.qasm` | 1 | 0.23 | 0.27 | 0.04 |
| `ghz_indep_qiskit_15.qasm` | 1 | 0.22 | 0.27 | 0.04 |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.42 | 0.36 | 0.06 |
| `ghz_indep_qiskit_15.qasm` | 2 | 0.23 | 0.28 | 0.06 |
| `ghz_indep_qiskit_15.qasm` | 2 | 0.22 | 0.28 | 0.07 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 16 | 0.43 | 0.52 | 0.09 |

## ⚠️ Outliers / Worst Predictions (Bottom 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 243.68 | 15.07 | 228.61 |
| `shor_15_4_indep_qiskit_18.qasm` | 64 | 339.78 | 93.76 | 246.01 |
| `twolocalrandom_indep_qiskit_30.qasm` | 32 | 269.13 | 15.07 | 254.06 |
| `twolocalrandom_indep_qiskit_30.qasm` | 128 | 331.28 | 15.23 | 316.04 |
| `grover-noancilla_indep_qiskit_11.qasm` | 1 | 422.97 | 28.19 | 394.78 |
| `grover-noancilla_indep_qiskit_11.qasm` | 1 | 451.80 | 28.19 | 423.60 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 499.49 | 15.07 | 484.42 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 700.76 | 15.07 | 685.69 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 830.60 | 15.07 | 815.54 |
| `twolocalrandom_indep_qiskit_30.qasm` | 256 | 853.15 | 15.23 | 837.92 |
