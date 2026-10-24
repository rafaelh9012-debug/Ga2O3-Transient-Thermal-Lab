# Update the existing V1 GitHub repository to V2

Your GitHub repository already exists and is deployed separately from the steady-state application:

https://github.com/rafaelh9012-debug/Ga2O3-Transient-Thermal-Lab

**Do not run `git init` again, create another repository, or overwrite `.git/`.**

1. Extract this V2 ZIP into its own folder.
2. Copy the **contents** of the V2 `Ga2O3_Transient_Thermal_Lab` folder over the files of your already tracked V1 project, choosing to replace the matching application files. Keep your original `.git/` folder untouched. Alternatively, see the PowerShell commands in the response that delivered the V2 ZIP.
3. Open PowerShell in the existing tracked repository folder and run:

```powershell
git status
git add -A
git commit -m "V2: Turbo heatmaps, clearer charts and equation rendering"
git push origin main
```

Your existing Streamlit Community Cloud app normally updates automatically when GitHub receives the new commit. If it does not, open Streamlit Community Cloud → Manage app → Reboot/Rerun.

Cloud entry point stays `Python_Code/app.py`; Python 3.12 is a good choice.

The original steady-state repo `Ga2O3-Thermal-Lab` is unaffected.

---

# Deploy this as a **separate** public Streamlit application

This is a **new GitHub repository**, not a replacement for your existing `Ga2O3-Thermal-Lab` steady-state app.

## 1 — Create an empty GitHub repository

Go to https://github.com/new while signed into `rafaelh9012-debug`.

- Repository name: **`Ga2O3-Transient-Thermal-Lab`**
- Description: `Interactive transient thermal simulation of β-Ga₂O₃ diodes showing surface temperature rise during turn-on and decay during turn-off.`
- Visibility: Public (if you want to share source code)
- Do **not** initialize with GitHub README, .gitignore or license; they already live in this project package.

Do not create it inside or overwrite `Ga2O3-Thermal-Lab`.

## 2 — Extract ZIP, then open PowerShell in the NEW project folder

If the new ZIP is extracted inside Downloads:

```powershell
cd "$HOME\Downloads\Ga2O3_Transient_Thermal_Lab"
git init
git branch -M main
git remote add origin https://github.com/rafaelh9012-debug/Ga2O3-Transient-Thermal-Lab.git
git add -A
git status
```

Before committing, check that `.runtime/`, `.venv/`, and `__pycache__/` are NOT staged (they are excluded by `.gitignore`).

```powershell
git commit -m "Initial release: Ga2O3 Transient Thermal Lab"
git push -u origin main
```

If Git says user.name / user.email are missing, set them using `git config --global user.name "RafaelDaSquidman"` and `git config --global user.email "YOUR_PRIVATE_GITHUB_EMAIL_OR_NOREPLY"` locally. No passwords, tokens, private keys, or one-time codes need to be shared. If GitHub refuses push because an existing README commit was added online, do not force-push; reconcile the branches instead.

You can confirm the upload here: https://github.com/rafaelh9012-debug/Ga2O3-Transient-Thermal-Lab

## 3 — Create a separate Streamlit Cloud app

Visit https://share.streamlit.io and select **Create app → I have an app**. Authenticate with your own GitHub account, then set:

| Field | Value |
|---|---|
| Repository | `rafaelh9012-debug/Ga2O3-Transient-Thermal-Lab` |
| Branch | `main` |
| Main file path | **`Python_Code/app.py`** |
| Suggested custom subdomain | `rafaeldasquidman-ga2o3-transient` (if available) |
| Python version | **3.12**, if it is offered |
| Secrets / API keys | None |

Click Deploy and inspect build logs for missing dependencies. Streamlit will install from `Python_Code/requirements.txt` automatically and load `.streamlit/config.toml`.

**No live Streamlit URL exists simply because the ZIP was created.** You receive the actual clickable URL after successfully deploying; for example the suggested subdomain above is **not guaranteed to be available**.

## 4 — Update in the future

```powershell
git add -A
git commit -m "Describe your update"
git push
```

Streamlit normally detects commits to `main` and updates the deployed app. Keep the original `Ga2O3-Thermal-Lab` repository unchanged.

## Official docs

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
