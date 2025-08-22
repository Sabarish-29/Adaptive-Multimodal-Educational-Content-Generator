import hashlib


def provenance_hash(prompt: str, model: str, unit: str):
    return hashlib.sha256(f"{prompt}|model={model}|unit={unit}".encode()).hexdigest()


def test_provenance_hash_deterministic():
    h1 = provenance_hash("Generate", "llm_stub", "unit1")
    h2 = provenance_hash("Generate", "llm_stub", "unit1")
    assert h1 == h2


def test_provenance_hash_changes_with_prompt():
    h1 = provenance_hash("Generate A", "llm_stub", "unit1")
    h2 = provenance_hash("Generate B", "llm_stub", "unit1")
    assert h1 != h2
