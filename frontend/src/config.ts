export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
export const API_VERSION = import.meta.env.VITE_API_VERSION || "v1";
export const API_URL = `${API_BASE_URL}/api/${API_VERSION}`;
export const ENABLE_LOGGING =
  import.meta.env.VITE_ENABLE_LOGGING === "true" || import.meta.env.DEV;

export const logError = (...args: unknown[]) => {
  if (ENABLE_LOGGING) {
    console.error("[Failure Lab]", ...args);
  }
};
