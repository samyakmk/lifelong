import type { Measurement } from "./models";

const drawDate = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
});

export function formatDrawDate(date: string) {
    return drawDate.format(new Date(date + "T00:00:00Z"));
}

export function formatVisit(date: string, timeZone: string) {
    return new Intl.DateTimeFormat("en-US", {
        weekday: "short", month: "short", day: "numeric", hour: "numeric",
        minute: "2-digit", timeZoneName: "short", timeZone,
    }).format(new Date(date));
}

export function formatSlotDay(date: string, timeZone: string) {
    return new Intl.DateTimeFormat("en-US", {
        weekday: "long", month: "long", day: "numeric", timeZone,
    }).format(new Date(date));
}

export function formatSlotTime(date: string, timeZone: string) {
    return new Intl.DateTimeFormat("en-US", {
        hour: "numeric", minute: "2-digit", timeZone,
    }).format(new Date(date));
}

export function referenceRange(measurement: Measurement) {
    const { reference_low: low, reference_high: high, unit } = measurement;
    if (low === null && high === null) {
        return "Range unavailable";
    }
    if (low === null) {
        return `≤ ${high} ${unit}`;
    }
    if (high === null) {
        return `≥ ${low} ${unit}`;
    }
    return `${low}–${high} ${unit}`;
}
