# Your part: alerts (Telegram + English / Tamil / Hindi messages)

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
git checkout -b feature/alerts
Expand-Archive -Path "$HOME\Downloads\part-alerts.zip" -DestinationPath . -Force
pytest
python -m scripts.alerts_demo
git add -A
git commit -m "Add Telegram alerts with English, Tamil and Hindi templates"
git push -u origin feature/alerts
```
Expected: `pytest` ends with "passed" (no failures), and the demo prints alert messages (they say
`delivered=False` because no Telegram bot is configured, which is normal).

Then on github.com open the repo, click **Compare & pull request** for `feature/alerts`, and create the Pull Request.
Aathi will review and merge it.

## What the code does (be able to explain this)
When a settlement's landslide risk crosses a level (watch 50%, warning 70%, emergency 85%), an alert text is
produced in English, Tamil and Hindi and sent to a Telegram chat. The same level is never sent twice for the same
settlement, and a new alert goes out only if the level goes up.
- `src/alerts/messages.py`: the levels and the text of every alert
- `src/alerts/telegram.py`: sends a message through a Telegram bot (does nothing if no token is set)
- `src/alerts/dispatch.py`: decides who gets alerted, without repeats
