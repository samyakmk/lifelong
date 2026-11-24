import { Text, View } from "react-native";

import type { Insight } from "../models";
import { Badge, Panel, styles } from "../ui";
import { Sources } from "./Sources";

export function Insights({ insights, onOpen }: { insights: Insight[]; onOpen: (id: number) => void }) {
    return (
        <>
            {insights.map((entry) => (
                <Panel key={`${entry.code}:${entry.change.unit}`}>
                    <View style={styles.separated}>
                        <Text accessibilityRole="header" style={[styles.sectionTitle, { flex: 1 }]}>{entry.name}</Text>
                        <Badge text={
                            entry.change.direction === "stable" ? "Stable" :
                                entry.change.direction === "decreased" ? "Decreased" : "Increased"
                        } />
                    </View>
                    <Text style={styles.body}>{entry.summary}</Text>
                    <Sources points={entry.sources} onOpen={onOpen} />
                </Panel>
            ))}
        </>
    );
}
