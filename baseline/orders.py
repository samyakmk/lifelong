from dataclasses import dataclass


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
        "Your order is approved. Booking will be available in the next demo phase.",
    ),
    "booked": OrderStep(
        "Booked",
        "Attend your draw",
        "Your draw is on the calendar. Check your appointment for visit details.",
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
        "Your report is published. The report viewer will be available in a later demo phase.",
    ),
}


def latest_member_order(db, member_id):
    return db.execute(
        """SELECT o.id, o.kind, o.status, o.created_at, c.name AS draw_center,
                  p.amount_cents, p.status AS purchase_status
           FROM orders o
           JOIN purchases p ON p.id = o.purchase_id AND p.member_id = o.member_id
           JOIN draw_centers c ON c.id = o.draw_center_id
           WHERE o.member_id = ? ORDER BY o.id DESC LIMIT 1""",
        (member_id,),
    ).fetchone()
