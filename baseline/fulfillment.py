import json
from dataclasses import dataclass
from pathlib import Path

from .orders import ORDER_STEPS, appointment_details, draw_center, latest_member_order, member_order
from .schedule import timestamp

FIXTURES = Path(__file__).with_name("fixtures")


class WorkflowError(Exception):
    def __init__(self, code, message, status=409):
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class StaffAction:
    label: str
    before: str
    after: str


STAFF_ACTIONS = {
    "approve": StaffAction("Approve order", "awaiting_review", "approved"),
    "collect": StaffAction("Mark collected", "booked", "collected"),
    "import": StaffAction("Import sample results", "collected", "results_imported"),
    "publish": StaffAction("Publish results", "results_imported", "published"),
}
STATUS_RANK = {status: index for index, status in enumerate(ORDER_STEPS)}


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def advance(db, order_id, status):
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def save_appointment(db, order_id, slot):
    db.execute(
        "INSERT INTO appointments (order_id, slot_id, starts_at) VALUES (?, ?, ?)",
        (order_id, slot["id"], slot["starts_at"]),
    )
    advance(db, order_id, "booked")


def available_slots(db, member_id, order_id=None):
    order = (
        latest_member_order(db, member_id) if order_id is None else member_order(db, member_id, order_id)
    )
    if order is None and order_id is not None:
        raise WorkflowError("order_not_found", "Order not found.", 404)
    availability = {
        "order_id": order["id"] if order else None,
        "status": order["status"] if order else None,
        "draw_center": draw_center(order) if order else None,
        "slots": [],
    }
    if order and order["status"] == "approved":
        availability["slots"] = [
            dict(slot) for slot in db.execute(
                """SELECT s.id, s.starts_at FROM draw_slots s
                   WHERE s.draw_center_id = ? AND s.starts_at > ?
                   AND NOT EXISTS (SELECT 1 FROM appointments a WHERE a.slot_id = s.id)
                   ORDER BY s.starts_at""",
                (order["draw_center_id"], timestamp()),
            )
        ]
    return availability


def book_slot(db, member_id, order_id, slot_id):
    with db:
        db.execute("BEGIN IMMEDIATE")
        order = member_order(db, member_id, order_id)
        if order is None:
            raise WorkflowError("order_not_found", "Order not found.", 404)
        existing = appointment_details(order)
        if existing:
            if existing["slot_id"] == slot_id:
                return existing
            raise WorkflowError("already_booked", "This order already has an appointment.")
        if order["status"] != "approved":
            raise WorkflowError("order_not_approved", "This order must be approved before booking.")

        slot = db.execute(
            """SELECT s.id, s.starts_at FROM draw_slots s
               WHERE s.id = ? AND s.draw_center_id = ? AND s.starts_at > ?
               AND NOT EXISTS (SELECT 1 FROM appointments a WHERE a.slot_id = s.id)""",
            (slot_id, order["draw_center_id"], timestamp()),
        ).fetchone()
        if slot is None:
            raise WorkflowError("slot_unavailable", "This slot is unavailable. Choose another time.")
        save_appointment(db, order["id"], slot)
        return appointment_details(member_order(db, member_id, order_id))


def import_report(db, order_id, report, at):
    report_id = db.execute(
        "INSERT INTO reports (order_id, summary, imported_at) VALUES (?, ?, ?)",
        (order_id, report["summary"], at),
    ).lastrowid
    db.executemany(
        """INSERT INTO report_measurements
           (report_id, code, name, group_name, value, unit, reference_low, reference_high)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (report_id, row["code"], row["name"], row["group"], row["value"], row["unit"],
             row.get("reference_low"), row.get("reference_high"))
            for row in report["measurements"]
        ],
    )


def apply_staff_step(db, order_id, action, at, report=None):
    if action == "approve":
        db.execute("UPDATE orders SET approved_at = ? WHERE id = ?", (at, order_id))
    elif action == "collect":
        db.execute("UPDATE orders SET collected_at = ? WHERE id = ?", (at, order_id))
    elif action == "import":
        import_report(db, order_id, report if report is not None else fixture("sample-report.json"), at)
    elif action == "publish":
        updated = db.execute(
            "UPDATE reports SET published_at = ? WHERE order_id = ? AND published_at IS NULL",
            (at, order_id),
        )
        if not updated.rowcount:
            raise WorkflowError("missing_draft", "Import a report draft before publishing.")
    advance(db, order_id, STAFF_ACTIONS[action].after)


def fulfill_order(db, member_id, order_id, action):
    command = STAFF_ACTIONS.get(action)
    if command is None:
        raise WorkflowError("action_not_found", "Staff action not found.", 404)
    with db:
        db.execute("BEGIN IMMEDIATE")
        order = member_order(db, member_id, order_id)
        if order is None:
            raise WorkflowError("order_not_found", "Order not found.", 404)
        if STATUS_RANK[order["status"]] >= STATUS_RANK[command.after]:
            return
        if order["status"] != command.before:
            raise WorkflowError("invalid_transition", "The order is not ready for that action.")
        apply_staff_step(db, order_id, action, timestamp())
