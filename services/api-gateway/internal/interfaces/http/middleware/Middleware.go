// ==============================================================================
// Nemo API Gateway — HTTP Middleware Stack
// ==============================================================================

package middleware

import (
"fmt"
"net/http"
"strings"
"time"

"github.com/gin-gonic/gin"
"github.com/golang-jwt/jwt/v5"
"github.com/google/uuid"
"github.com/prometheus/client_golang/prometheus"
"github.com/prometheus/client_golang/prometheus/promauto"
"github.com/rs/zerolog"

"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/cache"
)

// ============================================================================
// Request ID Middleware
// ============================================================================

// RequestID adds a unique request ID to each request.
func RequestID() gin.HandlerFunc {
return func(c *gin.Context) {
requestID := c.GetHeader("X-Request-ID")
if requestID == "" {
requestID = uuid.New().String()
}
c.Set("request_id", requestID)
c.Header("X-Request-ID", requestID)
c.Next()
}
}

// ============================================================================
// Structured Logger Middleware
// ============================================================================

// StructuredLogger logs each request with structured fields for Loki.
func StructuredLogger(logger zerolog.Logger) gin.HandlerFunc {
return func(c *gin.Context) {
start := time.Now()
path := c.Request.URL.Path
raw := c.Request.URL.RawQuery
c.Next()

latency := time.Since(start)
statusCode := c.Writer.Status()
clientIP := c.ClientIP()
method := c.Request.Method
requestID, _ := c.Get("request_id")

if raw != "" {
path = path + "?" + raw
}

event := logger.Info()
if statusCode >= 500 {
event = logger.Error()
} else if statusCode >= 400 {
event = logger.Warn()
}

event.
Str("log_type", "access").
Str("request_id", fmt.Sprintf("%v", requestID)).
Str("method", method).
Str("path", path).
Int("status", statusCode).
Dur("latency", latency).
Str("client_ip", clientIP).
Int("body_size", c.Writer.Size()).
Str("user_agent", c.Request.UserAgent()).
Msg("HTTP request")
}
}

// ============================================================================
// Recovery Middleware
// ============================================================================

// Recovery recovers from panics and logs the error.
func Recovery(logger zerolog.Logger) gin.HandlerFunc {
return func(c *gin.Context) {
defer func() {
if err := recover(); err != nil {
logger.Error().
Str("log_type", "panic").
Interface("error", err).
Str("path", c.Request.URL.Path).
Msg("Panic recovered")
c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{
"error": "Internal server error",
})
}
}()
c.Next()
}
}

// ============================================================================
// CORS Middleware
// ============================================================================

// CORS configures Cross-Origin Resource Sharing.
func CORS(cfg *config.Config) gin.HandlerFunc {
return func(c *gin.Context) {
origin := c.Request.Header.Get("Origin")
c.Header("Access-Control-Allow-Origin", origin)
c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
c.Header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Request-ID")
c.Header("Access-Control-Allow-Credentials", "true")
c.Header("Access-Control-Max-Age", "3600")
if c.Request.Method == "OPTIONS" {
c.AbortWithStatus(http.StatusNoContent)
return
}
c.Next()
}
}

// ============================================================================
// Auth Middleware
// ============================================================================

// Auth validates JWT tokens.
func Auth(jwtCfg config.JWTConfig) gin.HandlerFunc {
return func(c *gin.Context) {
authHeader := c.GetHeader("Authorization")
if authHeader == "" {
c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Missing authorization header"})
return
}

parts := strings.SplitN(authHeader, " ", 2)
if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization format"})
return
}
tokenString := parts[1]

token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
}
return []byte(jwtCfg.Secret), nil
})
if err != nil || !token.Valid {
c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
return
}

claims, ok := token.Claims.(jwt.MapClaims)
if !ok {
c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid token claims"})
return
}

c.Set("user_id", claims["sub"])
c.Set("user_email", claims["email"])
c.Next()
}
}

// ============================================================================
// Rate Limiting Middleware
// ============================================================================

// RateLimit enforces per-user rate limits using Redis.
func RateLimit(redis *cache.RedisClient, cfg config.RateLimitConfig) gin.HandlerFunc {
return func(c *gin.Context) {
if !cfg.Enabled {
c.Next()
return
}

var key string
if cfg.PerUser {
userID, exists := c.Get("user_id")
if exists {
key = fmt.Sprintf("%v", userID)
} else {
key = c.ClientIP()
}
} else {
key = c.ClientIP()
}

allowed, remaining, err := redis.CheckRateLimit(
c.Request.Context(),
key,
c.FullPath(),
cfg.RPS,
time.Second,
)
if err != nil {
// On Redis failure, allow the request (fail-open)
c.Next()
return
}

c.Header("X-RateLimit-Limit", fmt.Sprintf("%d", cfg.RPS))
c.Header("X-RateLimit-Remaining", fmt.Sprintf("%d", remaining))

if !allowed {
c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
"error":      "Rate limit exceeded",
"retry_after": "1s",
})
return
}

c.Next()
}
}

// ============================================================================
// Metrics Middleware
// ============================================================================

var (
httpRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
Name: "nemo_gateway_http_requests_total",
Help: "Total number of HTTP requests",
}, []string{"method", "path", "status"})

httpRequestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
Name:    "nemo_gateway_http_request_duration_seconds",
Help:    "HTTP request duration in seconds",
Buckets: prometheus.DefBuckets,
}, []string{"method", "path"})
)

// Metrics records Prometheus metrics for each request.
func Metrics() gin.HandlerFunc {
return func(c *gin.Context) {
start := time.Now()
c.Next()
duration := time.Since(start).Seconds()
status := fmt.Sprintf("%d", c.Writer.Status())
path := c.FullPath()
if path == "" {
path = c.Request.URL.Path
}
httpRequestsTotal.WithLabelValues(c.Request.Method, path, status).Inc()
httpRequestDuration.WithLabelValues(c.Request.Method, path).Observe(duration)
}
}
