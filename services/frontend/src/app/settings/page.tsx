"use client";

// ==============================================================================
// Settings Page — Model configuration and system settings
// ==============================================================================

import { useQuery, useMutation } from "@tanstack/react-query";
import { modelsApi, type Model } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { Settings, RefreshCw, Cpu } from "lucide-react";
import { toast } from "sonner";

export default function SettingsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => modelsApi.list().then((r) => r.data),
  });

  const reloadMutation = useMutation({
    mutationFn: () => modelsApi.reload(),
    onSuccess: () => toast.success("Model configuration reloaded"),
    onError: () => toast.error("Failed to reload"),
  });

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <Settings className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Settings</h1>
              <p className="text-muted-foreground text-sm">
                System configuration and model management
              </p>
            </div>
          </div>

          {/* Models Section */}
          <section className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Cpu className="h-5 w-5" />
                Available Models
              </h2>
              <button
                onClick={() => reloadMutation.mutate()}
                disabled={reloadMutation.isPending}
                className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-border hover:bg-accent transition-colors"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${reloadMutation.isPending ? "animate-spin" : ""}`}
                />
                Reload Config
              </button>
            </div>

            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-16 bg-secondary rounded-xl animate-pulse"
                  />
                ))}
              </div>
            ) : (
              <div className="grid gap-3">
                {(data?.models || []).map((model: Model) => (
                  <div
                    key={model.id}
                    className="border border-border rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-sm">{model.name}</h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {model.provider} · Context:{" "}
                          {(model.context_window / 1000).toFixed(0)}K tokens
                        </p>
                      </div>
                      <div className="flex gap-1">
                        {model.capabilities?.map((cap) => (
                          <span
                            key={cap}
                            className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded"
                          >
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* System Info */}
          <section>
            <h2 className="text-lg font-semibold mb-4">System Info</h2>
            <div className="grid grid-cols-2 gap-4">
              <InfoCard label="Platform" value="Nemo v0.1.0" />
              <InfoCard
                label="Architecture"
                value="Microservices + Event-Driven"
              />
              <InfoCard
                label="LLM Providers"
                value="OpenAI, Anthropic, Google"
              />
              <InfoCard label="Vector Store" value="ChromaDB" />
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-border rounded-xl p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium mt-0.5">{value}</p>
    </div>
  );
}
