// ==============================================================================
// Nemo API Gateway — Redis Client
// ==============================================================================

package cache

import (
"context"
"encoding/json"
"fmt"
"time"

"github.com/redis/go-redis/v9"

"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
)

// RedisClient wraps the Redis client with application-specific helpers.
type RedisClient struct {
client *redis.Client
}

// NewRedisClient creates a new Redis client from config.
func NewRedisClient(cfg config.RedisConfig) (*RedisClient, error) {
client := redis.NewClient(&redis.Options{
Addr:     cfg.Addr(),
Password: cfg.Password,
DB:       cfg.DB,
})

ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

if _, err := client.Ping(ctx).Result(); err != nil {
return nil, fmt.Errorf("redis ping: %w", err)
}

return &RedisClient{client: client}, nil
}

// Close closes the Redis client connection.
func (r *RedisClient) Close() error {
return r.client.Close()
}

// Client returns the underlying redis.Client for direct access.
func (r *RedisClient) Client() *redis.Client {
return r.client
}

// SetSession stores a session in Redis with an expiry.
func (r *RedisClient) SetSession(ctx context.Context, sessionID string, data interface{}, expiry time.Duration) error {
jsonData, err := json.Marshal(data)
if err != nil {
return fmt.Errorf("marshal session data: %w", err)
}
return r.client.Set(ctx, "session:"+sessionID, jsonData, expiry).Err()
}

// GetSession retrieves a session from Redis.
func (r *RedisClient) GetSession(ctx context.Context, sessionID string) (string, error) {
return r.client.Get(ctx, "session:"+sessionID).Result()
}

// DeleteSession removes a session from Redis.
func (r *RedisClient) DeleteSession(ctx context.Context, sessionID string) error {
return r.client.Del(ctx, "session:"+sessionID).Err()
}

// CheckRateLimit checks and increments a rate limit counter.
// Returns whether the request is allowed, the remaining count, and any error.
func (r *RedisClient) CheckRateLimit(ctx context.Context, key, path string, limit int, window time.Duration) (bool, int, error) {
rateKey := fmt.Sprintf("rate:%s:%s", key, path)

pipe := r.client.Pipeline()
incr := pipe.Incr(ctx, rateKey)
pipe.Expire(ctx, rateKey, window)
_, err := pipe.Exec(ctx)
if err != nil {
return false, 0, fmt.Errorf("rate limit check: %w", err)
}

count := int(incr.Val())
remaining := limit - count
if remaining < 0 {
remaining = 0
}

return count <= limit, remaining, nil
}

// CacheResponse stores a cached API response.
func (r *RedisClient) CacheResponse(ctx context.Context, key string, data interface{}, expiry time.Duration) error {
jsonData, err := json.Marshal(data)
if err != nil {
return fmt.Errorf("marshal cache data: %w", err)
}
return r.client.Set(ctx, "cache:"+key, jsonData, expiry).Err()
}

// GetCachedResponse retrieves a cached API response.
func (r *RedisClient) GetCachedResponse(ctx context.Context, key string) (string, error) {
return r.client.Get(ctx, "cache:"+key).Result()
}

// SetWorkflowState stores workflow execution state.
func (r *RedisClient) SetWorkflowState(ctx context.Context, workflowID string, state interface{}) error {
jsonData, err := json.Marshal(state)
if err != nil {
return fmt.Errorf("marshal workflow state: %w", err)
}
return r.client.Set(ctx, "workflow:"+workflowID, jsonData, 24*time.Hour).Err()
}

// GetWorkflowState retrieves workflow execution state.
func (r *RedisClient) GetWorkflowState(ctx context.Context, workflowID string) (string, error) {
return r.client.Get(ctx, "workflow:"+workflowID).Result()
}
