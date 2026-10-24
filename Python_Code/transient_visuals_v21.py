"""Presentation and offline report exports for transient Ga2O3 studies."""
from __future__ import annotations
from dataclasses import asdict
from html import escape
import io
import json
import zipfile
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from plotly.colors import get_colorscale
from transient_model import Curve, TransientSettings, as_records

INK = '#142b42'
MUTED = '#51687e'
BG = '#f1f6fa'
ORANGE = '#d7663d'
TEAL = '#068c97'
COLORS = [ORANGE, TEAL]


def format_time(t: float | None) -> str:
    if t is None or not np.isfinite(t):
        return 'Not reached'
    if t >= 1:
        return f'{t:.3g} s'
    if t >= 1e-3:
        return f'{t*1e3:.3g} ms'
    if t >= 1e-6:
        return f'{t*1e6:.3g} µs'
    return f'{t*1e9:.3g} ns'


# Plotly can confuse some reserved dark-theme hex colors with Streamlit theme
# placeholders. Explicit RGB stops keep scientific colormaps literal in both
# Streamlit and offline HTML, regardless of the viewer's local theme.
HEATMAP_PALETTES = ('Turbo', 'Viridis', 'Cividis', 'Inferno')


def scientific_colorscale(palette: str = 'Turbo'):
    if palette not in HEATMAP_PALETTES:
        raise ValueError(f"Unsupported heatmap palette: {palette}")
    result = []
    for value, color in get_colorscale(palette):
        if color.startswith('#') and len(color) == 7:
            color = 'rgb({},{},{})'.format(*(int(color[i:i+2], 16) for i in (1, 3, 5)))
        result.append([float(value), color])
    return result


def theme(fig, height=450, top_margin=56, show_legend=True):
    """Consistent, readable Plotly charts with reserved room for legends."""
    fig.update_layout(
        template='plotly_white', height=height, autosize=True,
        paper_bgcolor='white', plot_bgcolor='#f7fafc',
        font=dict(family='Arial, sans-serif', size=13, color=INK),
        margin=dict(l=72, r=36, t=top_margin, b=68),
        hoverlabel=dict(bgcolor=INK, font_color='white', font_size=13),
        showlegend=show_legend,
        legend=dict(
            orientation='h', x=0.5, xanchor='center',
            y=1.095, yanchor='bottom',
            font=dict(size=12, color=INK),
            bgcolor='rgba(255,255,255,0.9)',
            itemsizing='constant', tracegroupgap=10),
        modebar=dict(bgcolor='rgba(0,0,0,0)', color=MUTED),
        hovermode='closest',
    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor='#b4c6d4',
                     showgrid=True, gridcolor='#e8edf2', zeroline=False,
                     automargin=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='#b4c6d4',
                     showgrid=True, gridcolor='#e8edf2', zeroline=False,
                     automargin=True)
    return fig


def phase_plot(curves: tuple[Curve, Curve], phase: str, log_time=False, unit='C'):
    if phase not in ('on', 'off'):
        raise ValueError('phase must be on or off')
    if unit not in ('C', 'K'):
        raise ValueError('Temperature unit must be C or K')
    on = phase == 'on'
    fig = go.Figure()
    for curve, color, marker in zip(curves, COLORS, ['circle', 'square']):
        time = curve.on_s if on else curve.off_s
        c = curve.on_c if on else curve.off_c
        y = c if unit == 'C' else c + 273.15
        # Logarithmic axes cannot display t=0. Filter display arrays rather
        # than modifying the original curve or any other chart.
        valid = time > 0 if log_time else np.ones(len(time), dtype=bool)
        x_display, y_display = time[valid], y[valid]
        label = f'{curve.thickness_um:g} µm substrate'
        fig.add_trace(go.Scatter(
            x=x_display, y=y_display, name=label, mode='lines',
            line=dict(color=color, width=3.4),
            hovertemplate='Time: %{x:.5g} s<br>Surface: %{y:.3f} '
                          + ('°C' if unit == 'C' else 'K') + '<extra>' + label + '</extra>'))
        fig.add_trace(go.Scatter(x=[x_display[-1]], y=[y_display[-1]],
                                 mode='markers', marker=dict(size=9, color=color,
                                                             symbol=marker),
                                 showlegend=False, hoverinfo='skip'))
    theme(fig, height=445, top_margin=58)
    fig.update_layout(xaxis_title='Elapsed time since switching (s)',
                      yaxis_title='Surface temperature (°C)' if unit == 'C' else 'Surface temperature (K)')
    if log_time:
        fig.update_xaxes(type='log')
    return fig


