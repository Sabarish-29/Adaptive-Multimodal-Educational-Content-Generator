import importlib
import os
from unittest.mock import patch
from common_utils import encryption as enc_mod


class DummyKMSClient:
    def __init__(self, *a, **k):
        pass

    def generate_data_key(self, KeyId, KeySpec):
        assert KeySpec == "AES_256"
        seed = os.getenv("TEST_ROT_SEED", "A")
        pt = (seed * 32).encode()[:32]
        ct = (seed * 40).encode()
        return {"Plaintext": pt, "CiphertextBlob": ct}


def _reload():
    importlib.reload(enc_mod)


@patch("boto3.client", lambda *a, **k: DummyKMSClient())
def test_kms_ciphertext_cached_and_rotate(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.setenv("ENCRYPTION_PROVIDER", "aws_kms")
    monkeypatch.setenv("AWS_KMS_KEY_ID", "alias/test")
    monkeypatch.setenv("ENCRYPTION_KMS_DATA_KEY_TTL_SECONDS", "100")
    monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)
    _reload()
    e1 = enc_mod.get_encryptor()
    c1 = getattr(enc_mod, "_kms_ciphertext_b64", None)
    assert c1 is not None
    e2 = enc_mod.get_encryptor()
    assert getattr(enc_mod, "_kms_ciphertext_b64", None) == c1
    # Force rotate
    monkeypatch.setenv("ENCRYPTION_KMS_FORCE_ROTATE", "true")
    monkeypatch.setenv("TEST_ROT_SEED", "B")
    _reload()
    e3 = enc_mod.get_encryptor()
    c2 = getattr(enc_mod, "_kms_ciphertext_b64", None)
    assert c2 is not None and c2 != c1
    assert e3.decrypt(e3.encrypt("rotate")) == "rotate"
