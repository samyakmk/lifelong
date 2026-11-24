import { SymbolView } from "expo-symbols";
import type { SymbolViewProps } from "expo-symbols";
import type { PropsWithChildren } from "react";
import {
    ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View,
} from "react-native";
import type { ScrollViewProps, StyleProp, ViewStyle } from "react-native";

export const color = {
    canvas: "#F5F5ED",
    surface: "#FFFFFF",
    forest: "#16382C",
    deep: "#102D24",
    ink: "#1C2E25",
    muted: "#4E6358",
    line: "#D9E2D8",
    sage: "#E8EEE5",
    light: "#E8F0E7",
    lime: "#DCF292",
    amber: "#81521B",
    amberLight: "#FAEFD8",
    error: "#8B3632",
    errorLight: "#FCEAE6",
};

export type SymbolName = SymbolViewProps["name"];

export function Icon({ name, size = 20, tint = color.forest }: {
    name: SymbolName;
    size?: number;
    tint?: string;
}) {
    return <SymbolView name={name} size={size} tintColor={tint} weight="medium" accessible={false} />;
}

export function Brand() {
    return (
        <View style={styles.brand} accessible accessibilityLabel="Baseline Lab Demo">
            <View style={styles.mark}>
                <Icon name="waveform.path.ecg" size={21} tint={color.lime} />
            </View>
            <Text style={styles.brandText}>Baseline Lab</Text>
        </View>
    );
}

export function ScreenScroll({ children, contentContainerStyle, ...props }: ScrollViewProps) {
    return (
        <ScrollView
            {...props}
            style={[styles.scroll, props.style]}
            contentContainerStyle={[styles.scrollContent, contentContainerStyle]}
        >
            {children}
        </ScrollView>
    );
}

export function Panel({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
    return <View style={[styles.panel, style]}>{children}</View>;
}

export function Button({ label, onPress, variant = "primary", icon, busy = false, disabled = false }: {
    label: string;
    onPress: () => void;
    variant?: "primary" | "light" | "quiet";
    icon?: SymbolName;
    busy?: boolean;
    disabled?: boolean;
}) {
    const labelColor = variant === "primary" ? color.surface : color.forest;
    return (
        <Pressable
            accessibilityRole="button"
            accessibilityLabel={label}
            accessibilityState={{ disabled: disabled || busy, busy }}
            disabled={disabled || busy}
            onPress={onPress}
            style={({ pressed }) => [
                styles.button, styles[variant], (pressed || disabled) && styles.dim,
            ]}
        >
            <Text style={[styles.buttonText, { color: labelColor }]}>{label}</Text>
            {busy ? <ActivityIndicator color={labelColor} /> : icon && <Icon name={icon} size={16} tint={labelColor} />}
        </Pressable>
    );
}

export function Badge({ text, tone = "sage" }: { text: string; tone?: "sage" | "amber" | "dark" }) {
    return (
        <View style={[styles.badge, styles[tone]]}>
            <Text style={[styles.badgeText, tone === "dark" && styles.badgeLight, tone === "amber" && styles.badgeAmber]}>
                {text}
            </Text>
        </View>
    );
}

export function Loading({ label }: { label: string }) {
    return (
        <View style={styles.loading} accessible accessibilityRole="progressbar" accessibilityLabel={label}>
            <ActivityIndicator color={color.forest} />
            <Text style={styles.body}>{label}</Text>
        </View>
    );
}

export function ErrorNote({ text, onRetry }: { text: string; onRetry?: () => void }) {
    return (
        <View style={styles.error}>
            <Text accessibilityRole="alert" style={styles.errorText}>{text}</Text>
            {onRetry && <Button label="Try again" variant="quiet" onPress={onRetry} />}
        </View>
    );
}

export function Empty({ title, text, icon }: { title: string; text: string; icon: SymbolName }) {
    return (
        <Panel style={styles.empty}>
            <Icon name={icon} size={26} />
            <Text accessibilityRole="header" style={styles.sectionTitle}>{title}</Text>
            <Text style={styles.body}>{text}</Text>
        </Panel>
    );
}

export const styles = StyleSheet.create({
    screen: { flex: 1, backgroundColor: color.canvas },
    scroll: { flex: 1 },
    scrollContent: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 24, gap: 15 },
    brand: { flexDirection: "row", alignItems: "center", gap: 9 },
    mark: { width: 37, height: 37, borderRadius: 13, backgroundColor: color.forest, alignItems: "center", justifyContent: "center" },
    brandText: { color: color.ink, fontFamily: "Georgia", fontSize: 19 },
    title: { color: color.ink, fontFamily: "Georgia", fontSize: 37, letterSpacing: -1.8 },
    sectionTitle: { color: color.ink, fontSize: 19, fontWeight: "700", letterSpacing: -0.4 },
    body: { color: color.muted, fontSize: 15, lineHeight: 21 },
    small: { color: color.muted, fontSize: 13, lineHeight: 18 },
    overline: { color: color.muted, fontSize: 12, fontWeight: "700", letterSpacing: 0.9, textTransform: "uppercase" },
    panel: { borderRadius: 20, padding: 16, backgroundColor: color.surface, borderWidth: 1, borderColor: color.line, gap: 8 },
    row: { flexDirection: "row", alignItems: "center", gap: 10 },
    separated: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10 },
    button: { minHeight: 48, borderRadius: 14, paddingHorizontal: 15, paddingVertical: 10, flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 8 },
    primary: { backgroundColor: color.forest },
    light: { backgroundColor: color.lime },
    quiet: { backgroundColor: color.sage },
    dim: { opacity: 0.62 },
    buttonText: { fontSize: 16, fontWeight: "700", textAlign: "center", flexShrink: 1 },
    badge: { borderRadius: 30, paddingHorizontal: 9, paddingVertical: 5, alignSelf: "flex-start" },
    sage: { backgroundColor: color.sage },
    amber: { backgroundColor: color.amberLight },
    dark: { backgroundColor: "#2C4D3E" },
    badgeText: { fontSize: 12, fontWeight: "700", color: color.forest },
    badgeLight: { color: color.lime },
    badgeAmber: { color: color.amber },
    loading: { paddingVertical: 26, flexDirection: "row", justifyContent: "center", gap: 10, alignItems: "center" },
    error: { backgroundColor: color.errorLight, borderRadius: 13, padding: 12, gap: 10 },
    errorText: { color: color.error, fontSize: 14, lineHeight: 20 },
    empty: { alignItems: "flex-start", gap: 10 },
});
