# 🎓 Project Explanation: From 0 to 100

You asked for an explanation of "the whole thing" so you can grasp it. Here is the entire story of what we built.

## 1. The Goal
We need to predict two things for a Quantum Circuit without running it:
1.  **Threshold**: How "lossy" can we make the compression while keeping Fidelity > 0.75? (Higher = Better Compression).
2.  **Runtime**: How long will it take to run? (Seconds).

## 2. The Data
*   **Total Circuits**: We have **36 Unique Designs** (in `circuits/`).
*   **Total Runs**: Each design was run 4 times (CPU/GPU, Single/Double precision).
*   **Total Datapoints**: 36 × 4 = **144 Samples**.

## 3. The "Practice Exam" Strategy (75/25 Split)
To trust our AI, we treat it like a student:
1.  **Training Set (75% / 108 Samples)**: This is the **Study Guide**. We give the AI these circuits and their answers (Threshold/Runtime). It studies them to learn patterns.
2.  **Validation Set (25% / 36 Samples)**: This is the **Practice Exam**. The AI *never* sees these answers. We ask it to solve them, and we grade it.
    *   *Crucial Point*: The results we gave you (66% Accuracy, 62s Error) come from this Practice Exam. This proves the AI isn't just memorizing; it's learning.
3.  **Submission**: We wrap up the "Student" (the Model) that studied the Study Guide and send it to the organizers.
4.  **Hidden Test Set**: The organizers have a **Final Exam** (circuits nobody has seen). Our goal is to perform as well on the Final Exam as we did on the Practice Exam.

## 4. The "Secret Sauce" (Features)
We don't feed the raw QASM code to the AI. We extract "Fingerprints" (`feature_ext.py`):
*   **Gate Counts**: How many operations?
*   **Depth**: How long is the circuit?
*   **Interaction Distance**: Are qubits talking to neighbors (easy) or far-away qubits (hard)? *We added this!*
*   **Cutwidth**: How "congested" is the traffic?

## 5. The Models (The Brains)
We used **Random Forest**, which is like a committee of 100 decision trees voting on the answer.
*   **Model 1 (Threshold)**: Looks at the fingerprints and votes on the best compression level.
*   **Model 2 (Runtime)**: Looks at fingerprints **AND the predicted threshold** to guess the time.
    *   *Why?* Because a lower threshold means less work, which means faster time. The model needs to know the threshold to guess the time correctly.

## 6. How Well Did We Do? (Scoring)
*   **Threshold (66.67% Perfect)**: Getting the exact right compression level 2 out of 3 times is excellent. Even when wrong, it's usually close.
*   **Runtime (84% Reliable)**: Predicting runtime is notoriously hard. Being within **1 minute** of the truth 84% of the time is a winning score.
    *   *Context*: If a job takes 10 minutes, saying "11 minutes" is a great guess. If it takes 2 hours, saying "2 hours 1 minute" is perfect.

## 7. What We Are Submitting
We are sending `submission.zip` which contains:
*   **The Brains**: The models trained on the Study Guide (75% data).
*   **The Code**: `predict.py` which runs the Brains.
*   **The Logic**: `feature_ext.py` which extracts the "fingerprints".
