# Postman Tests — Test-API

This document explains everything shipped in [postman/](postman/):

- What the collection covers (folder by folder, request by request)
- The Postman test scripts used to validate each response
- How to run the collection from the Postman app **and** from the CLI (Newman)
- How the two data-driven test flows work and how to run them
- Optional workshop exercises using the intentionally buggy endpoints

Related source of truth:

- API contract and rules → [README.md](README.md)
- App entry point → [main.py](main.py)
- Routes → [routes/keys.py](routes/keys.py), [routes/ranges.py](routes/ranges.py), [routes/matchscore.py](routes/matchscore.py), [routes/admin.py](routes/admin.py), [routes/buggy.py](routes/buggy.py), [routes/health.py](routes/health.py)
- Validators → [utils/validators.py](utils/validators.py)
- Error envelope → [utils/errors.py](utils/errors.py)

---

## 1. Files in `postman/`

| File | Purpose |
| --- | --- |
| [postman/Test-API.postman_collection.json](postman/Test-API.postman_collection.json) | The collection: all requests + test scripts |
| [postman/Test-API.postman_environment.json](postman/Test-API.postman_environment.json) | Environment with `baseUrl` and reserved test IDs |
| [postman/data-driven-matchscore.csv](postman/data-driven-matchscore.csv) | Iterations for the MatchScore data-driven test |
| [postman/data-driven-status-codes.csv](postman/data-driven-status-codes.csv) | Iterations for the error-status-code data-driven test |

Environment variables:

| Key | Default | Used by |
| --- | --- | --- |
| `baseUrl` | `http://127.0.0.1:8000` | Every request |
| `keyId` | `9001` | Keys CRUD |
| `rangeId` | `9002` | Ranges CRUD |
| `matchId` | `9003` | MatchScore CRUD |
| `conflictId` | `9099` | 409 conflict test |

---

## 2. Prerequisites

1. Start the API:

    ```powershell
    cd Test-API
    .\.venv\Scripts\Activate.ps1
    uvicorn main:app --reload
    ```

2. Import into Postman:
    - **Collections** → *Import* → select [postman/Test-API.postman_collection.json](postman/Test-API.postman_collection.json).
    - **Environments** → *Import* → select [postman/Test-API.postman_environment.json](postman/Test-API.postman_environment.json).
    - Choose environment "**Test-API - Local**" (top-right dropdown).

3. Optional (CLI): install Newman.

    ```powershell
    npm install -g newman newman-reporter-htmlextra
    ```

---

## 3. Collection layout (folder by folder)

The collection is intentionally ordered so it can be run end-to-end in the
**Collection Runner** without manual steps.

### 01 — Health & Metadata

| Request | Method | Expected | What the test asserts |
| --- | --- | --- | --- |
| `GET /healthcheck` | GET | 200 | Body is a 1-item array with `status: "Healthy"` and `message: "Health check passed"` |
| `GET /version` | GET | 200 | 1-item array; `name === "Test-API"`; `version` is a string |
| `GET /stats` | GET | 200 | 1-item array containing numeric counts for `keys`, `ranges`, `matchscore` |

### 02 — Setup: Reset stores

| Request | Method | Expected | Notes |
| --- | --- | --- | --- |
| `POST /admin/reset` | POST | 200 | Wipes every store so the run is deterministic |

### 03 — Keys (Positive CRUD)

Uses env var `keyId = 9001`.

| Request | Method | Expected | Key assertions |
| --- | --- | --- | --- |
| `POST /keys` (create) | POST | 201 | Response has `Keys` array; captured into collection var `lastKeys` |
| `POST /keys` (idempotent re-run) | POST | 201 | **Same payload works again** and returns the same `Keys` |
| `GET /keys` (list) | GET | 200 | List contains `keyId` |
| `GET /keys/{id}` | GET | 200 | Record round-trips with the correct `Id` / `DataType` |
| `PUT /keys/{id}` | PUT | 200 | New `Data` / `DataType` reflected in response |
| `PATCH /keys/{id}` | PATCH | 200 | Only patched field changed |
| `DELETE /keys/{id}` | DELETE | 200 | `deleted: true`, `store: "keys"` |

### 04 — Keys (Negative & Validation)

