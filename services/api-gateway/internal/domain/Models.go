// ==============================================================================
// Nemo API Gateway — Domain Models
// ==============================================================================

package domain

import (
"time"
)

// User represents an application user.
type User struct {
ID           string    `json:"id"`
Email        string    `json:"email"`
Name         string    `json:"name"`
PasswordHash string    `json:"-"`
CreatedAt    time.Time `json:"created_at"`
UpdatedAt    time.Time `json:"updated_at"`
}

// Conversation represents a chat conversation.
type Conversation struct {
ID        string    `json:"id"`
UserID    string    `json:"user_id"`
Title     string    `json:"title"`
CreatedAt time.Time `json:"created_at"`
UpdatedAt time.Time `json:"updated_at"`
}

// Message represents a single message in a conversation.
type Message struct {
ID             string    `json:"id"`
ConversationID string    `json:"conversation_id"`
Role           string    `json:"role"`
Content        string    `json:"content"`
ModelProvider  string    `json:"model_provider,omitempty"`
ModelID        string    `json:"model_id,omitempty"`
TokensUsed     int       `json:"tokens_used,omitempty"`
CreatedAt      time.Time `json:"created_at"`
}

// AuditLogEntry represents an audit trail record.
type AuditLogEntry struct {
ID        string    `json:"id"`
UserID    string    `json:"user_id"`
Action    string    `json:"action"`
Resource  string    `json:"resource"`
Details   string    `json:"details"`
CreatedAt time.Time `json:"created_at"`
}
