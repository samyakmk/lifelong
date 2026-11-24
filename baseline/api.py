import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta

from flask import Blueprint, g, jsonify, request

from .accounts import authenticate_member
from .chat import MAX_QUESTION_LENGTH, SUGGESTIONS, answer_question, valid_question
from .db import get_db
from .fulfillment import WorkflowError, available_slots, book_slot
from .orders import member_dashboard
from .results import insights, published_reports, trends
from .schedule import timestamp

api = Blueprint("api", __name__, url_prefix="/api/v1")
TOKEN_LIFETIME = timedelta(hours=24)
TOKEN_FORMAT = re.compile(r"[A-Za-z0-9_-]{43}")


def api_error(code, message, status):
    return jsonify(error={"code": code, "message": message}), status


def valid_id(value):
    return type(value) is int and 0 < value <= 2**63 - 1


def token_digest(token):
    return hashlib.sha256(token.encode("ascii")).hexdigest()


@api.before_request
def authorize():
    if request.endpoint == "api.sign_in":
        return None
    auth = request.authorization
    if auth is not None and auth.type == "bearer" and TOKEN_FORMAT.fullmatch(auth.token or ""):
        g.token_digest = token_digest(auth.token)
        g.api_member = get_db().execute(
            """SELECT m.id, m.name, m.email FROM member_tokens t JOIN members m ON m.id = t.member_id
               WHERE t.token_digest = ? AND t.revoked_at IS NULL AND t.expires_at > ?""",
            (g.token_digest, timestamp()),
        ).fetchone()
        if g.api_member is not None:
            return None
    response, status = api_error("unauthorized", "A valid member bearer token is required.", 401)
    response.headers["WWW-Authenticate"] = "Bearer"
    return response, status


@api.errorhandler(WorkflowError)
def workflow_error(error):
    return api_error(error.code, str(error), error.status)


@api.errorhandler(413)
def body_too_large(_error):
    return api_error("body_too_large", "The request body is too large.", 413)


@api.post("/auth/sign-in")
def sign_in():
    fields = request.get_json(silent=True)
    if not isinstance(fields, dict):
        return api_error("invalid_request", "Send an email and password as JSON.", 400)
    email, password = fields.get("email"), fields.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or len(email) > 254:
        return api_error("invalid_request", "Send an email and password as JSON strings.", 400)
    db = get_db()
    member_id = authenticate_member(db, email, password)
    if member_id is None:
        return api_error("invalid_credentials", "That email and password didn’t match.", 401)
    token = secrets.token_urlsafe(32)
    expires_at = timestamp(datetime.now(UTC) + TOKEN_LIFETIME)
    with db:
        db.execute(
            "INSERT INTO member_tokens (token_digest, member_id, expires_at) VALUES (?, ?, ?)",
            (token_digest(token), member_id, expires_at),
        )
    return jsonify(access_token=token, token_type="Bearer", expires_at=expires_at)


@api.post("/auth/sign-out")
def sign_out():
    db = get_db()
    with db:
        db.execute(
            "UPDATE member_tokens SET revoked_at = ? WHERE token_digest = ?",
            (timestamp(), g.token_digest),
        )
    return "", 204


@api.get("/member")
def dashboard():
    return jsonify(member_dashboard(get_db(), g.api_member))


@api.get("/member/slots")
def slots():
    order_id = None
    raw = request.args.get("order_id")
    if raw is not None:
        if not raw.isascii() or not raw.isdecimal() or len(raw) > 19 or not valid_id(int(raw)):
            return api_error("invalid_request", "Use a positive integer order_id.", 400)
        order_id = int(raw)
    return jsonify(available_slots(get_db(), g.api_member["id"], order_id))


@api.post("/member/book")
def book():
    fields = request.get_json(silent=True)
    if not isinstance(fields, dict) or not all(valid_id(fields.get(key)) for key in ("order_id", "slot_id")):
        return api_error("invalid_request", "Send positive integer order_id and slot_id fields.", 400)
    appointment = book_slot(get_db(), g.api_member["id"], fields["order_id"], fields["slot_id"])
    return jsonify(appointment=appointment)


@api.get("/member/reports")
def reports():
    return jsonify(reports=published_reports(get_db(), g.api_member["id"]))


@api.get("/member/reports/<int:report_id>")
def report(report_id):
    matches = published_reports(get_db(), g.api_member["id"], report_id) if valid_id(report_id) else []
    if not matches:
        return api_error("report_not_found", "Report not found.", 404)
    return jsonify(report=matches[0])


@api.get("/member/trends")
def member_trends():
    return jsonify(trends=trends(published_reports(get_db(), g.api_member["id"])))


@api.get("/member/insights")
def member_insights():
    return jsonify(insights=insights(published_reports(get_db(), g.api_member["id"])))


@api.get("/member/chat")
def suggestions():
    return jsonify(suggestions=list(SUGGESTIONS))


@api.post("/member/chat")
def chat():
    fields = request.get_json(silent=True)
    question = fields.get("question") if isinstance(fields, dict) else None
    if not valid_question(question):
        return api_error("invalid_request", f"Enter a question of up to {MAX_QUESTION_LENGTH} characters.", 400)
    return jsonify(answer_question(published_reports(get_db(), g.api_member["id"]), question))
