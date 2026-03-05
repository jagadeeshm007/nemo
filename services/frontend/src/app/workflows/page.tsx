"use client";

// ==============================================================================
// Workflows Page — Workflow management and execution monitoring
// ==============================================================================

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workflowsApi, type Workflow, type WorkflowRun } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { cn, formatRelativeTime } from "@/lib/utils";
import {
  GitBranch,
  Play,
  XCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4 text-muted-foreground" />,
  running: <Play className="h-4 w-4 text-blue-500 animate-pulse" />,
  completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  failed: <AlertCircle className="h-4 w-4 text-destructive" />,
  cancelled: <XCircle className="h-4 w-4 text-muted-foreground" />,
};

export default function WorkflowsPage() {
  const queryClient = useQueryClient();
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

  const { data: workflows, isLoading } = useQuery({
    queryKey: ["workflows"],
    queryFn: () => workflowsApi.list().then((r) => r.data),
  });

  const { data: runs } = useQuery({
    queryKey: ["workflow-runs", selectedWorkflow],
    queryFn: () =>
      workflowsApi.listRuns(selectedWorkflow || undefined).then((r) => r.data),
    enabled: !!selectedWorkflow,
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: (workflowId: string) => workflowsApi.start(workflowId, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-runs"] });
      toast.success("Workflow started");
    },
    onError: () => toast.error("Failed to start workflow"),
  });

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <GitBranch className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Workflows</h1>
              <p className="text-muted-foreground text-sm">
                Multi-step AI workflows and execution monitoring
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Workflow Definitions */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Definitions</h2>
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-20 bg-secondary rounded-xl animate-pulse"
                    />
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {(workflows?.workflows || []).map((wf: Workflow) => (
                    <div
                      key={wf.id}
                      onClick={() => setSelectedWorkflow(wf.id)}
                      className={cn(
                        "border rounded-xl p-4 cursor-pointer transition-colors",
                        selectedWorkflow === wf.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-accent/30",
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium text-sm">{wf.name}</h3>
                          <p className="text-xs text-muted-foreground mt-1">
                            {wf.description}
                          </p>
                          <div className="flex gap-1 mt-2">
                            {wf.tags?.map((tag) => (
                              <span
                                key={tag}
                                className="text-[10px] bg-secondary px-1.5 py-0.5 rounded"
                              >
                                {tag}
                              </span>
                            ))}
                            <span className="text-[10px] text-muted-foreground ml-1">
                              {wf.step_count} steps
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startMutation.mutate(wf.id);
                          }}
                          className="p-2 rounded-lg hover:bg-primary/10 text-primary transition-colors"
                          title="Start workflow"
                        >
                          <Play className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Workflow Runs */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Recent Runs</h2>
              {selectedWorkflow ? (
                <div className="space-y-3">
                  {(runs?.runs || []).map((run: WorkflowRun) => (
                    <div
                      key={run.run_id}
                      className="border border-border rounded-xl p-4"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {STATUS_ICONS[run.status] || null}
                        <span className="text-sm font-medium capitalize">
                          {run.status}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground font-mono">
                        {run.run_id.slice(0, 8)}...
                      </p>
                      {run.started_at && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Started {formatRelativeTime(run.started_at)}
                        </p>
                      )}
                    </div>
                  ))}
                  {(runs?.runs || []).length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No runs yet. Click play to start.
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Select a workflow to view runs
                </p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
