import os
import datetime
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import OperationFailure

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
DB_NAME = os.getenv("MONGODB_DB", "edu")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

now = datetime.datetime.utcnow()

# Collection: learners
learners = db.learners
learners.create_index([("user_id", ASCENDING)], unique=True, name="user_id_idx")
learners.create_index(
    [("active", ASCENDING)],
    partialFilterExpression={"active": True},
    name="active_partial_idx",
)

if not learners.find_one({"user_id": "learner_demo"}):
    learners.insert_one(
        {
            "user_id": "learner_demo",
            "disabilities": ["dyslexia"],
            "accommodations": {"font": "OpenDyslexic", "speed": "normal"},
            "preferences": {"modalities": ["text", "audio"], "reading_level": "grade5"},
            "languages": ["en"],
            "consent": {"parental": True, "timestamp": now},
            "active": True,
            "created_at": now,
            "updated_at": now,
        }
    )


def ensure_collection_with_validator(name: str, validator: dict | None):
    existing = db.list_collection_names()
    if name not in existing:
        opts = {}
        if validator:
            opts["validator"] = validator
            opts["validationLevel"] = "moderate"
        db.create_collection(name, **opts)
    elif validator:
        try:
            db.command(
                {"collMod": name, "validator": validator, "validationLevel": "moderate"}
            )
        except OperationFailure:
            pass


# Validators (lightweight)
learner_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["user_id", "preferences"],
        "properties": {
            "user_id": {"bsonType": "string"},
            "preferences": {
                "bsonType": "object",
                "properties": {"reading_level": {"bsonType": "string"}},
            },
        },
    }
}

content_bundle_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["learner_id", "unit_id", "content", "hashes"],
        "properties": {
            "learner_id": {"bsonType": "string"},
            "hashes": {"bsonType": "object", "required": ["input_hash", "output_hash"]},
            "provenance": {"bsonType": "object"},
        },
    }
}

ensure_collection_with_validator("learners", learner_validator)
ensure_collection_with_validator("content_bundles", content_bundle_validator)

# Collection: content_bundles
content_bundles = db.content_bundles
content_bundles.create_index(
    [("unit_id", ASCENDING), ("objective_id", ASCENDING), ("created_at", ASCENDING)],
    name="unit_objective_created_idx",
)
content_bundles.create_index(
    [("hashes.input_hash", ASCENDING)], name="input_hash_unique_idx", unique=True
)
content_bundles.create_index(
    [("provenance.provenance_hash", ASCENDING)], name="provenance_hash_idx"
)

# Collection: sessions
sessions = db.sessions
sessions.create_index(
    [("learner_id", ASCENDING), ("status", ASCENDING)], name="learner_status_idx"
)
sessions.create_index([("started_at", ASCENDING)], name="started_at_idx")

# Collection: events (TTL)
events = db.events
events.create_index(
    [("learner_id", ASCENDING), ("timestamp", ASCENDING)], name="learner_timestamp_idx"
)
events.create_index(
    [("session_id", ASCENDING), ("timestamp", ASCENDING)], name="session_timestamp_idx"
)
# TTL 90 days (~7776000 seconds)
events.create_index("timestamp", expireAfterSeconds=7776000, name="events_ttl_idx")

# Collection: policies
policies = db.policies
policies.create_index(
    [("type", ASCENDING), ("active", ASCENDING)], name="type_active_idx"
)
if not policies.find_one({"type": "bandit", "active": True}):
    policies.insert_one(
        {
            "type": "bandit",
            "algorithm": "thompson",
            "arms": [
                {
                    "id": "text_audio_medium",
                    "modalities": ["text", "audio"],
                    "chunk_size": "medium",
                    "difficulty": 0,
                },
                {
                    "id": "text_only_small",
                    "modalities": ["text"],
                    "chunk_size": "small",
                    "difficulty": -1,
                },
                {
                    "id": "text_visual_large",
                    "modalities": ["text", "image"],
                    "chunk_size": "large",
                    "difficulty": 1,
                },
            ],
            "priors": {"alpha": 1, "beta": 1},
            "active": True,
            "created_at": now,
        }
    )

# Bandit posteriors & feedback indexes
db.bandit_posteriors.create_index(
    [("arm_id", ASCENDING)], name="arm_id_idx", unique=True
)
db.arm_feedback.create_index(
    [("learner_id", ASCENDING), ("arm", ASCENDING)], name="learner_arm_idx"
)
db.adaptation_recs.create_index(
    [("learner_id", ASCENDING), ("created_at", ASCENDING)], name="learner_created_idx"
)

# Evaluations index
db.evaluations.create_index([("bundle_id", ASCENDING)], name="bundle_id_idx")

# Basic search index for curriculum (placeholder)
curriculum = db.curriculum_assets
curriculum.create_index([("text", TEXT)], name="text_search_idx")

# Audit logs collection (security / compliance)
audit_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["event", "created_at"],
        "properties": {
            "event": {"bsonType": "string"},
            "user_id": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
        },
    }
}
ensure_collection_with_validator("audit_logs", audit_validator)
db.audit_logs.create_index(
    [("event", ASCENDING), ("created_at", ASCENDING)], name="event_created_idx"
)
db.audit_logs.create_index([("created_at", ASCENDING)], name="created_idx")

# Additional validators
bandit_posterior_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["arm_id", "alpha", "beta"],
        "properties": {
            "arm_id": {"bsonType": "string"},
            "alpha": {"bsonType": "int"},
            "beta": {"bsonType": "int"},
        },
    }
}
arm_feedback_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["learner_id", "arm", "reward", "success"],
        "properties": {
            "learner_id": {"bsonType": "string"},
            "arm": {"bsonType": "string"},
            "reward": {"bsonType": ["double", "int"]},
            "success": {"bsonType": "bool"},
        },
    }
}
evaluation_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["bundle_id", "pass", "created_at"],
        "properties": {
            "bundle_id": {"bsonType": "string"},
            "pass": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
        },
    }
}
ensure_collection_with_validator("bandit_posteriors", bandit_posterior_validator)
ensure_collection_with_validator("arm_feedback", arm_feedback_validator)
ensure_collection_with_validator("evaluations", evaluation_validator)

print("Seed data inserted / indexes ensured.")
