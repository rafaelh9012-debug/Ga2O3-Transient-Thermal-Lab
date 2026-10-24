# V2.1 Startup Import Hotfix

The V2 Streamlit deployment reported `ImportError` from `Python_Code/app.py` while importing `visuals`. One plausible cause is a mixed V1/V2 cached module during a Streamlit Cloud hot reload: V2 added the `HEATMAP_PALETTES` symbol, which V1 lacked. The full Cloud traceback is redacted in the screenshot, so this cause cannot be confirmed from the screenshot alone.

## Changes

- Duplicated the complete V2 plotting implementation to `Python_Code/transient_visuals_v21.py` with a uniquely versioned name.
- Updated `app.py`, `export_transient_results.py`, and presentation tests to import from the new module.
- Retained a small `visuals.py` compatibility shim for existing scripts.
- Added tests covering the **exact imports** in the Streamlit app and export script.
- CI checks those imports before running the full numerical tests.
- Maintained the Turbo heatmaps, clean headings, and corrected LaTeX from V2.

This hotfix does not change the thermal solver, default settings, or scientific results. The static `OPEN_WEB_VERSION.htm` remains the V2 Turbo export and still works without Python.

## Deploy

1. Reboot the Streamlit app first using Manage app > Reboot app. This can clear an old module without code changes.
2. If the ImportError persists, apply the `Ga2O3_Transient_Thermal_Lab_V2_1_Hotfix_Only.zip` files to the **existing V1 Git working directory**, preserving its `.git` folder.
3. Run `git add -A`, `git commit -m "V2.1: fix Streamlit startup import"`, and `git push origin main`.
4. Verify CI checks and reboot the app.

If a new error occurs, inspect `Manage app > Logs` for the full ImportError name and module path.
