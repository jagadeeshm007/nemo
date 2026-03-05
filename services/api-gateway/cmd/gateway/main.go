// ==============================================================================
// Nemo API Gateway — Entry Point
// ==============================================================================

package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/cache"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/database"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/kafka"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/logging"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/interfaces/http/router"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load config: %v\n", err)
		os.Exit(1)
	}

	// Initialize structured logger
	logger := logging.NewLogger(cfg.LogLevel, cfg.LogFormat)
	logger.Info().Str("service", "api-gateway").Msg("Starting Nemo API Gateway")

	// Initialize database connection
	db, err := database.NewPostgresPool(cfg.Postgres)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to connect to PostgreSQL")
	}
	defer db.Close()
	logger.Info().Msg("Connected to PostgreSQL")

	// Initialize Redis
	redisClient, err := cache.NewRedisClient(cfg.Redis)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to connect to Redis")
	}
	defer redisClient.Close()
	logger.Info().Msg("Connected to Redis")

	// Initialize Kafka producer
	kafkaProducer, err := kafka.NewProducer(cfg.Kafka)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to connect to Kafka")
	}
	defer kafkaProducer.Close()
	logger.Info().Msg("Connected to Kafka")

	// Build HTTP router
	r := router.New(router.Dependencies{
		Config:   cfg,
		Logger:   logger,
		DB:       db,
		Redis:    redisClient,
		Kafka:    kafkaProducer,
	})

	// Create HTTP server
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.HTTPPort),
		Handler:      r,
		ReadTimeout:  time.Duration(cfg.ReadTimeout) * time.Second,
		WriteTimeout: time.Duration(cfg.WriteTimeout) * time.Second,
		IdleTimeout:  time.Duration(cfg.IdleTimeout) * time.Second,
	}

	// Start server in a goroutine
	go func() {
		logger.Info().Int("port", cfg.HTTPPort).Msg("HTTP server starting")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal().Err(err).Msg("HTTP server failed")
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info().Msg("Shutting down API Gateway...")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Error().Err(err).Msg("Forced shutdown")
	}

	logger.Info().Msg("API Gateway stopped")
}
