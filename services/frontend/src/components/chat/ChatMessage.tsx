"use client";

// ==============================================================================
// Chat Message — Single message bubble with markdown rendering
// ==============================================================================

import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "@/store/chatStore";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={cn(
        "flex gap-3 max-w-4xl",
        isAssistant ? "" : "ml-auto flex-row-reverse",
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "shrink-0 h-8 w-8 rounded-full flex items-center justify-center",
          isAssistant
            ? "bg-primary/10 text-primary"
            : "bg-accent text-foreground",
        )}
      >
        {isAssistant ? (
          <Bot className="h-4 w-4" />
        ) : (
          <User className="h-4 w-4" />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          "rounded-2xl px-4 py-2.5 max-w-[85%]",
          isAssistant
            ? "bg-card border border-border"
            : "bg-primary text-primary-foreground",
        )}
      >
        {isAssistant ? (
          <div
            className={cn(
              "prose prose-sm dark:prose-invert max-w-none",
              message.isStreaming && "streaming-cursor",
            )}
          >
            <ReactMarkdown>{message.content || "Thinking..."}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        )}

        {message.model && (
          <p className="text-[10px] text-muted-foreground mt-1 opacity-60">
            {message.model}
          </p>
        )}
      </div>
    </div>
  );
}
