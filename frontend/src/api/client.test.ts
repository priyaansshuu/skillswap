import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, clearSession, saveSession, session } from "./client";

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
});
describe("account sessions", () => {
  it("keeps credentials per tab and drops expired sessions", () => {
    saveSession("test-session", 60);
    expect(session()?.token).toBe("test-session");
    expect(localStorage.getItem("skillswap-session")).toBeNull();
    sessionStorage.setItem(
      "skillswap-session",
      JSON.stringify({ token: "old-test-session", expiresAt: 0 }),
    );
    expect(session()).toBeNull();
  });
  it("clears an invalid session and notifies the app after a server rejection", async () => {
    saveSession("test-session", 60);
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              error: { code: "INVALID_TOKEN", message: "Please log in again" },
            }),
            { status: 401 },
          ),
      ),
    );
    const expired = vi.fn();
    window.addEventListener("skillswap:expired", expired);
    await expect(api("/me")).rejects.toBeInstanceOf(ApiError);
    expect(session()).toBeNull();
    expect(expired).toHaveBeenCalledTimes(1);
    window.removeEventListener("skillswap:expired", expired);
  });
  it("returns an actionable network error instead of an unhandled fetch failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Connection refused");
      }),
    );
    await expect(api("/me")).rejects.toMatchObject({
      code: "NETWORK_ERROR",
      status: 0,
    });
  });
});
