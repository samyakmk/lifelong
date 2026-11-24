# Baseline Lab Demo

A local interview demo for preventive lab testing. The public website, staff portal, web member portal, and Expo iOS app use one Flask backend and SQLite database.

## Setup and run

Run from the repository root with Python 3.12 and Node.js with npm.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix mobile ci
npm run demo:seed
npm start
```

The default server uses `http://127.0.0.1:5050` and stores data in `instance/baseline.sqlite3`. Staff and upcoming weekday draw slots are initialized at startup. The seed creates Casey Harper’s published draws on April 10 and October 16, 2025. Repeating the seed preserves her existing case.

| Demo account | Email | Password |
| --- | --- | --- |
| Staff | `staff@example.test` | `BaselineStaffDemo-27!` |
| Casey Harper | `casey.harper@example.test` | `BaselineCaseyDemo-27!` |

### Browser

Open these Chrome tabs in order. Using `localhost` for Casey keeps her cookie separate from the public signup and staff tabs on `127.0.0.1`. Both hostnames reach the same database.

```sh
open -a "Google Chrome" \
  http://127.0.0.1:5050/ \
  http://127.0.0.1:5050/staff \
  http://localhost:5050/member
```

Sign into staff and leave its queue open. Sign in as Casey on the third tab and open Results. Leave the first tab at the public offer with its member account signed out.

### iOS Simulator

Boot the iPhone simulator if needed, and start Metro in a separate terminal:

```sh
xcrun simctl list devices available
xcrun simctl boot 'iPhone 17 Pro'
xcrun simctl bootstatus 'iPhone 17 Pro' -b
npm run ios
```

If the device is already booted, skip the boot command. Sign in as Casey and open Results before the interview. The member session lasts 24 hours and is stored in SecureStore. For a server started on port 5055, launch Metro with `EXPO_PUBLIC_BASELINE_API_URL=http://127.0.0.1:5055/api/v1 npm run ios` and use port 5055 in the browser URLs too. [Simulator details and screenshots](mobile/README.md)

### Reset for another rehearsal

Stop your current Flask process, then create and seed a separate database:

```sh
mkdir -p instance
export BASELINE_INSTANCE_DIR="$(mktemp -d "$PWD/instance/demo-XXXXXX")"
npm run demo:seed
npm start
```

The server prints the database path. Set `BASELINE_INSTANCE_DIR` to the directory containing that database to reopen it later. To keep another loopback instance running, use `npm start -- --port 5055` for the fresh one. Sign in again on each prepared surface after switching databases.

## Four-scene interview checklist

1. **Public website.** Show the $149 Baseline Panel and Alder Draw Center. Use a new synthetic email, complete intake, and place the simulated order.
2. **Staff portal.** Refresh the queue and find the new signup at Awaiting review. Open Casey’s case and show the baseline and follow-up orders, appointments, collection dates, and published reports.
3. **Web member portal.** Switch to Casey’s prepared Results tab. Open Trends and show LDL at **142 mg/dL on April 10, 2025** and **104 mg/dL on October 16, 2025**. Read the LDL insight, then ask **“What changed in my LDL cholesterol since my first test?”** in Chat. Point to the two report sources for the **38 mg/dL decrease**.
4. **iOS Simulator.** Switch to Casey’s prepared iOS Results. Show the published report, the same trend and insight, and the answer with the same source values and dates.

Finish each scene before switching surfaces. Run the fulfillment walkthrough separately so the interview can use Casey’s finished reports.

## Verification walkthroughs

1. **Browser fulfillment.** Create a fresh member in public signup, approve the order in staff, and use **Book a draw** on the member Home screen. Check the booking confirmation and the staff appointment. Mark collected and import the sample report in staff. Confirm the member Results page says **Reports pending**. Publish in staff, then reload Results and open the saved report.
2. **Cross-surface parity.** Sign in as Casey on web and iOS and compare her report, LDL trend, insight, and Chat response against the dates and values above. Create a separate synthetic member, approve their order in staff, and book in iOS. Refresh that member’s web Home and booking pages and the staff case to verify the same location and time.

## What is simulated

The Baseline Panel is a fictional $149 offer. Checkout records a simulated purchase. Appointments are local demo slots for Alder Draw Center. Staff actions simulate collection and report publication. The sample fixtures and prepared reports contain synthetic measurements and reference ranges. Guided Chat answers from that member’s published measurements in SQLite.

The seven web pages are `/`, `/join`, `/staff`, `/staff/members/<id>`, `/member`, `/member/book`, and `/member/results`. The four iOS screens are Sign in, Home, Book a draw, and Results.

## Checks and exports

```sh
npm test
npm --prefix mobile run typecheck
npm run build
npm run build:ios
```

The tests cover signup, booking, publication, CSRF, member ownership, token expiry, and report parity. The default website build packages Flask and the synthetic fixtures in `dist/baseline-web.zip`. The iOS build exports the JavaScript bundle and assets to `dist/ios`.

## Schema and service handoff

- `members`, `intakes`, `consents`, `purchases`, and the baseline order are written together during signup. Each member can have one baseline and multiple follow-up orders. Separate `staff_users` records authorize staff sessions. `member_tokens` stores hashes of expiring, revocable API bearer tokens.
- Orders follow `awaiting_review` → `approved` → `booked` → `collected` → `results_imported` → `published`. SQLite rejects skipped or reversed status updates. The fulfillment service writes each stage’s appointment, collection timestamp, report draft, or publication timestamp in the same transaction as the status change.
- `draw_slots` holds draw-center availability. `appointments` reserves one slot per order and one order per slot. `reports` holds one report per order. `report_measurements` stores values, units, and reference ranges. Startup migrates phase 1 databases in place.
- The web member portal and iOS API use the same dashboard, slot and booking services, published reports, trend and insight calculations, and guided chat. Drafts are visible to staff until publication.

[Member API reference](docs/member-api.md) · [Public funnel research](docs/signup-research.md)
