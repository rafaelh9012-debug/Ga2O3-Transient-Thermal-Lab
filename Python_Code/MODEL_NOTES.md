# Scientific model — Ga₂O₃ Transient Thermal Lab

## Scope

An **independent exploratory thermal simulation**, extending the finite-volume steady-state solver used by the previous Ga₂O₃ Thermal Lab. It generates **two separate temperature-versus-time curves**: power-on heating and power-off cooling. The app uses two substrate thicknesses by default (630 µm and 50 µm). **It is not a transient simulation or validation provided by Chiang et al.** The underlying 2024 paper is a *steady-state* comparison; no device thermal transient trace or measured thermal resistance/time constant was supplied here.

## PDE and physical inputs

With `r` the radius and `z` depth, the axisymmetric model is

\[
\rho c_p\frac{\partial T}{\partial t}
=\frac{1}{r}\frac{\partial}{\partial r}\left(r k_r(T)\frac{\partial T}{\partial r}\right)
+\frac{\partial}{\partial z}\left(k_z(T)\frac{\partial T}{\partial z}\right)+Q(r,z,t).
\]

The time-dependent term introduces **mass density** `ρ` (default `5950 kg/m³`) and **specific heat** `c_p` (default `490 J/kg/K`) as constant, adjustable bulk values in both the substrate and drift layer. They determine the energy storage per cell, `m_i = ρ c_p V_i` in J/K. β-Ga₂O₃ density ~5.95 g/cm³ is documented by [Leibniz IKZ](https://www.ikz-berlin.de/en/offer/gallium-oxide); a summary of ~490 J/kg/K heat capacity is in [Crystals (2025), Table 1](https://doi.org/10.3390/cryst15100909). Properties can depend on temperature, doping and crystal quality; constant cp is a deliberate modeling simplification.

Directional steady conductivity is from Table I of Chiang et al. (2024):

- Through thickness: `k_z(T) = 18765 T^(-1.26)` W/(m·K)
- In-plane directions: `k_100(T) = 11078 T^(-1.21)`, `k_010(T) = 659992 T^(-1.77)` W/(m·K)
- Effective radial `k_r(T) = sqrt(k_100 * k_010)` assumes a reduced 2D rotationally symmetric approximation.

Default option uses `k(300 K)` held constant, to make the temporal solver linear and the physical transient easier to interpret. The user can instead select `k(T)` or isotropic constant conductivity; the latter two options change both steady temperature and transient dynamics. Temperature in the laws is **Kelvin**.

The volume source `Q = q'' / d` W/m³ is uniform within the 10 µm drift layer below the contact, zero elsewhere. `q''` is entered in W/cm² and converted to SI by `×10⁴`. The circular diode contact default radius is 500 µm. There is **no electrical circuit/transistor switching submodel**: power steps instantaneously at the phase change. This is the temperature response to an ideal step in dissipated heat, **not an electrical rise or fall time**.

## Initial conditions, boundaries and measured location

- Before switching ON, the substrate is solved to zero-power thermal equilibrium (including any ambient-vs-sink difference).
- During ON, dissipated power is constant for the selected duration.
- At the instant of switch OFF, the entire final ON 2D field is retained, and volumetric heating is set to zero.
- The bottom wafer face has fixed `T_sink`; the top has convection `h` to `T_ambient`. Center and outer radial wall are no-flux boundaries.
- The plotted **surface** is reconstructed at the actual top Robin boundary using the half-cell conduction resistance and convective resistance. Readout is the axis-centered surface temperature or area-averaged temperature within the contact.
- The solid heat-sink temperature stays fixed after switch-off: no sink/package dynamics are simulated.

### Time discretization

The existing steady finite-volume matrix `A(T)` has dimensions W/K. At backward-Euler time step Δt the conserved balance is

`M (u^{n+1} - u^n)/Δt + A(T^{n+1}) u^{n+1} = b^{n+1}`

where `M = diag(ρ cp V_i)` [J/K], `u = T - T_sink`, and `b` includes the on/off heat source and Robin ambient terms. Face conductance uses exact radial annulus geometry and half-cell series resistances as in the 2D steady solver. The linear step solves directly for the **temperature increment** to avoid subtracting nearly equal large values for tiny Δt. Temperature-dependent conductivity uses damped Picard iteration at each time step. The time grid is geometric: very short early steps followed by progressively longer steps, capturing very fast thin-wafer behavior without requiring millions of samples.

Energy residuals are checked against storage change + boundary loss − source input. Finite time-step resolution still introduces temporal discretization error: use more samples and a finer mesh to assess sensitivity.

## Model limitations

This simplified thermal-only model omits actual distributed electrical Joule heating, conduction through metal contacts, die attach, heat-sink transient capacity, thermal boundary resistance, radiation, substrate dopant-dependent properties, detailed monoclinic conductivity tensor, 3D crystal orientation, and electrical current rise/fall times. It assumes density and heat capacity are uniform and temperature-independent. **The original 2024 paper's reported steady temperature peaks (155°C and 55°C at 1500 W/cm²) are *not* predicted by the parent steady model.** Its default `k(T)` case produced a much hotter 630 µm wafer in that approximation. Do not imply validation of the transient curves from numerical convergence alone.

The plotted rise-to-90% metric is relative to the **calculated power-on steady-state temperature rise**. If heating is too short to reach the threshold, it is shown as “Not reached.” The cooldown 90% metric means decay to 10% of the switch-off temperature excess, again only if that threshold actually occurred within the simulated interval. Cooling time starts at the switch OFF instant, not at the start of the overall experiment.

## References

1. Chiang, C.-C., Li, J.-S., Wan, H.-H., Ren, F., Pearton, S. J. (2024). *Effect of Substrate Thinning on Temperature Rise in Ga₂O₃ Rectifiers*. ECS Journal of Solid State Science and Technology, 13, 115001. https://doi.org/10.1149/2162-8777/ad89fa
2. [Leibniz IKZ — Gallium oxide, bulk properties](https://www.ikz-berlin.de/en/offer/gallium-oxide)
3. [Crystals (2025), Table 1, heat-capacity and density overview](https://doi.org/10.3390/cryst15100909)
4. [Streamlit Community Cloud — repository structure](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
