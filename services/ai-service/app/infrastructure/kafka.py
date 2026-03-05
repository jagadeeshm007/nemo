# ==============================================================================
# AI Service — Kafka Event Bus
# ==============================================================================

import json
import time
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.config import Settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class KafkaEventBus:
    """Async Kafka producer/consumer for event-driven communication."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._producer: AIOKafkaProducer | None = None
        self._consumers: dict[str, AIOKafkaConsumer] = {}

    async def connect(self) -> None:
        """Initialize Kafka producer."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._settings.kafka_broker_list,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await self._producer.start()
            logger.info("Kafka producer connected")
        except Exception as e:
            logger.warning(f"Kafka connection failed (non-fatal): {e}")
            self._producer = None

    async def disconnect(self) -> None:
        """Shutdown Kafka connections."""
        if self._producer:
            await self._producer.stop()
        for consumer in self._consumers.values():
            await consumer.stop()
        logger.info("Kafka disconnected")

    async def publish(
        self,
        topic: str,
        event_type: str,
        payload: dict,
        correlation_id: str | None = None,
    ) -> None:
        """Publish an event to a Kafka topic."""
        if not self._producer:
            logger.warning(f"Kafka not connected, skipping event: {event_type}")
            return

        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "timestamp": time.time(),
            "source_service": "ai-service",
            "correlation_id": correlation_id or str(uuid4()),
            "payload": payload,
        }

        await self._producer.send(topic, value=event, key=event["event_id"])
        logger.debug(f"Event published: {event_type} -> {topic}")

    async def subscribe(
        self,
        topic: str,
        group_id: str | None = None,
    ) -> AIOKafkaConsumer:
        """Create a consumer for a topic."""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self._settings.kafka_broker_list,
            group_id=group_id or self._settings.kafka_group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        await consumer.start()
        self._consumers[topic] = consumer
        logger.info(f"Subscribed to topic: {topic}")
        return consumer
