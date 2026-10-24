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


def theme(fig, height=450):
    fig.update_layout(template='plotly_white', height=height, paper_bgcolor='white',
                      plot_bgcolor='#f7fafc', font=dict(family='Arial, sans-serif', size=13, color=INK),
                      margin=dict(l=62, r=34, t=75, b=65),
                      hoverlabel=dict(bgcolor=INK, font_color='white', font_size=13),
                      legend=dict(orientation='h', x=0, y=1.16, font_size=13),
                      modebar=dict(bgcolor='rgba(0,0,0,0)', color=MUTED),
                      hovermode='x unified')
    fig.update_xaxes(showline=True, linewidth=1, linecolor='#b4c6d4', showgrid=True, gridcolor='#e8edf2', zeroline=False)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='#b4c6d4', showgrid=True, gridcolor='#e8edf2', zeroline=False)
    return fig


def phase_plot(curves: tuple[Curve, Curve], phase: str, log_time=False, unit='C'):
    on = phase == 'on'
    fig = go.Figure()
    for curve, color, marker in zip(curves, COLORS, ['circle','square']):
        t = curve.on_s if on else curve.off_s
        c = curve.on_c if on else curve.off_c
        y = c if unit == 'C' else c + 273.15
        label = f'{curve.thickness_um:g} µm substrate'
        fig.add_trace(go.Scatter(x=t, y=y, name=label, mode='lines',
                                 line=dict(color=color, width=3.3),
                                 hovertemplate='Time: %{x:.5g} s<br>Surface: %{y:.3f} '+('°C' if unit=='C' else 'K')+'<extra>'+label+'</extra>'))
        fig.add_trace(go.Scatter(x=[t[-1]], y=[y[-1]], mode='markers',
                                 marker=dict(size=9,color=color,symbol=marker),
                                 showlegend=False, hoverinfo='skip'))
    if on:
        title = 'Turn ON  |  surface heating response'
        subtitle = 'Heat source switched on at t = 0; initially at zero-power thermal equilibrium'
    else:
        title = 'Turn OFF  |  surface cooling response'
        subtitle = 'Source set to zero at t = 0; starts from the final temperature field of the ON phase'
    theme(fig)
    fig.update_layout(title=dict(text=f'{title}<br><sup style="color:{MUTED}">{subtitle}</sup>', x=.005, font_size=20),
                      xaxis_title='Elapsed time since switching ('+'s)',
                      yaxis_title='Surface temperature (°C)' if unit=='C' else 'Surface temperature (K)')
    if log_time:
        fig.update_xaxes(type='log')
        for trace in fig.data:
            if len(trace.x) > 1 and trace.x[0] == 0:
                trace.x = trace.x[1:]
    return fig


def combined_plot(curves, settings):
    fig = make_subplots(rows=1, cols=2, subplot_titles=['Source ON','Source OFF'], horizontal_spacing=.13)
    for case, color in zip(curves, COLORS):
        label = f'{case.thickness_um:g} µm'
        for i,(t,y) in enumerate([(case.on_s,case.on_c),(case.off_s,case.off_c)],1):
            fig.add_trace(go.Scatter(x=t, y=y, mode='lines', line=dict(color=color,width=3),
                                     name=label, legendgroup=label, showlegend=i==1,
                                     hovertemplate='%{x:.5g} s<br>%{y:.2f} °C<extra>'+label+'</extra>'),row=1,col=i)
    theme(fig, 460)
    fig.update_layout(title='Transient β-Ga₂O₃ thermal response: switch ON vs switch OFF')
    for i in (1,2):
        fig.update_xaxes(title_text='Elapsed time (s)',row=1,col=i)
        fig.update_yaxes(title_text='Surface (°C)' if i==1 else None,row=1,col=i)
    return fig


