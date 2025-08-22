import importlib
from unittest.mock import patch
from common_utils import encryption as enc_mod


class DummyKMSClient:
    def __init__(self, *a, **k):
        pass

    def generate_data_key(self, KeyId, KeySpec):
        assert KeySpec == "AES_256"
        # Return 32-byte plaintext key
        return {"Plaintext": b"K" * 32, "CiphertextBlob": b"X" * 64}


def _reload():
    importlib.reload(enc_mod)


@patch("boto3.client", lambda *a, **k: DummyKMSClient())
def test_kms_provider_roundtrip(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("ENCRYPTION_PROVIDER", "aws_kms")
    monkeypatch.setenv("AWS_KMS_KEY_ID", "alias/test")
    monkeypatch.setenv("ENCRYPTION_KMS_DATA_KEY_TTL_SECONDS", "1")
    _reload()
    e = enc_mod.get_encryptor()
    msg = "kms secret"
    c = e.encrypt(msg)
    assert c != msg
    assert e.decrypt(c) == msg


@patch("boto3.client", lambda *a, **k: DummyKMSClient())
def test_kms_cache_reuse(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("ENCRYPTION_PROVIDER", "aws_kms")
    monkeypatch.setenv("AWS_KMS_KEY_ID", "alias/test")
    monkeypatch.setenv("ENCRYPTION_KMS_DATA_KEY_TTL_SECONDS", "3600")
    _reload()
    e1 = enc_mod.get_encryptor()
    k1 = e1.encrypt("a")  # primes cache
    # Subsequent call should reuse singleton; not easy to assert key, but ensure encrypt/decrypt still works
    e2 = enc_mod.get_encryptor()
    assert e1 is e2
    assert e2.decrypt(e2.encrypt("b")) == "b"


@patch("boto3.client", lambda *a, **k: DummyKMSClient())
def test_strong_requires_kms_when_no_local_key(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.setenv("REQUIRE_STRONG_ENCRYPTION", "true")
    monkeypatch.setenv("ENCRYPTION_PROVIDER", "aws_kms")
    monkeypatch.setenv("AWS_KMS_KEY_ID", "alias/test")
    _reload()  # Should not raise


def test_strong_raises_without_any_key(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.setenv("REQUIRE_STRONG_ENCRYPTION", "true")
    monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("ENCRYPTION_PROVIDER", raising=False)
    monkeypatch.delenv("AWS_KMS_KEY_ID", raising=False)
    try:
        _reload()
    except RuntimeError as e:
        assert "Strong encryption required" in str(e)
    else:
        raise AssertionError("Expected RuntimeError due to missing key sources")
