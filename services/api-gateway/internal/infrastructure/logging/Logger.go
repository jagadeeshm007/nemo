// ==============================================================================
// Nemo API Gateway — Structured Logger (zerolog)
// ==============================================================================

package logging

import (
"os"
"time"

"github.com/rs/zerolog"
)

// NewLogger creates a configured zerolog.Logger instance.
func NewLogger(level, format string) zerolog.Logger {
// Parse level
lvl, err := zerolog.ParseLevel(level)
if err != nil {
lvl = zerolog.InfoLevel
}

// Build logger
var logger zerolog.Logger
if format == "console" {
logger = zerolog.New(zerolog.ConsoleWriter{
Out:        os.Stdout,
TimeFormat: time.RFC3339,
}).With().Timestamp().Caller().Logger().Level(lvl)
} else {
logger = zerolog.New(os.Stdout).With().Timestamp().Caller().Logger().Level(lvl)
}

return logger
}

// AuditLog writes an audit log entry for compliance and security tracking.
func AuditLog(logger zerolog.Logger, action, userID, resource, details string) {
logger.Info().
Str("log_type", "audit").
Str("action", action).
Str("user_id", userID).
Str("resource", resource).
Str("details", details).
Str("timestamp", time.Now().UTC().Format(time.RFC3339)).
Msg("Audit event")
}

// TraceLog writes a trace log entry for distributed tracing correlation.
func TraceLog(logger zerolog.Logger, traceID, spanID, operation string) {
logger.Debug().
Str("log_type", "trace").
Str("trace_id", traceID).
Str("span_id", spanID).
Str("operation", operation).
Msg("Trace event")
}
