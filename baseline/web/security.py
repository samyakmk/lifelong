import secrets

from flask import request, session


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


def valid_form():
    return request.method != "POST" or matches_session("csrf_token", request.form.get("csrf_token"))


def change_identity(role, identity=None):
    session.pop("csrf_token", None)
    if role == "member_id":
        session.pop("checkout_key", None)
    if identity is None:
        session.pop(role, None)
    else:
        session.permanent = True
        session[role] = identity
