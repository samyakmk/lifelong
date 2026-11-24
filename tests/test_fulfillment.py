import re
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from baseline import create_app
from baseline.db import get_db
from baseline.demo_identity import PREPARED_EMAIL, PREPARED_PASSWORD, STAFF_EMAIL, STAFF_PASSWORD
from baseline.seed import seed_prepared_member

PREFIX = "/api/v1"
MEMBER_PASSWORD = "PhaseTwoDemo-27!"
LDL_QUESTION = "What changed in my LDL cholesterol since my first test?"


def hidden(response, field):
    return re.search(rb'name="' + field.encode() + rb'" value="([^"]+)"', response.data)[1].decode()


def staff_action_path(member_id, order_id, action):
    return f"/staff/members/{member_id}/orders/{order_id}/{action}"


class FulfillmentTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.app = create_app(directory.name)
        self.app.testing = True
        self.client = self.app.test_client()
        self.staff = self.app.test_client()

    def enroll(self, name="Jordan Rowan", email="jordan@example.test"):
        browser = self.app.test_client()
        form = browser.get("/join")
        response = browser.post("/join", data={
            "csrf_token": hidden(form, "csrf_token"),
            "checkout_key": hidden(form, "checkout_key"),
            "email": email, "name": name, "password": MEMBER_PASSWORD,
            "goal": "establish_baseline", "prior_testing": "no", "draw_time": "morning",
            "consent": "yes",
        })
        self.assertEqual(response.status_code, 303)
        auth = self.bearer(email, MEMBER_PASSWORD)
        member = self.client.get(PREFIX + "/member", headers=auth).json
        return browser, auth, member["member"]["id"], member["order"]["id"]

    def bearer(self, email, password):
        response = self.client.post(PREFIX + "/auth/sign-in", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        return {"Authorization": "Bearer " + response.json["access_token"]}

    def staff_login(self):
        page = self.staff.get("/staff")
        response = self.staff.post("/staff", data={
            "csrf_token": hidden(page, "csrf_token"), "email": STAFF_EMAIL, "password": STAFF_PASSWORD,
        })
        self.assertEqual(response.status_code, 303)

    def action(self, member_id, order_id, action, expected=303):
        case = self.staff.get(f"/staff/members/{member_id}")
        response = self.staff.post(staff_action_path(member_id, order_id, action), data={
            "csrf_token": hidden(case, "csrf_token"),
        })
        self.assertEqual(response.status_code, expected)
        return response

    def booking(self, auth, order_id, slot_id):
        return self.client.post(
            PREFIX + "/member/book", headers=auth, json={"order_id": order_id, "slot_id": slot_id}
        )

    def prepared(self):
        with self.app.app_context():
            db = get_db()
            first = seed_prepared_member(db)
            self.assertEqual(seed_prepared_member(db), first)
        return self.bearer(PREPARED_EMAIL, PREPARED_PASSWORD)

    def test_signup_through_publication_keeps_drafts_and_other_accounts_private(self):
        prepared = self.prepared()
        browser, auth, member_id, order_id = self.enroll()
        self.staff_login()
        queue = self.staff.get("/staff")
        self.assertIn(b"Jordan Rowan", queue.data)
        self.assertIn(b"Casey Harper", queue.data)
        self.assertIn(b"Awaiting review", queue.data)
        self.assertIn(b"Approve order", queue.data)

        self.assertEqual(self.booking(auth, order_id, 1).json["error"]["code"], "order_not_approved")
        self.action(member_id, order_id, "publish", expected=409)
        self.action(member_id, order_id, "approve")
        self.action(member_id, order_id, "approve")
        self.assertIn(b"Schedule your draw", browser.get("/member").data)

        availability = self.client.get(PREFIX + "/member/slots", headers=auth).json
        slot = availability["slots"][0]
        booked = self.booking(auth, order_id, slot["id"])
        replay = self.booking(auth, order_id, slot["id"])
        self.assertEqual(booked.status_code, 200)
        self.assertEqual(replay.json, booked.json)
        self.assertEqual(booked.json["appointment"]["starts_at"], slot["starts_at"])
        other_slot = availability["slots"][1]["id"]
        self.assertEqual(self.booking(auth, order_id, other_slot).json["error"]["code"], "already_booked")
        self.assertIn(b"Draw appointment", browser.get("/member").data)

        self.action(member_id, order_id, "collect")
        self.action(member_id, order_id, "import")
        self.action(member_id, order_id, "import")
        case = self.staff.get(f"/staff/members/{member_id}")
        self.assertIn(b"Draft", case.data)
        self.assertIn(b"136 mg/dL", case.data)
        with self.app.app_context():
            db = get_db()
            draft = db.execute("SELECT id, published_at FROM reports WHERE order_id = ?", (order_id,)).fetchone()
            self.assertIsNone(draft["published_at"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM appointments WHERE order_id = ?", (order_id,)).fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM reports WHERE order_id = ?", (order_id,)).fetchone()[0], 1)

        for resource in ("reports", "trends", "insights"):
            self.assertEqual(self.client.get(f"{PREFIX}/member/{resource}", headers=auth).json[resource], [])
        answer = self.client.post(PREFIX + "/member/chat", headers=auth, json={"question": "What is my latest LDL?"})
        self.assertEqual(answer.json["kind"], "insufficient_data")
        self.assertEqual(answer.json["sources"], [])
        for headers in (auth, prepared):
            self.assertEqual(self.client.get(f"{PREFIX}/member/reports/{draft['id']}", headers=headers).status_code, 404)

        self.action(member_id, order_id, "publish")
        self.action(member_id, order_id, "publish")
        own = self.client.get(f"{PREFIX}/member/reports/{draft['id']}", headers=auth).json["report"]
        self.assertIsNotNone(own["published_at"])
        other = self.client.get(PREFIX + "/member/reports", headers=prepared).json["reports"]
        self.assertEqual(len(other), 2)
        self.assertEqual(self.client.get(f"{PREFIX}/member/reports/{draft['id']}", headers=prepared).status_code, 404)
        self.assertEqual(self.client.get(f"{PREFIX}/member/reports/{other[0]['id']}", headers=auth).status_code, 404)
        self.assertEqual(len(self.client.get(PREFIX + "/member/trends", headers=auth).json["trends"][0]["points"]), 1)
        self.assertEqual(self.client.get(PREFIX + "/member/insights", headers=auth).json["insights"], [])
        answer = self.client.post(PREFIX + "/member/chat", headers=auth, json={"question": "What is my latest LDL?"})
        self.assertEqual([point["value"] for point in answer.json["sources"]], [136])
        self.assertIn(b"Your report is published", browser.get("/member").data)

    def test_prepared_trends_insights_and_answers_are_source_grounded(self):
        auth = self.prepared()
        result = self.client.get(PREFIX + "/member/reports", headers=auth).json
        reports = result["reports"]
        self.assertEqual([report["collection_date"] for report in reports], ["2025-04-10", "2025-10-16"])
        with self.app.app_context():
            db = get_db()
            for table in ("orders", "purchases", "appointments", "reports"):
                self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 2)

        trends = self.client.get(PREFIX + "/member/trends", headers=auth).json["trends"]
        ldl = next(item for item in trends if item["code"] == "ldl")
        self.assertEqual([point["value"] for point in ldl["points"]], [142, 104])
        self.assertEqual(ldl["change"], {"delta": -38, "direction": "decreased", "unit": "mg/dL"})
        insights = self.client.get(PREFIX + "/member/insights", headers=auth).json["insights"]
        self.assertEqual({item["change"]["direction"] for item in insights}, {"increased", "decreased", "stable"})
        self.assertIn("upper limit 129 mg/dL", next(item for item in insights if item["code"] == "ldl")["summary"])

        cases = (
            (LDL_QUESTION, "change", [142, 104]),
            ("What was my latest hemoglobin A1c?", "latest", [5.3]),
            ("Which values were outside the range on my first test?", "outside_range", [213, 142]),
            ("Should I take medication for my LDL?", "unsupported", []),
        )
        for question, kind, values in cases:
            with self.subTest(question=question):
                answer = self.client.post(PREFIX + "/member/chat", headers=auth, json={"question": question}).json
                self.assertEqual(answer["kind"], kind)
                self.assertEqual([point["value"] for point in answer["sources"]], values)
                self.assertTrue(answer["suggestions"])
                if kind == "change":
                    self.assertIn("decreased by 38 mg/dL", answer["answer"])
                    self.assertEqual([point["report_id"] for point in answer["sources"]], [report["id"] for report in reports])
        with self.app.app_context():
            db = get_db()
            with db:
                db.execute(
                    """UPDATE report_measurements SET unit = 'mmol/L', value = 2.69
                       WHERE report_id = ? AND code = 'ldl'""",
                    (reports[1]["id"],),
                )
        mixed = self.client.get(PREFIX + "/member/trends", headers=auth).json["trends"]
        self.assertEqual([item["change"] for item in mixed if item["code"] == "ldl"], [None, None])
        answer = self.client.post(PREFIX + "/member/chat", headers=auth, json={"question": LDL_QUESTION}).json
        self.assertEqual(answer["kind"], "insufficient_data")
        self.assertIn("different units", answer["answer"])

    def test_staff_authorization_cookie_csrf_and_resource_ownership(self):
        browser, auth, member_id, order_id = self.enroll()
        _, other_auth, other_member_id, _ = self.enroll("Robin Shaw", "robin@example.test")
        target = staff_action_path(member_id, order_id, "approve")
        self.assertEqual(browser.get(f"/staff/members/{member_id}").status_code, 303)
        self.assertEqual(browser.post(target).status_code, 403)
        self.assertEqual(browser.get(PREFIX + "/member").status_code, 401)
        self.assertEqual(self.client.get(PREFIX + f"/member/slots?order_id={order_id}", headers=other_auth).status_code, 404)
        self.assertEqual(self.booking(other_auth, order_id, 1).status_code, 404)
        self.staff_login()
        self.assertEqual(self.staff.post(target, data={"csrf_token": "invalid"}).status_code, 400)
        self.action(other_member_id, order_id, "approve", expected=404)
        self.assertEqual(self.client.get(PREFIX + "/member", headers=auth).json["order"]["status"], "awaiting_review")
        staff_page = self.staff.get("/staff")
        self.assertEqual(self.staff.post("/staff/sign-out", data={"csrf_token": hidden(staff_page, "csrf_token")}).status_code, 303)
        self.assertEqual(self.staff.post(target).status_code, 403)

    def test_tokens_are_hashed_revocable_and_expiring(self):
        _, auth, _, _ = self.enroll()
        token = auth["Authorization"].split()[1]
        with self.app.app_context():
            digest = get_db().execute("SELECT token_digest FROM member_tokens").fetchone()[0]
        self.assertNotIn(token, digest)
        self.assertEqual(len(digest), 64)
        self.assertEqual(self.client.post(PREFIX + "/auth/sign-out", headers=auth).status_code, 204)
        self.assertEqual(self.client.get(PREFIX + "/member", headers=auth).status_code, 401)
        active = self.bearer("jordan@example.test", MEMBER_PASSWORD)
        with self.app.app_context():
            db = get_db()
            with db:
                db.execute("UPDATE member_tokens SET expires_at = '2000-01-01T00:00:00+00:00'")
        self.assertEqual(self.client.get(PREFIX + "/member", headers=active).status_code, 401)

    def test_slot_contention_and_failed_status_update_leave_consistent_records(self):
        _, first_auth, first_member, first_order = self.enroll()
        _, second_auth, second_member, second_order = self.enroll("Robin Shaw", "robin@example.test")
        self.staff_login()
        self.action(first_member, first_order, "approve")
        self.action(second_member, second_order, "approve")
        slot_id = self.client.get(PREFIX + "/member/slots", headers=first_auth).json["slots"][0]["id"]
        with self.app.app_context():
            db = get_db()
            db.execute(
                """CREATE TRIGGER fail_booking BEFORE UPDATE OF status ON orders
                   WHEN NEW.status = 'booked' BEGIN SELECT RAISE(ABORT, 'test booking failure'); END"""
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.booking(first_auth, first_order, slot_id)
        with self.app.app_context():
            db = get_db()
            self.assertEqual(db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0], 0)
            db.execute("DROP TRIGGER fail_booking")

        def claim(values):
            headers, order_id = values
            response = self.app.test_client().post(
                PREFIX + "/member/book", headers=headers, json={"order_id": order_id, "slot_id": slot_id}
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(claim, [(first_auth, first_order), (second_auth, second_order)]))
        self.assertEqual(sorted(outcomes), [200, 409])
        with self.app.app_context():
            self.assertEqual(get_db().execute("SELECT COUNT(*) FROM appointments").fetchone()[0], 1)

    def test_browser_booking_and_publication_use_the_shared_fulfillment_records(self):
        browser, auth, member_id, order_id = self.enroll()
        self.staff_login()
        self.action(member_id, order_id, "approve")
        slots = self.client.get(PREFIX + "/member/slots", headers=auth).json["slots"]
        booking = browser.get("/member/book")
        self.assertIn(b"Alder Draw Center", booking.data)
        self.assertEqual(booking.headers["Cache-Control"], "no-store")
        form = {"order_id": order_id, "slot_id": slots[0]["id"]}
        self.assertEqual(browser.post("/member/book", data=form).status_code, 400)
        form["csrf_token"] = hidden(booking, "csrf_token")
        booked = browser.post("/member/book", data=form, follow_redirects=True)
        self.assertIn(b"Appointment booked", booked.data)
        self.assertIn(b"Before your draw", booked.data)
        self.assertEqual(browser.post("/member/book", data=form).status_code, 303)
        appointment = self.client.get(PREFIX + "/member", headers=auth).json["appointment"]
        self.assertEqual(appointment["starts_at"], slots[0]["starts_at"])
        self.assertEqual(appointment["slot_id"], slots[0]["id"])

        self.action(member_id, order_id, "collect")
        self.action(member_id, order_id, "import")
        pending = browser.get("/member/results")
        self.assertIn(b"Reports pending", pending.data)
        self.assertNotIn(b"136 mg/dL", pending.data)
        self.assertEqual(browser.get("/member/results?draw=1").status_code, 404)
        self.action(member_id, order_id, "publish")
        report = browser.get("/member/results?draw=1")
        self.assertIn(b"Clinician summary", report.data)
        self.assertIn(b"136 mg/dL", report.data)

    def test_api_booking_appears_on_web_and_other_member_cannot_change_it(self):
        browser, auth, member_id, order_id = self.enroll()
        other, _, other_member, other_order = self.enroll("Robin Shaw", "robin@example.test")
        self.staff_login()
        self.action(member_id, order_id, "approve")
        self.action(other_member, other_order, "approve")
        slot = self.client.get(PREFIX + "/member/slots", headers=auth).json["slots"][0]
        form = other.get("/member/book")
        denied = other.post("/member/book", data={
            "csrf_token": hidden(form, "csrf_token"), "order_id": order_id, "slot_id": slot["id"],
        })
        self.assertEqual(denied.status_code, 404)
        self.assertEqual(self.booking(auth, order_id, slot["id"]).status_code, 200)
        for path in ("/member", "/member/book"):
            page = browser.get(path)
            self.assertIn(slot["starts_at"].encode(), page.data)
            self.assertIn(b"184 Alder Way", page.data)
        self.assertNotIn(b"Appointment booked", other.get("/member/book").data)

    def test_web_results_match_the_prepared_member_api_and_require_a_session(self):
        auth = self.prepared()
        self.assertEqual(self.client.get("/member/results").location, "/member")
        browser = self.app.test_client()
        sign_in = browser.get("/member")
        browser.post("/member", data={
            "csrf_token": hidden(sign_in, "csrf_token"),
            "email": PREPARED_EMAIL, "password": PREPARED_PASSWORD,
        })
        report = browser.get("/member/results")
        self.assertEqual(report.headers["Cache-Control"], "no-store")
        self.assertIn(b"Follow-up panel", report.data)
        self.assertIn(b"Oct 16, 2025", report.data)
        self.assertIn(b"Baseline panel", browser.get("/member/results?draw=1").data)
        trend = browser.get("/member/results?view=trends")
        self.assertIn(b'data-date="2025-04-10"', trend.data)
        self.assertIn(b'data-value="142.0"', trend.data)
        self.assertIn(b'data-date="2025-10-16"', trend.data)
        self.assertIn(b'data-value="104.0"', trend.data)
        self.assertIn(b"Decreased by 38 mg/dL", trend.data)
        self.assertIn(b"LDL cholesterol decreased by 38 mg/dL", browser.get("/member/results?view=insights").data)

        compose = browser.get("/member/results?view=chat")
        self.assertEqual(browser.post("/member/results", data={"question": LDL_QUESTION}).status_code, 400)
        answer = browser.post("/member/results?view=chat", data={
            "csrf_token": hidden(compose, "csrf_token"), "question": LDL_QUESTION,
        })
        api_answer = self.client.post(PREFIX + "/member/chat", headers=auth, json={"question": LDL_QUESTION})
        self.assertIn(api_answer.json["answer"].encode(), answer.data)
        self.assertIn(b'href="/member/results?draw=1"', answer.data)
        self.assertIn(b'href="/member/results?draw=2"', answer.data)
