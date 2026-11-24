from dataclasses import dataclass

from .catalog import DRAW_ADDRESS, DRAW_PREP, DRAW_TIMEZONE


@dataclass(frozen=True)
class OrderStep:
    label: str
    next_title: str
    next_detail: str


ORDER_STEPS = {
    "awaiting_review": OrderStep(
        "Awaiting review",
        "Order review",
        "The demo team will review your intake before booking opens.",
    ),
    "approved": OrderStep(
        "Approved",
        "Schedule your draw",
        "Your order is approved and ready to book at the draw center.",
    ),
    "booked": OrderStep(
        "Booked",
        "Attend your draw",
        "Your draw is on the calendar. See when and where to go below.",
    ),
    "collected": OrderStep(
        "Collected",
        "Lab processing",
        "Your sample has been collected. Results are pending.",
    ),
    "results_imported": OrderStep(
        "Results imported",
        "Report review",
        "Your results have arrived and are being reviewed before publication.",
    ),
    "published": OrderStep(
        "Published",
        "Review your results",
        "Your report is published and ready to review.",
    ),
}


ORDER_SELECT = """SELECT o.id, o.kind, o.status, o.created_at, o.approved_at, o.collected_at,
                        c.id AS draw_center_id, c.name AS draw_center, p.amount_cents,
                        p.status AS purchase_status, a.id AS appointment_id, a.slot_id, a.starts_at
                 FROM orders o
                 JOIN purchases p ON p.id = o.purchase_id AND p.member_id = o.member_id
                 JOIN draw_centers c ON c.id = o.draw_center_id
                 LEFT JOIN appointments a ON a.order_id = o.id
                 WHERE o.member_id = ?"""


def latest_member_order(db, member_id):
    return db.execute(
        ORDER_SELECT + " ORDER BY o.id DESC LIMIT 1", (member_id,)
    ).fetchone()


def member_order(db, member_id, order_id):
    return db.execute(ORDER_SELECT + " AND o.id = ?", (member_id, order_id)).fetchone()


def member_orders(db, member_id):
    return db.execute(ORDER_SELECT + " ORDER BY o.id", (member_id,)).fetchall()


def draw_center(order):
    return {"name": order["draw_center"], "address": DRAW_ADDRESS, "timezone": DRAW_TIMEZONE}


def appointment_details(order):
    if order["appointment_id"] is None:
        return None
    return {
        "id": order["appointment_id"],
        "order_id": order["id"],
        "slot_id": order["slot_id"],
        "starts_at": order["starts_at"],
        "draw_center": draw_center(order),
        "prep": DRAW_PREP,
    }


def member_dashboard(db, member):
    order = latest_member_order(db, member["id"])
    dashboard = {"member": dict(member), "order": None, "next_step": None, "appointment": None}
    if order is not None:
        status = order["status"]
        step = ORDER_STEPS[status]
        dashboard["order"] = {
            key: order[key] for key in (
                "id", "kind", "status", "created_at", "collected_at", "amount_cents", "purchase_status"
            )
        }
        dashboard["order"].update(draw_center=order["draw_center"], status_label=step.label)
        dashboard["next_step"] = {"title": step.next_title, "detail": step.next_detail}
        dashboard["appointment"] = appointment_details(order)
    return dashboard
