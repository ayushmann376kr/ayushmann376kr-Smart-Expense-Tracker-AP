import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app import create_app


class ExpenseApiTestCase(unittest.TestCase):
    def setUp(self):
        # Fresh temp JSON file per test so tests never interfere with each other.
        fd, self.db_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(self.db_path, "w") as f:
            json.dump([], f)
        self.app = create_app(storage_path=self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.db_path)

    def add(self, title="Coffee", amount=4.5, category="Food", date="2026-08-01"):
        return self.client.post(
            "/expenses",
            json={"title": title, "amount": amount, "category": category, "date": date},
        )

    # ---- Add expense ----

    def test_add_expense_success(self):
        resp = self.add()
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["title"], "Coffee")
        self.assertEqual(data["amount"], 4.5)
        self.assertEqual(data["category"], "Food")
        self.assertEqual(data["date"], "2026-08-01")
        self.assertIn("id", data)

    def test_add_expense_missing_title(self):
        resp = self.client.post(
            "/expenses", json={"amount": 4.5, "category": "Food", "date": "2026-08-01"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_add_expense_negative_amount(self):
        resp = self.add(amount=-5)
        self.assertEqual(resp.status_code, 400)

    def test_add_expense_zero_amount(self):
        resp = self.add(amount=0)
        self.assertEqual(resp.status_code, 400)

    def test_add_expense_non_numeric_amount(self):
        resp = self.add(amount="five dollars")
        self.assertEqual(resp.status_code, 400)

    def test_add_expense_bad_date_format(self):
        resp = self.add(date="08/01/2026")
        self.assertEqual(resp.status_code, 400)

    def test_add_expense_empty_body(self):
        resp = self.client.post("/expenses", json={})
        self.assertEqual(resp.status_code, 400)

    def test_add_expense_no_json_body(self):
        resp = self.client.post("/expenses")
        self.assertEqual(resp.status_code, 400)

    # ---- List / filter ----

    def test_list_expenses_empty(self):
        resp = self.client.get("/expenses")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), [])

    def test_list_expenses(self):
        self.add(title="Coffee", category="Food")
        self.add(title="Bus", category="Transport")
        resp = self.client.get("/expenses")
        self.assertEqual(len(resp.get_json()), 2)

    def test_filter_by_category(self):
        self.add(title="Coffee", category="Food")
        self.add(title="Lunch", category="Food")
        self.add(title="Bus", category="Transport")
        resp = self.client.get("/expenses?category=Food")
        data = resp.get_json()
        self.assertEqual(len(data), 2)
        self.assertTrue(all(e["category"] == "Food" for e in data))

    def test_filter_by_category_case_insensitive(self):
        self.add(title="Coffee", category="Food")
        resp = self.client.get("/expenses?category=food")
        self.assertEqual(len(resp.get_json()), 1)

    def test_filter_by_category_no_matches(self):
        self.add(title="Coffee", category="Food")
        resp = self.client.get("/expenses?category=Entertainment")
        self.assertEqual(resp.get_json(), [])

    # ---- Totals ----

    def test_total_overall_and_by_category(self):
        self.add(title="Coffee", amount=4.5, category="Food")
        self.add(title="Lunch", amount=10.5, category="Food")
        self.add(title="Bus", amount=2.0, category="Transport")
        resp = self.client.get("/expenses/total")
        data = resp.get_json()
        self.assertEqual(data["overall_total"], 17.0)
        self.assertEqual(data["by_category"]["Food"], 15.0)
        self.assertEqual(data["by_category"]["Transport"], 2.0)

    def test_total_empty(self):
        resp = self.client.get("/expenses/total")
        data = resp.get_json()
        self.assertEqual(data["overall_total"], 0)
        self.assertEqual(data["by_category"], {})

    def test_total_filtered_by_category(self):
        self.add(title="Coffee", amount=4.5, category="Food")
        self.add(title="Bus", amount=2.0, category="Transport")
        resp = self.client.get("/expenses/total?category=Food")
        data = resp.get_json()
        self.assertEqual(data["category"], "Food")
        self.assertEqual(data["total"], 4.5)

    def test_total_filtered_by_category_no_matches(self):
        resp = self.client.get("/expenses/total?category=Nonexistent")
        self.assertEqual(resp.get_json()["total"], 0)

    # ---- Get single expense ----

    def test_get_single_expense(self):
        created = self.add().get_json()
        resp = self.client.get(f"/expenses/{created['id']}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["id"], created["id"])

    def test_get_single_expense_not_found(self):
        resp = self.client.get("/expenses/does-not-exist")
        self.assertEqual(resp.status_code, 404)

    # ---- Delete ----

    def test_delete_expense(self):
        created = self.add().get_json()
        resp = self.client.delete(f"/expenses/{created['id']}")
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get("/expenses")
        self.assertEqual(resp.get_json(), [])

    def test_delete_expense_not_found(self):
        resp = self.client.delete("/expenses/does-not-exist")
        self.assertEqual(resp.status_code, 404)

    def test_delete_then_totals_update(self):
        created = self.add(amount=10).get_json()
        self.add(amount=5)
        self.client.delete(f"/expenses/{created['id']}")
        resp = self.client.get("/expenses/total")
        self.assertEqual(resp.get_json()["overall_total"], 5)

    # ---- Persistence across app instances (same file) ----

    def test_persists_to_file_across_app_instances(self):
        self.add(title="Coffee")
        second_app = create_app(storage_path=self.db_path)
        second_client = second_app.test_client()
        resp = second_client.get("/expenses")
        self.assertEqual(len(resp.get_json()), 1)


if __name__ == "__main__":
    unittest.main()
