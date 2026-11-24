import { useCallback, useState } from "react";
import { Keyboard, KeyboardAvoidingView, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { errorMessage } from "../api";
import type { ChatAnswer } from "../models";
import { useSession } from "../session";
import { Button, color, ErrorNote, Icon, Loading, Panel, ScreenScroll, styles } from "../ui";
import { useRemote } from "../useRemote";
import { Sources } from "./Sources";

export function Chat({ active, onOpen }: { active: boolean; onOpen: (id: number) => void }) {
    const { memberRequest } = useSession();
    const load = useCallback((signal: AbortSignal) => memberRequest<{ suggestions: string[] }>("/member/chat", { signal }), [memberRequest]);
    const prompts = useRemote(load, active);
    const [question, setQuestion] = useState("");
    const [asked, setAsked] = useState("");
    const [answer, setAnswer] = useState<ChatAnswer | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);

    async function ask(input: string) {
        const trimmed = input.trim();
        if (!trimmed || busy) {
            return;
        }
        Keyboard.dismiss();
        setAsked(trimmed);
        setQuestion("");
        setAnswer(null);
        setError(null);
        setBusy(true);
        try {
            setAnswer(await memberRequest<ChatAnswer>("/member/chat", { body: { question: trimmed } }));
        } catch (failure) {
            setError(errorMessage(failure));
        } finally {
            setBusy(false);
        }
    }

    return (
        <KeyboardAvoidingView
            behavior="padding"
            style={[local.screen, !active && local.hidden]}
            accessibilityElementsHidden={!active}
        >
            <ScreenScroll keyboardShouldPersistTaps="handled">
                {asked ? (
                    <View style={local.questionBubble}><Text style={local.questionText}>{asked}</Text></View>
                ) : (
                    <Panel>
                        <View style={styles.row}><Icon name="bubble.left.and.bubble.right" /><Text accessibilityRole="header" style={styles.sectionTitle}>Ask about your results</Text></View>
                        <Text style={styles.body}>Ask about a lab value, how it changed between draws, or which results fell outside the lab’s range.</Text>
                    </Panel>
                )}
                {!!busy && <Loading label="Looking up your reports…" />}
                {error && <ErrorNote text={error} onRetry={() => void ask(asked)} />}
                {answer && (
                    <Panel>
                        <View style={styles.row}><Icon name="text.alignleft" /><Text accessibilityRole="header" style={styles.sectionTitle}>Baseline reply</Text></View>
                        <Text accessibilityLiveRegion="polite" style={local.answer}>{answer.answer}</Text>
                        {answer.sources.length > 0 && (
                            <>
                                <Text accessibilityRole="header" style={styles.overline}>Sources</Text>
                                <Sources points={answer.sources} onOpen={onOpen} showMarker={answer.kind === "outside_range"} />
                            </>
                        )}
                    </Panel>
                )}
                {!asked && (
                    <View style={local.suggestions}>
                        <Text accessibilityRole="header" style={styles.overline}>Suggested questions</Text>
                        {prompts.error && <ErrorNote text={prompts.error} onRetry={() => void prompts.reload()} />}
                        {!prompts.data && !prompts.error && <Loading label="Loading suggestions…" />}
                        {prompts.data?.suggestions.map((suggestion) => (
                            <Pressable
                                key={suggestion}
                                accessibilityRole="button"
                                onPress={() => void ask(suggestion)}
                                style={({ pressed }) => [local.suggestion, pressed && styles.dim]}
                            >
                                <Text style={local.suggestionText}>{suggestion}</Text>
                                <Icon name="arrow.up.right" size={15} />
                            </Pressable>
                        ))}
                    </View>
                )}
            </ScreenScroll>
            <View style={local.composer}>
                <TextInput
                    accessibilityLabel="Ask about your lab results"
                    testID="chat-question"
                    placeholder="Ask about your lab results"
                    placeholderTextColor={color.muted}
                    value={question}
                    onChangeText={setQuestion}
                    maxLength={500}
                    multiline
                    style={local.input}
                />
                <Button label="Send" onPress={() => void ask(question)} disabled={!question.trim()} busy={busy} />
            </View>
        </KeyboardAvoidingView>
    );
}

const local = StyleSheet.create({
    screen: { flex: 1 },
    hidden: { display: "none" },
    questionBubble: { alignSelf: "flex-end", maxWidth: "88%", borderRadius: 16, borderBottomRightRadius: 5, paddingHorizontal: 13, paddingVertical: 9, backgroundColor: color.forest },
    questionText: { color: color.surface, fontSize: 15, lineHeight: 21 },
    answer: { color: color.ink, fontSize: 16, lineHeight: 23, marginVertical: 2 },
    suggestions: { gap: 8 },
    suggestion: { minHeight: 46, flexDirection: "row", alignItems: "center", gap: 9, borderRadius: 13, backgroundColor: color.sage, paddingHorizontal: 12, paddingVertical: 10 },
    suggestionText: { flex: 1, color: color.forest, fontSize: 15, lineHeight: 20, fontWeight: "600" },
    composer: { flexDirection: "row", alignItems: "flex-end", gap: 8, backgroundColor: color.canvas, borderTopWidth: 1, borderTopColor: color.line, paddingHorizontal: 16, paddingVertical: 8 },
    input: { flex: 1, minHeight: 48, maxHeight: 110, borderRadius: 13, borderWidth: 1, borderColor: color.line, backgroundColor: color.surface, color: color.ink, paddingHorizontal: 11, paddingVertical: 12, fontSize: 16 },
});
