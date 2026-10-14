import { createContext, useContext } from "react";
import type { Me } from "./api/types";

export type Auth = {
  loggedIn: boolean;
  me: Me | undefined;
  loading: boolean;
  error: Error | null;
  login: (token: string, seconds: number) => void;
  logout: () => void;
  expired: boolean;
};
export const AuthContext = createContext<Auth | null>(null);
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw Error("AuthProvider is required");
  return value;
}
