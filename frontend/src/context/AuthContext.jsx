import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import * as authApi from "../api/auth.js";
import { getToken, setToken } from "../api/client.js";

/**
 * Auth context.
 *
 * Exposes:
 *   - user         : the current user object, or null
 *   - isLoading    : true while we're validating a stored JWT on first load
 *   - isAuthed     : convenience boolean
 *   - signup({email, password})
 *   - login({email, password})
 *   - logout()
 *
 * JWTs are persisted in localStorage (see api/client.js). On app boot, if a
 * token is present we hit /auth/me to either hydrate the user or wipe a
 * stale/expired token.
 */

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = getToken();
      if (!token) {
        if (!cancelled) setIsLoading(false);
        return;
      }
      try {
        const me = await authApi.fetchMe();
        if (!cancelled) setUser(me);
      } catch {
        setToken(null);
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async ({ email, password }) => {
    const tokens = await authApi.login({ email, password });
    setToken(tokens.access_token);
    const me = await authApi.fetchMe();
    setUser(me);
    return me;
  }, []);

  const signup = useCallback(async ({ email, password }) => {
    const tokens = await authApi.signup({ email, password });
    setToken(tokens.access_token);
    const me = await authApi.fetchMe();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthed: !!user,
      login,
      signup,
      logout,
    }),
    [user, isLoading, login, signup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside an <AuthProvider>.");
  }
  return ctx;
}
