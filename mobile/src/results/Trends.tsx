import { useState } from "react";
import { ActionSheetIOS, Pressable, StyleSheet, Text, View } from "react-native";

import { formatDrawDate } from "../format";
import type { Trend } from "../models";
import { Badge, color, Icon, Panel, styles } from "../ui";
import { Sources } from "./Sources";

export const trendKey = (trend: Trend) => `${trend.code}:${trend.unit}`;

const HEIGHT = 140;
const INSET = 10;

function chartBounds(values: number[]) {
    const min = Math.min(...values);
    const max = Math.max(...values);
    const raw = (max - min) / 2 || Math.max(Math.abs(min) * 0.07, 0.1);
    const magnitude = 10 ** Math.floor(Math.log10(raw));
    const step = (raw <= 2 * magnitude ? 2 : raw <= 5 * magnitude ? 5 : 10) * magnitude;
    const bottom = Math.floor(min / step) * step;
    const top = Math.ceil(max / step) * step;
    return top > bottom ? { bottom, top } : { bottom: bottom - step, top: top + step };
}

function TrendChart({ trend }: { trend: Trend }) {
    const [width, setWidth] = useState(0);
    const { points, unit } = trend;
    const { bottom, top } = chartBounds(points.map((point) => point.value));
    const dates = points.map((point) => Date.parse(point.collection_date));
    const first = dates[0];
    const last = dates[dates.length - 1];
    const positions = points.map((point, index) => ({
        x: first === last ? width / 2 : INSET + (dates[index] - first) / (last - first) * (width - 2 * INSET),
        y: INSET + (top - point.value) / (top - bottom) * (HEIGHT - 2 * INSET),
    }));
    const chartLabel = `${trend.name} trend. ${points.map((point) =>
        `${formatDrawDate(point.collection_date)}: ${point.value} ${unit}`
    ).join(". ")}`;

    return (
        <View
            accessible
            accessibilityRole="image"
            accessibilityLabel={chartLabel}
            style={local.chart}
        >
            <View style={local.axis}>
                {[top, (top + bottom) / 2, bottom].map((tick) => (
                    <Text key={tick} style={local.tick}>{tick.toLocaleString("en-US", { maximumFractionDigits: 3 })}</Text>
                ))}
            </View>
            <View style={local.plotColumn}>
                <View style={local.plot} onLayout={(event) => setWidth(event.nativeEvent.layout.width)}>
                    {[INSET, HEIGHT / 2, HEIGHT - INSET].map((line) => (
                        <View key={line} style={[local.gridline, { top: line }]} />
                    ))}
                    {width > 2 * INSET && positions.slice(1).map((point, index) => {
                        const start = positions[index];
                        const dx = point.x - start.x;
                        const dy = point.y - start.y;
                        const length = Math.hypot(dx, dy);
                        return (
                            <View
                                key={points[index + 1].report_id}
                                style={[local.line, {
                                    width: length,
                                    left: (point.x + start.x - length) / 2,
                                    top: (point.y + start.y) / 2 - 1,
                                    transform: [{ rotate: `${Math.atan2(dy, dx)}rad` }],
                                }]}
                            />
                        );
                    })}
                    {width > 2 * INSET && positions.map((point, index) => (
                        <View key={points[index].report_id} style={[local.dot, { left: point.x - 5, top: point.y - 5 }]} />
                    ))}
                </View>
                <View style={styles.separated}>
                    <Text style={styles.small}>{formatDrawDate(points[0].collection_date)}</Text>
                    {points.length > 1 && <Text style={styles.small}>{formatDrawDate(points[points.length - 1].collection_date)}</Text>}
                </View>
            </View>
        </View>
    );
}

export function Trends({ trends, selected, onSelect, onOpen }: {
    trends: Trend[];
    selected: string | null;
    onSelect: (key: string) => void;
    onOpen: (id: number) => void;
}) {
    const trend = trends.find((item) => trendKey(item) === selected)
        ?? trends.find((item) => item.code === "ldl")
        ?? trends[0];
    const delta = trend.change;
    const direction = delta?.direction;
    const change = delta && (direction === "stable"
        ? "Stable"
        : `${direction === "decreased" ? "↓" : "↑"} ${Math.abs(delta.delta)} ${delta.unit}`);

    function chooseBiomarker() {
        ActionSheetIOS.showActionSheetWithOptions(
            {
                title: "Choose a biomarker",
                options: [...trends.map((item) => `${item.name} · ${item.unit}`), "Cancel"],
                cancelButtonIndex: trends.length,
            },
            (index) => {
                const choice = trends[index];
                if (choice) {
                    onSelect(trendKey(choice));
                }
            },
        );
    }

    return (
        <>
            <Pressable
                accessibilityRole="button"
                accessibilityLabel={`Choose biomarker, ${trend.name} selected`}
                onPress={chooseBiomarker}
                style={({ pressed }) => [local.marker, pressed && styles.dim]}
            >
                <Icon name="line.3.horizontal.decrease" />
                <View style={local.markerLabel}>
                    <Text style={styles.small}>Biomarker</Text>
                    <Text style={local.markerName}>{trend.name}</Text>
                </View>
                <Icon name="chevron.up.chevron.down" size={15} />
            </Pressable>
            <Panel style={local.chartPanel}>
                <View style={styles.separated}>
                    <View style={local.markerLabel}>
                        <Text accessibilityRole="header" style={styles.sectionTitle}>{trend.name}</Text>
                        <Text style={styles.small}>{trend.unit}</Text>
                    </View>
                    {change && <Badge text={change} />}
                </View>
                <TrendChart trend={trend} />
                {!delta && <Text style={styles.small}>Another comparable draw is needed to measure change.</Text>}
            </Panel>
            <Panel>
                <Text accessibilityRole="header" style={styles.sectionTitle}>Draw values</Text>
                <Sources points={trend.points} onOpen={onOpen} />
            </Panel>
        </>
    );
}

const local = StyleSheet.create({
    marker: { minHeight: 54, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 8, backgroundColor: color.sage, flexDirection: "row", alignItems: "center", gap: 9 },
    markerLabel: { flex: 1, gap: 2 },
    markerName: { color: color.ink, fontWeight: "700", fontSize: 16 },
    chartPanel: { gap: 13 },
    chart: { flexDirection: "row", gap: 8 },
    axis: { width: 35, height: HEIGHT, justifyContent: "space-between", paddingTop: 2, paddingBottom: 2 },
    tick: { color: color.muted, fontSize: 12, textAlign: "right" },
    plotColumn: { flex: 1, gap: 6 },
    plot: { height: HEIGHT, position: "relative" },
    gridline: { height: 1, backgroundColor: color.line, position: "absolute", width: "100%" },
    line: { height: 3, borderRadius: 2, backgroundColor: color.forest, position: "absolute" },
    dot: { width: 10, height: 10, borderRadius: 5, borderWidth: 2, borderColor: color.forest, backgroundColor: color.lime, position: "absolute" },
});
