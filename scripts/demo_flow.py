"""Minimal demo flow: create/get profile, generate lesson, start session, post event, fetch analytics."""

import requests
import datetime

BASE_PROFILES = "http://localhost:8000"
BASE_CONTENT = "http://localhost:8003"
BASE_SESSIONS = "http://localhost:8002"
BASE_ANALYTICS = "http://localhost:8004"

learner_id = "learner_demo"

print("Fetching profile...")
r = requests.get(f"{BASE_PROFILES}/v1/learners/{learner_id}/profile")
print(r.status_code, r.json())

print("Generating lesson...")
r = requests.post(
    f"{BASE_CONTENT}/v1/generate/lesson",
    json={
        "learner_id": learner_id,
        "unit_id": "unit_math_1",
        "objectives": ["addition basics"],
    },
)
print(r.status_code, r.json())

print("Starting session...")
r = requests.post(
    f"{BASE_SESSIONS}/v1/sessions",
    json={"learner_id": learner_id, "unit_id": "unit_math_1"},
)
session_id = r.json()["session_id"]
print("Session:", session_id)

print("Posting event...")
now = datetime.datetime.utcnow().isoformat() + "Z"
r = requests.post(
    f"{BASE_SESSIONS}/v1/sessions/{session_id}/events",
    json={"type": "answer", "timestamp": now, "payload": {"correct": True}},
)
print(r.status_code, r.json())

print("Fetching analytics...")
r = requests.get(f"{BASE_ANALYTICS}/v1/analytics/learner/{learner_id}/progress")
print(r.status_code, r.json())
