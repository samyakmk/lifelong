from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from ..catalog import INTAKE_QUESTIONS
from ..db import get_db
from ..demo_identity import authenticate_staff
from ..fulfillment import STAFF_ACTIONS, WorkflowError, fulfill_order
from ..orders import ORDER_STEPS, member_orders
from ..results import reference_text, staff_reports
from .security import change_identity, valid_form

staff = Blueprint("staff", __name__, url_prefix="/staff")
ACTIONS_BY_STATUS = {action.before: (code, action.label) for code, action in STAFF_ACTIONS.items()}
NEXT_ACTIONS = {
    **{status: label for status, (_, label) in ACTIONS_BY_STATUS.items()},
    "approved": "Await member booking",
    "published": "Review published case",
}


@staff.before_request
def authorize():
    g.staff = get_db().execute(
        "SELECT id, email FROM staff_users WHERE id = ?", (session.get("staff_id"),)
    ).fetchone()
    if request.endpoint != "staff.index" and g.staff is None:
        if request.method == "POST":
            abort(403)
        return redirect(url_for("staff.index"), code=303)
    if not valid_form():
        return render_template(
            "staff/error.html", title="This form has expired",
            message="Open the staff queue to continue.",
        ), 400
    return None


@staff.route("", methods=["GET", "POST"])
def index():
    db = get_db()
    if g.staff is None:
        email, error = "", None
        if request.method == "POST":
            email = request.form.get("email", "")
            staff_id = authenticate_staff(db, email, request.form.get("password", ""))
            if staff_id is not None:
                change_identity("staff_id", staff_id)
                return redirect(url_for("staff.index"), code=303)
            error = "That staff email and password didn’t match."
        return render_template("staff/sign_in.html", email=email, error=error), 401 if error else 200

    if request.method == "POST":
        return redirect(url_for("staff.index"), code=303)
    queue = db.execute(
        """SELECT m.id, m.name, m.email, o.id AS order_id, o.status, o.kind,
                  (SELECT COUNT(*) FROM orders p WHERE p.member_id = m.id AND p.status = 'published')
                     AS published_draws
           FROM members m
           LEFT JOIN orders o ON o.id = (SELECT MAX(lo.id) FROM orders lo WHERE lo.member_id = m.id)
           ORDER BY CASE o.status
                        WHEN 'awaiting_review' THEN 0 WHEN 'results_imported' THEN 1
                        WHEN 'collected' THEN 2 WHEN 'booked' THEN 3
                        WHEN 'approved' THEN 4 ELSE 5 END,
                    o.id DESC, m.id DESC"""
    ).fetchall()
    return render_template("staff/queue.html", queue=queue, steps=ORDER_STEPS, next_actions=NEXT_ACTIONS)


def render_case(member_id, error=None):
    db = get_db()
    member = None
    if 0 < member_id <= 2**63 - 1:
        member = db.execute(
            "SELECT id, name, email, created_at FROM members WHERE id = ?", (member_id,)
        ).fetchone()
    if member is None:
        abort(404)
    intake = db.execute("SELECT * FROM intakes WHERE member_id = ?", (member_id,)).fetchone()
    consents = db.execute(
        "SELECT version, accepted_at FROM consents WHERE member_id = ? ORDER BY id", (member_id,)
    ).fetchall()
    return render_template(
        "staff/case.html", member=member, intake=intake, consents=consents,
        questions=INTAKE_QUESTIONS, orders=member_orders(db, member_id),
        reports={report["order_id"]: report for report in staff_reports(db, member_id)},
        steps=ORDER_STEPS, actions=ACTIONS_BY_STATUS, next_actions=NEXT_ACTIONS,
        reference_text=reference_text, error=error,
    )


@staff.get("/members/<int:member_id>")
def case(member_id):
    return render_case(member_id)


@staff.post("/members/<int:member_id>/orders/<int:order_id>/<action>")
def apply_order_action(member_id, order_id, action):
    if not 0 < member_id <= 2**63 - 1 or not 0 < order_id <= 2**63 - 1:
        abort(404)
    try:
        fulfill_order(get_db(), member_id, order_id, action)
    except WorkflowError as error:
        if error.status == 404:
            abort(404)
        return render_case(member_id, error=str(error)), error.status
    flash({
        "approve": "Order approved. The member can now book a draw.",
        "collect": "Collection recorded.",
        "import": "Sample results saved as a draft.",
        "publish": "Report published to the member.",
    }[action])
    return redirect(url_for("staff.case", member_id=member_id, _anchor=f"order-{order_id}"), code=303)


@staff.post("/sign-out")
def sign_out():
    change_identity("staff_id")
    return redirect(url_for("staff.index"), code=303)
