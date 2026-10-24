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
