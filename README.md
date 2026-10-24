# Ga₂O₃ Transient Thermal Lab

**Independent second Streamlit application** by **RafaelDaSquidman**. Explore the predicted **temperature at a diode surface vs time** as its heat source **switches on** and **switches off**, comparing two β-Ga₂O₃ substrate thicknesses. Includes 2D conduction with physical thermal energy storage, configurable power, material properties, heat-sink parameters, and downloadable data. This is educational/model research, **not experimentally validated transient behavior**. See [MODEL_NOTES.md](Python_Code/MODEL_NOTES.md).

## V2 interface updates

The heatmaps now default to **Turbo** with a shared temperature scale, with an optional independent-contrast view for the thin substrate. ON/OFF chart titles and legends no longer overlap. The physics tab displays the equation as formatted mathematics; the offline preview has also been regenerated. See [QA_V2_CHANGELOG.md](QA_V2_CHANGELOG.md).

## 3 ways to access

1. **Public web app (after you deploy):** people use the full model via the separate Streamlit URL without installing Python. See [DEPLOY_TO_STREAMLIT.md](DEPLOY_TO_STREAMLIT.md).
2. **Offline preview:** double-click `OPEN_WEB_VERSION.htm` in Chrome, Edge or Firefox to explore the **precomputed default results** with hover/pan/zoom. It does not re-solve equations. Works without internet or Python.
3. **Local Python / Spyder:** open `START_APP.py` in Spyder and click Run, or double-click `RUN_WITH_EXISTING_PYTHON.bat` if Windows can locate a compatible interpreter. The script uses the existing interpreter, creates `.runtime`, installs missing Python libraries if needed (first-run internet may be required), and runs Streamlit locally. It **never installs Python** and contains **no custom EXE**. Python 3.11+ required.

## Direct command-line startup

From this folder with Python 3.11+ and dependencies installed:

```powershell
python -m pip install -r Python_Code/requirements.txt
python -m streamlit run Python_Code/app.py
```

## Default experiment

- Substrates: 630 µm vs 50 µm; drift thickness: 10 µm
- Circular contact radius: 500 µm; model radius: 1000 µm
- Power density: 500 W/cm² (adjustable to 1500)
- Heat source ON for 0.3 seconds, then OFF for 0.3 seconds
- Density: 5950 kg/m³; heat capacity: 490 J/(kg·K)
- Bottom: 300 K fixed; top: convection 10 W/(m²·K) to 300 K
- 2D r–z axisymmetric; directional conductivity held at 300 K initially

## Layout

| File | Purpose |
|---|---|
| `Python_Code/app.py` | Streamlit app — **main entry point for cloud deployment** |
| `Python_Code/transient_model.py` | Physically derived 2D transient solver |
| `Python_Code/steady_reference.py` | Provenance-preserving previous finite-volume steady solver |
| `Python_Code/visuals.py` | Plotly charts, export bundle, offline HTML |
| `OPEN_WEB_VERSION.htm` | Standalone offline interactive snapshot |
| `START_APP.py` | Existing-Python launcher for Spyder and similar IDEs |
| `RUN_WITH_EXISTING_PYTHON.bat` | Windows interpreter discovery and launch |
| `Python_Code/requirements.txt` | Streamlit Cloud dependencies |
| `Python_Code/export_transient_results.py` | Recreate offline HTML and CSV/ZIP reports |
| `.streamlit/config.toml` | High-contrast Streamlit light theme |
| `Python_Code/MODEL_NOTES.md` | Scientific scope, equations, assumptions and sources |
| `Python_Code/tests/` | Numerical verification tests |
| `DEPLOY_TO_STREAMLIT.md` | Git and cloud deployment instructions |

## Validation

```powershell
cd Python_Code
python -m unittest discover -s tests -v
```

See [VALIDATION.md](Python_Code/VALIDATION.md) and [QA_V2_CHANGELOG.md](QA_V2_CHANGELOG.md). Numerical verification is not experimental validation.

**Companion steady-state app repo:** https://github.com/rafaelh9012-debug/Ga2O3-Thermal-Lab

To regenerate an offline snapshot after changing the inputs, run `python Python_Code/export_transient_results.py --power 500 --output examples`; the new snapshot goes into `examples/` and does not automatically overwrite the root-level preview.