| Request | Method | Expected | Key assertions |
| --- | --- | --- | --- |
| `POST /keys []` | POST | 400 | Error envelope with `status: 400`, `path: "/keys"` |
| `POST /keys` duplicate Ids in body | POST | 400 | `details.duplicate_ids` populated |
| `POST /keys` invalid `DataType` | POST | 422 | Envelope with `status: 422`, `details` is an array |
| `POST /keys` extra field | POST | 422 | Pydantic `extra="forbid"` fires |
| `POST /keys` `Data` length 201 | POST | 422 | Length constraint fires (uses `pm.variables.set('longData', 'A'.repeat(201))` in a pre-request) |
| `POST /keys` same Id, different content (create) | POST | 201 | Seeds `conflictId` with `"ORIGINAL VALUE"` |
| `POST /keys` same Id, different content (conflict) | POST | 409 | `details.conflicts` reported |
| `GET /keys/999999` | GET | 404 | Envelope carries `error: true`, `status: 404` |
| `PUT /keys/{conflictId}` with body `Id: 12345` | PUT | 400 | `details.path_id` and `details.body_id` both present |
| `DELETE /keys/888888` | DELETE | 404 | 404 |

### 05 — Ranges (CRUD)

Uses env var `rangeId = 9002`. Covers `POST`, `GET`, `PATCH`, `DELETE`.
Key assertion for `POST`: every entry has both `Key` and `Value` and
`Key <= Value` (lexicographical bounds).

### 06 — MatchScore (CRUD & rules)

| Request | Expected | Key assertion |
| --- | --- | --- |
| Identical names | 201 | `Score === 100`, `Decision === "A"` |
| Very different names | 201 | `Decision === "R"`, `Score < 85` |
| `GET /matchscore/{id}` | 200 | Round-trips the record |
| Invalid `DataType` (`"N"`) | 422 | Pydantic rejects — allowed values are `"A"` and `"Name"` |

### 07 — Buggy endpoints (documenting defects)

Each test asserts the **correct** behavior. They are **expected to FAIL**
against the current implementation and are the defect log for
[routes/buggy.py](routes/buggy.py):

| Request | Correct behavior asserted | Actual (buggy) behavior |
| --- | --- | --- |
| `POST /buggy/keys []` | 400 | 201 with `[]` |
| `POST /buggy/matchscore` | Response `Data1 === request Data1` | Server swaps `Data1` and `Data2` |
| `GET /buggy/matchscore/{missing}` | 404 | 200 with `[]` |
| `DELETE /buggy/ranges/{missing}` | 404 | 200 `deleted: true` |
| `GET /buggy/echo` | No `storage_path` / `debug_token` fields | Leaks both |

### 08 — Data-Driven: MatchScore (CSV)

Single request iterated over
[postman/data-driven-matchscore.csv](postman/data-driven-matchscore.csv).
See §5 for how to run.

### 09 — Data-Driven: Error status codes (CSV)

Single request iterated over
[postman/data-driven-status-codes.csv](postman/data-driven-status-codes.csv).
See §5 for how to run.

### 10 — Teardown

`POST /admin/reset` to leave the API clean.

---

## 4. Test-script patterns used in this collection

The scripts stick to a small, teachable vocabulary.

### 4.1 Status-code assertion

```javascript
pm.test('Status is 201', function () {
    pm.response.to.have.status(201);
});
```

### 4.2 Response shape / values

```javascript
pm.test('Perfect match -> Score 100 / Decision A', function () {
    const body = pm.response.json();
    pm.expect(body).to.be.an('array').with.lengthOf(1);
    pm.expect(body[0]).to.include({ Score: 100, Decision: 'A' });
});
```

### 4.3 Standard error envelope (any failure)

```javascript
pm.test('Standard error envelope', function () {
    const body = pm.response.json();
    pm.expect(body).to.include({ error: true, status: 400 });
    pm.expect(body).to.have.property('timestamp');
    pm.expect(body).to.have.property('path', '/keys');
});
```

### 4.4 Sharing state between requests

```javascript
// after POST /keys
pm.collectionVariables.set('lastKeys', JSON.stringify(pm.response.json()[0].Keys));

// on the idempotent re-run
const previous = JSON.parse(pm.collectionVariables.get('lastKeys') || '[]');
pm.expect(pm.response.json()[0].Keys).to.eql(previous);
```

