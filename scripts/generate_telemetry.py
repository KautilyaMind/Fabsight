from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from fabsight.simulation import generate_telemetry,save_telemetry  # noqa:E402
if __name__=="__main__":
 p=argparse.ArgumentParser(); p.add_argument("--runs",type=int,default=2000); a=p.parse_args(); runs,readings=generate_telemetry(a.runs); save_telemetry(runs,readings); print(f"Generated {len(runs)} synthetic telemetry runs and {len(readings)} time-series readings.\nThese are arbitrary-scale educational simulation relationships, not production specifications.")
