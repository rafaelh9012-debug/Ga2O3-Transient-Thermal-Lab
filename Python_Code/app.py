"""Run locally: python -m streamlit run app.py"""
import streamlit as st

from transient_model import TransientSettings, simulate_comparison
from visuals import phase_plot, field_plot, result_zip, offline_html, format_time, timeseries_frame, HEATMAP_PALETTES

st.set_page_config(page_title='Ga₂O₃ | Transient Thermal Lab',page_icon='🌡️', layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.stApp{background:#edf3f8;color:#142b42}
.block-container{padding-top:1.5rem;max-width:1480px}
[data-testid="stSidebar"]{background:#f8fbfe;border-right:1px solid #d7e2eb}
[data-testid="stMetric"]{background:#fff;border:1px solid #d5e1ec;border-radius:13px;padding:15px 20px;min-height:116px}
[data-testid="stMetricLabel"]{color:#405870!important;font-weight:600}
[data-testid="stMetricValue"]{color:#142b42!important}
[data-testid="stMetricDelta"]{color:#405870!important}
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label,[data-testid="stWidgetLabel"] label{color:#142b42!important}
[data-testid="stAlert"] *{color:inherit}
.stTabs [data-baseweb="tab"]{color:#364d65!important;font-weight:650}
.stTabs [aria-selected="true"]{color:#087c86!important}
.hero{border-bottom:5px solid #08a1a8;border-radius:17px;background:#142a42;color:white;padding:28px 36px;margin-bottom:21px}
.hero .eyebrow{font-size:11px;font-weight:800;color:#87e1e1;letter-spacing:2px}
.hero h1{color:#fff!important;margin:6px 0;font-size:36px;line-height:1.2}
.hero p{color:#dceaf5;margin:0;font-size:15px;line-height:1.6}
.section-heading{border-left:4px solid #079ea8;padding-left:14px;margin-top:22px;margin-bottom:4px;line-height:1.5;color:#142b42!important;font-size:1.35rem}
.note{border:1px solid #eadab5;background:#fff7e5;color:#714b05!important;padding:13px 18px;border-radius:10px;line-height:1.55;margin:12px 0}
.note strong{color:#623b00!important}
.smallnote{color:#495d70!important;font-size:13px}
[data-testid="stMetricDelta"] div{color:#405870!important;background:transparent!important}
[data-testid="stMetricDelta"] svg{display:none!important}
[data-testid="stCaptionContainer"] p{color:#51687e!important}
[data-testid="stMarkdownContainer"] p{line-height:1.55}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:12px;flex-wrap:wrap}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False,max_entries=12)
def cached_run(settings):
    return simulate_comparison(settings)

with st.sidebar:
    st.markdown('### <span style="color:#142b42">Simulation controls</span>',unsafe_allow_html=True)
    st.caption('Set the experiment, then click Run transient simulation. Values use physical units.')
    with st.form('settings'):
        power=st.slider('Power density (W/cm²)',0,1500,500,25)
        a_um=st.number_input('Substrate A thickness (µm)',min_value=20.,max_value=1000.,value=630.,step=10.)
        b_um=st.number_input('Substrate B thickness (µm)',min_value=20.,max_value=1000.,value=50.,step=10.)
        on_ms=st.number_input('Diode ON duration (milliseconds)',min_value=.01,max_value=100000.,value=300.,step=25.,format='%.3f')
        off_ms=st.number_input('Diode OFF duration (milliseconds)',min_value=.01,max_value=100000.,value=300.,step=25.,format='%.3f')
        conductivity_label=st.selectbox('Thermal conductivity', ['Fixed at 300 K · directional', 'Temperature-dependent k(T)', 'Constant isotropic k'])
        readout=st.selectbox('Surface reading', ['Center','Contact average'],help='Center: temperature at the axis at the physical top boundary. Contact average: area-weighted surface under the circular contact.')
        with st.expander('Material · boundaries · resolution'):
            rho=st.number_input('Density (kg/m³)',min_value=500.,max_value=20000.,value=5950.,step=50.)
            cp=st.number_input('Specific heat (J/kg/K)',min_value=50.,max_value=3000.,value=490.,step=10.)
            drift=st.number_input('Heated drift-layer thickness (µm)',min_value=1.,max_value=50.,value=10.,step=1.)
            contact=st.number_input('Contact radius (µm)',min_value=25.,max_value=1500.,value=500.,step=25.)
            outer=st.number_input('Model radius (µm)',min_value=50.,max_value=3000.,value=1000.,step=50.)
            sink=st.number_input('Bottom sink (K)',min_value=200.,max_value=500.,value=300.,step=1.)
            ambient=st.number_input('Air temperature (K)',min_value=200.,max_value=500.,value=300.,step=1.)
            h=st.number_input('Top convection h (W/m²/K)',min_value=0.,max_value=1000.,value=10.,step=5.)
            kconst=st.number_input('Isotropic k for constant mode (W/m/K)',min_value=1.,max_value=500.,value=14.,step=1.)
            mesh=st.selectbox('Mesh', ['Fast','Balanced','Detailed'])
            steps=st.slider('Samples per phase',25,100,55,5)
        run=st.form_submit_button('Run transient simulation',type='primary',use_container_width=True)
    st.caption('Local numerical solve · no API keys · no commercial solver required.')

settings=TransientSettings(power_w_cm2=float(power),substrate_a_um=float(a_um),substrate_b_um=float(b_um),
    drift_um=float(drift),contact_radius_um=float(contact),domain_radius_um=float(outer),
    sink_k=float(sink),ambient_k=float(ambient),h_w_m2k=float(h),
    conductivity={'Fixed at 300 K · directional':'frozen','Temperature-dependent k(T)':'temperature','Constant isotropic k':'constant'}[conductivity_label],
    constant_k=float(kconst),density_kg_m3=float(rho),cp_j_kgk=float(cp),
    heating_s=float(on_ms)/1000.,cooling_s=float(off_ms)/1000.,points_per_phase=int(steps),mesh_name=mesh,surface_readout=readout)

st.markdown('''<div class="hero"><div class="eyebrow">RAFAELDASQUIDMAN · SEMICONDUCTOR TRANSIENT HEAT TRANSFER</div>
<h1>Ga₂O₃ Transient Thermal Lab</h1><p>How quickly does a diode heat up when switched ON — and cool down when switched OFF?<br>
Interactive time-dependent, 2D axisymmetric conduction with an explicit thermal-energy storage term.</p></div>''',unsafe_allow_html=True)

try:
    with st.spinner('Solving switch-on and switch-off temperature histories for both substrates…'):
        curves=cached_run(settings)
except (ValueError,RuntimeError,OverflowError) as exc:
    st.error(f'Simulation stopped: {exc}')
    st.info('Reduce the input power, shorten the time range, switch to fixed-at-300-K conductivity, or decrease mesh resolution.')
    st.stop()

A,B=curves
v=st.columns(4)
v[0].metric(f'ON end · {A.thickness_um:g} µm',f'{A.end_on_c:.1f} °C', f'+{A.end_on_c-A.baseline_c:.1f} K rise',delta_color='off')
v[1].metric(f'ON end · {B.thickness_um:g} µm',f'{B.end_on_c:.1f} °C', f'+{B.end_on_c-B.baseline_c:.1f} K rise',delta_color='off')
v[2].metric(f'OFF end · {A.thickness_um:g} µm',f'{A.end_off_c:.1f} °C','After cooldown',delta_color='off')
v[3].metric(f'OFF end · {B.thickness_um:g} µm',f'{B.end_off_c:.1f} °C','After cooldown',delta_color='off')

st.markdown('<div class="note"><strong>Interpretation:</strong> The diode turns ON at the beginning of the heating plot, then its source is set to zero at the beginning of the cooling plot. The OFF curve starts from the exact final ON temperature field. These are thermal-model predictions, not measured turn-on switching speeds or a reproduction of the paper’s transient data.</div>',unsafe_allow_html=True)
if max(A.final_on_field_c.max(),B.final_on_field_c.max())>600 and settings.conductivity=='temperature':
    st.warning('High predicted temperatures extrapolate k(T) beyond well-characterized operating conditions. Treat them as a model sensitivity study, not verified safe junction temperatures.')

u1,u2,u3=st.columns([1,1,2])
with u1:
    temp_unit=st.selectbox('Temperature display',['°C','K'])
with u2:
    log_time=st.toggle('Logarithmic time axis',value=False,help='Useful for seeing early microsecond-scale changes; the t=0 point is omitted from logarithmic plots.')
with u3:
    st.caption('Both plots use their own elapsed-time axis. Hover to inspect the predicted surface temperatures. Colors are consistent between plots.')

st.markdown('<h3 class="section-heading">1 · Heating response — diode turns ON</h3>',unsafe_allow_html=True)
st.caption('Heat source switched ON at t = 0. Curves start from the zero-power equilibrium state. Orange = thick substrate; teal = thin substrate.')
st.plotly_chart(phase_plot(curves,'on',log_time=log_time,unit='K' if temp_unit=='K' else 'C'),use_container_width=True,config={'displaylogo':False,'scrollZoom':True})
st.markdown('<h3 class="section-heading">2 · Cooling response — diode turns OFF</h3>',unsafe_allow_html=True)
st.caption('Heat source switched OFF at t = 0. Each curve starts at its own final ON temperature; there is no artificial reset.')
st.plotly_chart(phase_plot(curves,'off',log_time=log_time,unit='K' if temp_unit=='K' else 'C'),use_container_width=True,config={'displaylogo':False,'scrollZoom':True})

st.markdown('### Transient response metrics')
a90=A.summary();b90=B.summary()
col1,col2=st.columns(2)
for col,c,summary in [(col1,A,a90),(col2,B,b90)]:
    with col:
        st.markdown(f'**{c.thickness_um:g} µm substrate**')
        st.write(f'**Rise to 90% of steady-state temperature rise:** {format_time(summary["rise_time_to_90pct_steady_s"])}')
        st.write(f'**Cooldown to 10% of switch-off temperature excess:** {format_time(summary["cooling_time_to_10pct_switch_off_excess_s"])}')
        st.caption(f'Steady power-on surface reference: {c.steady_on_c:.2f} °C. Unreached time thresholds are not extrapolated.')

maps, data, about = st.tabs(['Temperature fields','Results & downloads','Physics & limitations'])
with maps:
    st.markdown('#### Snapshot at the moment the diode turns OFF')
    palette=st.selectbox('Temperature map palette',HEATMAP_PALETTES,index=0,help='Turbo is the default. Use the checkbox below to choose a shared or individually enhanced scale.')
    separate_contrast=st.checkbox('Enhance thin-substrate detail (separate color scales)',value=False,help='On: each heatmap uses its own local temperature range. Off: both use exactly the same temperature-to-color mapping for quantitative comparison.')
    st.plotly_chart(field_plot(curves,palette=palette,shared_scale=not separate_contrast),use_container_width=True,config={'displaylogo':False,'scrollZoom':True})
    if separate_contrast:
        st.caption('Separate color scales emphasize each substrate’s thermal gradient; compare the numerical colorbars, not the colors directly. Depth axes show actual thickness.')
    else:
        st.caption('Shared colorbar: the same color represents the same temperature in both substrates. Depth axes show actual thickness.')
    st.caption('Maps show cell-center temperatures; time curves reconstruct the physical top-boundary temperature.')
with data:
    st.dataframe(timeseries_frame(curves),use_container_width=True,hide_index=True,height=280)
    try:
        st.download_button('Download CSV, 2D fields & model diagnostics (.zip)',data=result_zip(curves,settings),
                           file_name='Ga2O3_Transient_Results.zip',mime='application/zip')
        st.download_button('Download an offline interactive HTML snapshot (.htm)',data=offline_html(curves,settings,palette=palette),
                           file_name='Ga2O3_Transient_Offline.htm',mime='text/html')
    except Exception as exc:
        st.warning(f'Export could not be assembled: {exc}')
with about:
    st.markdown('**Governing equation**')
    st.latex(r"""\begin{aligned}
    \rho c_p \frac{\partial T}{\partial t}
    &= \frac{1}{r} \frac{\partial}{\partial r}
    \left(r k_r(T) \frac{\partial T}{\partial r}\right) \\
    &\quad+ \frac{\partial}{\partial z}
    \left(k_z(T) \frac{\partial T}{\partial z}\right)
    + Q(r,z,t)
    \end{aligned}""")
    st.markdown("""
- **ON:** uniform volumetric heating inside the drift layer, under the circular contact.
- **OFF:** heat source is set to zero; stored thermal energy continues diffusing out.
- **Bottom:** fixed-temperature heat sink. **Top:** convection to ambient. **Sides:** insulated/symmetry.
- **Material:** density and heat capacity are adjustable constants, shared by drift layer and substrate.
- **Numerics:** conservative 2D axisymmetric finite volumes; implicit backward Euler in time; Picard iteration for the nonlinear k(T) option.
- **Limitations:** axisymmetry approximates in-plane anisotropy. This thermal-only simulation omits contacts, packaging, electrical switching, interface resistance, radiation, and detailed spatial Joule heating.
""")
    st.caption('Reference 2D steady-state conductivity model: Chiang et al. (2024), DOI 10.1149/2162-8777/ad89fa. Transient heat capacity is an added modeling parameter, not sourced from the original paper.')
    st.markdown('**Previous steady-state project:** [Ga2O3 Thermal Lab](https://github.com/rafaelh9012-debug/Ga2O3-Thermal-Lab). This new transient application is a separate project.')
    st.markdown('**Representative material-property references:** [Leibniz IKZ — density](https://www.ikz-berlin.de/en/offer/gallium-oxide); [2025 Ga₂O₃ review — heat capacity](https://doi.org/10.3390/cryst15100909). These are approximate bulk values, not calibrated for your sample.')
    st.markdown('**Numerical diagnostics**')
    st.json({f'{c.thickness_um:g}µm':{'max_relative_time_step_residual':c.max_step_residual,
                                     'max_relative_energy_balance_error':c.heat_balance_error} for c in curves})

st.caption('© RafaelDaSquidman · An exploratory research and educational thermal model, not device certification or an experimentally validated temperature predictor.')
