# 🎤 Presentation & Live Demo Guide

## 1. 🚨 Live Demo Instructions (CRITICAL)

**When:** At the start of your presentation (or via DM just before), the judges will give you a **Holdout Bundle**.

**What to do:**
1.  **Download** their holdout bundle (e.g., `holdout.zip`).
2.  **Unzip** it. It will likely contain:
    *   A JSON file (Tasks List).
    *   A Folder of QASM circuits.
3.  **Run Your Code**.
    *   Open your terminal.
    *   Run the command below (replacing `<PATH_KEYS>` with what they not gave you).

### The Command to Run
```bash
python predict.py --tasks <PATH_TO_THEIR_TASKS.json> --circuits <PATH_TO_THEIR_QASM_FOLDER> --id-map <PATH_TO_THEIR_ID_MAP.json> --out predictions.json
```

*   **Note**: If they don't give an ID Map (the docs say they might provide it "at scoring time"), check if the `tasks.json` has filenames directly. `predict.py` handles both cases automatically.

4.  **Submit Results**:
    *   Upload the generated `predictions.json` to the link they provide.

---

## 2. 🗣️ The "Story" (Script Points)

**Slide 1: The Problem**
*   "We trained an AI to predict Quantum Compression (Threshold) and Runtime without running the circuit."
*   "Why? To save expensive quantum computer time."

**Slide 2: The Data Strategy**
*   "We treated the AI like a student taking an exam."
*   "We split our data: **75% Study Guide** (Training) vs **25% Practice Exam** (Validation)."
*   "We strictly removed 'broken' data to ensure high quality."

**Slide 3: The Secret Sauce (Features)**
*   "Standard features (Gate Counts) weren't enough."
*   "We added **Interaction Distance**: Measuring how far qubits have to 'talk' to each other."
*   "We added **Cutwidth**: Measuring congestion."
*   "This improved our accuracy by ~5 seconds."

**Slide 4: The Smart Model**
*   "We chained our models."
*   "First, we predict the **Threshold**."
*   "Then, we feed that prediction into the **Runtime Model**."
*   "Result: The Runtime model knows that 'Lower Threshold = Faster Run'."

**Slide 5: Results**
*   "Threshold Accuracy: **66.67%** (Exact Match)."
*   "Runtime Accuracy: **84%** (Within 1 minute)."
*   "We are confident our model generalizes well."

---

## 3. 📂 What to Show (If Asked)
*   **If date asked for code**: Show `predict.py`. It's clean and has the chaining logic.
*   **If asked for error analysis**: Open `model_report.md`. It shows the exact breakdown.
