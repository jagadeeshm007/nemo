// ==============================================================================
// API Gateway — Health Handler
// ==============================================================================

package handlers

import (
"context"
"net/http"
"time"

"github.com/gin-gonic/gin"
"github.com/jackc/pgx/v5/pgxpool"
"github.com/rs/zerolog"

"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/cache"
)

// HealthHandler provides health and readiness endpoints.
type HealthHandler struct {
db     *pgxpool.Pool
redis  *cache.RedisClient
logger zerolog.Logger
}

// NewHealthHandler creates a new HealthHandler.
func NewHealthHandler(db *pgxpool.Pool, redis *cache.RedisClient, logger zerolog.Logger) *HealthHandler {
return &HealthHandler{db: db, redis: redis, logger: logger}
}

// Health returns basic health status.
func (h *HealthHandler) Health(c *gin.Context) {
c.JSON(http.StatusOK, gin.H{
"status":  "healthy",
"service": "api-gateway",
"time":    time.Now().UTC().Format(time.RFC3339),
})
}

// Ready checks all dependencies and returns readiness status.
func (h *HealthHandler) Ready(c *gin.Context) {
ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Second)
defer cancel()

checks := make(map[string]string)
allHealthy := true

// Check Postgres
if err := h.db.Ping(ctx); err != nil {
allHealthy = false
checks["postgres"] = "unhealthy: " + err.Error()
} else {
checks["postgres"] = "healthy"
}

// Check Redis
if _, err := h.redis.Client().Ping(ctx).Result(); err != nil {
allHealthy = false
checks["redis"] = "unhealthy: " + err.Error()
} else {
checks["redis"] = "healthy"
}

status := http.StatusOK
statusText := "ready"
if !allHealthy {
status = http.StatusServiceUnavailable
statusText = "not ready"
}

c.JSON(status, gin.H{
"status": statusText,
"checks": checks,
"time":   time.Now().UTC().Format(time.RFC3339),
})
}
