# Baseline Lab Demo

A local interview MVP for preventive lab testing. The public site offers one fictional **Baseline Panel** for **$149 one time** at **Alder Draw Center**, a fictional draw partner. Staff fulfillment and the native iOS member app use the shared Flask backend. Use synthetic account and intake details.

## Setup and run

Run from the repository root with Python 3.12 and Node.js with npm. Flask is the only direct Python dependency.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm run demo:seed
npm start
```

Open the [public site](http://127.0.0.1:5050/), [member sign-in](http://127.0.0.1:5050/member), or [staff queue](http://127.0.0.1:5050/staff). The server binds to loopback. Use `npm start -- --port 5052` for a second local server. The app uses `instance/baseline.sqlite3` by default. The database and browser session signing key persist across restarts.

| Demo account | Email | Password |
| --- | --- | --- |
| Staff | `staff@example.test` | `BaselineStaffDemo-27!` |
| Prepared member, Casey Harper | `casey.harper@example.test` | `BaselineCaseyDemo-27!` |

The staff account and upcoming weekday slots are created on startup. Restarting the server or running the seed refreshes the upcoming slots and preserves existing bookings. The separate seed command prepares Casey’s two published draws on April 10 and October 16, 2025. Rerunning the seed preserves the same two orders, appointments, and reports. A new public signup always has its own baseline order at **Awaiting review**.

## Native iOS app

With the seeded backend running, install the Expo project dependencies and open it in the booted simulator:

```sh
npm --prefix mobile ci
npm run ios
```

The app uses the same member credentials listed above. [Simulator setup, rehearsal instructions, and screenshots](mobile/README.md)

## Fresh rehearsal database

Use a separate instance to rehearse signup and fulfillment again.

```sh
mkdir -p instance
export BASELINE_INSTANCE_DIR="$(mktemp -d "$PWD/instance/demo-XXXXXX")"
npm run demo:seed
npm start
```

The server prints the database path. To reopen that rehearsal, set `BASELINE_INSTANCE_DIR` to the directory containing the database before running `npm start`. `npm run demo:fresh` starts a separate empty instance for a signup-only run.

## Verify the staff and member handoff

1. Sign up through the public site with a new fictional email and password. Open staff and verify the new member appears with **Approve order** as the next action.
2. Open the case and approve the order. Sign in to the API with the new member’s credentials, list slots, and book one. Reload the staff case and member dashboard to see the same appointment.
3. In staff, choose **Mark collected** and **Import sample results**. Confirm that staff can open the draft and that the member’s report list, trends, and insights are empty. The member’s chat should say results are pending publication.
4. Choose **Publish results** and verify the member can fetch the report. Casey’s API account should still show just its own two reports.
5. Open Casey’s staff case for the interview. Ask the member API “What changed in my LDL cholesterol since my first test?” The sourced answer is a decrease of 38 mg/dL, from 142 on April 10 to 104 on October 16, 2025.

[API reference and copyable booking and chat commands](docs/member-api.md)

## Checks and exports

```sh
npm test
npm run build
```

The tests cover signup, the staff-to-member handoff, retry and slot contention, publication and ownership, token expiry and revocation, and trend and chat evidence. The default website build packages the runnable project and synthetic fixtures in `dist/baseline-web.zip`. `npm run build:web` selects the same target. `npm run build:ios` and `npm run build -- ios` export the iOS JavaScript bundle and assets to `dist/ios`.

## Schema and fulfillment handoff

- `members`, `intakes`, `consents`, `purchases`, and the baseline order are written together during signup. Each member can have one baseline and multiple follow-up orders. Separate `staff_users` records authorize staff browser sessions, and `member_tokens` stores hashes of expiring, revocable API bearer tokens.
- `orders` follow `awaiting_review` → `approved` → `booked` → `collected` → `results_imported` → `published`. SQLite rejects skipped or reversed status updates. The fulfillment service writes the appointment, collection timestamp, report draft, or publication timestamp in the same transaction as its corresponding status change.
- `draw_slots` is the draw center’s availability. `appointments` reserves one slot per order and one order per slot. `reports` holds one report per order and `report_measurements` holds normalized values and reference ranges. Startup migrates phase 1 databases in place, preserving prior records.
- `baseline/orders.py` and `baseline/fulfillment.py` provide the shared order and booking logic. `baseline/results.py` is the member-scoped source for published reports, trends, insights, and local guided chat. `baseline/api.py` exposes those services under `/api/v1`. The Jinja dashboard and API use the same member dashboard logic.

[Funnel research and design decisions](docs/signup-research.md)
