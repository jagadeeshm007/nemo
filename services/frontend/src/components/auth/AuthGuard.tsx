"use client";

// ==============================================================================
// AuthGuard — Protects routes, redirects unauthenticated users to /login
// ==============================================================================

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Loader2, Bot } from "lucide-react";

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function AuthGuard({ children, requiredRoles }: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuthStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Show loading spinner during auth initialization
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-primary/20 flex items-center justify-center">
            <Bot className="h-7 w-7 text-primary" />
          </div>
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Not authenticated — will redirect
  if (!isAuthenticated) {
    return null;
  }

  // Check required roles
  if (requiredRoles && requiredRoles.length > 0 && user) {
    const hasRole = requiredRoles.some((role) =>
      user.realm_roles.includes(role),
    );
    if (!hasRole) {
      return (
        <div className="flex h-screen items-center justify-center bg-background">
          <div className="text-center max-w-md px-8">
            <h2 className="text-xl font-bold mb-2">Access Denied</h2>
            <p className="text-muted-foreground text-sm">
              You don&apos;t have permission to access this page. Required role:{" "}
              {requiredRoles.join(" or ")}.
            </p>
            <button
              onClick={() => router.push("/")}
              className="mt-6 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm hover:bg-primary/90 transition-colors"
            >
              Go Home
            </button>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}
