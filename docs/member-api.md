# Member JSON API

Base URL for local development is `http://127.0.0.1:5050/api/v1`. Send `Content-Type: application/json` with request bodies. Every endpoint except sign-in requires `Authorization: Bearer <access_token>`. Tokens are opaque, expire after 24 hours, and are revoked individually on sign-out. The API uses the same member accounts as web sign-in.

| Method and path | Request | Successful response |
| --- | --- | --- |
| `POST /auth/sign-in` | `{"email":"…","password":"…"}` | `access_token`, `token_type` (`Bearer`), and UTC `expires_at` |
| `POST /auth/sign-out` | Bearer token | `204` |
| `GET /member` | Bearer token | `member` (ID, name, email), latest `order`, `next_step` (title and detail), and `appointment`. Order, next step, and appointment can be null. |
| `GET /member/slots` | Optional `?order_id=3`, defaults to the latest order | `order_id`, `status`, `draw_center` (name, address, timezone), and `slots` (ID and UTC start time). Slots are offered for approved orders. |
| `POST /member/book` | `{"order_id":3,"slot_id":1}` | `appointment` (ID, order and slot IDs, start time, draw center and visit prep). Retrying the same booking returns the same record. |
| `GET /member/reports` | Bearer token | `reports`, oldest collection first |
| `GET /member/reports/{id}` | Published report ID | `report` |
| `GET /member/trends` | Bearer token | `trends` with marker code, name, unit, dated points, and a nullable first-to-last `change` |
| `GET /member/insights` | Bearer token | `insights` with marker code, name, factual summary, change, and source points |
| `GET /member/chat` | Bearer token | `suggestions` for guided Q&A |
| `POST /member/chat` | `{"question":"What changed in my LDL cholesterol since my first test?"}` | `kind`, `answer`, `sources`, and `suggestions` |

Each report includes an ID, order ID, draw kind, collection date at the draw center, import and publication timestamps, summary, and measurements. Measurements include a stable code, name, group, value, unit, nullable reference bounds, and a reference flag of `below`, `within`, `above`, or `unavailable`. Trend and chat source points also carry the collection date, report ID, and order ID. A change has a signed `delta`, `unit`, and `direction` of `increased`, `decreased`, or `stable`. Trends group points by marker code and matching unit and compute changes only across comparable values.

Chat answers latest values, comparable change over time, and reference-range questions based on published measurements. Reference-range questions default to the latest draw and can specify the first. Insufficient data and unsupported questions are normal chat responses with an explanatory answer and suggestions.

Errors have the form `{"error":{"code":"order_not_approved","message":"This order must be approved before booking."}}`. Use `400` for invalid input, `401` for failed sign-in or a missing, expired, or revoked bearer token, `404` for an unavailable or inaccessible order or report, and `409` for an invalid booking state or unavailable slot. Draft reports are private to staff and a request for one from the member API returns `404`.

## Book the new member

After public signup and staff approval, use the new member’s synthetic credentials. Replace the sample sign-in values with the ones used at signup.

```sh
BASELINE_API=http://127.0.0.1:5050/api/v1
BASELINE_TOKEN=$(curl -fsS "$BASELINE_API/auth/sign-in" \
  -H 'Content-Type: application/json' \
  -d '{"email":"fresh@example.test","password":"your-demo-password"}' \
  | .venv/bin/python -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')

BASELINE_BOOKING=$(curl -fsS "$BASELINE_API/member/slots" -H "Authorization: Bearer $BASELINE_TOKEN" \
  | .venv/bin/python -c 'import json, sys; data=json.load(sys.stdin); print(json.dumps({"order_id":data["order_id"], "slot_id":data["slots"][0]["id"]}))')
curl -fsS "$BASELINE_API/member/book" -H "Authorization: Bearer $BASELINE_TOKEN" \
  -H 'Content-Type: application/json' -d "$BASELINE_BOOKING"
curl -fsS "$BASELINE_API/member" -H "Authorization: Bearer $BASELINE_TOKEN"
```

After staff imports the draft, run the next command. It should return an empty list before publication and the saved report once staff publishes it.

```sh
curl -fsS "$BASELINE_API/member/reports" -H "Authorization: Bearer $BASELINE_TOKEN"
```

## Ask about the prepared member’s LDL change

Run `npm run demo:seed` on the instance served by the API first.

```sh
BASELINE_API=http://127.0.0.1:5050/api/v1
BASELINE_CASEY_TOKEN=$(curl -fsS "$BASELINE_API/auth/sign-in" \
  -H 'Content-Type: application/json' \
  -d '{"email":"casey.harper@example.test","password":"BaselineCaseyDemo-27!"}' \
  | .venv/bin/python -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')

curl -fsS "$BASELINE_API/member/chat" -H "Authorization: Bearer $BASELINE_CASEY_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What changed in my LDL cholesterol since my first test?"}'
curl -fsS "$BASELINE_API/member/trends" -H "Authorization: Bearer $BASELINE_CASEY_TOKEN"
```

Expect the two source reports dated `2025-04-10` and `2025-10-16`, LDL values of 142 and 104 mg/dL, and a change of −38 mg/dL.
