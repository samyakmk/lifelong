import secrets

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for,
)

from ..accounts import EmailInUse, authenticate_member, create_member, validate_signup
from ..catalog import CONSENT_TEXT, INTAKE_QUESTIONS, PLAN, TEST_GROUPS
from ..db import get_db
from ..orders import ORDER_STEPS, latest_member_order

web = Blueprint(
    "web", __name__, template_folder="templates", static_folder="static", static_url_path="/assets"
)


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def matches_session(key, submitted):
    expected = session.get(key)
    return bool(
        expected and submitted and submitted.isascii()
        and secrets.compare_digest(expected, submitted)
    )


@web.before_request
def prepare_request():
    if request.method == "POST" and not matches_session("csrf_token", request.form.get("csrf_token")):
        return render_template(
            "error.html", title="This form has expired",
            message="Open a fresh page to continue.",
        ), 400
    if "member_id" in session:
        g.member = get_db().execute(
            "SELECT id, name FROM members WHERE id = ?", (session["member_id"],)
        ).fetchone()
        if g.member is None:
            session.clear()
    else:
        g.member = None


@web.after_request
def set_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.endpoint in {"web.join", "web.member", "web.sign_out"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@web.context_processor
def template_values():
    return {"plan": PLAN, "csrf_token": csrf_token}


def sign_in(member_id):
    session.clear()
    session.permanent = True
    session["member_id"] = member_id


@web.get("/")
def landing():
    return render_template("landing.html", test_groups=TEST_GROUPS)


@web.route("/join", methods=["GET", "POST"])
def join():
    if g.member is not None:
        return redirect(url_for("web.member"), code=303)

    errors = {}
    values = {}
    checkout_key = session.get("checkout_key")
    if request.method == "POST":
        if not matches_session("checkout_key", request.form.get("checkout_key")):
            return render_template(
                "error.html", title="This signup has expired",
                message="Open a fresh signup form to continue.",
            ), 400

        values = {
            key: request.form.get(key, "")
            for key in ("email", "name", "consent", *INTAKE_QUESTIONS)
        }
        signup, errors = validate_signup(request.form)
        if signup is not None:
            try:
                member_id = create_member(get_db(), signup, checkout_key)
            except EmailInUse:
                errors["email"] = "An account is already using this email. Sign in to continue."
            else:
                sign_in(member_id)
                return redirect(url_for("web.member"), code=303)

    if checkout_key is None:
        checkout_key = secrets.token_urlsafe(32)
        session["checkout_key"] = checkout_key

    return render_template(
        "join.html", values=values, errors=errors, checkout_key=checkout_key,
        intake_questions=INTAKE_QUESTIONS, consent_text=CONSENT_TEXT,
    ), 422 if errors else 200


@web.route("/member", methods=["GET", "POST"])
def member():
    if g.member is not None:
        if request.method == "POST":
            return redirect(url_for("web.member"), code=303)
        order = latest_member_order(get_db(), g.member["id"])
        step = ORDER_STEPS[order["status"]] if order else None
        return render_template("member.html", order=order, step=step, order_steps=ORDER_STEPS)

    email = ""
    error = None
    if request.method == "POST":
        email = request.form.get("email", "")
        member_id = authenticate_member(get_db(), email, request.form.get("password", ""))
        if member_id is not None:
            sign_in(member_id)
            return redirect(url_for("web.member"), code=303)
        error = "That email and password didn’t match. Try again."

    return render_template("sign_in.html", email=email, error=error), 401 if error else 200


@web.post("/member/sign-out")
def sign_out():
    session.clear()
    return redirect(url_for("web.member"), code=303)
