import unittest
import logging
from erm_autofiller import ERMAutofiller, NA_FLAG

class TestERMAutofiller(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.df_rad = {
            "AuthorizedAmount": {"value": 100000.0, "source": "RAD"},
            "BilledToDateAmount": {"value": 75000.0, "source": "RAD"},
            "AwardNumber": {"value": "12345", "source": "RAD"}
        }
        self.df_sharepoint_clean = {
            "ID": {"value": 1, "source": "Sharepoint PI request form"},
            "AwardNumber": {"value": "12345", "source": "Sharepoint PI request form"}
        }
        self.mod_id = 1

        self.autofiller = ERMAutofiller(self.df_rad, self.df_sharepoint_clean, self.mod_id)

    def test_ri1(self):
        result = self.autofiller.ri1()
        expected = {
            "val": NA_FLAG,
            "notes": "SFI current not possible with current data."
        }
        self.assertEqual(result, expected)

    def test_ri2(self):
        result = self.autofiller.ri2()
        expected = {
            "val": "$25000.00",
            "notes": "Calculated as Total Authorized ($100000.00) minus Billed to Date ($75000.00)."
        }
        self.assertEqual(result, expected)

    def test_ri3(self):
        result = self.autofiller.ri3()
        expected = {
            "val": "NO",
            "notes": "NO, because Billed to Date ($75000.00) is not greater than Total Authorized Amount ($100000.00)."
        }
        self.assertEqual(result, expected)

    def test_ri4(self):
        result = self.autofiller.ri4()
        expected = {
            "val": "YES",
            "notes": "YES, because Award Balance ($25000.00) is greater than or equal to 25% of Total Authorized Amount ($100000.00)."
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    unittest.main()