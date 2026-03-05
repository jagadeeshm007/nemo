// ==============================================================================
// Register API Route — Creates a new user in Keycloak via Admin REST API
// ==============================================================================

import { NextRequest, NextResponse } from "next/server";

const KEYCLOAK_URL =
  process.env.KEYCLOAK_URL ||
  process.env.NEXT_PUBLIC_KEYCLOAK_URL ||
  "http://localhost:8180";
const KEYCLOAK_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM || "nemo";
const KEYCLOAK_ADMIN_USERNAME = process.env.KEYCLOAK_ADMIN_USERNAME || "admin";
const KEYCLOAK_ADMIN_PASSWORD = process.env.KEYCLOAK_ADMIN_PASSWORD || "admin";

interface RegisterBody {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

// ── Get Admin Token ─────────────────────────────────────────────────────────

async function getAdminToken(): Promise<string> {
  const response = await fetch(
    `${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token`,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "password",
        client_id: "admin-cli",
        username: KEYCLOAK_ADMIN_USERNAME,
        password: KEYCLOAK_ADMIN_PASSWORD,
      }).toString(),
    },
  );

  if (!response.ok) {
    throw new Error("Failed to obtain admin token");
  }

  const data = await response.json();
  return data.access_token;
}

// ── POST /api/auth/register ─────────────────────────────────────────────────

export async function POST(request: NextRequest) {
  try {
    const body: RegisterBody = await request.json();

    // Validate input
    if (!body.username || !body.email || !body.password) {
      return NextResponse.json(
        { error: "Username, email, and password are required" },
        { status: 400 },
      );
    }

    if (body.username.length < 3) {
      return NextResponse.json(
        { error: "Username must be at least 3 characters" },
        { status: 400 },
      );
    }

    if (body.password.length < 6) {
      return NextResponse.json(
        { error: "Password must be at least 6 characters" },
        { status: 400 },
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { error: "Invalid email format" },
        { status: 400 },
      );
    }

    // Get admin token
    const adminToken = await getAdminToken();

    // Create user in Keycloak
    const createResponse = await fetch(
      `${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${adminToken}`,
        },
        body: JSON.stringify({
          username: body.username,
          email: body.email,
          firstName: body.firstName || "",
          lastName: body.lastName || "",
          enabled: true,
          emailVerified: true,
          credentials: [
            {
              type: "password",
              value: body.password,
              temporary: false,
            },
          ],
          realmRoles: ["nemo-user"],
        }),
      },
    );

    if (createResponse.status === 409) {
      return NextResponse.json(
        { error: "Username or email already exists" },
        { status: 409 },
      );
    }

    if (!createResponse.ok) {
      const errorData = await createResponse.json().catch(() => ({}));
      console.error("Keycloak user creation failed:", errorData);
      return NextResponse.json(
        { error: errorData.errorMessage || "Failed to create user" },
        { status: createResponse.status },
      );
    }

    // Extract user ID from Location header
    const locationHeader = createResponse.headers.get("Location");
    const userId = locationHeader?.split("/").pop();

    // Assign nemo-user role if userId is available
    if (userId) {
      try {
        // Get the nemo-user role ID
        const rolesResponse = await fetch(
          `${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/roles/nemo-user`,
          {
            headers: { Authorization: `Bearer ${adminToken}` },
          },
        );

        if (rolesResponse.ok) {
          const role = await rolesResponse.json();

          // Assign role to user
          await fetch(
            `${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users/${userId}/role-mappings/realm`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${adminToken}`,
              },
              body: JSON.stringify([role]),
            },
          );
        }
      } catch (err) {
        console.warn("Failed to assign role, user still created:", err);
      }
    }

    return NextResponse.json(
      { message: "User registered successfully" },
      { status: 201 },
    );
  } catch (err) {
    console.error("Registration error:", err);
    return NextResponse.json(
      { error: "Registration service unavailable" },
      { status: 503 },
    );
  }
}
