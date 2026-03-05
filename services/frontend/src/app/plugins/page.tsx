"use client";

// ==============================================================================
// Plugins Page — Plugin management UI
// ==============================================================================

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pluginsApi, type Plugin } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { cn } from "@/lib/utils";
import { Puzzle, Power, PowerOff, Play } from "lucide-react";
import { toast } from "sonner";

export default function PluginsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["plugins"],
    queryFn: () => pluginsApi.list().then((r) => r.data),
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => pluginsApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      toast.success("Plugin activated");
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => pluginsApi.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      toast.success("Plugin deactivated");
    },
  });

  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 mb-8">
              <Puzzle className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Plugins</h1>
                <p className="text-muted-foreground text-sm">
                  Manage integrations and tool plugins
                </p>
              </div>
            </div>

            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-24 bg-secondary rounded-xl animate-pulse"
                  />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {(data?.plugins || []).map((plugin: Plugin) => (
                  <div
                    key={plugin.id}
                    className="border border-border rounded-xl p-5 hover:bg-accent/30 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium">{plugin.name}</h3>
                          <span
                            className={cn(
                              "text-xs px-2 py-0.5 rounded-full",
                              plugin.state === "active"
                                ? "bg-green-500/10 text-green-500"
                                : "bg-muted text-muted-foreground",
                            )}
                          >
                            {plugin.state}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {plugin.description}
                        </p>
                        <div className="flex gap-2 flex-wrap">
                          {plugin.actions?.map((action) => (
                            <span
                              key={action.name}
                              className="text-xs bg-secondary px-2 py-1 rounded"
                            >
                              {action.name}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {plugin.state === "active" ? (
                          <button
                            onClick={() => deactivateMutation.mutate(plugin.id)}
                            className="p-2 rounded-lg hover:bg-destructive/10 text-destructive transition-colors"
                            title="Deactivate"
                          >
                            <PowerOff className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => activateMutation.mutate(plugin.id)}
                            className="p-2 rounded-lg hover:bg-green-500/10 text-green-500 transition-colors"
                            title="Activate"
                          >
                            <Power className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
