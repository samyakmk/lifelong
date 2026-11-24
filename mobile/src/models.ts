export type OrderStatus =
    | "awaiting_review"
    | "approved"
    | "booked"
    | "collected"
    | "results_imported"
    | "published";

export interface DrawCenter {
    name: string;
    address: string;
    timezone: string;
}

export interface Appointment {
    id: number;
    order_id: number;
    slot_id: number | null;
    starts_at: string;
    draw_center: DrawCenter;
    prep: string;
}

export interface Dashboard {
    member: { id: number; name: string; email: string };
    order: { id: number; status: OrderStatus; status_label: string; draw_center: string } | null;
    next_step: { title: string; detail: string } | null;
    appointment: Appointment | null;
}

export interface Slot {
    id: number;
    starts_at: string;
}

export interface Availability {
    order_id: number | null;
    status: OrderStatus | null;
    draw_center: DrawCenter | null;
    slots: Slot[];
}

export interface Measurement {
    code: string;
    name: string;
    group: string;
    value: number;
    unit: string;
    reference_low: number | null;
    reference_high: number | null;
    reference_flag: "below" | "within" | "above" | "unavailable";
}

export interface MemberReport {
    id: number;
    kind: "baseline" | "follow_up";
    collection_date: string;
    summary: string;
    measurements: Measurement[];
}

export interface SourcePoint extends Measurement {
    report_id: number;
    order_id: number;
    collection_date: string;
}

export interface Change {
    delta: number;
    direction: "increased" | "decreased" | "stable";
    unit: string;
}

export interface Trend {
    code: string;
    name: string;
    unit: string;
    points: SourcePoint[];
    change: Change | null;
}

export interface Insight {
    code: string;
    name: string;
    summary: string;
    change: Change;
    sources: SourcePoint[];
}

export interface ChatAnswer {
    kind: "change" | "latest" | "first" | "outside_range" | "unsupported" | "insufficient_data";
    answer: string;
    sources: SourcePoint[];
    suggestions: string[];
}
