import unittest
from datetime import date, timedelta
from app import compute_aging_bucket

class TestAgingBucket(unittest.TestCase):
    def test_current_due_future(self):
        self.assertEqual(compute_aging_bucket(date.today() + timedelta(days=1)), "Current")
    def test_current_due_today(self):
        self.assertEqual(compute_aging_bucket(date.today()), "Current")
    def test_0_30(self):
        self.assertEqual(compute_aging_bucket(date.today() - timedelta(days=7)), "0-30")
    def test_31_60(self):
        self.assertEqual(compute_aging_bucket(date.today() - timedelta(days=45)), "31-60")
    def test_61_90(self):
        self.assertEqual(compute_aging_bucket(date.today() - timedelta(days=75)), "61-90")
    def test_90_plus(self):
        self.assertEqual(compute_aging_bucket(date.today() - timedelta(days=120)), "90+")

if __name__ == "__main__":
    unittest.main()
