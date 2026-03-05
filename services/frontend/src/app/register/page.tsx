"use client";

// ==============================================================================
// Register Page — Account creation form
// ==============================================================================

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Bot, Eye, EyeOff, Loader2, AlertCircle, Check } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const passwordChecks = {
    length: password.length >= 6,
    match: password === confirmPassword && confirmPassword.length > 0,
  };

  const canSubmit =
    username.length >= 3 &&
    email.includes("@") &&
    passwordChecks.length &&
    passwordChecks.match &&
    !isLoading;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError(null);

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match");
      return;
    }

    try {
      await register(username, email, password, firstName, lastName);
      router.push("/");
    } catch {
      // Error is set in the store
    }
  };

  const displayError = validationError || error;

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
          <h1 className="text-4xl font-bold mb-4">Join Nemo</h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Create your account to access the enterprise agentic RAG platform.
            Chat with AI, upload documents, and build powerful workflows.
          </p>
          <div className="mt-12 space-y-4 text-left">
            {[
              "Multi-model AI chat with streaming responses",
              "Document upload and semantic search (RAG)",
              "Plugin ecosystem and workflow automation",
              "Enterprise-grade security and observability",
            ].map((feature) => (
              <div
                key={feature}
                className="flex items-center gap-3 text-sm text-muted-foreground"
              >
                <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                  <Check className="h-3 w-3 text-primary" />
                </div>
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel — Register Form */}
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
            <h2 className="text-2xl font-bold">Create account</h2>
            <p className="text-muted-foreground mt-1">
              Get started with Nemo in seconds
            </p>
          </div>

          {/* Error Banner */}
          {displayError && (
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{displayError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name Row */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label
                  htmlFor="firstName"
                  className="text-sm font-medium leading-none"
                >
                  First name
                </label>
                <input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="John"
                  autoComplete="given-name"
                  autoFocus
                  className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="lastName"
                  className="text-sm font-medium leading-none"
                >
                  Last name
                </label>
                <input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Doe"
                  autoComplete="family-name"
                  className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                />
              </div>
            </div>

            {/* Username */}
            <div className="space-y-2">
              <label
                htmlFor="username"
                className="text-sm font-medium leading-none"
              >
                Username <span className="text-destructive">*</span>
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="johndoe"
                required
                minLength={3}
                autoComplete="username"
                className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
              {username.length > 0 && username.length < 3 && (
                <p className="text-xs text-destructive">
                  Must be at least 3 characters
                </p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="text-sm font-medium leading-none"
              >
                Email <span className="text-destructive">*</span>
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="john@example.com"
                required
                autoComplete="email"
                className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium leading-none"
              >
                Password <span className="text-destructive">*</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 6 characters"
                  required
                  minLength={6}
                  autoComplete="new-password"
                  className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 pr-11 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
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

            {/* Confirm Password */}
            <div className="space-y-2">
              <label
                htmlFor="confirmPassword"
                className="text-sm font-medium leading-none"
              >
                Confirm password <span className="text-destructive">*</span>
              </label>
              <input
                id="confirmPassword"
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                required
                autoComplete="new-password"
                className="flex h-11 w-full rounded-lg border border-input bg-secondary/50 px-4 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
            </div>

            {/* Password Strength Indicators */}
            {password.length > 0 && (
              <div className="space-y-1.5">
                <PasswordCheck
                  label="At least 6 characters"
                  passed={passwordChecks.length}
                />
                {confirmPassword.length > 0 && (
                  <PasswordCheck
                    label="Passwords match"
                    passed={passwordChecks.match}
                  />
                )}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create account"
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className="text-center text-sm text-muted-foreground mt-6">
            Already have an account?{" "}
            <a
              href="/login"
              className="text-primary hover:underline font-medium"
            >
              Sign in
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

function PasswordCheck({ label, passed }: { label: string; passed: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <div
        className={`h-3.5 w-3.5 rounded-full flex items-center justify-center ${
          passed
            ? "bg-green-500/20 text-green-500"
            : "bg-muted text-muted-foreground"
        }`}
      >
        {passed && <Check className="h-2.5 w-2.5" />}
      </div>
      <span className={passed ? "text-green-500" : "text-muted-foreground"}>
        {label}
      </span>
    </div>
  );
}
