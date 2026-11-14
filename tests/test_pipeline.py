"""Pipeline smoke test with a SYNTHETIC file in the documented POWER CSV layout (layout not yet checked against a real download)."""
import os, subprocess, sys, tempfile, unittest
import pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), "..")

class T(unittest.TestCase):
    def test_roundtrip(self):
        d = tempfile.mkdtemp()
        f = os.path.join(d, "power_daily_T2M_testloc.csv")
        days = pd.date_range("2001-10-01", "2002-03-31")
        with open(f, "w") as fh:
            fh.write("NASA/POWER synthetic\n-BEGIN HEADER-\nx\n-END HEADER-\nYEAR,MO,DY,T2M\n")
            for i, x in enumerate(days):
                t = -999 if i == 10 else -10.0
                fh.write(f"{x.year},{x.month},{x.day},{t}\n")
        out = os.path.join(d, "o.csv"); aud = os.path.join(d, "a.csv")
        subprocess.check_call([sys.executable, "-I", os.path.join(ROOT, "scripts/build_nasa_daily_temperature.py"), f, "-o", out])
        o = pd.read_csv(out)
        self.assertEqual(len(o), 182)
        self.assertEqual(o["temperature_c"].isna().sum(), 1)
        subprocess.check_call([sys.executable, "-I", os.path.join(ROOT, "scripts/audit_daily_temperature.py"), out, aud])
        a = pd.read_csv(aud)
        self.assertFalse(bool(a.loc[0, "included_in_trend"]))
        self.assertEqual(a.loc[0, "valid_days"], 181)
unittest.main() if __name__ == "__main__" else None
