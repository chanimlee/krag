# Python Environment

This project uses the following Python executable on this Windows workstation:

```text
C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe
```

## Why This Path Is Fixed

The plain `python` command may point to PsychoPy Python on this machine. That environment did not have all required packages for the TF-IDF retrieval scripts, especially `scikit-learn` and `joblib`.

Use the Python 3.13 executable above for project scripts unless the environment is deliberately changed.

## Recommended Commands

Run these commands from the project root.

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\check_env.py
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\build_tfidf_index.py
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\test_retrieval.py --query "-는다고 하다를 활용한 읽기 문항" --top-k 5 --target both
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\run_retrieval_smoke_test.py
```

## Install Requirements

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
```
