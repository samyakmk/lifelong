import { ActionSheetIOS, Pressable, StyleSheet, Text, View } from "react-native";

import { formatDrawDate, referenceRange } from "../format";
import type { Measurement, MemberReport } from "../models";
import { Badge, color, Icon, Panel, styles } from "../ui";

export function Report({ reports, report, onSelect }: {
    reports: MemberReport[];
    report: MemberReport;
    onSelect: (id: number) => void;
}) {
    const groups = new Map<string, Measurement[]>();
    for (const measurement of report.measurements) {
        const group = groups.get(measurement.group) ?? [];
        group.push(measurement);
        groups.set(measurement.group, group);
    }

    function chooseDraw() {
        ActionSheetIOS.showActionSheetWithOptions(
            {
                title: "Choose a published draw",
                options: [...reports.map((entry) =>
                    `${entry.kind === "baseline" ? "Baseline" : "Follow-up"} · ${formatDrawDate(entry.collection_date)}`
                ), "Cancel"],
                cancelButtonIndex: reports.length,
            },
            (index) => {
                const choice = reports[index];
                if (choice) {
                    onSelect(choice.id);
                }
            },
        );
    }

    return (
        <>
            {reports.length > 1 && (
                <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={`Choose draw, ${formatDrawDate(report.collection_date)} selected`}
                    onPress={chooseDraw}
                    style={({ pressed }) => [local.draw, pressed && styles.dim]}
                >
                    <Icon name="calendar" />
                    <Text style={local.drawText}>Choose draw</Text>
                    <Text style={styles.small}>{formatDrawDate(report.collection_date)}</Text>
                    <Icon name="chevron.up.chevron.down" size={14} />
                </Pressable>
            )}
            <View style={local.hero}>
                <Badge text="Published" tone="dark" />
                <Text accessibilityRole="header" style={local.heroTitle}>
                    {report.kind === "baseline" ? "Baseline panel" : "Follow-up panel"}
                </Text>
                <Text style={local.heroDate}>Collected {formatDrawDate(report.collection_date)}</Text>
            </View>
            <Panel>
                <View style={styles.row}>
                    <Icon name="text.alignleft" />
                    <Text accessibilityRole="header" style={styles.sectionTitle}>Clinician summary</Text>
                </View>
                <Text style={styles.body}>{report.summary.replace(/^Sample clinician summary:\s*/i, "")}</Text>
            </Panel>
            {Array.from(groups, ([group, measurements]) => (
                <View key={group} style={local.group}>
                    <Text accessibilityRole="header" style={styles.sectionTitle}>{group}</Text>
                    <Panel style={local.measurements}>
                        {measurements.map((measurement, index) => {
                            const flagged = measurement.reference_flag === "above" || measurement.reference_flag === "below";
                            return (
                                <View key={measurement.code} style={[local.measurement, index > 0 && local.rule]}>
                                    <View style={local.measurementLabel}>
                                        <Text style={local.name}>{measurement.name}</Text>
                                        <Text style={styles.small}>{referenceRange(measurement)}</Text>
                                    </View>
                                    <View style={local.valueBlock}>
                                        <Text style={local.value}>{measurement.value} <Text style={styles.small}>{measurement.unit}</Text></Text>
                                        {flagged && <Badge text={measurement.reference_flag === "above" ? "Above range" : "Below range"} tone="amber" />}
                                    </View>
                                </View>
                            );
                        })}
                    </Panel>
                </View>
            ))}
        </>
    );
}

const local = StyleSheet.create({
    draw: { minHeight: 49, flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 13, backgroundColor: color.sage },
    drawText: { flex: 1, color: color.ink, fontSize: 15, fontWeight: "700" },
    hero: { padding: 18, borderRadius: 20, backgroundColor: color.deep, gap: 7 },
    heroTitle: { color: color.surface, fontFamily: "Georgia", fontSize: 28, letterSpacing: -0.65 },
    heroDate: { color: color.light, fontSize: 14 },
    group: { gap: 8 },
    measurements: { paddingVertical: 0, gap: 0 },
    measurement: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 10, paddingVertical: 12 },
    rule: { borderTopWidth: 1, borderTopColor: color.line },
    measurementLabel: { flex: 1, gap: 2 },
    name: { color: color.ink, fontSize: 15, fontWeight: "600" },
    valueBlock: { alignItems: "flex-end", gap: 4, flexShrink: 1 },
    value: { color: color.ink, fontSize: 17, fontWeight: "700", textAlign: "right" },
});
