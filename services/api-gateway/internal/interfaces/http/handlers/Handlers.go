// ==============================================================================
// API Gateway — Model, Plugin, Workflow, Document, Config Handlers
// ==============================================================================

package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"

	"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/kafka"
)

// PrometheusHandler returns the Prometheus metrics endpoint.
func PrometheusHandler() gin.HandlerFunc {
	h := promhttp.Handler()
	return func(c *gin.Context) {
		h.ServeHTTP(c.Writer, c.Request)
	}
}

// ============================================================================
// Model Handler
// ============================================================================

type ModelHandler struct {
	config *config.Config
	logger zerolog.Logger
}

func NewModelHandler(cfg *config.Config, logger zerolog.Logger) *ModelHandler {
	return &ModelHandler{config: cfg, logger: logger}
}

func (h *ModelHandler) ListModels(c *gin.Context) {
	// TODO: Forward to AI Service via gRPC ListModels
	c.JSON(http.StatusOK, gin.H{"models": []interface{}{}, "status": "pending_grpc_integration"})
}

func (h *ModelHandler) GetModel(c *gin.Context) {
	provider := c.Param("provider")
	model := c.Param("model")
	h.logger.Debug().Str("provider", provider).Str("model", model).Msg("Get model config")
	c.JSON(http.StatusOK, gin.H{"provider": provider, "model": model})
}

func (h *ModelHandler) UpdateModel(c *gin.Context) {
	provider := c.Param("provider")
	model := c.Param("model")
	h.logger.Info().Str("provider", provider).Str("model", model).Msg("Update model config")
	// TODO: Forward to AI Service via gRPC UpdateModelConfig
	c.JSON(http.StatusOK, gin.H{"updated": true})
}

// ============================================================================
// Plugin Handler
// ============================================================================

type PluginHandler struct {
	config *config.Config
	logger zerolog.Logger
}

func NewPluginHandler(cfg *config.Config, logger zerolog.Logger) *PluginHandler {
	return &PluginHandler{config: cfg, logger: logger}
}

func (h *PluginHandler) ListPlugins(c *gin.Context) {
	// TODO: Forward to Plugin Service via gRPC
	c.JSON(http.StatusOK, gin.H{"plugins": []interface{}{}, "total": 0})
}

func (h *PluginHandler) GetPlugin(c *gin.Context) {
	pluginID := c.Param("id")
	h.logger.Debug().Str("plugin_id", pluginID).Msg("Get plugin")
	c.JSON(http.StatusOK, gin.H{"id": pluginID})
}

func (h *PluginHandler) Activate(c *gin.Context) {
	pluginID := c.Param("id")
	h.logger.Info().Str("plugin_id", pluginID).Msg("Activate plugin")
	c.JSON(http.StatusOK, gin.H{"id": pluginID, "state": "active"})
}

func (h *PluginHandler) Deactivate(c *gin.Context) {
	pluginID := c.Param("id")
	h.logger.Info().Str("plugin_id", pluginID).Msg("Deactivate plugin")
	c.JSON(http.StatusOK, gin.H{"id": pluginID, "state": "inactive"})
}

func (h *PluginHandler) UpdateConfig(c *gin.Context) {
	pluginID := c.Param("id")
	h.logger.Info().Str("plugin_id", pluginID).Msg("Update plugin config")
	c.JSON(http.StatusOK, gin.H{"updated": true})
}

func (h *PluginHandler) ExecuteAction(c *gin.Context) {
	pluginID := c.Param("id")
	h.logger.Info().Str("plugin_id", pluginID).Msg("Execute plugin action")
	c.JSON(http.StatusOK, gin.H{"plugin_id": pluginID, "status": "executed"})
}

// ============================================================================
// Workflow Handler
// ============================================================================

type WorkflowHandler struct {
	config *config.Config
	logger zerolog.Logger
}

func NewWorkflowHandler(cfg *config.Config, logger zerolog.Logger) *WorkflowHandler {
	return &WorkflowHandler{config: cfg, logger: logger}
}

