// ==============================================================================
// API Client — Axios instance with interceptors (uses auth store)
// ==============================================================================

import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.nemo.local";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// ── Request interceptor: attach JWT from auth store ─────────────────────────
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    // Read token from localStorage (kept in sync by auth store)
    const token = localStorage.getItem("nemo_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response interceptor: handle 401 ────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        // Import auth store dynamically to avoid circular deps
        const { useAuthStore } = await import("@/store/authStore");
        const { refreshAuth, isAuthenticated } = useAuthStore.getState();

        if (isAuthenticated) {
          const refreshed = await refreshAuth();
          if (refreshed && error.config) {
            // Retry the failed request with new token
            const token = localStorage.getItem("nemo_token");
            error.config.headers.Authorization = `Bearer ${token}`;
            return axios(error.config);
          }
        }

        // Refresh failed or not authenticated — redirect to login
        localStorage.removeItem("nemo_token");
        localStorage.removeItem("nemo_refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// ── Typed API helpers ───────────────────────────────────────────────────────

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  model: string;
  messages: Message[];
  conversation_id?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  id: string;
  model: string;
  content: string;
  conversation_id: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface Model {
  id: string;
  provider: string;
  name: string;
  context_window: number;
  capabilities: string[];
}

export interface Plugin {
  id: string;
  name: string;
  description: string;
  state: string;
  category: string;
  actions: { name: string; description: string }[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  step_count: number;
  tags: string[];
}

export interface WorkflowRun {
  run_id: string;
  workflow_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
}

// ── Chat ────────────────────────────────────────────────────────────────────
export const chatApi = {
  send: (data: ChatRequest) => api.post<ChatResponse>("/chat", data),

  stream: (data: ChatRequest): EventSource => {
    // SSE requires a different approach
    const url = `${API_URL}/api/v1/chat/stream`;
    const eventSource = new EventSource(url);
    return eventSource;
  },

  listConversations: () => api.get("/chat/conversations"),
  getConversation: (id: string) => api.get(`/chat/conversations/${id}`),
  deleteConversation: (id: string) => api.delete(`/chat/conversations/${id}`),
};

// ── Models ──────────────────────────────────────────────────────────────────
export const modelsApi = {
  list: () => api.get<{ models: Model[] }>("/models"),
  providers: () => api.get("/models/providers"),
  reload: () => api.post("/models/reload"),
};

// ── Plugins ─────────────────────────────────────────────────────────────────
export const pluginsApi = {
  list: () => api.get<{ plugins: Plugin[] }>("/plugins"),
  get: (id: string) => api.get<Plugin>(`/plugins/${id}`),
  activate: (id: string) => api.post(`/plugins/${id}/activate`),
  deactivate: (id: string) => api.post(`/plugins/${id}/deactivate`),
  execute: (id: string, action: string, params: Record<string, unknown>) =>
    api.post(`/plugins/${id}/execute`, {
      action_name: action,
      parameters: params,
    }),
};

// ── Workflows ───────────────────────────────────────────────────────────────
export const workflowsApi = {
  list: () => api.get<{ workflows: Workflow[] }>("/workflows"),
  get: (id: string) => api.get(`/workflows/${id}`),
  start: (workflowId: string, inputData: Record<string, unknown>) =>
    api.post("/workflows/start", {
      workflow_id: workflowId,
      input_data: inputData,
    }),
  listRuns: (workflowId?: string) =>
    api.get<{ runs: WorkflowRun[] }>("/workflows/runs", {
      params: { workflow_id: workflowId },
    }),
  getRun: (runId: string) => api.get(`/workflows/runs/${runId}`),
  cancelRun: (runId: string) => api.post(`/workflows/runs/${runId}/cancel`),
};

// ── Documents ───────────────────────────────────────────────────────────────
export const documentsApi = {
  upload: (file: File, collection: string = "default") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("collection", collection);
    return api.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: (collection?: string) =>
    api.get("/documents", { params: { collection } }),
  get: (id: string) => api.get(`/documents/${id}`),
  delete: (id: string) => api.delete(`/documents/${id}`),
};