### 4.5 Pre-request scripts (dynamic data)

```javascript
// Used by "Data > 200 chars -> 422"
pm.variables.set('longData', 'A'.repeat(201));
```

### 4.6 Collection-level scripts

Two live at the collection root:

- **Pre-request**: sets `baseUrl` to `http://127.0.0.1:8000` if the
  environment forgot to.
- **Test**: asserts every response body is valid JSON. Combined with
  per-request status/body assertions, this gives you one line of defense
  against silent format regressions.

### 4.7 Reading CSV row values in tests

```javascript
const expectedDecision = pm.iterationData.get('expectedDecision');
const expectedMinScore = Number(pm.iterationData.get('expectedMinScore'));
```

---

## 5. Data-driven testing — end-to-end how-to

Postman's Collection Runner and Newman both iterate a request folder
once per row of a CSV/JSON file, exposing the row via
`pm.iterationData`. The request body substitutes `{{columnName}}`
placeholders from the same row.

### 5.1 The MatchScore CSV

File: [postman/data-driven-matchscore.csv](postman/data-driven-matchscore.csv)

```csv
iterationId,data1,data2,dataType,expectedDecision,expectedMinScore
600001,Bruce Wayne,Bruce Wayne,Name,A,85
600002,Bruce Wayne,BRUCE WAYNE,Name,A,85
600003,Bruce Wayne,Wayne Bruce,Name,R,0
600004,100 Park Avenue,100 Park Ave,A,A,85
600005,42 Elm Street,7 Oak Street,A,R,0
600006,Diana Prince,Wonder Woman,Name,R,0
```

How each column is used by request **08 — Data-Driven: MatchScore (CSV)**:

- `iterationId` → substituted into the JSON body as `Id`. Unique per row
  so multiple runs don't collide.
- `data1`, `data2`, `dataType` → substituted into the JSON body.
- `expectedDecision` → asserted against `body[0].Decision`.
- `expectedMinScore` → asserted against `body[0].Score` (minimum threshold).

Request body template:

```json
[
  {
    "Id": {{iterationId}},
    "Data1": "{{data1}}",
    "Data2": "{{data2}}",
    "DataType": "{{dataType}}"
  }
]
```

Test script:

```javascript
pm.test('Status is 201', function () { pm.response.to.have.status(201); });
const body = pm.response.json();
const expectedDecision = pm.iterationData.get('expectedDecision');
const expectedMinScore = Number(pm.iterationData.get('expectedMinScore'));
pm.test('Decision matches CSV expectation: ' + expectedDecision, function () {
    pm.expect(body[0].Decision).to.eql(expectedDecision);
});
pm.test('Score respects the CSV minimum: >= ' + expectedMinScore, function () {
    pm.expect(body[0].Score).to.be.at.least(expectedMinScore);
});
```

### 5.2 The Error-Codes CSV

File: [postman/data-driven-status-codes.csv](postman/data-driven-status-codes.csv)

```csv
errorCode
400
401
403
404
409
418
422
500
503
```

URL: `{{baseUrl}}/error/{{errorCode}}`. Each row is one request; the
test asserts `pm.response.code === Number(errorCode)` and that the
error envelope's `status` field agrees.

### 5.3 Running data-driven in the Postman app

1. Open the collection → click **Run**.
2. Select **only** the target folder (e.g. `08 - Data-Driven: MatchScore (CSV)`).
3. Under **Data**, click **Select File** and pick the matching CSV.
4. Postman auto-detects iterations = number of CSV rows.
5. Click **Preview** to sanity-check that column-to-variable mapping is right.
6. Click **Run Test-API - QA Workshop**.

Repeat for `09 - Data-Driven: Error status codes (CSV)` with the other CSV.

### 5.4 Running data-driven with Newman

```powershell
# MatchScore
newman run postman/Test-API.postman_collection.json `
  -e postman/Test-API.postman_environment.json `
  --folder "08 - Data-Driven: MatchScore (CSV)" `
  -d postman/data-driven-matchscore.csv `
  -r cli,htmlextra `
  --reporter-htmlextra-export reports/matchscore-dd.html

# Error codes
newman run postman/Test-API.postman_collection.json `
  -e postman/Test-API.postman_environment.json `
  --folder "09 - Data-Driven: Error status codes (CSV)" `
  -d postman/data-driven-status-codes.csv `
  -r cli,htmlextra `
  --reporter-htmlextra-export reports/errors-dd.html
```

