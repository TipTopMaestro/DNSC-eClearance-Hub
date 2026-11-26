
import { API_BASE_URL } from "./config.js";

const TOKEN_KEY = "dnsc_access_token";

export function setToken(token) {
    sessionStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
    sessionStorage.removeItem(TOKEN_KEY);
}

export async function apiRequest(
    endpoint,
    {
        method = "GET",
        body,
        authenticated = true
    } = {}
) {
    const headers = {
        "Accept": "application/json"
    };

    if (body !== undefined) {
        headers["Content-Type"] = "application/json";
    }

    if (authenticated) {
        const token = getToken();

        if (!token) {
            throw new Error("Please log in first.");
        }

        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            method,
            headers,
            credentials: "omit",
            cache: "no-store",
            body: body !== undefined
                ? JSON.stringify(body)
                : undefined
        }
    );

    const data = await response.json()
        .catch(() => null);

    if (!response.ok) {
        if (
            response.status === 401
            && authenticated
        ) {
            clearToken();
        }

        const error = new Error(
            typeof data?.detail === "string"
                ? data.detail
                : `Request failed (${response.status})`
        );

        error.status = response.status;

        throw error;
    }

    return data;
}
