# Verification record

Tests performed in the packaging environment with Python 3.13 and NumPy/SciPy.

- Ten automated checks pass (`python -m unittest discover -s tests -v`).
- Power-off starts from exactly the ending temperature of power-on: no artificial discontinuity.
- Temperature increases under source heating and decreases after switching the source off.
- At zero power and fixed equal initial/sink/ambient temperature, both phases remain constant.
- Numerical conservation tracks cell energy storage against heat generation and boundary flux.
- For the representative frozen-k cases, time-step linear residuals are near machine precision.
- A thinner 50 µm wafer cools and heats more rapidly than a 630 µm wafer under the specified simplified model.
- Increasing the volumetric thermal heat capacity slows heating but leaves the steady-state result unchanged.
- Different top ambient and sink temperatures produce a physically consistent zero-power equilibrium.
- Nonlinear k(T) case solves without numerical divergence at 300 W/cm² in the validation scenario.

**Limit:** Browser-based live Streamlit validation and Windows-specific installer testing were not available in this execution environment. The offline Plotly `.htm` preview was successfully generated; the full Streamlit app itself should be smoke-tested after deployment. The numerical tests do not establish agreement with measured diode transients or a published TCAD transient solution.


## V2 presentation and export regression (October 24, 2026)

The original ten transient numerical tests remain unchanged and pass. Six additional
`test_presentation.py` checks validate literal RGB Turbo color stops, shared versus
independent heatmap limits, plot title removal and logarithmic time handling, expected
spatial heating direction, and the CSV/ZIP/offline HTML output.
**16 tests passed** in the full local Python suite.

**Limitation:** this runner could not open a GUI browser or install Streamlit to
inspect the deployed interface itself. Visual QA of the deployed Streamlit page
should be completed after publishing V2. This does not affect the original
numerical validation limitations.
