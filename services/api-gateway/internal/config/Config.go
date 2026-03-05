// ==============================================================================
// API Gateway — Configuration
// ==============================================================================

package config

import (
	"fmt"
	"os"
	"strconv"
)

// Config holds all gateway configuration.
type Config struct {
	Env          string
	LogLevel     string
	LogFormat    string
	HTTPPort     int
	GRPCPort     int
	ReadTimeout  int
	WriteTimeout int
	IdleTimeout  int

	Postgres PostgresConfig
	Redis    RedisConfig
	Kafka    KafkaConfig
	JWT      JWTConfig
	RateLimit RateLimitConfig
	Services ServicesConfig
}

type PostgresConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	DBName   string
	SSLMode  string
}

func (p PostgresConfig) DSN() string {
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%d/%s?sslmode=%s",
		p.User, p.Password, p.Host, p.Port, p.DBName, p.SSLMode,
	)
}

type RedisConfig struct {
	Host     string
	Port     int
	Password string
	DB       int
}

func (r RedisConfig) Addr() string {
	return fmt.Sprintf("%s:%d", r.Host, r.Port)
}

type KafkaConfig struct {
	Brokers []string
	GroupID string
}

type JWTConfig struct {
	Secret           string
	TokenExpiry      int // hours
	RefreshExpiry    int // days
}

type RateLimitConfig struct {
	Enabled  bool
	RPS      int
	Burst    int
	PerUser  bool
}

type ServicesConfig struct {
	AIServiceGRPC       string
	PluginServiceGRPC   string
	WorkflowServiceGRPC string
	VectorServiceGRPC   string
}

// Load reads configuration from environment variables.
func Load() (*Config, error) {
	cfg := &Config{
		Env:          getEnv("NEMO_ENV", "development"),
		LogLevel:     getEnv("NEMO_LOG_LEVEL", "info"),
		LogFormat:    getEnv("NEMO_LOG_FORMAT", "json"),
		HTTPPort:     getEnvInt("GATEWAY_HTTP_PORT", 8080),
		GRPCPort:     getEnvInt("GATEWAY_GRPC_PORT", 9090),
		ReadTimeout:  getEnvInt("GATEWAY_READ_TIMEOUT", 30),
		WriteTimeout: getEnvInt("GATEWAY_WRITE_TIMEOUT", 60),
		IdleTimeout:  getEnvInt("GATEWAY_IDLE_TIMEOUT", 120),

		Postgres: PostgresConfig{
			Host:     getEnv("POSTGRES_HOST", "localhost"),
			Port:     getEnvInt("POSTGRES_PORT", 5432),
			User:     getEnv("POSTGRES_USER", "nemo"),
			Password: getEnv("POSTGRES_PASSWORD", "nemo_secret_change_me"),
			DBName:   getEnv("POSTGRES_DB", "nemo"),
			SSLMode:  getEnv("POSTGRES_SSL_MODE", "disable"),
		},

		Redis: RedisConfig{
			Host:     getEnv("REDIS_HOST", "localhost"),
			Port:     getEnvInt("REDIS_PORT", 6379),
			Password: getEnv("REDIS_PASSWORD", ""),
			DB:       getEnvInt("REDIS_DB", 0),
		},

		Kafka: KafkaConfig{
			Brokers: []string{getEnv("KAFKA_BROKERS", "localhost:9092")},
			GroupID: getEnv("KAFKA_GROUP_ID", "nemo-gateway"),
		},

		JWT: JWTConfig{
			Secret:        getEnv("JWT_SECRET", "change-this-to-a-real-secret-in-production"),
			TokenExpiry:   getEnvInt("JWT_TOKEN_EXPIRY_HOURS", 24),
			RefreshExpiry: getEnvInt("JWT_REFRESH_EXPIRY_DAYS", 30),
		},

		RateLimit: RateLimitConfig{
			Enabled: getEnvBool("RATE_LIMIT_ENABLED", true),
			RPS:     getEnvInt("RATE_LIMIT_RPS", 100),
			Burst:   getEnvInt("RATE_LIMIT_BURST", 200),
			PerUser: getEnvBool("RATE_LIMIT_PER_USER", true),
		},

		Services: ServicesConfig{
			AIServiceGRPC:       getEnv("AI_SERVICE_GRPC", "localhost:50051"),
			PluginServiceGRPC:   getEnv("PLUGIN_SERVICE_GRPC", "localhost:50052"),
			WorkflowServiceGRPC: getEnv("WORKFLOW_SERVICE_GRPC", "localhost:50053"),
			VectorServiceGRPC:   getEnv("VECTOR_SERVICE_GRPC", "localhost:50054"),
		},
	}

	return cfg, nil
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	if val := os.Getenv(key); val != "" {
		if i, err := strconv.Atoi(val); err == nil {
			return i
		}
	}
	return defaultVal
}

func getEnvBool(key string, defaultVal bool) bool {
	if val := os.Getenv(key); val != "" {
		if b, err := strconv.ParseBool(val); err == nil {
			return b
		}
	}
	return defaultVal
}
