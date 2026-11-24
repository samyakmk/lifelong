# Baseline Lab Demo

Phase 1 of a local interview MVP for preventive lab testing. The public site offers one fictional **Baseline Panel** for **$149 one time** at **Alder Draw Center**, a fictional draw partner. Use synthetic account and intake details.

## Setup and run

Run these commands from this repository’s root. This project uses Python 3.12 and Node.js with npm. Flask is the only direct Python dependency. npm runs commands without installing frontend dependencies.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm start
```

Open [http://127.0.0.1:5050](http://127.0.0.1:5050). The server binds to loopback. Visit **Get started**, finish the three steps, and confirm the dashboard shows **Awaiting review**. To sign back in, use the credentials you just created at [/member](http://127.0.0.1:5050/member). To switch ports, run `npm start -- --port 5051`.

The server initializes `instance/baseline.sqlite3` and stores the local session signing key beside it. Both persist across restarts. The app needs no external services or environment file.

## Fresh demo database

Stop the running server with Ctrl+C, then run:

```sh
npm run demo:fresh
```

This starts the same site on port 5050 with a new, empty database under `instance/demo-*/`. Previous data stays in its original directory. The server prints the database path at startup. To reopen a particular demo later, replace the sample directory below with the one printed by the server:

```sh
BASELINE_INSTANCE_DIR=instance/demo-REPLACE_ME npm start
```

## Checks and exports

```sh
npm test
npm run build
```

The default build packages the runnable Flask project in `dist/baseline-web.zip`, with the same setup instructions and without local database files, the virtual environment, or environment files. `npm run build:web` selects the same target.

`npm run build:ios` and `npm run build -- ios` reserve the iOS target. Phase 3 will add the native Expo client in `mobile/`. The root command delegates to the mobile package’s `export:ios` script once that client exists.

## Schema and fulfillment handoff

- `members` stores the normalized email and Werkzeug password hash. `intakes` captures the three demo answers, and `consents` records the version, accepted text, and timestamp.
- `purchases` stores the plan and simulated amount. A unique checkout key makes a retried signup idempotent. The baseline order, purchase, member, intake, and consent commit together.
- `orders` belongs to a member, a purchase owned by that member, and a draw center. Each member can have one baseline and multiple follow-up orders. `appointments` and `reports` each attach to one order. Store the collection timestamp on the order and use the report’s publication timestamp to gate report access. A member can accrue multiple published reports on different orders.
- The order starts at `awaiting_review` and progresses through `approved` → `booked` → `collected` → `results_imported` → `published`. SQLite checks the status values and rejects out-of-sequence updates. Later workflow services should update orders and related appointment or report records in the same transaction.
- `baseline/accounts.py` owns account creation and password verification. `baseline/orders.py` reads order state for an authenticated member ID. Flask routes, templates, and browser assets live under `baseline/web/`. Phase 2 can call the same account and order logic from a JSON API with its own mobile token sessions. Phase 3 can use that API and the same stored credentials.
- The browser uses an HTTP-only, same-site signed session cookie and server-checked CSRF tokens for POSTs. The dashboard takes its member ID from the session. This local phase ends at order review.

[Funnel research and design decisions](docs/signup-research.md)
