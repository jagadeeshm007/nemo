// ==============================================================================
// Nemo API Gateway — PostgreSQL Connection Pool
// ==============================================================================

package database

import (
"context"
"fmt"
"time"

"github.com/jackc/pgx/v5/pgxpool"

"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
)

// NewPostgresPool creates a new pgx connection pool from config.
func NewPostgresPool(cfg config.PostgresConfig) (*pgxpool.Pool, error) {
poolCfg, err := pgxpool.ParseConfig(cfg.DSN())
if err != nil {
return nil, fmt.Errorf("parse postgres config: %w", err)
}

poolCfg.MaxConns = 20
poolCfg.MinConns = 5
poolCfg.MaxConnLifetime = 30 * time.Minute
poolCfg.MaxConnIdleTime = 5 * time.Minute
poolCfg.HealthCheckPeriod = 1 * time.Minute

ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

pool, err := pgxpool.NewWithConfig(ctx, poolCfg)
if err != nil {
return nil, fmt.Errorf("create postgres pool: %w", err)
}

if err := pool.Ping(ctx); err != nil {
pool.Close()
return nil, fmt.Errorf("ping postgres: %w", err)
}

return pool, nil
}
