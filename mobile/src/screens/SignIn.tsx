import { useRef, useState } from "react";
import { Keyboard, KeyboardAvoidingView, StyleSheet, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { errorMessage } from "../api";
import { useSession } from "../session";
import { Brand, Button, color, ErrorNote, Icon, Panel, ScreenScroll, styles } from "../ui";

export function SignIn() {
    const session = useSession();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const passwordInput = useRef<TextInput>(null);

    async function submit() {
        if (busy) {
            return;
        }
        if (!email.trim() || !password) {
            setError("Enter your member email and password.");
            return;
        }
        Keyboard.dismiss();
        setBusy(true);
        setError(null);
        try {
            await session.signIn(email, password);
        } catch (failure) {
            setError(errorMessage(failure));
        } finally {
            setBusy(false);
        }
    }

    return (
        <SafeAreaView style={styles.screen}>
            <KeyboardAvoidingView behavior="padding" style={styles.screen}>
                <ScreenScroll keyboardShouldPersistTaps="handled">
                    <Brand />
                    <View style={local.hero}>
                        <View style={local.heroMark}><Icon name="waveform.path.ecg" size={29} tint={color.lime} /></View>
                        <Text style={local.heroTitle}>Your labs, in focus.</Text>
                        <Text style={local.heroCaption}>View your lab reports and follow what changes from one draw to the next.</Text>
                    </View>
                    <Panel style={local.form}>
                        <Text accessibilityRole="header" style={styles.sectionTitle}>Member sign in</Text>
                        <Text style={styles.body}>Use the same account as the Baseline website.</Text>
                        {(error || session.notice) && <ErrorNote text={error ?? session.notice ?? ""} />}
                        <View style={local.field}>
                            <Text style={local.label}>Email address</Text>
                            <TextInput
                                accessibilityLabel="Email address"
                                testID="sign-in-email"
                                value={email}
                                onChangeText={setEmail}
                                style={local.input}
                                autoCapitalize="none"
                                autoCorrect={false}
                                autoComplete="username"
                                keyboardType="email-address"
                                returnKeyType="next"
                                onSubmitEditing={() => passwordInput.current?.focus()}
                            />
                        </View>
                        <View style={local.field}>
                            <Text style={local.label}>Password</Text>
                            <TextInput
                                accessibilityLabel="Password"
                                testID="sign-in-password"
                                ref={passwordInput}
                                value={password}
                                onChangeText={setPassword}
                                style={local.input}
                                autoComplete="current-password"
                                secureTextEntry
                                returnKeyType="go"
                                onSubmitEditing={() => void submit()}
                            />
                        </View>
                        <Button label={busy ? "Signing in…" : "Sign in"} icon="arrow.right" busy={busy} onPress={() => void submit()} />
                    </Panel>
                    <Text style={styles.small}>Baseline Lab Demo · Use synthetic account details.</Text>
                </ScreenScroll>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const local = StyleSheet.create({
    hero: { backgroundColor: color.deep, borderRadius: 23, padding: 21, gap: 9 },
    heroMark: { alignSelf: "flex-start", padding: 10, borderRadius: 16, borderWidth: 1, borderColor: "#436657", marginBottom: 4 },
    heroTitle: { color: color.surface, fontFamily: "Georgia", fontSize: 32, letterSpacing: -1.1 },
    heroCaption: { color: color.light, fontSize: 15, lineHeight: 21 },
    form: { gap: 12 },
    field: { gap: 5 },
    label: { fontSize: 14, color: color.ink, fontWeight: "600" },
    input: { minHeight: 48, borderWidth: 1, borderColor: color.line, borderRadius: 11, backgroundColor: color.canvas, paddingHorizontal: 12, paddingVertical: 9, color: color.ink, fontSize: 16 },
});
