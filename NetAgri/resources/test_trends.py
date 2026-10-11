from django.test import SimpleTestCase

from .trends import monthly_summary


class TrendTests(SimpleTestCase):
    def test_monthly_average_and_annual_totals(self):
        daily = {
            "time": ["2023-01-10", "2023-01-20", "2024-01-05", "2024-02-01"],
            "temperature_2m_mean": [10.0, 14.0, 12.0, None],
            "precipitation_sum": [30.0, 10.0, 20.0, None],
        }
        rows, annual = monthly_summary(daily)
        jan, feb = rows[0], rows[1]
        self.assertEqual((jan["month"], jan["temp"], jan["rain"]), ("Jan", 12.0, 30))  # (40 + 20) / 2
        self.assertEqual((feb["temp"], feb["rain"]), (None, None))
        self.assertEqual(annual, [{"year": 2023, "rain": 40}, {"year": 2024, "rain": 20}])
