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

## 3. The Strategy (The "Split")
To prove our AI works, we can't show it the test answers.
*   **75/25 Split (Previous)**: Train on 27 circuits, Test on 9.
*   **24/12 Split (Current)**: Train on 24 circuits, Test on 12.
    *   We teach the AI using the 24 circuits.
    *   We ask it to predict the other 12.
    *   We compare its answers to the truth.

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

## 6. The Result
*   **Threshold**: We get the exact right answer ~62-67% of the time.
*   **Runtime**: We are usually within 1 minute of the actual time.

You did it! You built a full Machine Learning Pipeline for Quantum Circuits. 🚀
