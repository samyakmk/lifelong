import { useFocusEffect } from "@react-navigation/native";
import { useCallback, useRef, useState } from "react";
import { AppState } from "react-native";

import { errorMessage } from "./api";

export function useRemote<T>(load: (signal: AbortSignal) => Promise<T>, enabled = true) {
    const [data, setData] = useState<T | null>(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const running = useRef<AbortController | null>(null);

    const reload = useCallback(async () => {
        running.current?.abort();
        const controller = new AbortController();
        running.current = controller;
        setBusy(true);
        setError(null);
        try {
            const result = await load(controller.signal);
            if (!controller.signal.aborted) {
                setData(result);
            }
        } catch (failure) {
            if (!controller.signal.aborted) {
                setError(errorMessage(failure));
            }
        } finally {
            if (!controller.signal.aborted) {
                setBusy(false);
            }
        }
    }, [load]);

    useFocusEffect(useCallback(() => {
        if (!enabled) {
            return;
        }
        void reload();
        const foreground = AppState.addEventListener("change", (state) => {
            if (state === "active") {
                void reload();
            }
        });
        return () => {
            foreground.remove();
            running.current?.abort();
        };
    }, [enabled, reload]));

    return { data, busy, error, reload };
}
