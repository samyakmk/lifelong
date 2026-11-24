from decimal import Decimal

from .schedule import draw_date

REPORT_SELECT = """SELECT r.id AS report_id, r.summary, r.imported_at, r.published_at,
                          o.id AS order_id, o.kind, o.collected_at, o.status,
                          m.code, m.name, m.group_name, m.value, m.unit, m.reference_low, m.reference_high
                   FROM reports r JOIN orders o ON o.id = r.order_id
                   LEFT JOIN report_measurements m ON m.report_id = r.id
                   WHERE o.member_id = ?"""


def reference_flag(value, low, high):
    if low is not None and value < low:
        return "below"
    if high is not None and value > high:
        return "above"
    return "within" if low is not None or high is not None else "unavailable"


def load_reports(db, where, parameters):
    rows = db.execute(
        REPORT_SELECT + where + " ORDER BY o.collected_at, o.id, m.rowid", parameters
    )
    reports = {}
    for row in rows:
        report = reports.setdefault(row["report_id"], {
            "id": row["report_id"],
            "order_id": row["order_id"],
            "kind": row["kind"],
            "collection_date": draw_date(row["collected_at"]) if row["collected_at"] else None,
            "imported_at": row["imported_at"],
            "published_at": row["published_at"],
            "summary": row["summary"],
            "measurements": [],
        })
        if row["code"] is None:
            continue
        measurement = {
            key: row[key] for key in ("code", "name", "value", "unit", "reference_low", "reference_high")
        }
        measurement["group"] = row["group_name"]
        measurement["reference_flag"] = reference_flag(
            row["value"], row["reference_low"], row["reference_high"]
        )
        report["measurements"].append(measurement)
    return list(reports.values())


def published_reports(db, member_id, report_id=None):
    scope = " AND o.status = 'published' AND r.published_at IS NOT NULL AND o.collected_at IS NOT NULL"
    if report_id is not None:
        return load_reports(db, scope + " AND r.id = ?", (member_id, report_id))
    return load_reports(db, scope, (member_id,))


def staff_reports(db, member_id):
    return load_reports(db, "", (member_id,))


def source_point(report, measurement):
    return {
        "report_id": report["id"],
        "order_id": report["order_id"],
        "collection_date": report["collection_date"],
        **measurement,
    }


def measurement_change(first, last):
    if first["code"] != last["code"] or first["unit"] != last["unit"]:
        return None
    delta = Decimal(str(last["value"])) - Decimal(str(first["value"]))
    direction = "increased" if delta > 0 else "decreased" if delta < 0 else "stable"
    return {"delta": float(delta), "direction": direction, "unit": first["unit"]}


def trends(reports):
    series = {}
    for report in reports:
        for measurement in report["measurements"]:
            code, unit = measurement["code"], measurement["unit"]
            marker = series.setdefault((code, unit), {
                "code": code, "name": measurement["name"], "unit": unit, "points": [],
            })
            marker["points"].append(source_point(report, measurement))
    for marker in series.values():
        points = marker["points"]
        marker["change"] = measurement_change(points[0], points[-1]) if len(points) > 1 else None
    return list(series.values())


def reference_text(point):
    low, high = point["reference_low"], point["reference_high"]
    flag = point["reference_flag"]
    if flag == "unavailable":
        return "reference range not supplied"
    if low is None:
        return f"{flag} lab range, upper limit {high:g} {point['unit']}"
    if high is None:
        return f"{flag} lab range, lower limit {low:g} {point['unit']}"
    return f"{flag} lab range of {low:g}–{high:g} {point['unit']}"


def reading(point):
    return f"{point['value']:g} {point['unit']} on {point['collection_date']} ({reference_text(point)})"


def change_summary(first, last, change):
    if change["direction"] == "stable":
        headline = f"{last['name']} was stable"
    else:
        headline = f"{last['name']} {change['direction']} by {abs(change['delta']):g} {change['unit']}"
    return f"{headline}, from {reading(first)} to {reading(last)}."


def insights(reports):
    items = []
    for series in trends(reports):
        if series["change"] is not None:
            first, last = series["points"][0], series["points"][-1]
            items.append({
                "code": series["code"],
                "name": series["name"],
                "summary": change_summary(first, last, series["change"]),
                "change": series["change"],
                "sources": [first, last],
            })
    return items
