export const API_BASE_URL = (
    process.env.EXPO_PUBLIC_BASELINE_API_URL?.trim() || "http://127.0.0.1:5050/api/v1"
).replace(/\/+$/, "");

export class ApiError extends Error {
    constructor(readonly status: number, message: string) {
        super(message);
        this.name = "ApiError";
    }
}

export interface ApiOptions {
    method?: "GET" | "POST";
    body?: Record<string, unknown>;
    signal?: AbortSignal;
}

export async function request<T>(path: string, options: ApiOptions = {}, token?: string): Promise<T> {
    const controller = new AbortController();
    const cancel = () => controller.abort();
    const timeout = setTimeout(cancel, 12000);
    if (options.signal?.aborted) {
        cancel();
    }
    options.signal?.addEventListener("abort", cancel, { once: true });

    try {
        const response = await fetch(API_BASE_URL + path, {
            method: options.method ?? (options.body ? "POST" : "GET"),
            headers: {
                Accept: "application/json",
                ...(options.body && { "Content-Type": "application/json" }),
                ...(token && { Authorization: `Bearer ${token}` }),
            },
            body: options.body ? JSON.stringify(options.body) : undefined,
            signal: controller.signal,
        });
        if (response.status === 204) {
            return undefined as T;
        }
        const payload: unknown = await response.json().catch(() => null);
        if (!response.ok) {
            const error = (payload as { error?: { message?: unknown } } | null)?.error;
            const message = typeof error?.message === "string" ? error.message : "The member API returned an error.";
            throw new ApiError(response.status, message);
        }
        if (payload === null) {
            throw new ApiError(response.status, "The server returned an unexpected response.");
        }
        return payload as T;
    } catch (error) {
        if (error instanceof ApiError || options.signal?.aborted) {
            throw error;
        }
        throw new ApiError(0, "Can’t reach Baseline. Check that the local server is running and try again.");
    } finally {
        clearTimeout(timeout);
        options.signal?.removeEventListener("abort", cancel);
    }
}

export function errorMessage(error: unknown) {
    return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}
