# Test-API — QA Automation Workshop

A **teaching-oriented** Python REST API for the 8th-semester QA Automation
Workshop. It intentionally exposes:

- Positive and negative test surfaces
- Boundary and validation edge cases
- Predictable HTTP status codes
- A consistent error envelope
- A batch of **intentional defects** under `/buggy/*`
- Admin utilities for seeding and resetting state between test runs

Built with **FastAPI + Pydantic v2**, JSON file storage (no DB), and a
Postman collection wired for Collection Runner and Newman.

---

## 1. Setup and run

```powershell
cd Test-API
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/docs> for interactive Swagger, or
<http://127.0.0.1:8000/redoc> for ReDoc. Health check:
<http://127.0.0.1:8000/healthcheck>.

Logs are written to `logs/api.log`.

---

## 2. Contract summary

Every request body and every response body is a **JSON array**, even for
a single item. Failures use the standard error envelope:

```json
{
  "error": true,
  "message": "Duplicate Id found.",
  "details": { "conflicting_ids": [15] },
  "timestamp": "2026-08-01T12:34:56.789Z",
  "status": 409,
  "path": "/keys"
}
```

### Endpoint map

| Method | Path                        | Success | Purpose                            |
| ------ | --------------------------- | ------- | ---------------------------------- |
| GET    | `/healthcheck`              | 200     | Liveness probe                     |
| GET    | `/version`                  | 200     | Metadata (name/version)            |
| GET    | `/stats`                    | 200     | Record counts per store            |
| POST   | `/keys`                     | 201     | Generate keys                      |
| GET    | `/keys`                     | 200     | List all stored key requests       |
| GET    | `/keys/{id}`                | 200     | Fetch stored request by Id         |
| PUT    | `/keys/{id}`                | 200     | Full replace                       |
| PATCH  | `/keys/{id}`                | 200     | Partial update                     |
| DELETE | `/keys/{id}`                | 200     | Remove record                      |
| POST   | `/ranges`                   | 201     | Generate ranges                    |
| GET    | `/ranges`                   | 200     | List all                           |
| GET    | `/ranges/{id}`              | 200     | Fetch by Id                        |
| PUT    | `/ranges/{id}`              | 200     | Full replace                       |
| PATCH  | `/ranges/{id}`              | 200     | Partial update                     |
| DELETE | `/ranges/{id}`              | 200     | Remove record                      |
| POST   | `/matchscore`               | 201     | Compute score/decision             |
| GET    | `/matchscore`               | 200     | List all                           |
| GET    | `/matchscore/{id}`          | 200     | Fetch by Id                        |
| PUT    | `/matchscore/{id}`          | 200     | Full replace                       |
| PATCH  | `/matchscore/{id}`          | 200     | Partial update                     |
| DELETE | `/matchscore/{id}`          | 200     | Remove record                      |
| POST   | `/admin/seed`               | 201     | Load sample data                   |
| POST   | `/admin/reset`              | 200     | Clear every store                  |
| POST   | `/admin/reset/{store}`      | 200     | Clear one store                    |
| GET    | `/error/{code}`             | 4xx/5xx | Trigger any 4xx/5xx (teaching)     |
| GET    | `/error/boom`               | 500     | Unhandled exception (teaching)     |
| POST/GET/DELETE | `/buggy/*`         | varies  | Endpoints with intentional defects |

### Status codes returned

| Code | When                                                          |
| ---- | ------------------------------------------------------------- |
| 200  | Successful GET / PUT / PATCH / DELETE / healthcheck / version |
| 201  | Successful POST that creates a record                         |
| 400  | Empty array, duplicate Ids in body, mismatched path/body Id   |
| 404  | Id not found                                                  |
| 409  | Id already exists in the store                                |
| 422  | Pydantic validation error (bad types, wrong enum, too long)   |
| 500  | Unhandled exception (`/error/boom` or forced via `/error/500`)|

---

## 3. Learning objectives per endpoint

| Endpoint                        | Concept students practice                                     |
| ------------------------------- | ------------------------------------------------------------- |
| `GET /healthcheck`              | Smoke test, status code 200, response shape                   |
| `GET /version`, `GET /stats`    | Reading JSON, extracting values, environment variables        |
| `POST /keys`                    | Positive tests, JSON body, arrays, dynamic Ids                |
| `GET /keys/{id}`                | Chained requests, path variables                              |
| `GET /keys`                     | Pagination-ready collections, array assertions                |
| `PUT /keys/{id}` / `PATCH`      | Full vs partial updates, idempotency                          |
| `DELETE /keys/{id}`             | State cleanup, 404 after deletion                             |
| `POST /matchscore`              | Data-driven tests via CSV                                     |
| `POST /ranges`                  | Repeated positive pattern, comparing structures               |
| `/error/{code}`                 | Status-code drills, Collection Runner iterations              |
| `/error/boom`                   | Handling 500s in tests, logging                               |
| `/buggy/*`                      | Defect hunting, writing FAILING assertions to document bugs   |
| `/admin/seed`, `/admin/reset`   | Pre-request/setup/teardown, deterministic environments        |

---

## 4. Validation rules students can trip

- Body must be a non-empty **JSON array** → 400
- All fields must be present and correctly typed → 422
- `Id` must be an integer → 422
- Ids must be unique inside the body → 400
- Ids must be unique inside the store → 409
- `DataType` for `/keys` and `/ranges` must be `"A"` or `"N"` → 422
- `DataType` for `/matchscore` must be `"A"` or `"Name"` → 422
- `Data`, `Data1`, `Data2` are 1..200 characters → 422 outside range
- Extra fields (`extra="forbid"`) → 422
- Duplicate business content (same `Data + DataType`, different Ids) → 400
- Path Id must match body Id in `PUT` → 400

---

## 5. Standard error response

```json
{
  "error": true,
  "message": "<human message>",
  "details": <optional object|string|array>,
  "timestamp": "<ISO 8601 UTC>",
  "status": <int>,
  "path": "<request path>"
}
```

Every failure — validation, business, or unhandled — returns this shape.

---

## 6. Project layout

```
Test-API/
├── main.py                       # FastAPI factory + logging middleware
├── app.py                        # re-export
├── requirements.txt
├── README.md
├── POSTMAN_EXERCISES.md          # student exercises
├── routes/
│   ├── keys.py
│   ├── ranges.py
│   ├── matchscore.py
│   ├── health.py
│   ├── admin.py                  # seed / reset / version / stats / errors
│   └── buggy.py                  # intentional defects
├── models/
│   ├── common.py
│   ├── keys.py                   # KeyRequest / KeyPatch / KeyResponse
│   ├── ranges.py
│   ├── matchscore.py
│   └── health.py
├── services/
│   ├── key_generator.py
│   ├── range_generator.py
│   └── matcher.py
├── utils/
│   ├── file_storage.py           # save/get/list/delete/clear
│   ├── validators.py             # ensure_* helpers using APIError
│   ├── errors.py                 # APIError + error envelope + handlers
│   └── logging_config.py
├── data/                         # seed samples
│   ├── sample_keys.json
│   ├── sample_ranges.json
│   └── sample_matchscore.json
├── storage/                      # runtime JSON stores
│   ├── keys.json
│   ├── ranges.json
│   └── matchscore.json
├── logs/                         # generated at runtime
└── postman/
    ├── Test-API.postman_collection.json
    ├── Test-API.postman_environment.json
    ├── data-driven-matchscore.csv
    └── data-driven-status-codes.csv
```

---

## 7. Running the Postman collection

1. In Postman, **Import** both files from `postman/`.
2. Pick the environment "Test-API — Local" (top-right).
3. Start the API (`uvicorn main:app --reload`).
4. Click any request → **Send**.
5. Collection Runner:
   - Select the collection → **Run**.
   - Attach `data-driven-matchscore.csv` for request 09.
   - Attach `data-driven-status-codes.csv` for request 13.

### Newman (CLI)

```powershell
npm install -g newman newman-reporter-htmlextra
newman run postman/Test-API.postman_collection.json `
  -e postman/Test-API.postman_environment.json `
  -r cli,htmlextra `
  --reporter-htmlextra-export reports/newman-report.html
```

---

## 8. Intentional defects (`/buggy/*`)

| Path                              | Method | Hidden defect                                          |
| --------------------------------- | ------ | ------------------------------------------------------ |
| `/buggy/keys`                     | POST   | Accepts empty arrays instead of returning 400          |
| `/buggy/matchscore`               | POST   | Swaps `Data1` and `Data2` in the response              |
| `/buggy/matchscore/{id}`          | GET    | Returns `200` with `[]` when the Id is missing         |
| `/buggy/ranges/{id}`              | DELETE | Reports success even when nothing was deleted          |
| `/buggy/echo`                     | GET    | Leaks internal storage path and a fake secret token    |

Give students the endpoint list without the defects and ask them to
document each one.

---

## 9. Extensibility

Swap any of these three services without touching routes or models:

- `services/key_generator.py::generate_keys`
- `services/range_generator.py::generate_ranges`
- `services/matcher.py::score` (and `ACCEPT_THRESHOLD`)

---

## 10. See also

- `POSTMAN_EXERCISES.md` — progressive workshop exercises.
- `/docs` — Swagger UI with request/response examples.