def combined_plot(curves, settings):
    fig = make_subplots(rows=1, cols=2, subplot_titles=['Source ON', 'Source OFF'],
                        horizontal_spacing=.14)
    for case, color in zip(curves, COLORS):
        label = f'{case.thickness_um:g} µm'
        for i, (t, y) in enumerate([(case.on_s, case.on_c), (case.off_s, case.off_c)], 1):
            fig.add_trace(go.Scatter(x=t, y=y, mode='lines',
                                     line=dict(color=color, width=3), name=label,
                                     legendgroup=label, showlegend=i == 1,
                                     hovertemplate='%{x:.5g} s<br>%{y:.2f} °C<extra>'+label+'</extra>'),
                          row=1, col=i)
    theme(fig, 460, top_margin=75)
    for i in (1, 2):
        fig.update_xaxes(title_text='Elapsed time (s)', row=1, col=i)
        fig.update_yaxes(title_text='Surface (°C)' if i == 1 else None,
                         row=1, col=i)
    return fig


def field_plot(curves: tuple[Curve, Curve], palette: str = 'Turbo', shared_scale: bool = True):
    """Shared, literal RGB color scale. Subplots have separate physical depths."""
    scale = scientific_colorscale(palette)
    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=.15,
        subplot_titles=[f'{c.thickness_um:g} µm substrate · end of ON' for c in curves],
    )
    lo = min(float(c.final_on_field_c.min()) for c in curves)
    hi = max(float(c.final_on_field_c.max()) for c in curves)
    upper = max(hi, lo + 1e-5)
    for i, c in enumerate(curves, 1):
        if shared_scale:
            color_options = dict(coloraxis='coloraxis')
        else:
            color_options = dict(colorscale=scale, zmin=float(c.final_on_field_c.min()),
                                 zmax=max(float(c.final_on_field_c.max()),
                                          float(c.final_on_field_c.min())+1.e-5),
                                 colorbar=dict(title='°C', thickness=12, len=.68,
                                               x=.43 if i == 1 else 1.02, y=.5,
                                               outlinewidth=0))
        fig.add_trace(go.Heatmap(
            x=c.x_um, y=c.z_um, z=c.final_on_field_c,
            **color_options, zsmooth=False,
            hovertemplate=(f'<b>{c.thickness_um:g} µm substrate</b><br>'
                           'Radius: %{x:.2f} µm<br>Depth: %{y:.2f} µm'
                           '<br>Cell temperature: %{z:.2f} °C<extra></extra>')),
            row=1, col=i)
        fig.update_xaxes(title_text='Radius r (µm)', row=1, col=i)
        fig.update_yaxes(title_text='Depth z (µm)' if i == 1 else None,
                         range=[float(c.z_um[-1]), 0], row=1, col=i)
    theme(fig, height=485, top_margin=74, show_legend=False)
    fig.update_layout(
        # No floating title: the application/HTML provides the chart heading.
        margin=dict(l=75, r=110, t=82, b=65),
        coloraxis=dict(colorscale=scale, cmin=lo, cmax=upper,
                       showscale=shared_scale,
                       colorbar=dict(title='°C', thickness=15, len=.78,
                                     x=1.02, y=.5, outlinewidth=0)),
    )
    fig.update_annotations(font=dict(size=14, color=INK), yshift=8)
    return fig


