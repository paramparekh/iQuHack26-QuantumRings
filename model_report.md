# 📊 Runtime Model Performance Report

## Summary
| Metric | Value | Description |
| :--- | :--- | :--- |
| **Accuracy Score** | **75.73%** | % Predictions with error < 60s |
| **MAE** | **69.06 s** | Average prediction error in seconds |
| **Total Samples** | 103 | Circuit/Threshold Configurations |

## 🎯 Best Predictions (Top 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.38 | 0.38 | 0.00 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 16 | 0.43 | 0.44 | 0.01 |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.42 | 0.38 | 0.03 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 16 | 0.34 | 0.44 | 0.11 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 8 | 0.33 | 0.44 | 0.11 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 1 | 0.27 | 0.39 | 0.12 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 2 | 0.26 | 0.39 | 0.13 |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.24 | 0.38 | 0.14 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 8 | 0.28 | 0.44 | 0.16 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 2 | 0.23 | 0.39 | 0.16 |

## ⚠️ Outliers / Worst Predictions (Bottom 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `shor_15_4_indep_qiskit_18.qasm` | 64 | 339.78 | 120.08 | 219.69 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 243.68 | 18.55 | 225.13 |
| `twolocalrandom_indep_qiskit_30.qasm` | 32 | 269.13 | 18.55 | 250.58 |
| `twolocalrandom_indep_qiskit_30.qasm` | 128 | 331.28 | 18.17 | 313.11 |
| `grover-noancilla_indep_qiskit_11.qasm` | 1 | 422.97 | 24.52 | 398.46 |
| `grover-noancilla_indep_qiskit_11.qasm` | 1 | 451.80 | 24.52 | 427.28 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 499.49 | 18.55 | 480.94 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 700.76 | 18.55 | 682.22 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 830.60 | 18.55 | 812.06 |
| `twolocalrandom_indep_qiskit_30.qasm` | 256 | 853.15 | 17.99 | 835.16 |
