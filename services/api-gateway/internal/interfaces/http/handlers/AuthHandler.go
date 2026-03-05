// ==============================================================================
// API Gateway — Auth Handler
// ==============================================================================

package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog"

	"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
	"github.com/nemo-platform/nemo/services/api-gateway/internal/infrastructure/cache"
)

// AuthHandler manages authentication endpoints.
type AuthHandler struct {
	config *config.Config
	db     *pgxpool.Pool
	redis  *cache.RedisClient
	logger zerolog.Logger
}

// NewAuthHandler creates a new AuthHandler.
func NewAuthHandler(cfg *config.Config, db *pgxpool.Pool, redis *cache.RedisClient, logger zerolog.Logger) *AuthHandler {
	return &AuthHandler{config: cfg, db: db, redis: redis, logger: logger}
}

// RegisterRequest represents the registration payload.
type RegisterRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=8"`
	Name     string `json:"name" binding:"required"`
}

// LoginRequest represents the login payload.
type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

// AuthResponse contains the JWT tokens.
type AuthResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
	TokenType    string `json:"token_type"`
}

// Register creates a new user account.
func (h *AuthHandler) Register(c *gin.Context) {
	var req RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Check if user exists
	var exists bool
	err := h.db.QueryRow(context.Background(),
		"SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)", req.Email).Scan(&exists)
	if err != nil {
		h.logger.Error().Err(err).Msg("Database error during registration check")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}
	if exists {
		c.JSON(http.StatusConflict, gin.H{"error": "Email already registered"})
		return
	}

	// Create user (password hashing should be done with bcrypt in production)
	userID := uuid.New().String()
	_, err = h.db.Exec(context.Background(),
		`INSERT INTO users (id, email, name, password_hash, created_at, updated_at) 
		 VALUES ($1, $2, $3, $4, $5, $5)`,
		userID, req.Email, req.Name, req.Password, time.Now().UTC())
	if err != nil {
		h.logger.Error().Err(err).Msg("Failed to create user")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	// Generate tokens
	tokens, err := h.generateTokens(userID, req.Email)
	if err != nil {
		h.logger.Error().Err(err).Msg("Failed to generate tokens")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate tokens"})
		return
	}

	h.logger.Info().Str("user_id", userID).Str("email", req.Email).Msg("User registered")
	c.JSON(http.StatusCreated, tokens)
}

// Login authenticates a user and returns JWT tokens.
func (h *AuthHandler) Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Look up user (password verification should use bcrypt in production)
	var userID, passwordHash string
	err := h.db.QueryRow(context.Background(),
		"SELECT id, password_hash FROM users WHERE email = $1", req.Email).Scan(&userID, &passwordHash)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// TODO: Replace with bcrypt.CompareHashAndPassword in production
	if passwordHash != req.Password {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	tokens, err := h.generateTokens(userID, req.Email)
	if err != nil {
		h.logger.Error().Err(err).Msg("Failed to generate tokens")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate tokens"})
		return
	}

	h.logger.Info().Str("user_id", userID).Msg("User logged in")
	c.JSON(http.StatusOK, tokens)
}

// Refresh generates new tokens from a refresh token.
func (h *AuthHandler) Refresh(c *gin.Context) {
	var req struct {
		RefreshToken string `json:"refresh_token" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate refresh token
	token, err := jwt.Parse(req.RefreshToken, func(token *jwt.Token) (interface{}, error) {
		return []byte(h.config.JWT.Secret), nil
	})
	if err != nil || !token.Valid {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid refresh token"})
		return
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token claims"})
		return
	}

	userID, _ := claims["sub"].(string)
	email, _ := claims["email"].(string)

	tokens, err := h.generateTokens(userID, email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate tokens"})
		return
	}

	c.JSON(http.StatusOK, tokens)
}

func (h *AuthHandler) generateTokens(userID, email string) (*AuthResponse, error) {
	now := time.Now()

	// Access token
	accessClaims := jwt.MapClaims{
		"sub":   userID,
		"email": email,
		"iat":   now.Unix(),
		"exp":   now.Add(time.Duration(h.config.JWT.TokenExpiry) * time.Hour).Unix(),
		"type":  "access",
	}
	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, accessClaims)
	accessString, err := accessToken.SignedString([]byte(h.config.JWT.Secret))
	if err != nil {
		return nil, err
	}

	// Refresh token
	refreshClaims := jwt.MapClaims{
		"sub":   userID,
		"email": email,
		"iat":   now.Unix(),
		"exp":   now.Add(time.Duration(h.config.JWT.RefreshExpiry) * 24 * time.Hour).Unix(),
		"type":  "refresh",
	}
	refreshToken := jwt.NewWithClaims(jwt.SigningMethodHS256, refreshClaims)
	refreshString, err := refreshToken.SignedString([]byte(h.config.JWT.Secret))
	if err != nil {
		return nil, err
	}

	return &AuthResponse{
		AccessToken:  accessString,
		RefreshToken: refreshString,
		ExpiresIn:    h.config.JWT.TokenExpiry * 3600,
		TokenType:    "Bearer",
	}, nil
}
