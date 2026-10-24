"""Backward-compatible imports for scripts that used the original visuals module.

The Streamlit app imports transient_visuals_v21 directly to avoid stale-module
name collisions during cloud code updates.
"""
from transient_visuals_v21 import (
    INK, MUTED, BG, ORANGE, TEAL, COLORS,
    HEATMAP_PALETTES, scientific_colorscale, theme, format_time, phase_plot,
    combined_plot, field_plot, timeseries_frame, result_zip, offline_html,
)
