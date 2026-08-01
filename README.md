# Smart Expense Tracker API

A small REST API for tracking personal expenses: add, list, filter by
category, total (overall and by category), and delete.

**Stack:** Python 3 + Flask. Data is persisted to a local JSON file
(`expenses.json`, created automatically on first run) so it survives a
server restart — no database required.

## Project structure

```
src/            application code (Flask app + storage layer)
tests/          test suite (Python's built-in unittest)
requirements.txt
README.md
AI_NOTES.md
```

## Install

From the repo root, on a clean checkout:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the server

```bash
python3 -m src.app
```

The server starts on `http://localhost:8000`. To use a different port or
storage file:

```bash
EXPENSES_DB_PATH=my_expenses.json python3 -m src.app
```

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

Tests use Flask's built-in test client and a temporary JSON file per test,
so they don't touch `expenses.json` or require the server to be running.

## API reference

All request/response bodies are JSON. Dates are `YYYY-MM-DD` strings.

| Method | Path | Description |
|---|---|---|
| `POST` | `/expenses` | Add an expense |
| `GET` | `/expenses` | List all expenses |
| `GET` | `/expenses?category=Food` | List expenses filtered by category (case-insensitive) |
| `GET` | `/expenses/<id>` | Get a single expense |
| `DELETE` | `/expenses/<id>` | Delete an expense |
| `GET` | `/expenses/total` | Overall total + totals broken down by category |
| `GET` | `/expenses/total?category=Food` | Total for one category |

### Add an expense

```
POST /expenses
Content-Type: application/json

{
  "title": "Coffee",
  "amount": 4.5,
  "category": "Food",
  "date": "2026-08-01"
}
```

`201 Created` with the stored expense (server-generated `id` included).
`400 Bad Request` if `title`/`category` are missing or empty, `amount` is
not a positive number, or `date` isn't a valid `YYYY-MM-DD` string.

### Totals

```
GET /expenses/total
```

```json
{
  "overall_total": 17.0,
  "by_category": { "Food": 15.0, "Transport": 2.0 }
}
```

```
GET /expenses/total?category=Food
```

```json
{ "category": "Food", "total": 15.0 }
```

### Delete

```
DELETE /expenses/<id>
```

`204 No Content` on success, `404 Not Found` if the id doesn't exist.

## Design notes / trade-offs

- **IDs** are server-generated UUIDs (not client-supplied) to avoid
  collisions and keep delete/lookup unambiguous.
- **Storage** re-reads/re-writes the whole JSON file per request. Simple
  and correct at the scale this is meant for; wouldn't scale to a large
  dataset or high write concurrency, but nothing in the assignment calls
  for that, and swapping in a real DB later would only mean rewriting
  `src/storage.py`.
- **Validation** is hand-rolled (no Pydantic/Marshmallow) to keep the
  dependency list to just Flask.
- Category filtering is case-insensitive on the assumption that's the more
  forgiving/expected behavior for a personal tool.
