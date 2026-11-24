import { Pressable, StyleSheet, Text, View } from "react-native";

import { formatDrawDate } from "../format";
import type { SourcePoint } from "../models";
import { color, Icon, styles } from "../ui";

export function Sources({ points, onOpen, showMarker = false }: {
    points: SourcePoint[];
    onOpen: (reportId: number) => void;
    showMarker?: boolean;
}) {
    return (
        <View style={local.list}>
            {points.map((point) => (
                <Pressable
                    key={`${point.report_id}:${point.code}:${point.unit}`}
                    accessibilityRole="button"
                    accessibilityLabel={`${point.name}, ${point.value} ${point.unit}, ${formatDrawDate(point.collection_date)}, open report ${point.report_id}`}
                    onPress={() => onOpen(point.report_id)}
                    style={({ pressed }) => [local.row, pressed && styles.dim]}
                >
                    <View style={local.ref}>
                        {!!showMarker && <Text style={local.date}>{point.name}</Text>}
                        <Text style={showMarker ? styles.small : local.date}>{formatDrawDate(point.collection_date)}</Text>
                        <Text style={styles.small}>Report #{point.report_id}</Text>
                    </View>
                    <Text style={local.value}>{point.value} {point.unit}</Text>
                    <Icon name="arrow.up.right" size={13} />
                </Pressable>
            ))}
        </View>
    );
}

const local = StyleSheet.create({
    list: { gap: 6 },
    row: { minHeight: 48, paddingHorizontal: 10, paddingVertical: 7, flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 10, backgroundColor: color.sage },
    ref: { flex: 1 },
    date: { color: color.ink, fontSize: 13, fontWeight: "700" },
    value: { color: color.forest, fontSize: 14, fontWeight: "700", flexShrink: 1, textAlign: "right" },
});
