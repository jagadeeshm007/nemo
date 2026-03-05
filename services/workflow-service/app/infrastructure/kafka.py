# ==============================================================================
# Workflow Service — Kafka Producer / Consumer
# ==============================================================================

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def init_kafka(brokers: list[str]) -> None:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await _producer.start()
    logger.info("Kafka producer started")


async def close_kafka() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        logger.info("Kafka producer stopped")


async def publish_event(topic: str, event_type: str, payload: dict) -> None:
    if not _producer:
        logger.warning("Kafka producer not initialized — dropping event")
        return

    envelope = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "source": "workflow-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    await _producer.send_and_wait(topic, envelope)
    logger.debug("Published %s to %s", event_type, topic)
