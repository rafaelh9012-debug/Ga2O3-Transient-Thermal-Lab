"""Regression checks for scientific Plotly presentation and export paths.

These tests do not replace a browser-level Streamlit QA pass.
"""
import io
import unittest
import zipfile
import numpy as np

from transient_model import TransientSettings, simulate_comparison
from visuals import (HEATMAP_PALETTES, field_plot, phase_plot, offline_html,
                     result_zip, scientific_colorscale, timeseries_frame)


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = TransientSettings(power_w_cm2=150., heating_s=.04,
                                         cooling_s=.04, points_per_phase=20)
        cls.curves = simulate_comparison(cls.settings)

    def test_turbo_default_is_literal_rgb(self):
        fig = field_plot(self.curves)
        self.assertEqual(len(fig.data), 2)
        self.assertTrue(all(t.coloraxis == 'coloraxis' for t in fig.data))
        self.assertTrue(all(t.zsmooth is False for t in fig.data))
        self.assertTrue(all(c.startswith('rgb(') for _, c in fig.layout.coloraxis.colorscale))
        self.assertEqual(fig.layout.coloraxis.cmin, min(float(c.final_on_field_c.min()) for c in self.curves))
        self.assertEqual(fig.layout.coloraxis.cmax, max(float(c.final_on_field_c.max()) for c in self.curves))
        self.assertTrue(fig.layout.coloraxis.showscale)

    def test_separate_color_axes_have_local_limits(self):
        fig = field_plot(self.curves, 'Turbo', shared_scale=False)
        self.assertFalse(fig.layout.coloraxis.showscale)
        self.assertTrue(all(t.coloraxis is None for t in fig.data))
        for trace, curve in zip(fig.data, self.curves):
            self.assertAlmostEqual(trace.zmin, float(curve.final_on_field_c.min()))
            self.assertAlmostEqual(trace.zmax, float(curve.final_on_field_c.max()))
            self.assertTrue(trace.colorbar is not None)

    def test_alternative_palettes_preserve_rgb(self):
        for name in HEATMAP_PALETTES:
            with self.subTest(name=name):
                scale = scientific_colorscale(name)
                self.assertTrue(all(v.startswith('rgb(') for _, v in scale))
                self.assertTrue(all(0 <= p <= 1 for p, _ in scale))
                field_plot(self.curves, palette=name)
        with self.assertRaises(ValueError):
            field_plot(self.curves, palette='unknown')

    def test_time_charts_do_not_stack_plot_titles_and_legends(self):
        for phase in ('on', 'off'):
            with self.subTest(phase=phase):
                fig = phase_plot(self.curves, phase)
                self.assertFalse(fig.layout.title.text)
                self.assertGreaterEqual(fig.layout.margin.t, 56)
                self.assertEqual(fig.layout.legend.orientation, 'h')
                self.assertEqual(len(fig.data), 4)
                lg = phase_plot(self.curves, phase, log_time=True)
                self.assertEqual(lg.layout.xaxis.type, 'log')
                self.assertTrue(all(min(t.x) > 0 for t in lg.data))

    def test_temperatures_have_expected_spatial_direction(self):
        for c in self.curves:
            # Heat source is beneath the center contact, not the outer rim.
            self.assertGreater(c.final_on_field_c[0, 0], c.final_on_field_c[0, -1])

    def test_csv_zip_and_static_browser_artifact(self):
        frame = timeseries_frame(self.curves)
        self.assertGreater(len(frame), 40)
        self.assertTrue(np.isfinite(frame['surface_temp_C']).all())
        with zipfile.ZipFile(io.BytesIO(result_zip(self.curves, self.settings))) as z:
            self.assertIn('temperature_timeseries.csv', z.namelist())
            self.assertIn('parameters_diagnostics.json', z.namelist())
        html = offline_html(self.curves, self.settings)
        self.assertIn('Plotly.newPlot', html)
        self.assertIn('Heating response', html)
        self.assertIn('Cooling response', html)
        self.assertIn('rgb(48,18,59)', html)  # Turbo low endpoint
        self.assertIn('Shared Turbo palette', html)


if __name__ == '__main__':
    unittest.main()
