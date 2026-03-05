// ==============================================================================
// Keycloak OIDC Client — Token management, user info, logout
// ==============================================================================

import { decodeJwt } from "jose";

const KEYCLOAK_URL =
  process.env.NEXT_PUBLIC_KEYCLOAK_URL || "http://localhost:8180";
const KEYCLOAK_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM || "nemo";
const KEYCLOAK_CLIENT_ID =
  process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || "nemo-frontend";

const TOKEN_ENDPOINT = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`;
const LOGOUT_ENDPOINT = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout`;

// ── Types ───────────────────────────────────────────────────────────────────

export interface KeycloakTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  refresh_expires_in: number;
  token_type: string;
  scope: string;
}

export interface KeycloakUser {
  sub: string;
  preferred_username: string;
  email: string;
  email_verified: boolean;
  name: string;
  given_name: string;
  family_name: string;
  realm_roles: string[];
}

// ── Token Operations ────────────────────────────────────────────────────────

/**
 * Login with username + password via Resource Owner Password Credentials grant.
 * The nemo-frontend client has directAccessGrantsEnabled: true.
 */
export async function loginWithCredentials(
  username: string,
  password: string,
): Promise<KeycloakTokenResponse> {
  const body = new URLSearchParams({
    grant_type: "password",
    client_id: KEYCLOAK_CLIENT_ID,
    username,
    password,
    scope: "openid profile email roles",
  });

  const response = await fetch(TOKEN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401 || error.error === "invalid_grant") {
      throw new AuthError(
        "Invalid username or password",
        "INVALID_CREDENTIALS",
      );
    }
    if (error.error === "invalid_client") {
      throw new AuthError("Authentication service unavailable", "CLIENT_ERROR");
    }
    throw new AuthError(
      error.error_description || "Login failed",
      "LOGIN_FAILED",
    );
  }

  return response.json();
}

/**
 * Refresh an access token using a refresh token.
 */
export async function refreshAccessToken(
  refreshToken: string,
): Promise<KeycloakTokenResponse> {
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    client_id: KEYCLOAK_CLIENT_ID,
    refresh_token: refreshToken,
  });

  const response = await fetch(TOKEN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!response.ok) {
    throw new AuthError(
      "Session expired. Please log in again.",
      "TOKEN_EXPIRED",
    );
  }

  return response.json();
}

/**
 * Logout from Keycloak (invalidate refresh token).
 */
export async function logoutFromKeycloak(refreshToken: string): Promise<void> {
  try {
    await fetch(LOGOUT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: KEYCLOAK_CLIENT_ID,
        refresh_token: refreshToken,
      }).toString(),
    });
  } catch {
    // Best-effort logout — don't block the UI
  }
}

// ── User Info ───────────────────────────────────────────────────────────────

/**
 * Decode a JWT access token to extract user information.
 * Does NOT verify the signature (that's the API gateway's job).
 */
export function getUserFromToken(accessToken: string): KeycloakUser {
  const payload = decodeJwt(accessToken);

  return {
    sub: (payload.sub as string) || "",
    preferred_username: (payload.preferred_username as string) || "",
    email: (payload.email as string) || "",
    email_verified: (payload.email_verified as boolean) || false,
    name: (payload.name as string) || "",
    given_name: (payload.given_name as string) || "",
    family_name: (payload.family_name as string) || "",
    realm_roles: (payload.realm_roles as string[]) || [],
  };
}

/**
 * Check if an access token is expired (with 30s buffer).
 */
export function isTokenExpired(accessToken: string): boolean {
  try {
    const payload = decodeJwt(accessToken);
    const exp = (payload.exp || 0) as number;
    return Date.now() >= (exp - 30) * 1000;
  } catch {
    return true;
  }
}

// ── Error Class ─────────────────────────────────────────────────────────────

export class AuthError extends Error {
  code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "AuthError";
    this.code = code;
  }
}
