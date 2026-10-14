import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../auth";
import { clearSession } from "../api/client";
import { AuthPage } from "./account";

afterEach(() => {
  cleanup();
  clearSession();
  vi.unstubAllGlobals();
});
it("shows login errors while preserving the supplied email", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            error: {
              code: "INVALID_CREDENTIALS",
              message: "Invalid email or password",
            },
          }),
          { status: 401 },
        ),
    ),
  );
  render(
    <MemoryRouter>
      <QueryClientProvider
        client={
          new QueryClient({ defaultOptions: { queries: { retry: false } } })
        }
      >
        <AuthProvider>
          <AuthPage />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "member@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "Not-a-real-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Log in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Invalid email or password",
  );
  expect(screen.getByLabelText("Email")).toHaveValue("member@example.com");
  expect(screen.getByRole("button", { name: "Log in" })).toBeEnabled();
});

it("keeps the password label distinct from its registration instructions", () => {
  render(
    <MemoryRouter>
      <QueryClientProvider client={new QueryClient()}>
        <AuthProvider>
          <AuthPage register />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
  expect(
    screen.getByLabelText("Password", { exact: true }),
  ).toHaveAccessibleDescription("Use 12–128 characters.");
});
