const panel = document.querySelector("[data-trend]");
const canvas = panel.querySelector("[data-trend-chart]");
const context = canvas.getContext("2d");
const points = Array.from(panel.querySelectorAll("[data-chart-point]"), ({dataset}) => ({
    date: Date.parse(dataset.date),
    label: dataset.label,
    value: Number(dataset.value),
}));

function axisBounds(values) {
    const low = Math.min(...values);
    const high = Math.max(...values);
    const interval = (high - low) / 3 || Math.max(Math.abs(low) * 0.08, 0.1);
    const magnitude = 10 ** Math.floor(Math.log10(interval));
    const step = ([1, 2, 5, 10].find((size) => size * magnitude >= interval) ?? 10) * magnitude;
    const bottom = Math.floor(low / step) * step;
    const top = Math.ceil(high / step) * step;
    return top > bottom ? [bottom, top] : [bottom - step, top + step];
}

function draw() {
    const {width, height} = canvas.getBoundingClientRect();
    if (!width || !height) {
        return;
    }
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);

    context.font = "12px system-ui";
    const [min, max] = axisBounds(points.map(({value}) => value));
    const ticks = Array.from({length: 4}, (_, index) => max - index * (max - min) / 3);
    const labels = ticks.map((value) => value.toLocaleString("en-US", {maximumFractionDigits: 3}));
    const left = Math.max(35, ...labels.map((label) => context.measureText(label).width + 12));
    const right = width - 12;
    const top = 27;
    const bottom = height - 35;
    const earliest = points[0].date;
    const latest = points.at(-1).date;

    context.textBaseline = "middle";
    context.textAlign = "right";
    labels.forEach((label, index) => {
        const y = top + index * (bottom - top) / 3;
        context.strokeStyle = "#d6e0d1";
        context.beginPath();
        context.moveTo(left, y);
        context.lineTo(right, y);
        context.stroke();
        context.fillStyle = "#505e51";
        context.fillText(label, left - 8, y);
    });

    const positions = points.map(({date, value}) => ({
        x: earliest === latest ? (left + right) / 2 : left + 8 + (date - earliest) / (latest - earliest) * (right - left - 16),
        y: top + (max - value) / (max - min) * (bottom - top),
    }));
    context.strokeStyle = "#28563e";
    context.lineWidth = 2.5;
    context.beginPath();
    positions.forEach(({x, y}, index) => {
        if (index === 0) {
            context.moveTo(x, y);
        } else {
            context.lineTo(x, y);
        }
    });
    context.stroke();
    positions.forEach(({x, y}) => {
        context.beginPath();
        context.arc(x, y, 5, 0, Math.PI * 2);
        context.fillStyle = "#d9ed9a";
        context.fill();
        context.stroke();
    });

    context.fillStyle = "#505e51";
    context.textAlign = points.length === 1 ? "center" : "left";
    context.fillText(points[0].label, points.length === 1 ? positions[0].x : left, bottom + 19);
    if (points.length > 1) {
        context.textAlign = "right";
        context.fillText(points.at(-1).label, right, bottom + 19);
    }
}

if (context && points.length) {
    canvas.closest("figure").hidden = false;
    new ResizeObserver(draw).observe(canvas);
    draw();
}
