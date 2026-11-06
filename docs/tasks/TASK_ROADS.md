# Your part: road-network cascade (which villages get cut off?)

The code is finished. **Do not edit or add any file.** Your job is to run the tests and push.
If anything fails, send Aathi a screenshot of the error. Do not try to fix it yourself.

## Windows setup (do once)
Install **Git for Windows** (git-scm.com) and **Python 3.12 or newer** (python.org, tick "Add python.exe to PATH").
Accept the GitHub collaborator invitation from your email first. Then open **PowerShell**:
```powershell
git clone https://github.com/Aathi06/landslide-ews.git
cd landslide-ews
git config user.name "Your Name"
git config user.email "the-email-on-your-GitHub-account"
py -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
The first push opens a browser window to log in to GitHub. Log in and it continues.

## Run and push
```powershell
git checkout -b feature/roads
Expand-Archive -Path "$HOME\Downloads\part-roads.zip" -DestinationPath . -Force
pip install networkx
pytest
git add -A
git commit -m "Add road-network cascade: cut risky edges, find isolated villages"
git push -u origin feature/roads
```
Expected: `pytest` ends with "passed" and no failures. The road tests need no internet.

Then on github.com open the repo, click **Compare & pull request** for `feature/roads`, and create the Pull Request.
Aathi will review and merge it.

## Optional, only if Aathi asks: the real-roads run
```powershell
pip install -r requirements-roads.txt
python -m scripts.roads_demo
```
This downloads the real Nilgiris road network from OpenStreetMap. Send Aathi whatever it prints, including any error.

## What the code does (be able to explain this)
Roads are a graph of junctions and road segments. Where the landslide risk on a segment is above the alert
threshold, the segment is removed. Then for each village the code checks whether it can still reach a hospital and
how much longer the route has become. Villages with no route left are "isolated".
- `src/roads/cascade.py`: the cutting and the isolation check
- `src/roads/graph.py`: downloads roads and hospitals from OpenStreetMap
