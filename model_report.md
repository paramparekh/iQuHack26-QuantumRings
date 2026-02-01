# 📊 Runtime Model Performance Report

## Summary
| Metric | Value | Description |
| :--- | :--- | :--- |
| **Accuracy Score** | **8.64%** | 100% - Weighted Percentage Error |
| **MAE** | **61.98 s** | Average prediction error in seconds |
| **Total Samples** | 103 | Circuit/Threshold Configurations |

## 🎯 Best Predictions (Top 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `wstate_indep_qiskit_30.qasm` | 1 | 0.24 | 0.24 | 0.00 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 4 | 0.25 | 0.24 | 0.01 |
| `qftentangled_indep_qiskit_30.qasm` | 2 | 12.81 | 12.80 | 0.01 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 2 | 0.23 | 0.25 | 0.02 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 1 | 0.22 | 0.20 | 0.03 |
| `wstate_indep_qiskit_30.qasm` | 2 | 0.36 | 0.33 | 0.03 |
| `twolocalrandom_indep_qiskit_30.qasm` | 2 | 0.71 | 0.75 | 0.04 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 2 | 0.26 | 0.22 | 0.04 |
| `wstate_indep_qiskit_30.qasm` | 2 | 0.33 | 0.29 | 0.04 |
| `twolocalrandom_indep_qiskit_30.qasm` | 4 | 0.92 | 0.88 | 0.04 |

## ⚠️ Outliers / Worst Predictions (Bottom 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `shor_15_4_indep_qiskit_18.qasm` | 32 | 60.40 | 256.22 | 195.82 |
| `twolocalrandom_indep_qiskit_30.qasm` | 32 | 269.13 | 69.64 | 199.49 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 243.68 | 42.21 | 201.47 |
| `grover-noancilla_indep_qiskit_11.qasm` | 1 | 422.97 | 153.13 | 269.84 |
| `grover-noancilla_indep_qiskit_11.qasm` | 1 | 451.80 | 172.56 | 279.23 |
| `twolocalrandom_indep_qiskit_30.qasm` | 128 | 331.28 | 38.67 | 292.60 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 499.49 | 68.96 | 430.53 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 700.76 | 9.81 | 690.95 |
| `twolocalrandom_indep_qiskit_30.qasm` | 256 | 853.15 | 64.79 | 788.36 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 830.60 | 16.21 | 814.39 |
