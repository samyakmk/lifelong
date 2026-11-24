import re
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from werkzeug.security import check_password_hash

from baseline import create_app
from baseline.db import get_db
from baseline.orders import ORDER_STEPS

PASSWORD = "fictional-demo-password"


class SignupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = create_app(Path(self.directory.name))
        self.app.testing = True
        self.client = self.app.test_client()

    @staticmethod
    def token(response):
        return re.search(rb'name="csrf_token" value="([^"]+)"', response.data)[1].decode()

    def form(self, client, email="avery@example.test", name="Avery Quinn"):
        response = client.get("/join")
        return {
            "csrf_token": self.token(response),
            "checkout_key": re.search(rb'name="checkout_key" value="([^"]+)"', response.data)[1].decode(),
            "email": email,
            "name": name,
            "password": PASSWORD,
            "goal": "establish_baseline",
            "prior_testing": "no",
            "draw_time": "morning",
            "consent": "yes",
        }

    def assert_record_counts(self, expected):
        with self.app.app_context():
            db = get_db()
            for table in ("members", "intakes", "consents", "purchases", "orders"):
                with self.subTest(table=table):
                    self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], expected)

    def test_signup_creates_linked_records_and_persists_account_and_session(self):
        result = self.client.post("/join", data=self.form(self.client))
        self.assertEqual(result.status_code, 303)
        self.assertEqual(result.location, "/member")
        self.assert_record_counts(1)
        with self.app.app_context():
            record = get_db().execute(
                """SELECT o.status, o.kind, i.goal, c.version, p.status AS purchase_status,
                          p.amount_cents, m.password_hash
                   FROM orders o JOIN purchases p ON p.id = o.purchase_id
                   JOIN members m ON m.id = o.member_id AND m.id = p.member_id
                   JOIN intakes i ON i.member_id = m.id
                   JOIN consents c ON c.member_id = m.id"""
            ).fetchone()
        self.assertEqual(tuple(record)[:6], (
            "awaiting_review", "baseline", "establish_baseline", "demo-v1", "simulated", 14900,
        ))
        self.assertNotEqual(record["password_hash"], PASSWORD)
        self.assertTrue(check_password_hash(record["password_hash"], PASSWORD))

        restarted = create_app(Path(self.directory.name)).test_client()
        cookie_name = self.app.config["SESSION_COOKIE_NAME"]
        restarted.set_cookie(cookie_name, self.client.get_cookie(cookie_name).value)
        dashboard = restarted.get("/member")
        self.assertIn(b"Awaiting review", dashboard.data)
        self.assertIn(b"#0001", dashboard.data)
        self.assertIn(b"no-store", dashboard.headers["Cache-Control"].encode())

        signed_out = restarted.post("/member/sign-out", data={"csrf_token": self.token(dashboard)})
        self.assertEqual(signed_out.status_code, 303)
        sign_in = restarted.get("/member")
        signed_in = restarted.post("/member", data={
            "csrf_token": self.token(sign_in),
            "email": "AVERY@example.test",
            "password": PASSWORD,
        }, follow_redirects=True)
        self.assertIn(b"Your demo order is confirmed", signed_in.data)
        self.assert_record_counts(1)

    def test_concurrent_replays_and_duplicate_email_leave_one_order(self):
        values = self.form(self.client)
        cookie_name = self.app.config["SESSION_COOKIE_NAME"]
        cookie = self.client.get_cookie(cookie_name).value

        def submit():
            replay = self.app.test_client()
            replay.set_cookie(cookie_name, cookie)
            return replay.post("/join", data=values).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(lambda _: submit(), range(2))), [303, 303])
        duplicate_client = self.app.test_client()
        duplicate = duplicate_client.post(
            "/join", data=self.form(duplicate_client, email="AVERY@example.test")
        )
        self.assertEqual(duplicate.status_code, 422)
        self.assertIn(b"An account is already using this email", duplicate.data)
        self.assert_record_counts(1)

    def test_missing_consent_invalid_intake_and_csrf_create_nothing(self):
        values = self.form(self.client)
        missing_token = {**values, "csrf_token": ""}
        bad_intake = {**values, "goal": "unknown", "consent": ""}
        self.assertEqual(self.client.post("/join", data=missing_token).status_code, 400)
        self.assertEqual(self.client.post("/join", data=bad_intake).status_code, 422)
        self.assertEqual(self.client.post("/member", data={}).status_code, 400)
        self.assertEqual(self.client.post("/member/sign-out", data={}).status_code, 400)
        self.assert_record_counts(0)

    def test_late_order_failure_rolls_back_signup(self):
        with self.app.app_context():
            db = get_db()
            db.execute(
                """CREATE TRIGGER fail_signup BEFORE INSERT ON orders
                   BEGIN SELECT RAISE(ABORT, 'test order failure'); END"""
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.client.post("/join", data=self.form(self.client))
        self.assert_record_counts(0)

    def test_member_dashboard_scopes_orders_to_authenticated_account(self):
        self.client.post("/join", data=self.form(self.client))
        other = self.app.test_client()
        other.post("/join", data=self.form(other, email="lee@example.test", name="Lee Lin"))
        with self.app.app_context():
            db = get_db()
            with db:
                db.execute("UPDATE orders SET status = 'approved' WHERE id = 2")
            with self.assertRaises(sqlite3.IntegrityError), db:
                db.execute("UPDATE orders SET status = 'published' WHERE id = 1")
        first = self.client.get("/member?member_id=2&order_id=2")
        second = other.get("/member?member_id=1&order_id=1")
        self.assertIn(b"#0001", first.data)
        self.assertNotIn(b"#0002", first.data)
        self.assertIn(b"Awaiting review", first.data)
        self.assertIn(b"#0002", second.data)
        self.assertIn(b"Schedule your draw", second.data)
        self.assertNotIn(b"#0001", second.data)

    def test_member_can_have_two_published_orders_with_distinct_reports(self):
        self.client.post("/join", data=self.form(self.client))
        with self.app.app_context():
            db = get_db()
            with db:
                db.execute(
                    """INSERT INTO purchases (member_id, checkout_key, plan_code, amount_cents)
                       VALUES (1, 'follow-up-checkout', 'baseline-panel', 14900)"""
                )
                db.execute(
                    """INSERT INTO orders (member_id, purchase_id, kind, draw_center_id)
                       VALUES (1, 2, 'follow_up', 1)"""
                )
                for order_id, collected_at in ((1, "2026-05-01"), (2, "2026-11-01")):
                    for status in list(ORDER_STEPS)[1:]:
                        db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
                    db.execute(
                        "UPDATE orders SET collected_at = ? WHERE id = ?", (collected_at, order_id)
                    )
                    db.execute(
                        "INSERT INTO reports (order_id, published_at) VALUES (?, CURRENT_TIMESTAMP)",
                        (order_id,),
                    )
            reports = db.execute(
                """SELECT o.collected_at FROM reports r JOIN orders o ON o.id = r.order_id
                   WHERE o.member_id = 1 AND o.status = 'published' AND r.published_at IS NOT NULL
                   ORDER BY o.collected_at"""
            ).fetchall()
        self.assertEqual([report['collected_at'] for report in reports], ["2026-05-01", "2026-11-01"])
