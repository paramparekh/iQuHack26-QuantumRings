# 📊 Runtime Model Performance Report

## Summary
| Metric | Value | Description |
| :--- | :--- | :--- |
| **Accuracy Score** | **77.71%** | % Predictions with error < 60s |
| **MAE** | **102.65 s** | Average prediction error in seconds |
| **Total Samples** | 166 | Circuit/Threshold Configurations |

## 🎯 Best Predictions (Top 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.38 | 0.38 | 0.01 |
| `portfolioqaoa_indep_qiskit_10.qasm` | 16 | 0.43 | 0.45 | 0.02 |
| `qaoa_indep_qiskit_16.qasm` | 1 | 0.42 | 0.38 | 0.04 |
| `ghz_indep_qiskit_30.qasm` | 2 | 0.32 | 0.36 | 0.04 |
| `ghz_indep_qiskit_30.qasm` | 2 | 0.32 | 0.36 | 0.04 |
| `ghz_indep_qiskit_30.qasm` | 1 | 0.26 | 0.34 | 0.08 |
| `wstate_indep_qiskit_15.qasm` | 2 | 0.29 | 0.38 | 0.09 |
| `wstate_indep_qiskit_30.qasm` | 2 | 0.46 | 0.55 | 0.09 |
| `ghz_indep_qiskit_15.qasm` | 1 | 0.24 | 0.33 | 0.09 |
| `wstate_indep_qiskit_15.qasm` | 1 | 0.25 | 0.35 | 0.10 |

## ⚠️ Outliers / Worst Predictions (Bottom 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
| `ae_indep_qiskit_130.qasm` | 2 | 759.61 | 80.99 | 678.62 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 700.76 | 18.34 | 682.43 |
| `ae_indep_qiskit_130.qasm` | 256 | 880.65 | 95.10 | 785.56 |
| `ae_indep_qiskit_130.qasm` | 128 | 882.68 | 95.10 | 787.59 |
| `ae_indep_qiskit_130.qasm` | 512 | 896.06 | 95.10 | 800.96 |
| `ae_indep_qiskit_130.qasm` | 2 | 889.72 | 80.99 | 808.73 |
| `twolocalrandom_indep_qiskit_30.qasm` | 64 | 830.60 | 18.34 | 812.27 |
| `twolocalrandom_indep_qiskit_30.qasm` | 256 | 853.15 | 18.34 | 834.81 |
| `ae_indep_qiskit_130.qasm` | 32 | 1948.52 | 95.10 | 1853.42 |
| `ae_indep_qiskit_130.qasm` | 32 | 2511.10 | 95.10 | 2416.00 |
