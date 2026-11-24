from datetime import date, datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from ..chat import MAX_QUESTION_LENGTH, SUGGESTIONS, answer_question, valid_question
from ..db import get_db
from ..fulfillment import WorkflowError, available_slots, book_slot
from ..orders import member_dashboard
from ..results import insights, published_reports, trends

portal = Blueprint("portal", __name__, url_prefix="/member")
RESULT_TABS = {"report": "Report", "trends": "Trends", "insights": "Insights", "chat": "Chat"}


@portal.before_request
def require_member():
    if g.member is None:
        return redirect(url_for("web.member"), code=303)
    return None


@portal.app_template_filter("draw_label")
def draw_label(day):
    return date.fromisoformat(day).strftime("%b %d, %Y").replace(" 0", " ")


def slot_days(availability):
    center = availability["draw_center"]
    if not center:
        return {}
    zone = ZoneInfo(center["timezone"])
    days = {}
    for slot in availability["slots"]:
        local = datetime.fromisoformat(slot["starts_at"]).astimezone(zone)
        day = days.setdefault(local.date().isoformat(), {"date": local.date(), "slots": []})
        day["slots"].append({
            **slot,
            "label": local.strftime("%I:%M %p").lstrip("0"),
            "zone": local.strftime("%Z"),
        })
    return days


@portal.route("/book", methods=["GET", "POST"])
def book():
    db = get_db()
    member_id = g.member["id"]
    error, status = None, 200
    if request.method == "POST":
        order_id = request.form.get("order_id", type=int)
        slot_id = request.form.get("slot_id", type=int)
        if any(value is None or not 0 < value <= 2**63 - 1 for value in (order_id, slot_id)):
            error, status = "Choose an available time to book your draw.", 400
        else:
            try:
                book_slot(db, member_id, order_id, slot_id)
            except WorkflowError as failure:
                if failure.status == 404:
                    abort(404)
                error, status = str(failure), failure.status
            else:
                return redirect(url_for("web.portal.book"), code=303)

    # Read the appointment and the slot list from the same snapshot during a concurrent booking.
    with db:
        db.execute("BEGIN")
        dashboard = member_dashboard(db, g.member)
        availability = available_slots(db, member_id)
    days = slot_days(availability)
    selected_day = request.args.get("day")
    if selected_day not in days:
        selected_day = next(iter(days), None)
    return render_template(
        "portal/book.html", **dashboard, center=availability["draw_center"],
        days=days, selected_day=selected_day, error=error,
    ), status


@portal.route("/results", methods=["GET", "POST"])
def results():
    reports = published_reports(get_db(), g.member["id"])
    tab = request.args.get("view", "report")
    if tab not in RESULT_TABS:
        tab = "report"
    context = {"tab": tab, "tabs": RESULT_TABS, "reports": reports}
    status = 200

    if request.method == "POST" or tab == "chat":
        question = request.form.get("question", "").strip()
        answer, error = None, None
        if request.method == "POST":
            if valid_question(question):
                answer = answer_question(reports, question)
            else:
                error = f"Enter a question of up to {MAX_QUESTION_LENGTH} characters."
                status = 400
        context.update(
            tab="chat", question=question[:MAX_QUESTION_LENGTH], answer=answer,
            suggestions=SUGGESTIONS, max_length=MAX_QUESTION_LENGTH, error=error,
        )
    elif tab == "report":
        report = reports[-1] if reports else None
        if "draw" in request.args:
            draw_id = request.args.get("draw", type=int)
            report = next((item for item in reports if item["id"] == draw_id), None)
            if report is None:
                abort(404)
        groups = {}
        if report:
            for measurement in report["measurements"]:
                groups.setdefault(measurement["group"], []).append(measurement)
        context.update(report=report, groups=groups)
    elif tab == "trends":
        series = trends(reports)
        index = request.args.get("biomarker", type=int)
        if index is None or not 0 <= index < len(series):
            index = next((i for i, marker in enumerate(series) if marker["code"] == "ldl"), 0)
        context.update(series=series, selected_index=index, trend=series[index] if series else None)
    elif tab == "insights":
        context["insights"] = insights(reports)

    return render_template("portal/results.html", **context), status
