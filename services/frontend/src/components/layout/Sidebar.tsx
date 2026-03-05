"use client";

// ==============================================================================
// Sidebar — Conversation list, navigation, model selector, user profile
// ==============================================================================

import { useChatStore, type Conversation } from "@/store/chatStore";
import { useAuthStore } from "@/store/authStore";
import { cn, truncate, formatRelativeTime } from "@/lib/utils";
import {
  MessageSquare,
  Plus,
  Trash2,
  Settings,
  Puzzle,
  GitBranch,
  FileText,
  Bot,
  LogOut,
  User,
  Shield,
} from "lucide-react";

export function Sidebar() {
  const {
    conversations,
    activeConversationId,
    selectedModel,
    createConversation,
    setActiveConversation,
    deleteConversation,
    setSelectedModel,
  } = useChatStore();

  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  const isAdmin = user?.realm_roles?.includes("nemo-admin");

  return (
    <aside className="w-72 border-r border-border bg-card flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="text-lg font-bold">Nemo</h1>
        </div>

        <button
          onClick={() => createConversation()}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors text-sm"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {/* Model Selector */}
      <div className="px-4 py-2 border-b border-border">
        <label className="text-xs text-muted-foreground mb-1 block">
          Model
        </label>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="w-full bg-secondary text-foreground text-sm rounded-md px-2 py-1.5 border border-border focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <optgroup label="OpenAI">
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4o-mini">GPT-4o Mini</option>
          </optgroup>
          <optgroup label="Anthropic">
            <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
            <option value="claude-3-haiku">Claude 3 Haiku</option>
          </optgroup>
          <optgroup label="Google">
            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
          </optgroup>
        </select>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">
            No conversations yet
          </p>
        ) : (
          conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConversationId}
              onSelect={() => setActiveConversation(conv.id)}
              onDelete={() => deleteConversation(conv.id)}
            />
          ))
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="border-t border-border p-2 space-y-1">
        <NavItem icon={Puzzle} label="Plugins" href="/plugins" />
        <NavItem icon={GitBranch} label="Workflows" href="/workflows" />
        <NavItem icon={FileText} label="Documents" href="/documents" />
        <NavItem icon={Settings} label="Settings" href="/settings" />
      </div>

      {/* User Profile */}
      {user && (
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <User className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user.name || user.preferred_username}
              </p>
              <div className="flex items-center gap-1">
                {isAdmin && <Shield className="h-3 w-3 text-primary" />}
                <p className="text-xs text-muted-foreground truncate">
                  {isAdmin ? "Admin" : "User"}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
}: {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      onClick={onSelect}
      className={cn(
        "group mx-2 px-3 py-2 rounded-lg cursor-pointer flex items-center justify-between transition-colors",
        isActive ? "bg-accent" : "hover:bg-accent/50",
      )}
    >
      <div className="flex items-center gap-2 min-w-0">
        <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
        <div className="min-w-0">
          <p className="text-sm truncate">{truncate(conversation.title, 30)}</p>
          <p className="text-xs text-muted-foreground">
            {formatRelativeTime(conversation.updatedAt)}
          </p>
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="opacity-0 group-hover:opacity-100 p-1 hover:text-destructive transition-all"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  );
}

function NavItem({
  icon: Icon,
  label,
  href,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
    >
      <Icon className="h-4 w-4" />
      {label}
    </a>
  );
}
