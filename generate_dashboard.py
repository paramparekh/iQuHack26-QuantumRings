import pandas as pd
import numpy as np

def generate_html():
    df = pd.read_csv('runtime_predictions.csv')
    
    # Calculate Metrics
    mae = np.mean(np.abs(df['true_runtime'] - df['pred_runtime']))
    
    # Weighted MAPE (Frequency weighted, handles small numbers better)
    # Sum(AbsError) / Sum(TrueRuntime)
    w_mape = np.sum(np.abs(df['true_runtime'] - df['pred_runtime'])) / np.sum(df['true_runtime'])
    accuracy_score = max(0, 100 * (1 - w_mape))
    
    # Sort by Error
    df['abs_diff'] = abs(df['true_runtime'] - df['pred_runtime'])
    df_sorted = df.sort_values('abs_diff')
    
    best_5 = df_sorted.head(5)
    worst_5 = df_sorted.tail(5)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Runtime Model Performance</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background: #f0f2f5; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            h1 {{ color: #1a1a1a; }}
            .score {{ font-size: 48px; font-weight: bold; color: #2ecc71; }}
            .metric {{ font-size: 18px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; }}
            .bad {{ color: #e74c3c; }}
            .good {{ color: #2ecc71; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Model Performance Report</h1>
            <div>
                <span class="metric">Overall Accuracy Score:</span><br>
                <span class="score">{accuracy_score:.1f}%</span>
            </div>
            <p>
                <b>Mean Absolute Error (MAE):</b> {mae:.2f} seconds<br>
                (On average, our prediction is within {mae:.0f} seconds of the true time)
            </p>
        </div>

        <div class="card">
            <h2>🎯 Best Predictions</h2>
            <table>
                <tr><th>Circuit</th><th>Threshold</th><th>True Time</th><th>Predicted</th><th>Error</th></tr>
                {rows_to_html(best_5)}
            </table>
        </div>

        <div class="card">
            <h2>⚠️ Outliers (Worst Predictions)</h2>
            <table>
                <tr><th>Circuit</th><th>Threshold</th><th>True Time</th><th>Predicted</th><th>Error</th></tr>
                {rows_to_html(worst_5, is_bad=True)}
            </table>
        </div>
    </body>
    </html>
    """
    
    with open('runtime_dashboard.html', 'w') as f:
        f.write(html)
    print("Dashboard generated: runtime_dashboard.html")
    print(f"Accuracy Score: {accuracy_score:.2f}%")

def rows_to_html(df_subset, is_bad=False):
    rows = ""
    color_class = "bad" if is_bad else "good"
    for _, row in df_subset.iterrows():
        rows += f"""
        <tr>
            <td>{row['filename']}</td>
            <td>{row['threshold']}</td>
            <td>{row['true_runtime']:.2f}s</td>
            <td>{row['pred_runtime']:.2f}s</td>
            <td class="{color_class}">{row['abs_diff']:.2f}s</td>
        </tr>
        """
    return rows

if __name__ == "__main__":
    generate_html()
