"use client";

// ==============================================================================
// Chat Input — Message input with send/stop controls
// ==============================================================================

import { useState, useRef, useCallback } from "react";
import { Send, Square } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (content: string) => void;
  isStreaming: boolean;
  onStop: () => void;
}

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, isStreaming, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleTextareaChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      // Auto-resize
      e.target.style.height = "auto";
      e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
    },
    [],
  );

  return (
    <div className="flex items-end gap-2">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder="Send a message..."
          rows={1}
          className="w-full resize-none bg-secondary border border-border rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground max-h-[200px]"
        />
      </div>

      {isStreaming ? (
        <button
          onClick={onStop}
          className="shrink-0 h-10 w-10 rounded-xl bg-destructive text-destructive-foreground flex items-center justify-center hover:bg-destructive/90 transition-colors"
          title="Stop generating"
        >
          <Square className="h-4 w-4" />
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className={cn(
            "shrink-0 h-10 w-10 rounded-xl flex items-center justify-center transition-colors",
            input.trim()
              ? "bg-primary text-primary-foreground hover:bg-primary/90"
              : "bg-secondary text-muted-foreground cursor-not-allowed",
          )}
          title="Send message"
        >
          <Send className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
