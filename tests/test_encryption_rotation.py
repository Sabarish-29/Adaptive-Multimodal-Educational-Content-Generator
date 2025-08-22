import importlib
import os
import base64
from common_utils import encryption as enc_mod


def fresh():
    importlib.reload(enc_mod)
    return enc_mod


def gen_key():
    return base64.b64encode(os.urandom(32)).decode()


def test_dual_key_decrypt_old_ciphertext(monkeypatch):
    # Step 1: encrypt with old key
    old_key = gen_key()
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", old_key)
    mod = fresh()
    e = mod.get_encryptor()
    secret = "rotate-me"
    c_old = e.encrypt(secret)

    # Step 2: rotate (new key primary, old as secondary)
    new_key = gen_key()
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", new_key)
    monkeypatch.setenv("FIELD_ENCRYPTION_SECONDARY_KEY", old_key)
    mod = fresh()
    e2 = mod.get_encryptor()
    # New encryptor should decrypt old ciphertext
    assert e2.decrypt(c_old) == secret
    # Ciphertext produced now should differ and decrypt properly
    c_new = e2.encrypt(secret)
    assert c_new != c_old
    assert e2.decrypt(c_new) == secret
