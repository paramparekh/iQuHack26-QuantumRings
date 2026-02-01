import pandas as pd
import numpy as np

def generate_md():
    df = pd.read_csv('runtime_predictions.csv')
    
    # Calculate Metrics
    mae = np.mean(np.abs(df['true_runtime'] - df['pred_runtime']))
    
    # Accuracy within 60 seconds
    within_60 = np.mean(np.abs(df['true_runtime'] - df['pred_runtime']) < 60.0)
    accuracy_score = within_60 * 100
    
    # Sort by Error
    df['abs_diff'] = abs(df['true_runtime'] - df['pred_runtime'])
    df_sorted = df.sort_values('abs_diff')
    
    best_10 = df_sorted.head(10)
    worst_10 = df_sorted.tail(10)
    
    md = f"""# 📊 Runtime Model Performance Report

## Summary
| Metric | Value | Description |
| :--- | :--- | :--- |
| **Accuracy Score** | **{accuracy_score:.2f}%** | % Predictions with error < 60s |
| **MAE** | **{mae:.2f} s** | Average prediction error in seconds |
| **Total Samples** | {len(df)} | Circuit/Threshold Configurations |

## 🎯 Best Predictions (Top 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in best_10.iterrows():
        md += f"| `{row['filename']}` | {row['input_threshold']} | {row['true_runtime']:.2f} | {row['pred_runtime']:.2f} | {row['abs_diff']:.2f} |\n"

    md += """
## ⚠️ Outliers / Worst Predictions (Bottom 10)
| Circuit | Threshold | True Time (s) | Predicted (s) | Error (s) |
| :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in worst_10.iterrows():
        md += f"| `{row['filename']}` | {row['input_threshold']} | {row['true_runtime']:.2f} | {row['pred_runtime']:.2f} | {row['abs_diff']:.2f} |\n"

    with open('model_report.md', 'w') as f:
        f.write(md)
        
    print("Markdown report generated: model_report.md")

if __name__ == "__main__":
    generate_md()
