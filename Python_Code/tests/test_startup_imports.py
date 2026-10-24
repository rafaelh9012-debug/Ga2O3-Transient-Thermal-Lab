"""Cloud startup import regression tests.

The older visuals module can remain loaded across Streamlit reloads, so the
app imports a versioned module directly. This test checks the precise symbols
imported by the entrypoint, without requiring a Streamlit server.
"""
import ast
from pathlib import Path
import unittest

import transient_visuals_v21 as presentation

ROOT = Path(__file__).resolve().parents[1]

class StartupImportTests(unittest.TestCase):
    def test_app_imports_resolve(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [item for node in tree.body if isinstance(node, ast.ImportFrom)
                   and node.module == "transient_visuals_v21" for item in node.names]
        self.assertGreaterEqual(len(imports), 7)
        for item in imports:
            with self.subTest(name=item.name):
                self.assertTrue(hasattr(presentation, item.name),
                                f"Cannot import {item.name} from transient_visuals_v21")

    def test_export_imports_resolve(self):
        source = (ROOT / "export_transient_results.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [item for node in tree.body if isinstance(node, ast.ImportFrom)
                   and node.module == "transient_visuals_v21" for item in node.names]
        self.assertEqual({item.name for item in imports},
                         {"offline_html", "timeseries_frame", "result_zip"})
        for item in imports:
            self.assertTrue(hasattr(presentation, item.name))

    def test_previous_module_remains_compatible(self):
        from visuals import phase_plot, field_plot, HEATMAP_PALETTES
        self.assertIs(phase_plot, presentation.phase_plot)
        self.assertIs(field_plot, presentation.field_plot)
        self.assertIn("Turbo", HEATMAP_PALETTES)

if __name__ == "__main__":
    unittest.main()
