"use client";

// ==============================================================================
// Documents Page — Document upload and management
// ==============================================================================

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { cn, formatRelativeTime } from "@/lib/utils";
import { FileText, Upload, Trash2, FileCheck, FileWarning } from "lucide-react";
import { toast } from "sonner";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

export default function DocumentsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsApi.list().then((r) => r.data),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document uploaded and indexed");
    },
    onError: () => toast.error("Upload failed"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document deleted");
    },
  });

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => uploadMutation.mutate(file));
    },
    [uploadMutation],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/plain": [".txt"],
      "text/markdown": [".md"],
      "text/csv": [".csv"],
      "application/json": [".json"],
      "application/pdf": [".pdf"],
    },
    maxSize: 50 * 1024 * 1024,
  });

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <FileText className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Documents</h1>
              <p className="text-muted-foreground text-sm">
                Upload and manage documents for RAG retrieval
              </p>
            </div>
          </div>

          {/* Upload Zone */}
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors mb-8",
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50",
            )}
          >
            <input {...getInputProps()} />
            <Upload
              className={cn(
                "h-10 w-10 mx-auto mb-3",
                isDragActive ? "text-primary" : "text-muted-foreground",
              )}
            />
            {isDragActive ? (
              <p className="text-primary font-medium">Drop files here</p>
            ) : (
              <>
                <p className="font-medium">
                  Drag & drop files here, or click to browse
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Supports TXT, MD, CSV, JSON, PDF (max 50MB)
                </p>
              </>
            )}
            {uploadMutation.isPending && (
              <p className="text-sm text-primary mt-2 animate-pulse">
                Uploading and processing...
              </p>
            )}
          </div>

          {/* Document List */}
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
            <div className="space-y-3">
              {(data?.documents || []).map((doc: Record<string, unknown>) => (
                <div
                  key={doc.document_id as string}
                  className="border border-border rounded-xl p-4 flex items-center justify-between hover:bg-accent/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {doc.status === "indexed" ? (
                      <FileCheck className="h-5 w-5 text-green-500" />
                    ) : doc.status === "failed" ? (
                      <FileWarning className="h-5 w-5 text-destructive" />
                    ) : (
                      <FileText className="h-5 w-5 text-muted-foreground" />
                    )}
                    <div>
                      <p className="text-sm font-medium">
                        {doc.filename as string}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {doc.collection as string} · {doc.chunk_count as number}{" "}
                        chunks ·{" "}
                        {((doc.file_size_bytes as number) / 1024).toFixed(1)}KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() =>
                      deleteMutation.mutate(doc.document_id as string)
                    }
                    className="p-2 rounded-lg hover:bg-destructive/10 text-destructive transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
              {(data?.documents || []).length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No documents uploaded yet
                </p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