def field_plot(curves: tuple[Curve,Curve]):
    fig = make_subplots(rows=1,cols=2, horizontal_spacing=.12,
                        subplot_titles=[f'{c.thickness_um:g} µm — end of heating' for c in curves])
    lo = min(float(c.final_on_field_c.min()) for c in curves)
    hi = max(float(c.final_on_field_c.max()) for c in curves)
    for i,c in enumerate(curves,1):
        fig.add_trace(go.Heatmap(x=c.x_um, y=c.z_um, z=c.final_on_field_c, zmin=lo,
                                 zmax=max(hi,lo+1.e-5),colorscale='Inferno',coloraxis='coloraxis',
                                 hovertemplate='Radius: %{x:.2f} µm<br>Depth: %{y:.2f} µm<br>Cell T: %{z:.2f} °C<extra></extra>'),row=1,col=i)
        fig.update_xaxes(title_text='Radius r (µm)',row=1,col=i)
        fig.update_yaxes(title_text='Depth z (µm)' if i==1 else None,autorange='reversed',row=1,col=i)
    theme(fig,450)
    fig.update_layout(title=dict(text='Temperature field at the instant of switch OFF',x=.005),
                      coloraxis=dict(colorscale='Inferno', cmin=lo, cmax=max(hi,lo+1.e-5),
                                     colorbar=dict(title='°C',thickness=14)))
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


def offline_html(curves,settings):
    on_html = pio.to_html(phase_plot(curves,'on'),include_plotlyjs=True,full_html=False,config={'displaylogo':False})
    off_html = pio.to_html(phase_plot(curves,'off'),include_plotlyjs=False,full_html=False,config={'displaylogo':False})
    fields_html = pio.to_html(field_plot(curves),include_plotlyjs=False,full_html=False,config={'displaylogo':False})
    summary_rows = ''.join(f'<tr><td>{c.thickness_um:g} µm</td><td>{c.end_on_c:.2f} °C</td><td>{c.end_off_c:.2f} °C</td><td>{format_time(c.summary()["rise_time_to_90pct_steady_s"])}</td></tr>' for c in curves)
    source = escape(json.dumps(as_records(curves,settings), indent=2))
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ga₂O₃ Transient Thermal Lab — Offline Report</title>
<style>body{{margin:0;background:#edf3f8;color:#142b42;font:16px -apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}}main{{max-width:1380px;margin:auto;padding:26px}}header{{background:#142b42;color:white;padding:32px;border-radius:17px;border-bottom:5px solid #00a5ae}}header h1{{margin:4px 0;font-size:36px}}header p{{color:#d4e5ef}}article{{background:white;border:1px solid #d8e1ec;border-radius:15px;padding:14px;margin:20px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #d4dfe9;text-align:left}}th{{background:#eff6fa}}.note{{padding:17px;background:#fff3d8;border-radius:9px;color:#6c4700}}small{{color:#617488}}details{{margin:24px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style></head><body><main><header><small style="color:#92e1e4">RAFAELDASQUIDMAN · SEMICONDUCTOR THERMAL MODELING</small><h1>Ga₂O₃ Transient Thermal Lab</h1><p>Offline interactive snapshot · Heat-up and cool-down of two diode substrates</p></header>
<p class="note"><strong>Offline preview:</strong> plots contain precomputed model curves and work without Python or internet. Changing simulation inputs requires the separate Streamlit app. The model is not calibrated to transient device measurements.</p>
<article><h2>Thermal response summary</h2><table><tr><th>Substrate</th><th>End of heating</th><th>End of cooling</th><th>90% of steady heating rise</th></tr>{summary_rows}</table></article><article>{on_html}</article><article>{off_html}</article><article>{fields_html}</article><details><summary>Simulation settings and diagnostics</summary><pre>{source}</pre></details><p><small>Temperature-time trajectories from implicit transient finite-volume heat conduction. Power turns off instantaneously; stored heat in the substrate decays toward its zero-power state.</small></p></main></body></html>'''