### 5.5 Extending the CSVs

- Add a new row to grow a test suite; keep `iterationId` unique.
- Add a new column and reference it either in the request body
  (`{{newColumn}}`) or in the test script (`pm.iterationData.get('newColumn')`).
- CSV values are strings — cast with `Number(...)` when comparing numerics.

---

## 6. Running the full collection

### 6.1 Postman app (Collection Runner)

1. Select the collection → **Run**.
2. Leave every folder ticked **except** the two data-driven folders
   (they need a CSV attached — run them separately per §5.3).
3. Iterations = 1, Delay = 0.
4. Click **Run Test-API - QA Workshop**.

Expected result: every folder from 01–06 and 10 is fully green;
folder **07 — Buggy endpoints** shows 5 failing assertions, one per
documented defect.

### 6.2 Newman (CLI)

Full run excluding data-driven folders:

```powershell
newman run postman/Test-API.postman_collection.json `
  -e postman/Test-API.postman_environment.json `
  --folder "01 - Health & Metadata" `
  --folder "02 - Setup: Reset stores" `
  --folder "03 - Keys (Positive CRUD)" `
  --folder "04 - Keys (Negative & Validation)" `
  --folder "05 - Ranges (CRUD)" `
  --folder "06 - MatchScore (CRUD & rules)" `
  --folder "07 - Buggy endpoints (documenting defects)" `
  --folder "10 - Teardown" `
  -r cli,htmlextra `
  --reporter-htmlextra-export reports/full-report.html
```

Or simply run everything and let the two data-driven folders execute
once each (they use the current environment values for placeholders,
so they will still POST/GET but without CSV variety):

```powershell
newman run postman/Test-API.postman_collection.json `
  -e postman/Test-API.postman_environment.json `
  -r cli,htmlextra `
  --reporter-htmlextra-export reports/full-report.html
```

---

## 7. Idempotency note (important for automation)

`POST /keys`, `POST /ranges`, and `POST /matchscore` are now **idempotent
for identical payloads**: re-posting the same `Id` with the same content
returns 201 instead of 409. Re-posting the same `Id` with **different**
content still returns 409 (see the tests in folder 04 — "same Id,
DIFFERENT content").

Practical consequence: your Postman scripts can safely re-run without
mutating the `Id` between runs. The guard lives in
[utils/validators.py](utils/validators.py) as `ensure_ids_are_new_or_identical`.

---

## 8. Workshop exercises (optional)

The buggy folder is deliberately failing — that is the exercise.
Suggested progression:

1. **Discover**: Run folder 07 and read each failing assertion.
2. **Document**: For each failure, write in your own words what the bug is,
   what the expected behavior should be, and what business risk it carries.
3. **Reproduce with your own request**: Copy any buggy request into a new
   folder called *My Bug Reports*, tighten the assertion, and prove the bug.
4. **Fix**: Open [routes/buggy.py](routes/buggy.py) and rewrite each
   endpoint to match the real one; re-run folder 07 — it should now be
   fully green.

Bonus data-driven exercises:

- Add rows to [postman/data-driven-matchscore.csv](postman/data-driven-matchscore.csv)
  that test boundary cases (empty tokens, punctuation, mixed casing, exact
  85-score threshold).
- Add rows to [postman/data-driven-status-codes.csv](postman/data-driven-status-codes.csv)
  covering `418`, `451`, `599`, and edge codes like `399` (should be
  rejected — see [routes/admin.py](routes/admin.py) `raise_status`).

---

## 9. Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `ECONNREFUSED 127.0.0.1:8000` | API not running — start `uvicorn main:app --reload` |
| `baseUrl` is `undefined` in URL | No environment selected in Postman; select "Test-API - Local" |
| Data-driven request runs only once | CSV not attached; re-open the runner and *Select File* |
| `{{iterationId}}` appears literally in the request | Folder runner without a CSV; either attach one or pass `-d` in Newman |
| All buggy folder tests pass | You are pointing at a fixed version of `routes/buggy.py` — the workshop expects them to fail against the shipped code |
| 409 on second run | Payload differs from stored content; either seed a fresh `Id` or clear via `POST /admin/reset` |
