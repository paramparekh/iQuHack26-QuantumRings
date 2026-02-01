import pandas as pd

def main():
    try:
        df = pd.read_csv('runtime_predictions.csv')
    except:
        print("Error: runtime_predictions.csv not found.")
        return

    txt_path = 'final_runtime_predictions.txt'
    
    with open(txt_path, 'w') as f:
        f.write("Circuit | Input Threshold | Predicted Runtime (s) | True Runtime (s) | Error (s)\n")
        f.write("-" * 80 + "\n")
        
        for _, row in df.iterrows():
            f.write(f"{row['filename']:<30} | {row['input_threshold']:<5} | {row['pred_runtime']:<20.2f} | {row['true_runtime']:<15.2f} | {abs(row['true_runtime'] - row['pred_runtime']):.2f}\n")
            
    print(f"Exported text list to {txt_path}")

if __name__ == "__main__":
    main()
