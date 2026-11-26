const isLocalDevelopment =
    ["localhost", "127.0.0.1"].includes(
        window.location.hostname
    ) && window.location.port === "5500";

export const API_BASE_URL = isLocalDevelopment
    ? "http://127.0.0.1:8000/api/v1"
    : "/api/v1";
