import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useState } from "react";
import { Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError, errorMessage } from "../api";
import { formatSlotDay, formatSlotTime, formatVisit } from "../format";
import type { Appointment, Availability, Slot } from "../models";
import type { RootStack } from "../navigation";
import { useSession } from "../session";
import { Button, color, Empty, ErrorNote, Icon, Loading, Panel, ScreenScroll, styles } from "../ui";
import { useRemote } from "../useRemote";

export function Book({ route, navigation }: NativeStackScreenProps<RootStack, "Book">) {
    const { orderId } = route.params;
    const { memberRequest } = useSession();
    const load = useCallback((signal: AbortSignal) => memberRequest<Availability>(`/member/slots?order_id=${orderId}`, { signal }), [memberRequest, orderId]);
    const availability = useRemote(load);
    const [selected, setSelected] = useState<number | null>(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const center = availability.data?.draw_center;
    const selection = availability.data?.slots.find((slot) => slot.id === selected);

    const days = new Map<string, Slot[]>();
    if (center) {
        for (const slot of availability.data?.slots ?? []) {
            const day = formatSlotDay(slot.starts_at, center.timezone);
            const slots = days.get(day) ?? [];
            slots.push(slot);
            days.set(day, slots);
        }
    }

    async function book() {
        if (!selection || saving) {
            return;
        }
        setSaving(true);
        setError(null);
        try {
            await memberRequest<{ appointment: Appointment }>("/member/book", {
                body: { order_id: orderId, slot_id: selection.id },
            });
            navigation.goBack();
        } catch (failure) {
            setError(errorMessage(failure));
            if (failure instanceof ApiError && failure.status === 409) {
                setSelected(null);
                void availability.reload();
            }
        } finally {
            setSaving(false);
        }
    }

    return (
        <SafeAreaView edges={["left", "right", "bottom"]} style={styles.screen}>
            <ScreenScroll refreshControl={
                <RefreshControl refreshing={availability.busy && availability.data !== null} onRefresh={() => void availability.reload()} tintColor={color.forest} />
            }>
                {center && (
                    <Panel>
                        <View style={styles.row}>
                            <Icon name="mappin.circle" />
                            <Text accessibilityRole="header" style={styles.sectionTitle}>{center.name}</Text>
                        </View>
                        <Text style={styles.body}>{center.address}</Text>
                    </Panel>
                )}
                {availability.error && <ErrorNote text={availability.error} onRetry={() => void availability.reload()} />}
                {error && <ErrorNote text={error} />}
                {!availability.data && !availability.error && <Loading label="Finding available times…" />}
                {availability.data && days.size === 0 && (
                    <Empty
                        icon="calendar"
                        title={availability.data.status === "booked" ? "Appointment already booked" : "No times available"}
                        text={availability.data.status === "booked" ? "Return Home to see your saved appointment." : "Refresh to check for an available time, or return Home to see your order status."}
                    />
                )}
                {center && Array.from(days, ([day, slots]) => (
                    <View key={day} style={local.day}>
                        <Text accessibilityRole="header" style={styles.sectionTitle}>{day}</Text>
                        <View style={local.slots}>
                            {slots.map((slot) => {
                                const active = selected === slot.id;
                                return (
                                    <Pressable
                                        key={slot.id}
                                        accessibilityRole="radio"
                                        accessibilityLabel={formatVisit(slot.starts_at, center.timezone)}
                                        accessibilityState={{ checked: active, disabled: saving }}
                                        disabled={saving}
                                        onPress={() => { setError(null); setSelected(slot.id); }}
                                        style={[local.slot, active && local.selected]}
                                    >
                                        <Text style={[local.slotLabel, active && local.selectedLabel]}>{formatSlotTime(slot.starts_at, center.timezone)}</Text>
                                    </Pressable>
                                );
                            })}
                        </View>
                    </View>
                ))}
            </ScreenScroll>
            {availability.data && (
                <View style={local.confirm}>
                    {selection && center && <Text style={styles.small}>{formatVisit(selection.starts_at, center.timezone)} · {center.name}</Text>}
                    {days.size > 0 ? (
                        <Button label={saving ? "Booking…" : "Confirm booking"} icon="checkmark" busy={saving} disabled={!selection} onPress={() => void book()} />
                    ) : (
                        <Button label="Return Home" variant="quiet" onPress={() => navigation.goBack()} />
                    )}
                </View>
            )}
        </SafeAreaView>
    );
}

const local = StyleSheet.create({
    day: { gap: 7 },
    slots: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
    slot: { minHeight: 45, justifyContent: "center", paddingHorizontal: 13, borderWidth: 1, borderColor: color.line, borderRadius: 12, backgroundColor: color.surface },
    selected: { backgroundColor: color.forest, borderColor: color.forest },
    slotLabel: { color: color.ink, fontSize: 15, fontWeight: "600" },
    selectedLabel: { color: color.surface },
    confirm: { paddingHorizontal: 20, paddingVertical: 12, borderTopWidth: 1, borderTopColor: color.line, gap: 7, backgroundColor: color.canvas },
});
