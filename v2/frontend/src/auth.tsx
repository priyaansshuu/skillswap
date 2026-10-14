import { useEffect, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, clearSession, saveSession, session } from "./api/client";
import type { Me } from "./api/types";

import { AuthContext as Context } from "./auth-context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loggedIn, setLoggedIn] = useState(!!session());
  const [expired, setExpired] = useState(false);
  const [sessionVersion, setSessionVersion] = useState(0);
  const client = useQueryClient();
  const me = useQuery({
    queryKey: ["me", sessionVersion],
    queryFn: ({ signal }) => api<Me>("/me", { signal }),
    enabled: loggedIn,
    retry: false,
  });
  function logout() {
    clearSession();
    setLoggedIn(false);
    client.clear();
  }
  function login(token: string, seconds: number) {
    saveSession(token, seconds);
    setExpired(false);
    client.clear();
    setLoggedIn(true);
    setSessionVersion((v) => v + 1);
    void client.invalidateQueries({ queryKey: ["me"] });
  }
  useEffect(() => {
    const expire = () => {
      clearSession();
      setLoggedIn(false);
      setExpired(true);
      client.clear();
    };
    window.addEventListener("skillswap:expired", expire);
    const current = session();
    const timer = current
      ? window.setTimeout(expire, Math.max(0, current.expiresAt - Date.now()))
      : undefined;
    return () => {
      window.removeEventListener("skillswap:expired", expire);
      if (timer) window.clearTimeout(timer);
    };
  }, [loggedIn, client, sessionVersion]);
  return (
    <Context.Provider
      value={{
        loggedIn,
        me: me.data,
        loading: loggedIn && me.isPending,
        error: me.error,
        login,
        logout,
        expired,
      }}
    >
      {children}
    </Context.Provider>
  );
}
