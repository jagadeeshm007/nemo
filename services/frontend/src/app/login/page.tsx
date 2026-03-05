"use client";

// ==============================================================================
// Login Page — Branded login form with Keycloak OIDC
// ==============================================================================

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Bot, Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await login(username, password);
      router.push("/");
    } catch {
      // Error is set in the store
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel — Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary/20 via-primary/10 to-background items-center justify-center p-12">
        <div className="max-w-md text-center">
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="h-16 w-16 rounded-2xl bg-primary/20 flex items-center justify-center">
              <Bot className="h-10 w-10 text-primary" />
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-4">Nemo</h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Enterprise Agentic RAG platform with multi-LLM orchestration,
            intelligent document retrieval, and a powerful plugin ecosystem.
          </p>
          <div className="mt-12 grid grid-cols-3 gap-6 text-sm text-muted-foreground">
            <div className="space-y-2">
              <div className="h-10 w-10 mx-auto rounded-lg bg-primary/10 flex items-center justify-center">
                <span className="text-primary text-lg">🤖</span>
              </div>
              <p>Multi-LLM</p>
            </div>
            <div className="space-y-2">
              <div className="h-10 w-10 mx-auto rounded-lg bg-primary/10 flex items-center justify-center">
                <span className="text-primary text-lg">📄</span>
              </div>
              <p>RAG Pipeline</p>
            </div>
            <div className="space-y-2">
              <div className="h-10 w-10 mx-auto rounded-lg bg-primary/10 flex items-center justify-center">
                <span className="text-primary text-lg">🔌</span>
              </div>
              <p>Plugin System</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel — Login Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-primary/20 flex items-center justify-center">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-2xl font-bold">Nemo</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold">Welcome back</h2>
            <p className="text-muted-foreground mt-1">
              Sign in to your account to continue
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div className="space-y-2">
              <label
                htmlFor="username"
                className="text-sm font-medium leading-none"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoComplete="username"
                autoFocus
                className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium leading-none"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                  className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 pr-11 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                New to Nemo?
              </span>
            </div>
          </div>

          {/* Register Link */}
          <a
            href="/register"
            className="w-full h-11 rounded-lg border border-border text-foreground font-medium text-sm hover:bg-accent transition-colors flex items-center justify-center"
          >
            Create an account
          </a>

          {/* Demo Credentials */}
          <div className="mt-8 rounded-lg border border-border bg-secondary/30 p-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Demo Credentials
            </p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p>
                <span className="font-mono text-foreground">admin</span> /{" "}
                <span className="font-mono text-foreground">admin123</span> —
                Full admin access
              </p>
              <p>
                <span className="font-mono text-foreground">user</span> /{" "}
                <span className="font-mono text-foreground">user123</span> —
                Standard user
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
