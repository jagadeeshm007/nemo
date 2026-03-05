// ==============================================================================
// Chat Store — Zustand state management for chat
// ==============================================================================

import { create } from "zustand";
import { generateId } from "@/lib/utils";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  model?: string;
  isStreaming?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  model: string;
  createdAt: Date;
  updatedAt: Date;
}

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  selectedModel: string;
  isStreaming: boolean;

  // Actions
  createConversation: () => string;
  setActiveConversation: (id: string) => void;
  addMessage: (
    conversationId: string,
    message: Omit<ChatMessage, "id" | "timestamp">,
  ) => string;
  updateMessage: (
    conversationId: string,
    messageId: string,
    content: string,
  ) => void;
  setMessageStreaming: (
    conversationId: string,
    messageId: string,
    streaming: boolean,
  ) => void;
  deleteConversation: (id: string) => void;
  setSelectedModel: (model: string) => void;
  setIsStreaming: (streaming: boolean) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  selectedModel: "gpt-4o",
  isStreaming: false,

  createConversation: () => {
    const id = generateId();
    const conversation: Conversation = {
      id,
      title: "New Conversation",
      messages: [],
      model: get().selectedModel,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    set((state) => ({
      conversations: [conversation, ...state.conversations],
      activeConversationId: id,
    }));
    return id;
  },

  setActiveConversation: (id) => {
    set({ activeConversationId: id });
  },

  addMessage: (conversationId, message) => {
    const messageId = generateId();
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: [
                ...conv.messages,
                { ...message, id: messageId, timestamp: new Date() },
              ],
              title:
                conv.messages.length === 0 && message.role === "user"
                  ? message.content.slice(0, 50)
                  : conv.title,
              updatedAt: new Date(),
            }
          : conv,
      ),
    }));
    return messageId;
  },

  updateMessage: (conversationId, messageId, content) => {
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: conv.messages.map((msg) =>
                msg.id === messageId ? { ...msg, content } : msg,
              ),
            }
          : conv,
      ),
    }));
  },

  setMessageStreaming: (conversationId, messageId, streaming) => {
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: conv.messages.map((msg) =>
                msg.id === messageId ? { ...msg, isStreaming: streaming } : msg,
              ),
            }
          : conv,
      ),
    }));
  },

  deleteConversation: (id) => {
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      activeConversationId:
        state.activeConversationId === id ? null : state.activeConversationId,
    }));
  },

  setSelectedModel: (model) => {
    set({ selectedModel: model });
  },

  setIsStreaming: (streaming) => {
    set({ isStreaming: streaming });
  },
}));
