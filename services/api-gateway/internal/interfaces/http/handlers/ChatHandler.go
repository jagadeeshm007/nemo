// ==============================================================================
// API Gateway — Chat Handler (proxies to AI Service via gRPC)
// ==============================================================================

package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog"

	"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/cache"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/kafka"
)

// ChatHandler manages chat-related endpoints.
type ChatHandler struct {
	config *config.Config
	redis  *cache.RedisClient
	kafka  *kafka.Producer
	logger zerolog.Logger
}

// NewChatHandler creates a new ChatHandler.
func NewChatHandler(cfg *config.Config, redis *cache.RedisClient, kafkaProducer *kafka.Producer, logger zerolog.Logger) *ChatHandler {
	return &ChatHandler{config: cfg, redis: redis, kafka: kafkaProducer, logger: logger}
}

// SendMessageRequest is the chat request body.
type SendMessageRequest struct {
	ConversationID string  `json:"conversation_id"`
	Message        string  `json:"message" binding:"required"`
	ModelProvider  string  `json:"model_provider"`
	ModelID        string  `json:"model_id"`
	Temperature    float32 `json:"temperature"`
	MaxTokens      int     `json:"max_tokens"`
	SystemPrompt   string  `json:"system_prompt"`
	UseTools       bool    `json:"use_tools"`
}

// SendMessage handles synchronous chat requests.
func (h *ChatHandler) SendMessage(c *gin.Context) {
	var req SendMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID, _ := c.Get("user_id")
	h.logger.Info().
		Str("user_id", userID.(string)).
		Str("conversation_id", req.ConversationID).
		Str("model", req.ModelProvider+"/"+req.ModelID).
		Msg("Chat message received")

	// TODO: Forward to AI Service via gRPC
	// conn, err := grpc.Dial(h.config.Services.AIServiceGRPC, grpc.WithInsecure())
	// client := aiv1.NewAIServiceClient(conn)
	// resp, err := client.Chat(ctx, &aiv1.ChatRequest{...})

	c.JSON(http.StatusOK, gin.H{
		"conversation_id": req.ConversationID,
		"message":         "Chat endpoint ready. Connect AI Service gRPC client.",
		"status":          "pending_implementation",
	})
}

// StreamMessage handles streaming chat requests via SSE.
func (h *ChatHandler) StreamMessage(c *gin.Context) {
	var req SendMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("Transfer-Encoding", "chunked")

	// TODO: Stream from AI Service via gRPC streaming
	// Stream SSE events back to client
	c.SSEvent("message", gin.H{"delta": "Streaming endpoint ready."})
	c.SSEvent("done", gin.H{"finish_reason": "stop"})
	c.Writer.Flush()
}

// ListConversations returns user's conversation history.
func (h *ChatHandler) ListConversations(c *gin.Context) {
	userID, _ := c.Get("user_id")
	h.logger.Debug().Str("user_id", userID.(string)).Msg("Listing conversations")

	// TODO: Query conversations from PostgreSQL
	c.JSON(http.StatusOK, gin.H{
		"conversations": []interface{}{},
		"total":         0,
	})
}

// GetConversation returns a specific conversation with messages.
func (h *ChatHandler) GetConversation(c *gin.Context) {
	conversationID := c.Param("id")
	h.logger.Debug().Str("conversation_id", conversationID).Msg("Getting conversation")

	// TODO: Query conversation and messages from PostgreSQL
	c.JSON(http.StatusOK, gin.H{
		"id":       conversationID,
		"messages": []interface{}{},
	})
}

// DeleteConversation deletes a conversation.
func (h *ChatHandler) DeleteConversation(c *gin.Context) {
	conversationID := c.Param("id")
	h.logger.Info().Str("conversation_id", conversationID).Msg("Deleting conversation")

	// TODO: Delete from PostgreSQL
	c.JSON(http.StatusOK, gin.H{"deleted": true})
}
