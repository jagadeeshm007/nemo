// ==============================================================================
// Nemo API Gateway — Kafka Producer
// ==============================================================================

package kafka

import (
"context"
"encoding/json"
"fmt"
"time"

kafkago "github.com/segmentio/kafka-go"
"github.com/rs/zerolog/log"

"github.com/nemo-platform/nemo/services/api-gateway/internal/config"
)

// Event represents a domain event to publish on Kafka.
type Event struct {
Type    string      `json:"type"`
Source  string      `json:"source"`
Subject string      `json:"subject"`
ID      string      `json:"id"`
Time    time.Time   `json:"time"`
Data    interface{} `json:"data"`
}

// Producer wraps a kafka-go writer.
type Producer struct {
writer *kafkago.Writer
}

// NewProducer creates a new Kafka producer from config.
func NewProducer(cfg config.KafkaConfig) (*Producer, error) {
writer := &kafkago.Writer{
Addr:         kafkago.TCP(cfg.Brokers...),
Balancer:     &kafkago.LeastBytes{},
BatchTimeout: 10 * time.Millisecond,
RequiredAcks: kafkago.RequireOne,
}

// Validate connectivity with a quick dial
conn, err := kafkago.Dial("tcp", cfg.Brokers[0])
if err != nil {
log.Warn().Err(err).Msg("Kafka connectivity check failed (non-fatal, will retry)")
} else {
conn.Close()
}

return &Producer{writer: writer}, nil
}

// Publish sends an event to the specified Kafka topic.
func (p *Producer) Publish(ctx context.Context, topic string, event Event) error {
data, err := json.Marshal(event)
if err != nil {
return fmt.Errorf("marshal event: %w", err)
}

msg := kafkago.Message{
Topic: topic,
Key:   []byte(event.Subject),
Value: data,
}

if err := p.writer.WriteMessages(ctx, msg); err != nil {
return fmt.Errorf("publish to %s: %w", topic, err)
}

return nil
}

// Close flushes and closes the Kafka writer.
func (p *Producer) Close() error {
if p.writer != nil {
return p.writer.Close()
}
return nil
}