def timeseries_frame(curves):
    records = []
    for c in curves:
        for phase, times, temps in [('Heating (ON)',c.on_s,c.on_c),('Cooling (OFF)',c.off_s,c.off_c)]:
            for t, temp in zip(times,temps):
                records.append(dict(substrate_um=c.thickness_um, phase=phase, time_s=t,
                                    surface_temp_C=temp,surface_temp_K=temp+273.15))
    return pd.DataFrame(records)


def result_zip(curves, settings):
    f=io.BytesIO()
    with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        z.writestr('temperature_timeseries.csv',timeseries_frame(curves).to_csv(index=False))
        z.writestr('parameters_diagnostics.json',json.dumps(as_records(curves,settings),indent=2))
        for c in curves:
            z.writestr(f'surface_field_{c.thickness_um:g}um_end_on.csv',
                       pd.DataFrame(c.final_on_field_c,index=c.z_um,columns=c.x_um).rename_axis('depth_um').to_csv())
        z.writestr('MODEL_NOTICE.txt', 'Thermal-only axisymmetric finite-volume model, not validated against transient measurements. See MODEL_NOTES.md in project.')
    return f.getvalue()


def offline_html(curves,settings,palette: str = "Turbo"):
    on_html = pio.to_html(phase_plot(curves,'on'),include_plotlyjs=True,full_html=False,config={'displaylogo':False})
    off_html = pio.to_html(phase_plot(curves,'off'),include_plotlyjs=False,full_html=False,config={'displaylogo':False})
    fields_html = pio.to_html(field_plot(curves, palette=palette),include_plotlyjs=False,full_html=False,config={'displaylogo':False})
    summary_rows = ''.join(f'<tr><td>{c.thickness_um:g} µm</td><td>{c.end_on_c:.2f} °C</td><td>{c.end_off_c:.2f} °C</td><td>{format_time(c.summary()["rise_time_to_90pct_steady_s"])}</td></tr>' for c in curves)
    source = escape(json.dumps(as_records(curves,settings), indent=2))
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ga₂O₃ Transient Thermal Lab — Offline Report</title>
<style>body{{margin:0;background:#edf3f8;color:#142b42;font:16px -apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}}main{{max-width:1380px;margin:auto;padding:26px}}header{{background:#142b42;color:white;padding:32px;border-radius:17px;border-bottom:5px solid #00a5ae}}header h1{{margin:4px 0;font-size:36px}}header p{{color:#d4e5ef}}article{{background:white;border:1px solid #d8e1ec;border-radius:15px;padding:14px;margin:20px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #d4dfe9;text-align:left}}th{{background:#eff6fa}}.note{{padding:17px;background:#fff3d8;border-radius:9px;color:#6c4700}}small{{color:#617488}}details{{margin:24px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style></head><body><main><header><small style="color:#92e1e4">RAFAELDASQUIDMAN · SEMICONDUCTOR THERMAL MODELING</small><h1>Ga₂O₃ Transient Thermal Lab</h1><p>Offline interactive snapshot · Heat-up and cool-down of two diode substrates</p></header>
<p class="note"><strong>Offline preview:</strong> plots contain precomputed model curves and work without Python or internet. Changing simulation inputs requires the separate Streamlit app. The model is not calibrated to transient device measurements.</p>
<article><h2>Thermal response summary</h2><table><tr><th>Substrate</th><th>End of heating</th><th>End of cooling</th><th>90% of steady heating rise</th></tr>{summary_rows}</table></article><article><h2>1 · Heating response — diode ON</h2><p>Source switched on at t = 0 from the zero-power equilibrium state.</p>{on_html}</article><article><h2>2 · Cooling response — diode OFF</h2><p>Source switched off at t = 0; starts at the final ON temperature.</p>{off_html}</article><article><h2>Temperature field when power switches OFF</h2><p>Shared {palette} palette and temperature limits for fair comparison; each depth axis follows its own thickness.</p>{fields_html}</article><details><summary>Simulation settings and diagnostics</summary><pre>{source}</pre></details><p><small>Temperature-time trajectories from implicit transient finite-volume heat conduction. Power turns off instantaneously; stored heat in the substrate decays toward its zero-power state.</small></p></main></body></html>'''
