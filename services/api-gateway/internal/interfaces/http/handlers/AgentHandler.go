// ==============================================================================
// API Gateway — Agent Handler
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

// AgentHandler manages agent execution endpoints.
type AgentHandler struct {
	config *config.Config
	redis  *cache.RedisClient
	kafka  *kafka.Producer
	logger zerolog.Logger
}

// NewAgentHandler creates a new AgentHandler.
func NewAgentHandler(cfg *config.Config, redis *cache.RedisClient, kafkaProducer *kafka.Producer, logger zerolog.Logger) *AgentHandler {
	return &AgentHandler{config: cfg, redis: redis, kafka: kafkaProducer, logger: logger}
}

// AgentExecuteRequest is the agent execution request payload.
type AgentExecuteRequest struct {
	Query         string   `json:"query" binding:"required"`
	ModelProvider string   `json:"model_provider"`
	ModelID       string   `json:"model_id"`
	MaxIterations int      `json:"max_iterations"`
	Tools         []string `json:"tools"`
	WorkflowID    string   `json:"workflow_id"`
	SystemPrompt  string   `json:"system_prompt"`
}

// Execute handles synchronous agent execution.
func (h *AgentHandler) Execute(c *gin.Context) {
	var req AgentExecuteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID, _ := c.Get("user_id")
	h.logger.Info().
		Str("user_id", userID.(string)).
		Str("workflow_id", req.WorkflowID).
		Int("max_iterations", req.MaxIterations).
		Msg("Agent execution requested")

	// TODO: Forward to AI Service via gRPC AgentExecute
	c.JSON(http.StatusOK, gin.H{
		"status":  "pending_implementation",
		"message": "Agent execution endpoint ready. Connect AI Service gRPC client.",
	})
}

// ExecuteStream handles streaming agent execution via SSE.
func (h *AgentHandler) ExecuteStream(c *gin.Context) {
	var req AgentExecuteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")

	// TODO: Stream from AI Service via gRPC streaming
	c.SSEvent("step", gin.H{"step": 1, "thought": "Agent streaming ready."})
	c.SSEvent("done", gin.H{"status": "complete"})
	c.Writer.Flush()
}
