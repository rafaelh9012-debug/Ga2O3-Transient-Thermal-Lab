"""Rebuild offline HTML plus result CSV/JSON/ZIP without starting Streamlit.

Run from project root:
    python Python_Code/export_transient_results.py --output examples
"""
from pathlib import Path
import argparse
from dataclasses import replace
import json
from transient_model import TransientSettings, simulate_comparison, as_records
from visuals import offline_html, timeseries_frame, result_zip


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=Path('examples'))
    ap.add_argument('--power',type=float,default=500.0,help='W/cm²')
    ap.add_argument('--on-ms',type=float,default=300.0)
    ap.add_argument('--off-ms',type=float,default=300.0)
    ap.add_argument('--thickness-a',type=float,default=630.0)
    ap.add_argument('--thickness-b',type=float,default=50.0)
    ap.add_argument('--conductivity',choices=['frozen','temperature','constant'],default='frozen')
    ap.add_argument('--mesh',choices=['Fast','Balanced','Detailed'],default='Fast')
    ap.add_argument('--samples',type=int,default=55)
    args = ap.parse_args()
    s=TransientSettings(power_w_cm2=args.power,heating_s=args.on_ms*1e-3,
                        cooling_s=args.off_ms*1e-3,substrate_a_um=args.thickness_a,
                        substrate_b_um=args.thickness_b,conductivity=args.conductivity,
                        mesh_name=args.mesh,points_per_phase=args.samples)
    curves=simulate_comparison(s)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'Ga2O3_Transient_Offline.htm').write_text(offline_html(curves,s),encoding='utf-8')
    timeseries_frame(curves).to_csv(args.output/'temperature_timeseries.csv',index=False)
    (args.output/'transient_diagnostics.json').write_text(json.dumps(as_records(curves,s),indent=2),encoding='utf-8')
    (args.output/'Ga2O3_Transient_Results.zip').write_bytes(result_zip(curves,s))
    print('Outputs written to',args.output.resolve())
    for c in curves:
        print(f'{c.thickness_um:g} µm: ON end {c.end_on_c:.3f} °C, OFF end {c.end_off_c:.3f} °C')

if __name__=='__main__':
    main()
