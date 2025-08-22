import importlib
from common_utils import encryption as enc_mod


def test_noop_roundtrip(monkeypatch):
    monkeypatch.delenv("FEATURE_FIELD_ENCRYPTION", raising=False)
    importlib.reload(enc_mod)
    e = enc_mod.get_encryptor()
    msg = "hello world"
    assert e.encrypt(msg) == msg
    assert e.decrypt(msg) == msg


def test_obfuscator_diff(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)
    importlib.reload(enc_mod)
    e = enc_mod.get_encryptor()
    msg = "hello world"
    c = e.encrypt(msg)
    assert c != msg
    assert e.decrypt(c) == msg


def test_real_encryptor(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    # 32-byte key
    import base64
    import os as _os

    key = base64.b64encode(_os.urandom(32)).decode()
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", key)
    importlib.reload(enc_mod)
    e = enc_mod.get_encryptor()
    msg = "secret message"
    c = e.encrypt(msg)
    assert c != msg
    assert e.decrypt(c) == msg
