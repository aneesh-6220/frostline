"""Checks against the real downloaded NASA POWER file (hand-checked values)."""
import os, sys, unittest
import pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import northlink_metrics as m

df = pd.read_csv(os.path.join(ROOT, "data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
dettah = df[df.location_id == "dettah_bay"]

class T(unittest.TestCase):
    def test_first_ten_days_hand_check(self):
        # Hand check from the raw POWER file: Oct 1-10 2001, T2M = 4.85, 4.75, -1.13, -1.78, 0.5, 3.31, 4.45, 1.08, 1.4, 1.57
        first = dettah.sort_values("date").head(10)["temperature_c"].tolist()
        self.assertEqual(first, [4.85, 4.75, -1.13, -1.78, 0.5, 3.31, 4.45, 1.08, 1.4, 1.57])
        self.assertAlmostEqual(sum(max(0, -t) for t in first), 2.91, places=6)
    def test_all_seasons_complete(self):
        for loc, g in df.groupby("location_id"):
            for y in range(2001, 2025):
                c = m.season_coverage(g, y, "full")
                self.assertTrue(c.complete, (loc, y))
                self.assertEqual(c.expected, m.expected_days(y, "full"))
    def test_no_duplicate_dates(self):
        self.assertFalse(df.duplicated(["location_id", "date"]).any())
unittest.main() if __name__ == "__main__" else None
