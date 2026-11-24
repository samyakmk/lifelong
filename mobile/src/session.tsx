import * as SecureStore from "expo-secure-store";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { PropsWithChildren } from "react";

import { API_BASE_URL, ApiError, request } from "./api";
import type { ApiOptions } from "./api";

const SESSION_KEY = "baseline.member.v1";

interface Session {
    token: string | null;
    restoring: boolean;
    notice: string | null;
    signIn: (email: string, password: string) => Promise<void>;
    signOut: () => Promise<void>;
    memberRequest: <T>(path: string, options?: ApiOptions) => Promise<T>;
}

const SessionContext = createContext<Session | null>(null);

export function SessionProvider({ children }: PropsWithChildren) {
    const [token, setToken] = useState<string | null>(null);
    const [restoring, setRestoring] = useState(true);
    const [notice, setNotice] = useState<string | null>(null);
    const current = useRef<string | null>(null);
    const removal = useRef<Promise<void> | null>(null);

    useEffect(() => {
        let mounted = true;
        async function restore() {
            try {
                const value = await SecureStore.getItemAsync(SESSION_KEY);
                const stored = value ? JSON.parse(value) : null;
                if (mounted && stored?.url === API_BASE_URL && typeof stored.token === "string") {
                    current.current = stored.token;
                    setToken(stored.token);
                }
            } catch {
                if (mounted) {
                    setNotice("Your saved session couldn’t be opened. Sign in to continue.");
                }
            } finally {
                if (mounted) {
                    setRestoring(false);
                }
            }
        }
        void restore();
        return () => { mounted = false; };
    }, []);

    const clearSession = useCallback((expected: string, message: string | null) => {
        if (current.current !== expected) {
            return;
        }
        current.current = null;
        removal.current = SecureStore.deleteItemAsync(SESSION_KEY).catch(() => {});
        setNotice(message);
        setToken(null);
    }, []);

    const signIn = useCallback(async (email: string, password: string) => {
        const result = await request<{ access_token: string }>("/auth/sign-in", {
            body: { email: email.trim(), password },
        });
        await removal.current;
        await SecureStore.setItemAsync(
            SESSION_KEY,
            JSON.stringify({ url: API_BASE_URL, token: result.access_token }),
            { keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY },
        );
        current.current = result.access_token;
        setNotice(null);
        setToken(result.access_token);
    }, []);

    const signOut = useCallback(async () => {
        const active = current.current;
        if (!active) {
            return;
        }
        try {
            await request<void>("/auth/sign-out", { method: "POST" }, active);
        } catch (error) {
            if (!(error instanceof ApiError && error.status === 401)) {
                throw error;
            }
        }
        clearSession(active, null);
        await removal.current;
    }, [clearSession]);

    const memberRequest = useCallback(async <T,>(path: string, options?: ApiOptions): Promise<T> => {
        const active = current.current;
        if (!active) {
            throw new ApiError(401, "Sign in to continue.");
        }
        try {
            return await request<T>(path, options, active);
        } catch (error) {
            if (error instanceof ApiError && error.status === 401) {
                clearSession(active, "Your session expired. Sign in to continue.");
            }
            throw error;
        }
    }, [clearSession]);

    return (
        <SessionContext.Provider value={{ token, restoring, notice, signIn, signOut, memberRequest }}>
            {children}
        </SessionContext.Provider>
    );
}

export function useSession() {
    const session = useContext(SessionContext);
    if (session === null) {
        throw new Error("SessionProvider is required.");
    }
    return session;
}
