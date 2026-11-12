export const SESSION_EXPIRED_EVENT = "webai:session-expired";

export async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return null;
  }

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    // A 401 outside the auth endpoints means the session expired; the
    // AuthProvider clears the user and protected routes send them to /login.
    if (response.status === 401 && !path.startsWith("/api/auth/")) {
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }
    const message = result?.detail || "Không thể hoàn tất yêu cầu. Vui lòng thử lại.";
    const error = new Error(typeof message === "string" ? message : "Dữ liệu gửi lên không hợp lệ.");
    error.status = response.status;
    throw error;
  }
  if (result === null) {
    throw new Error("Máy chủ trả về dữ liệu không hợp lệ. Vui lòng thử lại.");
  }
  return result;
}
