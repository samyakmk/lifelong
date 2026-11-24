CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intakes (
    member_id INTEGER PRIMARY KEY REFERENCES members(id),
    goal TEXT NOT NULL,
    prior_testing TEXT NOT NULL,
    draw_time TEXT NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consents (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    version TEXT NOT NULL,
    consent_text TEXT NOT NULL,
    accepted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (member_id, version)
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    checkout_key TEXT NOT NULL UNIQUE,
    plan_code TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'simulated' CHECK (status = 'simulated'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id, member_id)
);

CREATE TABLE IF NOT EXISTS draw_centers (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    purchase_id INTEGER NOT NULL UNIQUE,
    draw_center_id INTEGER NOT NULL REFERENCES draw_centers(id),
    kind TEXT NOT NULL CHECK (kind IN ('baseline', 'follow_up')),
    status TEXT NOT NULL DEFAULT 'awaiting_review' CHECK (status IN (
        'awaiting_review', 'approved', 'booked', 'collected', 'results_imported', 'published'
    )),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TEXT,
    collected_at TEXT,
    FOREIGN KEY (purchase_id, member_id) REFERENCES purchases(id, member_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS one_baseline_per_member
    ON orders (member_id) WHERE kind = 'baseline';
CREATE INDEX IF NOT EXISTS orders_by_member ON orders (member_id, id);

CREATE TABLE IF NOT EXISTS draw_slots (
    id INTEGER PRIMARY KEY,
    draw_center_id INTEGER NOT NULL REFERENCES draw_centers(id),
    starts_at TEXT NOT NULL,
    UNIQUE (draw_center_id, starts_at)
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id),
    slot_id INTEGER REFERENCES draw_slots(id),
    starts_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id),
    summary TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TEXT
);

CREATE TABLE IF NOT EXISTS report_measurements (
    report_id INTEGER NOT NULL REFERENCES reports(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    reference_low REAL,
    reference_high REAL,
    PRIMARY KEY (report_id, code),
    CHECK (reference_high >= reference_low)
);

CREATE TABLE IF NOT EXISTS staff_users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS member_tokens (
    token_digest TEXT PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    expires_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE TRIGGER IF NOT EXISTS enforce_order_progression
BEFORE UPDATE OF status ON orders
WHEN NEW.status <> OLD.status AND NOT (
    (OLD.status = 'awaiting_review' AND NEW.status = 'approved') OR
    (OLD.status = 'approved' AND NEW.status = 'booked') OR
    (OLD.status = 'booked' AND NEW.status = 'collected') OR
    (OLD.status = 'collected' AND NEW.status = 'results_imported') OR
    (OLD.status = 'results_imported' AND NEW.status = 'published')
)
BEGIN
    SELECT RAISE(ABORT, 'Invalid order status transition');
END;
