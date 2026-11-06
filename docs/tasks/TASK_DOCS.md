# Your part: report outline, demo script and documentation

The files are finished. **Do not edit or add any file.** Your job is to push them.
Aathi will fill in the TODO parts of the report with the real results later.

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
git checkout -b feature/docs
Expand-Archive -Path "$HOME\Downloads\part-docs.zip" -DestinationPath . -Force
git add -A
git commit -m "Add report outline and demo script"
git push -u origin feature/docs
```
Then on github.com open the repo, click **Compare & pull request** for `feature/docs`, and create the Pull Request.
Aathi will review and merge it.

## What the files are
- `docs/REPORT_OUTLINE.md`: section-by-section outline of the final report, with the known facts filled in
- `docs/DEMO_SCRIPT.md`: a 5-minute demo script and likely questions
