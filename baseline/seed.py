from datetime import date, datetime, time, timedelta

from .accounts import Signup, create_member
from .catalog import PLAN
from .demo_identity import PREPARED_EMAIL, PREPARED_PASSWORD
from .fulfillment import apply_staff_step, fixture, save_appointment
from .orders import member_orders
from .schedule import DRAW_ZONE, timestamp

BASELINE_CHECKOUT = "prepared-demo-baseline-v1"
FOLLOW_UP_CHECKOUT = "prepared-demo-follow-up-v1"


def create_follow_up(db, member_id, center_id):
    purchase_id = db.execute(
        "INSERT INTO purchases (member_id, checkout_key, plan_code, amount_cents) VALUES (?, ?, ?, ?)",
        (member_id, FOLLOW_UP_CHECKOUT, PLAN.code, PLAN.amount_cents),
    ).lastrowid
    db.execute(
        """INSERT INTO orders (member_id, purchase_id, draw_center_id, kind)
           VALUES (?, ?, ?, 'follow_up')""",
        (member_id, purchase_id, center_id),
    )


def complete_draw(db, member_id, order, sample, prepared):
    day = date.fromisoformat(prepared["collection_date"])
    visit = datetime.combine(day, time(9), DRAW_ZONE)
    scheduled = timestamp(visit)
    old = timestamp(visit - timedelta(days=7))
    db.execute("UPDATE orders SET created_at = ? WHERE id = ?", (old, order["id"]))
    db.execute(
        "UPDATE purchases SET created_at = ? WHERE id = (SELECT purchase_id FROM orders WHERE id = ?)",
        (old, order["id"]),
    )
    if order["kind"] == "baseline":
        db.execute("UPDATE members SET created_at = ? WHERE id = ?", (old, member_id))
        db.execute("UPDATE intakes SET submitted_at = ? WHERE member_id = ?", (old, member_id))
        db.execute("UPDATE consents SET accepted_at = ? WHERE member_id = ?", (old, member_id))
    apply_staff_step(db, order["id"], "approve", old)
    slot_id = db.execute(
        "INSERT INTO draw_slots (draw_center_id, starts_at) VALUES (?, ?)",
        (order["draw_center_id"], scheduled),
    ).lastrowid
    save_appointment(db, order["id"], {"id": slot_id, "starts_at": scheduled})
    db.execute("UPDATE appointments SET created_at = ? WHERE order_id = ?", (old, order["id"]))
    apply_staff_step(db, order["id"], "collect", timestamp(visit + timedelta(minutes=20)))
    report = {
        "summary": prepared["summary"],
        "measurements": [
            {**row, "value": prepared["values"][row["code"]]} for row in sample["measurements"]
        ],
    }
    apply_staff_step(db, order["id"], "import", timestamp(visit + timedelta(days=1)), report)
    apply_staff_step(db, order["id"], "publish", timestamp(visit + timedelta(days=2)))


def seed_prepared_member(db):
    sample, prepared = fixture("sample-report.json"), fixture("prepared-reports.json")
    member_id = create_member(
        db, Signup(PREPARED_EMAIL, "Casey Harper", PREPARED_PASSWORD, "track_changes", "yes", "morning"),
        BASELINE_CHECKOUT,
    )
    with db:
        db.execute("BEGIN IMMEDIATE")
        orders = member_orders(db, member_id)
        if len(orders) == 2 and all(order["status"] == "published" for order in orders):
            return member_id
        baseline = orders[0]
        if len(orders) != 1 or baseline["status"] != "awaiting_review":
            raise ValueError("The prepared case already has fulfillment activity. Use a fresh demo database.")
        create_follow_up(db, member_id, baseline["draw_center_id"])
        for order in member_orders(db, member_id):
            complete_draw(db, member_id, order, sample, prepared[order["kind"]])
    return member_id
