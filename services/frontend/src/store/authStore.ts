// ==============================================================================
// Auth Store — Zustand store for authentication state
// ==============================================================================

import { create } from "zustand";
import {
  loginWithCredentials,
  refreshAccessToken,
  logoutFromKeycloak,
  getUserFromToken,
  isTokenExpired,
  type KeycloakUser,
  AuthError,
} from "@/lib/keycloak";

// ── Types ───────────────────────────────────────────────────────────────────

interface AuthState {
  user: KeycloakUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (username: string, password: string) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string,
    firstName: string,
    lastName: string,
  ) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<boolean>;
  initAuth: () => Promise<void>;
  clearError: () => void;
}

type AuthStore = AuthState & AuthActions;

// ── Storage Keys ────────────────────────────────────────────────────────────

const STORAGE_KEYS = {
  ACCESS_TOKEN: "nemo_token",
  REFRESH_TOKEN: "nemo_refresh_token",
} as const;

// ── Store ───────────────────────────────────────────────────────────────────

export const useAuthStore = create<AuthStore>((set, get) => ({
  // State
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  // ── Login ───────────────────────────────────────────────────────────────
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });

    try {
      const tokens = await loginWithCredentials(username, password);
      const user = getUserFromToken(tokens.access_token);

      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);

      set({
        user,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof AuthError ? err.message : "An unexpected error occurred";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  // ── Register ────────────────────────────────────────────────────────────
  register: async (
    username: string,
    email: string,
    password: string,
    firstName: string,
    lastName: string,
  ) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          password,
          firstName,
          lastName,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new AuthError(
          data.error || "Registration failed",
          "REGISTRATION_FAILED",
        );
      }

      // Auto-login after successful registration
      await get().login(username, password);
    } catch (err) {
      const message =
        err instanceof AuthError ? err.message : "An unexpected error occurred";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  // ── Logout ──────────────────────────────────────────────────────────────
  logout: async () => {
    const { refreshToken } = get();

    if (refreshToken) {
      await logoutFromKeycloak(refreshToken);
    }

    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);

    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  // ── Refresh ─────────────────────────────────────────────────────────────
  refreshAuth: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return false;

    try {
      const tokens = await refreshAccessToken(refreshToken);
      const user = getUserFromToken(tokens.access_token);

      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);

      set({
        user,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
      });

      return true;
    } catch {
      // Refresh failed — clear auth state
      await get().logout();
      return false;
    }
  },

  // ── Initialize ──────────────────────────────────────────────────────────
  initAuth: async () => {
    if (typeof window === "undefined") {
      set({ isLoading: false });
      return;
    }

    const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);

    if (!accessToken || !refreshToken) {
      set({ isLoading: false });
      return;
    }

    // If access token is still valid, use it
    if (!isTokenExpired(accessToken)) {
      const user = getUserFromToken(accessToken);
      set({
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
      });
      return;
    }

    // Access token expired — try refresh
    try {
      const tokens = await refreshAccessToken(refreshToken);
      const user = getUserFromToken(tokens.access_token);

      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);

      set({
        user,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      // Both tokens expired — user needs to log in again
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      set({ isLoading: false });
    }
  },

  // ── Clear Error ─────────────────────────────────────────────────────────
  clearError: () => set({ error: null }),
}));
