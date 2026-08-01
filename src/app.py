import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, request

from src.storage import Storage

VALID_DATE_FMT = "%Y-%m-%d"


def create_app(storage_path=None):
    app = Flask(__name__)

    if storage_path is None:
        storage_path = os.environ.get("EXPENSES_DB_PATH", "expenses.json")
    storage = Storage(storage_path)
    app.storage = storage  # exposed for tests

    def error(message, status):
        return jsonify({"error": message}), status

    def validate_expense_payload(payload):
        
        if not isinstance(payload, dict):
            return None, "Request body must be a JSON object."

        title = payload.get("title")
        amount = payload.get("amount")
        category = payload.get("category")
        date_str = payload.get("date")

        if not isinstance(title, str) or not title.strip():
            return None, "'title' is required and must be a non-empty string."

        if not isinstance(category, str) or not category.strip():
            return None, "'category' is required and must be a non-empty string."

        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            return None, "'amount' is required and must be a number."
        if amount <= 0:
            return None, "'amount' must be greater than 0."

        if not isinstance(date_str, str):
            return None, "'date' is required and must be a string in YYYY-MM-DD format."
        try:
            datetime.strptime(date_str, VALID_DATE_FMT)
        except ValueError:
            return None, "'date' must be a valid date in YYYY-MM-DD format."

        cleaned = {
            "title": title.strip(),
            "amount": round(float(amount), 2),
            "category": category.strip(),
            "date": date_str,
        }
        return cleaned, None

    @app.route("/expenses", methods=["POST"])
    def add_expense():
        payload = request.get_json(silent=True)
        cleaned, err = validate_expense_payload(payload)
        if err:
            return error(err, 400)

        expense = {"id": str(uuid.uuid4()), **cleaned}
        storage.add(expense)
        return jsonify(expense), 201

    @app.route("/expenses", methods=["GET"])
    def list_expenses():
        category = request.args.get("category")
        expenses = storage.all()
        if category:
            expenses = [
                e for e in expenses if e["category"].lower() == category.lower()
            ]
        return jsonify(expenses), 200

    
    @app.route("/expenses/total", methods=["GET"])
    def get_total():
        category = request.args.get("category")
        expenses = storage.all()

        if category:
            filtered = [
                e for e in expenses if e["category"].lower() == category.lower()
            ]
            total = round(sum(e["amount"] for e in filtered), 2)
            return jsonify({"category": category, "total": total}), 200

        overall_total = round(sum(e["amount"] for e in expenses), 2)
        by_category = {}
        for e in expenses:
            by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]
        by_category = {k: round(v, 2) for k, v in by_category.items()}
        return jsonify({"overall_total": overall_total, "by_category": by_category}), 200

    @app.route("/expenses/<expense_id>", methods=["GET"])
    def get_expense(expense_id):
        expense = storage.get(expense_id)
        if expense is None:
            return error("Expense not found.", 404)
        return jsonify(expense), 200

    @app.route("/expenses/<expense_id>", methods=["DELETE"])
    def delete_expense(expense_id):
        deleted = storage.delete(expense_id)
        if not deleted:
            return error("Expense not found.", 404)
        return "", 204

    @app.errorhandler(404)
    def not_found(e):
        return error("Not found.", 404)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=8000)