func (h *WorkflowHandler) ListWorkflows(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"workflows": []interface{}{}, "total": 0})
}

func (h *WorkflowHandler) GetWorkflow(c *gin.Context) {
	workflowID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{"id": workflowID})
}

func (h *WorkflowHandler) StartWorkflow(c *gin.Context) {
	workflowID := c.Param("id")
	h.logger.Info().Str("workflow_id", workflowID).Msg("Start workflow")
	c.JSON(http.StatusAccepted, gin.H{"workflow_id": workflowID, "status": "started"})
}

func (h *WorkflowHandler) GetWorkflowRun(c *gin.Context) {
	runID := c.Param("runId")
	c.JSON(http.StatusOK, gin.H{"run_id": runID})
}

func (h *WorkflowHandler) CancelWorkflow(c *gin.Context) {
	runID := c.Param("runId")
	h.logger.Info().Str("run_id", runID).Msg("Cancel workflow")
	c.JSON(http.StatusOK, gin.H{"run_id": runID, "status": "cancelled"})
}

// ============================================================================
// Document Handler
// ============================================================================

type DocumentHandler struct {
	config *config.Config
	kafka  *kafka.Producer
	logger zerolog.Logger
}

func NewDocumentHandler(cfg *config.Config, kafkaProducer *kafka.Producer, logger zerolog.Logger) *DocumentHandler {
	return &DocumentHandler{config: cfg, kafka: kafkaProducer, logger: logger}
}

func (h *DocumentHandler) Upload(c *gin.Context) {
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "File is required"})
		return
	}
	h.logger.Info().Str("filename", file.Filename).Int64("size", file.Size).Msg("Document upload")

	// TODO: Forward to Vector Service, publish DocumentUploaded event
	c.JSON(http.StatusAccepted, gin.H{
		"filename": file.Filename,
		"size":     file.Size,
		"status":   "processing",
	})
}

func (h *DocumentHandler) ListDocuments(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"documents": []interface{}{}, "total": 0})
}

func (h *DocumentHandler) GetDocument(c *gin.Context) {
	docID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{"id": docID})
}

func (h *DocumentHandler) DeleteDocument(c *gin.Context) {
	docID := c.Param("id")
	h.logger.Info().Str("document_id", docID).Msg("Delete document")
	c.JSON(http.StatusOK, gin.H{"deleted": true})
}

func (h *DocumentHandler) Search(c *gin.Context) {
	var req struct {
		Query        string `json:"query" binding:"required"`
		CollectionID string `json:"collection_id"`
		TopK         int    `json:"top_k"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	// TODO: Forward to Vector Service via gRPC Search
	c.JSON(http.StatusOK, gin.H{"results": []interface{}{}, "total": 0})
}

func (h *DocumentHandler) ListCollections(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"collections": []interface{}{}, "total": 0})
}

func (h *DocumentHandler) CreateCollection(c *gin.Context) {
	var req struct {
		Name        string `json:"name" binding:"required"`
		Description string `json:"description"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"name": req.Name, "status": "created"})
}

// ============================================================================
// Config Handler
// ============================================================================

type ConfigHandler struct {
	config *config.Config
	logger zerolog.Logger
}

func NewConfigHandler(cfg *config.Config, logger zerolog.Logger) *ConfigHandler {
	return &ConfigHandler{config: cfg, logger: logger}
}

func (h *ConfigHandler) GetModelConfig(c *gin.Context) {
	// TODO: Load from configs/models.yaml or database
	c.JSON(http.StatusOK, gin.H{"status": "pending_implementation"})
}

func (h *ConfigHandler) UpdateModelConfig(c *gin.Context) {
	h.logger.Info().Msg("Updating model configuration")
	c.JSON(http.StatusOK, gin.H{"updated": true})
}

func (h *ConfigHandler) GetPluginConfig(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "pending_implementation"})
}

func (h *ConfigHandler) GetWorkflowConfig(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "pending_implementation"})
}
