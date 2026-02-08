#!/usr/bin/env bash
# NeuroSync AI – Kafka Topic Setup
# Creates all required Kafka topics for the event-driven architecture.
#
# Usage:
#   bash scripts/setup/setup_kafka.sh [BROKER]
#
# Requires: kafka CLI tools or docker exec into the Kafka container.

set -euo pipefail

BROKER="${1:-localhost:9092}"
PARTITIONS=3
REPLICATION=1

TOPICS=(
  "neurosync.sessions"
  "neurosync.cognitive"
  "neurosync.content"
  "neurosync.interventions"
  "neurosync.progress"
  "neurosync.peer"
  "neurosync.events.dead-letter"
)

echo "=== NeuroSync AI – Kafka Topic Setup ==="
echo "Broker: $BROKER"
echo ""

for topic in "${TOPICS[@]}"; do
  echo -n "Creating topic '$topic' … "
  kafka-topics --bootstrap-server "$BROKER" \
    --create \
    --if-not-exists \
    --topic "$topic" \
    --partitions "$PARTITIONS" \
    --replication-factor "$REPLICATION" \
    2>/dev/null && echo "✓" || echo "⚠ (may already exist)"
done

echo ""
echo "Listing topics:"
kafka-topics --bootstrap-server "$BROKER" --list

echo ""
echo "✅ Kafka topics ready."
