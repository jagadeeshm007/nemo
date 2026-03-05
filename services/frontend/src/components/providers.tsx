"use client";

// ==============================================================================
// Providers — React Query + Auth + Theme
// ==============================================================================

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { Toaster } from "sonner";
import { useAuthStore } from "@/store/authStore";

function AuthInitializer({ children }: { children: React.ReactNode }) {
  const { initAuth, refreshAuth, isAuthenticated } = useAuthStore();
  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null,
  );

  // Initialize auth on mount
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // Set up token refresh interval (every 4 minutes — tokens expire in 5min)
  useEffect(() => {
    if (isAuthenticated) {
      refreshIntervalRef.current = setInterval(
        () => {
          refreshAuth();
        },
        4 * 60 * 1000,
      );
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [isAuthenticated, refreshAuth]);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthInitializer>{children}</AuthInitializer>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
