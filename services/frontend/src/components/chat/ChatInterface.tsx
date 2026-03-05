"use client";

// ==============================================================================
// Chat Interface — Main chat window with streaming support
// ==============================================================================

import { useRef, useEffect, useState, useCallback } from "react";
import { useChatStore } from "@/store/chatStore";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { Bot } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export function ChatInterface() {
  const {
    conversations,
    activeConversationId,
    selectedModel,
    isStreaming,
    createConversation,
    addMessage,
    updateMessage,
    setMessageStreaming,
    setIsStreaming,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId,
  );

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      let conversationId = activeConversationId;
      if (!conversationId) {
        conversationId = createConversation();
      }

      // Add user message
      addMessage(conversationId, { role: "user", content });

      // Add placeholder assistant message
      const assistantMsgId = addMessage(conversationId, {
        role: "assistant",
        content: "",
        isStreaming: true,
      });

      setIsStreaming(true);

      // Build message history
      const conversation = useChatStore
        .getState()
        .conversations.find((c) => c.id === conversationId);
      const messages =
        conversation?.messages
          .filter((m) => !m.isStreaming)
          .map((m) => ({ role: m.role, content: m.content })) || [];

      try {
        // Stream via fetch + ReadableStream
        abortControllerRef.current = new AbortController();

        const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("nemo_token") || "" : ""}`,
          },
          body: JSON.stringify({
            model: selectedModel,
            messages,
            conversation_id: conversationId,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n");

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]") break;

                try {
                  const parsed = JSON.parse(data);
                  if (parsed.content) {
                    accumulated += parsed.content;
                    updateMessage(conversationId!, assistantMsgId, accumulated);
                  }
                } catch {
                  // Skip malformed JSON
                }
              }
            }
          }
        }
      } catch (error: unknown) {
        if (error instanceof Error && error.name !== "AbortError") {
          updateMessage(
            conversationId!,
            assistantMsgId,
            "Sorry, an error occurred while generating a response. Please try again.",
          );
        }
      } finally {
        setMessageStreaming(conversationId!, assistantMsgId, false);
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [
      activeConversationId,
      selectedModel,
      createConversation,
      addMessage,
      updateMessage,
      setMessageStreaming,
      setIsStreaming,
    ],
  );

  const handleStopStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  // Empty state
  if (!activeConversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
        <Bot className="h-16 w-16 text-muted-foreground/30 mb-4" />
        <h2 className="text-2xl font-semibold mb-2">Welcome to Nemo</h2>
        <p className="text-muted-foreground max-w-md mb-8">
          Your agentic RAG assistant. Start a conversation, upload documents, or
          explore plugins and workflows.
        </p>
        <div className="w-full max-w-2xl">
          <ChatInput
            onSend={handleSendMessage}
            isStreaming={false}
            onStop={handleStopStreaming}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="border-b border-border px-6 py-3 flex items-center justify-between shrink-0">
        <div>
          <h2 className="font-medium text-sm">{activeConversation.title}</h2>
          <p className="text-xs text-muted-foreground">
            {selectedModel} · {activeConversation.messages.length} messages
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {activeConversation.messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border px-6 py-4 shrink-0">
        <ChatInput
          onSend={handleSendMessage}
          isStreaming={isStreaming}
          onStop={handleStopStreaming}
        />
      </div>
    </div>
  );
}
