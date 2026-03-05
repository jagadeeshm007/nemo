// ==============================================================================
// Nemo API Gateway — HTTP Router
// ==============================================================================

package router

import (
"github.com/gin-gonic/gin"
"github.com/jackc/pgx/v5/pgxpool"
"github.com/rs/zerolog"

"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/cache"
"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/kafka"
"github.com/nemo-platform/nemo/services/api-gateway/internal/interfaces/http/handlers"
"github.com/nemo-platform/nemo/services/api-gateway/internal/interfaces/http/middleware"
)

// Dependencies holds all injected dependencies for the router.
type Dependencies struct {
Config *config.Config
Logger zerolog.Logger
DB     *pgxpool.Pool
Redis  *cache.RedisClient
Kafka  *kafka.Producer
}

// New creates and configures the HTTP router.
func New(deps Dependencies) *gin.Engine {
if deps.Config.Env == "production" {
gin.SetMode(gin.ReleaseMode)
}

r := gin.New()

// Global middleware
r.Use(middleware.RequestID())
r.Use(middleware.StructuredLogger(deps.Logger))
r.Use(middleware.Recovery(deps.Logger))
r.Use(middleware.CORS(deps.Config))
r.Use(middleware.Metrics())

// Health and readiness
healthHandler := handlers.NewHealthHandler(deps.DB, deps.Redis, deps.Logger)
r.GET("/health", healthHandler.Health)
r.GET("/ready", healthHandler.Ready)

// Prometheus metrics endpoint
r.GET("/metrics", handlers.PrometheusHandler())

// API v1
v1 := r.Group("/api/v1")
{
// Public routes
auth := handlers.NewAuthHandler(deps.Config, deps.DB, deps.Redis, deps.Logger)
v1.POST("/auth/register", auth.Register)
v1.POST("/auth/login", auth.Login)
v1.POST("/auth/refresh", auth.Refresh)

// Protected routes
protected := v1.Group("")
protected.Use(middleware.Auth(deps.Config.JWT))
protected.Use(middleware.RateLimit(deps.Redis, deps.Config.RateLimit))
{
// Chat / AI
chat := handlers.NewChatHandler(deps.Config, deps.Redis, deps.Kafka, deps.Logger)
protected.POST("/chat", chat.SendMessage)
protected.POST("/chat/stream", chat.StreamMessage)
protected.GET("/chat/conversations", chat.ListConversations)
protected.GET("/chat/conversations/:id", chat.GetConversation)
protected.DELETE("/chat/conversations/:id", chat.DeleteConversation)

// Agent
agent := handlers.NewAgentHandler(deps.Config, deps.Redis, deps.Kafka, deps.Logger)
protected.POST("/agent/execute", agent.Execute)
protected.POST("/agent/execute/stream", agent.ExecuteStream)

// Models
models := handlers.NewModelHandler(deps.Config, deps.Logger)
protected.GET("/models", models.ListModels)
protected.GET("/models/:provider/:model", models.GetModel)
protected.PUT("/models/:provider/:model", models.UpdateModel)

// Plugins
plugins := handlers.NewPluginHandler(deps.Config, deps.Logger)
protected.GET("/plugins", plugins.ListPlugins)
protected.GET("/plugins/:id", plugins.GetPlugin)
protected.POST("/plugins/:id/activate", plugins.Activate)
protected.POST("/plugins/:id/deactivate", plugins.Deactivate)
protected.PUT("/plugins/:id/config", plugins.UpdateConfig)
protected.POST("/plugins/:id/execute", plugins.ExecuteAction)

// Workflows
workflows := handlers.NewWorkflowHandler(deps.Config, deps.Logger)
protected.GET("/workflows", workflows.ListWorkflows)
protected.GET("/workflows/:id", workflows.GetWorkflow)
protected.POST("/workflows/:id/run", workflows.StartWorkflow)
protected.GET("/workflows/runs/:runId", workflows.GetWorkflowRun)
protected.DELETE("/workflows/runs/:runId", workflows.CancelWorkflow)

// Documents / Vector
docs := handlers.NewDocumentHandler(deps.Config, deps.Kafka, deps.Logger)
protected.POST("/documents/upload", docs.Upload)
protected.GET("/documents", docs.ListDocuments)
protected.GET("/documents/:id", docs.GetDocument)
protected.DELETE("/documents/:id", docs.DeleteDocument)
protected.POST("/documents/search", docs.Search)
protected.GET("/documents/collections", docs.ListCollections)
protected.POST("/documents/collections", docs.CreateCollection)

// Configuration management
configH := handlers.NewConfigHandler(deps.Config, deps.Logger)
protected.GET("/config/models", configH.GetModelConfig)
protected.PUT("/config/models", configH.UpdateModelConfig)
protected.GET("/config/plugins", configH.GetPluginConfig)
protected.GET("/config/workflows", configH.GetWorkflowConfig)
}
}

return r
}
