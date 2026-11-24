import re

from .results import change_summary, measurement_change, reading, source_point

MAX_QUESTION_LENGTH = 500
SUGGESTIONS = (
    "What changed in my LDL cholesterol since my first test?",
    "What was my latest hemoglobin A1c?",
    "Which values were outside the lab’s reference range on my latest draw?",
)
HELP = (
    "I can explain values in your published reports. Ask for a biomarker’s latest value, "
    "how a biomarker changed between draws, or which values were outside the lab’s reference range."
)
ALIASES = {
    "ldl": ("ldl", "low density lipoprotein", "bad cholesterol"),
    "hdl": ("hdl", "high density lipoprotein", "good cholesterol"),
    "total_cholesterol": ("total cholesterol",),
    "triglycerides": ("triglycerides", "triglyceride"),
    "glucose": ("glucose", "blood sugar"),
    "hemoglobin_a1c": ("hemoglobin a1c", "a1c", "hba1c"),
    "alt": ("alt", "alanine aminotransferase"),
    "creatinine": ("creatinine",),
    "ferritin": ("ferritin",),
    "tsh": ("tsh", "thyroid stimulating hormone"),
}
OUT_OF_RANGE = re.compile(r"\b(outside|out of (?:the )?range|out of.*reference range|abnormal|flagged|above range|below range)\b")
CHANGES = re.compile(r"\b(chang(?:e[ds]?|ing)|trend|compare|since|over time|increas\w*|decreas\w*|difference)\b")
LATEST = re.compile(r"\b(latest|current|most recent|last|what is|what was|how (?:high|low))\b")
FIRST_DRAW = re.compile(r"\b(first|initial|baseline)\b")
MEDICAL_ADVICE = re.compile(r"\b(diagnos\w*|dose|treat\w*|prescri\w*|should i|recommend\w*|cure|medication)\b")


def valid_question(question):
    return isinstance(question, str) and 1 <= len(question.strip()) <= MAX_QUESTION_LENGTH


def response(kind, answer, sources=()):
    return {"kind": kind, "answer": answer, "sources": list(sources), "suggestions": list(SUGGESTIONS)}


def answer_question(reports, question):
    normalized = " ".join(re.findall(r"\w+", question.lower()))
    if MEDICAL_ADVICE.search(normalized):
        return response("unsupported", HELP)
    matches = [
        code for code, names in ALIASES.items()
        if any(re.search(rf"\b{re.escape(name)}\b", normalized) for name in names)
    ]
    if not matches and "cholesterol" in normalized.split():
        matches = ["total_cholesterol"]
    marker = matches[0] if len(matches) == 1 else None
    outside = OUT_OF_RANGE.search(normalized)
    wants_change = CHANGES.search(normalized)
    if len(matches) > 1 or (not outside and not (marker and (wants_change or LATEST.search(normalized)))):
        return response("unsupported", HELP)
    if not reports:
        return response("insufficient_data", "Your account has no published results yet. " + HELP)

    first_draw = FIRST_DRAW.search(normalized)
    if outside:
        report = reports[0] if first_draw else reports[-1]
        points = [
            source_point(report, row) for row in report["measurements"] if marker is None or row["code"] == marker
        ]
        if not points:
            return response("insufficient_data", "The selected draw has no published values for that question.")
        flagged = [point for point in points if point["reference_flag"] in {"above", "below"}]
        if flagged:
            facts = "; ".join(f"{point['name']}: {reading(point)}" for point in flagged)
            return response("outside_range", f"Outside the lab’s reference range: {facts}.", flagged)
        with_ranges = [point for point in points if point["reference_flag"] != "unavailable"]
        if not with_ranges:
            return response(
                "insufficient_data", f"The report from {report['collection_date']} supplies no reference ranges for those values.", points
            )
        return response(
            "outside_range",
            f"On {report['collection_date']}, none of the selected values with a lab reference range were outside it.",
            with_ranges,
        )

    points = [
        source_point(report, row)
        for report in reports
        for row in report["measurements"]
        if row["code"] == marker
    ]
    if not points:
        return response("insufficient_data", "There is no published value for that biomarker yet.")
    if first_draw and points[0]["report_id"] != reports[0]["id"]:
        return response("insufficient_data", "Your first published report does not include that biomarker.")
    latest = points[-1]
    if wants_change:
        if len(points) < 2:
            return response(
                "insufficient_data", f"One published {latest['name']} value is available: {reading(latest)}. A second draw is needed to show change.", points
            )
        first = points[0]
        change = measurement_change(first, latest)
        if change is None:
            return response(
                "insufficient_data",
                f"The first and latest {latest['name']} values use different units: {reading(first)} and {reading(latest)}.",
                [first, latest],
            )
        return response("change", change_summary(first, latest, change), [first, latest])
    if first_draw:
        first = points[0]
        return response("first", f"Your first {first['name']} was {reading(first)}.", [first])
    return response("latest", f"Your latest {latest['name']} was {reading(latest)}.", [latest])
