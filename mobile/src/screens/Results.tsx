import { useCallback, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import type { Insight, MemberReport, Trend } from "../models";
import { Chat } from "../results/Chat";
import { Insights } from "../results/Insights";
import { Report } from "../results/Report";
import { Trends } from "../results/Trends";
import { useSession } from "../session";
import { Badge, color, Empty, ErrorNote, Loading, ScreenScroll, styles } from "../ui";
import { useRemote } from "../useRemote";

const sections = ["Report", "Trends", "Insights", "Chat"] as const;
type Section = typeof sections[number];

export function Results() {
    const { memberRequest } = useSession();
    const [section, setSection] = useState<Section>("Report");
    const [reportId, setReportId] = useState<number | null>(null);
    const [marker, setMarker] = useState<string | null>(null);

    const fetchReports = useCallback((signal: AbortSignal) => memberRequest<{ reports: MemberReport[] }>("/member/reports", { signal }), [memberRequest]);
    const fetchTrends = useCallback((signal: AbortSignal) => memberRequest<{ trends: Trend[] }>("/member/trends", { signal }), [memberRequest]);
    const fetchInsights = useCallback((signal: AbortSignal) => memberRequest<{ insights: Insight[] }>("/member/insights", { signal }), [memberRequest]);

    const reportState = useRemote(fetchReports);
    const trends = useRemote(fetchTrends, section === "Trends");
    const insights = useRemote(fetchInsights, section === "Insights");
    const reports = reportState.data?.reports ?? [];
    const report = reports.find((item) => item.id === reportId) ?? reports[reports.length - 1];

    function openSource(id: number) {
        setReportId(id);
        setSection("Report");
    }

    return (
        <SafeAreaView style={styles.screen} edges={["top", "left", "right"]}>
            <View style={local.heading}>
                <View style={styles.separated}>
                    <Text accessibilityRole="header" style={styles.title}>Results</Text>
                    {reports.length > 0 && <Badge text={`${reports.length} published ${reports.length === 1 ? "draw" : "draws"}`} />}
                </View>
                <View style={local.sections}>
                    {sections.map((tab) => {
                        const selected = tab === section;
                        return (
                            <Pressable
                                key={tab}
                                accessibilityRole="tab"
                                accessibilityState={{ selected }}
                                onPress={() => setSection(tab)}
                                style={[local.section, selected && local.active]}
                            >
                                <Text style={[local.sectionText, selected && local.activeText]}>{tab}</Text>
                            </Pressable>
                        );
                    })}
                </View>
            </View>
            {section !== "Chat" && (
                <ScreenScroll key={section}>
                    {section === "Report" && (
                        <>
                            {reportState.error && <ErrorNote text={reportState.error} onRetry={() => void reportState.reload()} />}
                            {!reportState.data && !reportState.error && <Loading label="Loading your reports…" />}
                            {reportState.data && !report && <Empty icon="doc.text" title="Reports pending" text="Published reports will appear here after the lab draw and staff review." />}
                            {report && <Report key={report.id} reports={reports} report={report} onSelect={setReportId} />}
                        </>
                    )}
                    {section === "Trends" && (
                        <>
                            {trends.error && <ErrorNote text={trends.error} onRetry={() => void trends.reload()} />}
                            {!trends.data && !trends.error && <Loading label="Loading trends…" />}
                            {trends.data?.trends.length === 0 && <Empty icon="chart.line.uptrend.xyaxis" title="No trends yet" text="Published biomarkers will appear here with their collection dates." />}
                            {!!trends.data?.trends.length && <Trends trends={trends.data.trends} selected={marker} onSelect={setMarker} onOpen={openSource} />}
                        </>
                    )}
                    {section === "Insights" && (
                        <>
                            {insights.error && <ErrorNote text={insights.error} onRetry={() => void insights.reload()} />}
                            {!insights.data && !insights.error && <Loading label="Loading insights…" />}
                            {insights.data?.insights.length === 0 && <Empty icon="chart.bar.xaxis" title="Insights pending" text="Insights appear after two published draws with comparable measurements." />}
                            {!!insights.data?.insights.length && <Insights insights={insights.data.insights} onOpen={openSource} />}
                        </>
                    )}
                </ScreenScroll>
            )}
            <Chat active={section === "Chat"} onOpen={openSource} />
        </SafeAreaView>
    );
}

const local = StyleSheet.create({
    heading: { gap: 9, paddingHorizontal: 20, paddingTop: 9, paddingBottom: 4 },
    sections: { flexDirection: "row", backgroundColor: color.sage, padding: 3, borderRadius: 14, gap: 3 },
    section: { flex: 1, minHeight: 44, alignItems: "center", justifyContent: "center", borderRadius: 11, paddingVertical: 5 },
    active: { backgroundColor: color.forest },
    sectionText: { color: color.forest, fontSize: 14, fontWeight: "700" },
    activeText: { color: color.surface },
});
