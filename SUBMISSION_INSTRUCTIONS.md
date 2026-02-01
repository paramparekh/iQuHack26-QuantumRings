# 🏁 Final Submission Instructions (Line-by-Line)

This guide tells you **exactly** what to do when the organizers DM you the holdout files.

## 1. Receive & Unzip
You will receive a zip file (e.g., `holdout_bundle.zip`).
1.  **Download** it.
2.  **Unzip** it into your `iQuHack26` folder.
    *   It should create a folder like `holdout/` containing:
        *   `tasks.json` (The list of questions)
        *   `circuits/` (The QASM files)
        *   `id_map.json` (OPTIONAL - might not be there)

## 2. Run The Prediction Command
Open your terminal in the `iQuHack26` folder.
Copy/Paste the command below, but **REPLACE the paths** with where you unzipped the files.

**If they provided `id_map.json`:**
```bash
python predict.py --tasks holdout/tasks.json --circuits holdout/circuits --id-map holdout/id_map.json --out predictions.json
```

**If they DID NOT providing `id_map.json`:** (Use this if you don't see one)
```bash
python predict.py --tasks holdout/tasks.json --circuits holdout/circuits --out predictions.json
```
*(Note: You can delete the `--id-map` part or leave it pointing to `holdout/id_map.json` if it doesn't exist, our script handles it).*

## 3. Upload Results
1.  You will see a new file: **`predictions.json`**.
2.  **Upload** this file to the Google Form / Submission Portal they provide.

## 4. Run Validator (Optional but Good)
If you extracted the `scripts/` folder from the repo earlier:
```bash
python scripts/validate_holdout_submission.py --public holdout/tasks.json --submission predictions.json
```
*(If it prints "Valid predictions parsed: X", you are perfect.)*

---

## 5. Submitting the Code (By 10:00 AM)
1.  Go to the Google Form.
2.  Upload **`submission.zip`** (It is already ready in your folder).
3.  Upload **`writeup.md`** (It is inside the zip, duplicate it if needed).
4.  Paste the **Run Command**:
    ```bash
    python predict.py --tasks <TASKS_JSON> --circuits <CIRCUITS_DIR> --id-map <ID_MAP> --out predictions.json
    ```

**Good Luck! You are going to crush it!** 🚀
