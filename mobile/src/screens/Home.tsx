import type { BottomTabScreenProps } from "@react-navigation/bottom-tabs";
import type { CompositeScreenProps } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useState } from "react";
import { Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { errorMessage } from "../api";
import { formatVisit } from "../format";
import type { Dashboard } from "../models";
import type { MemberTabs, RootStack } from "../navigation";
import { useSession } from "../session";
import { Badge, Brand, Button, color, Empty, ErrorNote, Icon, Loading, Panel, ScreenScroll, styles } from "../ui";
import { useRemote } from "../useRemote";

type Props = CompositeScreenProps<BottomTabScreenProps<MemberTabs, "Home">, NativeStackScreenProps<RootStack>>;

export function Home({ navigation }: Props) {
    const { memberRequest, signOut } = useSession();
    const load = useCallback((signal: AbortSignal) => memberRequest<Dashboard>("/member", { signal }), [memberRequest]);
    const dashboard = useRemote(load);
    const [signOutError, setSignOutError] = useState<string | null>(null);
    const [signingOut, setSigningOut] = useState(false);

    async function leave() {
        setSigningOut(true);
        setSignOutError(null);
        try {
            await signOut();
        } catch (error) {
            setSignOutError(errorMessage(error));
        } finally {
            setSigningOut(false);
        }
    }

    const { member, order, next_step: next, appointment } = dashboard.data ?? {};
    return (
        <SafeAreaView edges={["top", "left", "right"]} style={styles.screen}>
            <ScreenScroll refreshControl={
                <RefreshControl refreshing={dashboard.busy && dashboard.data !== null} onRefresh={() => void dashboard.reload()} tintColor={color.forest} />
            }>
                <View style={styles.separated}>
                    <Brand />
                    <Pressable
                        accessibilityRole="button"
                        disabled={signingOut}
                        accessibilityState={{ disabled: signingOut }}
                        onPress={() => void leave()}
                        style={local.signOut}
                    >
                        <Text style={local.signOutText}>{signingOut ? "Signing out…" : "Sign out"}</Text>
                    </Pressable>
                </View>
                {signOutError && <ErrorNote text={signOutError} onRetry={() => void leave()} />}
                {dashboard.error && <ErrorNote text={dashboard.error} onRetry={() => void dashboard.reload()} />}
                {!dashboard.data && !dashboard.error && <Loading label="Loading your dashboard…" />}
                {member && (
                    <>
                        <Text accessibilityRole="header" style={styles.title}>Hi, {member.name.split(" ")[0]}.</Text>
                        {order && next ? (
                            <View style={local.hero}>
                                <Badge text={order.status_label} tone="dark" />
                                <Text style={local.heroTitle}>{next.title}</Text>
                                <Text style={local.heroBody}>{next.detail}</Text>
                                {order.status === "approved" && (
                                    <Button label="Book a draw" variant="light" icon="calendar" onPress={() => navigation.navigate("Book", { orderId: order.id })} />
                                )}
                                {order.status === "published" && (
                                    <Button label="Open Results" variant="light" icon="arrow.right" onPress={() => navigation.navigate("Results")} />
                                )}
                            </View>
                        ) : (
                            <Empty icon="list.clipboard" title="No order yet" text="Your lab orders will appear here after you sign up on the website." />
                        )}
                        {appointment && (
                            <Panel>
                                <View style={styles.row}>
                                    <Icon name="calendar" />
                                    <Text accessibilityRole="header" style={styles.sectionTitle}>{order?.status === "booked" ? "Draw appointment" : "Most recent draw"}</Text>
                                </View>
                                <Text style={local.visit}>{formatVisit(appointment.starts_at, appointment.draw_center.timezone)}</Text>
                                <Text style={styles.body}>{appointment.draw_center.name}</Text>
                                <Text style={styles.small}>{appointment.draw_center.address}</Text>
                                {order?.status === "booked" && (
                                    <View style={local.prep}>
                                        <Text style={local.prepTitle}>Before your draw</Text>
                                        <Text style={styles.body}>{appointment.prep}</Text>
                                    </View>
                                )}
                            </Panel>
                        )}
                    </>
                )}
            </ScreenScroll>
        </SafeAreaView>
    );
}

const local = StyleSheet.create({
    signOut: { minHeight: 44, justifyContent: "center", paddingHorizontal: 6 },
    signOutText: { color: color.forest, fontSize: 15, fontWeight: "600" },
    hero: { backgroundColor: color.deep, borderRadius: 23, padding: 20, gap: 12 },
    heroTitle: { color: color.surface, fontFamily: "Georgia", fontSize: 29, letterSpacing: -0.7 },
    heroBody: { color: color.light, fontSize: 15, lineHeight: 21 },
    visit: { color: color.ink, fontWeight: "700", fontSize: 17, marginTop: 4 },
    prep: { borderTopWidth: 1, borderTopColor: color.line, paddingTop: 10, marginTop: 4, gap: 3 },
    prepTitle: { color: color.ink, fontSize: 14, fontWeight: "700" },
});
