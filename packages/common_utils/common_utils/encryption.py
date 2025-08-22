"""Pluggable encryption interface.

Modes (selected by env):
    FEATURE_FIELD_ENCRYPTION=true enables field protection.
    REQUIRE_STRONG_ENCRYPTION=true enforces a *non*-placeholder implementation (AES-GCM or KMS derived key) at import/load time.

Key sourcing strategies (priority order):
    1. If FIELD_ENCRYPTION_KEY is set (base64 16/24/32 raw bytes) use direct AES-GCM ("local static key").
    2. Else if ENCRYPTION_PROVIDER=aws_kms resolve a data key from AWS KMS (GenerateDataKey) and keep it in-memory with TTL rotation.
    3. Else fall back to SimpleObfuscator (unless strong required, which raises).

AWS KMS integration (lightweight):
    ENCRYPTION_PROVIDER=aws_kms
    AWS_KMS_KEY_ID=<arn-or-alias>
    AWS_REGION=<region> (optional; else uses typical AWS defaults / config)
    ENCRYPTION_KMS_DATA_KEY_TTL_SECONDS=3600 (rotation cadence; process-local)

    We call GenerateDataKey (AES_256) and store only the plaintext in memory; ciphertext blob is discarded (because we re-generate on TTL expiry).
    This is NOT as secure as envelope encrypting every value with its own data key; it's a pragmatic step that avoids storing a static key in env.
    For production hardening: persist and reuse the *ciphertext* data key, support per-record envelope, and integrate centralized rotation signals.

Usage:
    from common_utils.encryption import get_encryptor
    enc = get_encryptor()
    protected = enc.encrypt(text)
    plain = enc.decrypt(protected)

Metrics:
    encryption_mode Gauge (0=disabled,1=placeholder,2=aes-gcm-local,3=aes-gcm-kms)
"""

from __future__ import annotations
import os
import base64
import hashlib
import hmac
import time
from typing import Protocol

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
except Exception:  # cryptography optional
    AESGCM = None  # type: ignore
try:
    from prometheus_client import Gauge, REGISTRY  # type: ignore
except Exception:  # pragma: no cover - prometheus optional
    Gauge = None  # type: ignore
    REGISTRY = None  # type: ignore


def _has_valid_local_key() -> bool:
    key_b64 = os.getenv("FIELD_ENCRYPTION_KEY")
    if not (AESGCM and key_b64):
        return False
    try:
        raw = base64.b64decode(key_b64)
        return len(raw) in (16, 24, 32)
    except Exception:
        return False


def _kms_configured() -> bool:
    return os.getenv("ENCRYPTION_PROVIDER", "").lower() == "aws_kms" and bool(
        os.getenv("AWS_KMS_KEY_ID")
    )


# Import-time enforcement: if strong encryption is required, ensure either local key or KMS config is present.
if (
    os.getenv("FEATURE_FIELD_ENCRYPTION", "false").lower() == "true"
    and os.getenv("REQUIRE_STRONG_ENCRYPTION", "false").lower() == "true"
):
    if not (_has_valid_local_key() or _kms_configured()):
        raise RuntimeError(
            "Strong encryption required but neither valid FIELD_ENCRYPTION_KEY nor aws_kms provider configured at import"
        )


class Encryptor(Protocol):
    def encrypt(self, value: str) -> str: ...
    def decrypt(self, value: str) -> str: ...


class NoopEncryptor:
    def encrypt(self, value: str) -> str:
        return value

    def decrypt(self, value: str) -> str:
        return value


class SimpleObfuscator:
    _KEY = 0x42

    def encrypt(self, value: str) -> str:
        raw = value.encode()
        xored = bytes([b ^ self._KEY for b in raw])
        return base64.b64encode(xored).decode()

    def decrypt(self, value: str) -> str:
        try:
            data = base64.b64decode(value.encode())
            raw = bytes([b ^ self._KEY for b in data])
            return raw.decode()
        except Exception:
            return value


class RealEncryptor:
    """AES-GCM encryptor with provided raw key bytes (16/24/32)."""

    def __init__(self, key: bytes):
        self._aes = AESGCM(key)  # type: ignore[arg-type]

    def encrypt(self, value: str) -> str:
        nonce = os.urandom(12)
        ct = self._aes.encrypt(nonce, value.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, value: str) -> str:
        try:
            raw = base64.b64decode(value.encode())
            nonce, ct = raw[:12], raw[12:]
            pt = self._aes.decrypt(nonce, ct, None)
            return pt.decode()
        except Exception:
            return value


class _KMSDataKeyCache:
    """Process-local cache for a generated KMS data key.

    NOTE: For production you should store the *ciphertext* data key and only keep the plaintext ephemeral.
    """

    def __init__(self):
        self._plaintext: bytes | None = None
        self._expires_at: float = 0.0

    def get_key(self) -> bytes | None:
        if self._plaintext and time.time() < self._expires_at:
            return self._plaintext
        return None

    def set_key(self, key: bytes, ttl: int):
        self._plaintext = key
        self._expires_at = time.time() + ttl


_kms_cache = _KMSDataKeyCache()
_kms_ciphertext_b64: str | None = (
    None  # stored ciphertext blob for observability / potential future persistence
)


def _kms_generate_data_key() -> tuple[bytes, bytes]:
    # Lazy import boto3 to avoid hard dependency if feature unused
    try:
        import boto3  # type: ignore
    except Exception as e:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "aws_kms encryption provider requested but boto3 not installed"
        ) from e
    key_id = os.getenv("AWS_KMS_KEY_ID")
    if not key_id:
        raise RuntimeError(
            "AWS_KMS_KEY_ID is required when ENCRYPTION_PROVIDER=aws_kms"
        )
    client = boto3.client("kms", region_name=os.getenv("AWS_REGION"))
    resp = client.generate_data_key(KeyId=key_id, KeySpec="AES_256")
    plaintext = resp["Plaintext"]  # type: ignore[index]
    ciphertext = resp.get("CiphertextBlob")  # type: ignore[assignment]
    if not isinstance(ciphertext, (bytes, bytearray)):
        raise RuntimeError("KMS did not return CiphertextBlob")
    return plaintext, ciphertext  # type: ignore[return-value]


def _resolve_key() -> tuple[bytes | None, int]:
    """Return (key_bytes, mode_code) where mode_code maps to encryption_mode gauge semantics.

    mode_code: 2=aes-gcm-local, 3=aes-gcm-kms
    """
    # 1. Static local key
    if _has_valid_local_key():
        raw = base64.b64decode(os.getenv("FIELD_ENCRYPTION_KEY", ""))
        return raw, 2
    # 2. AWS KMS provider
    if _kms_configured():
        ttl = int(os.getenv("ENCRYPTION_KMS_DATA_KEY_TTL_SECONDS", "3600"))
        force_rotate = (
            os.getenv("ENCRYPTION_KMS_FORCE_ROTATE", "false").lower() == "true"
        )
        cached = None if force_rotate else _kms_cache.get_key()
        if cached is None:
            plaintext, ciphertext = _kms_generate_data_key()
            if len(plaintext) not in (16, 24, 32):  # Should be 32 from AES_256
                raise RuntimeError("KMS returned unexpected data key length")
            _kms_cache.set_key(plaintext, ttl)
            cached = plaintext
            # store ciphertext blob for potential reuse / rotation validation
            try:
                import base64 as _b64

                global _kms_ciphertext_b64
                _kms_ciphertext_b64 = _b64.b64encode(ciphertext).decode()
            except Exception:
                pass
        return cached, 3
    return None, -1


_SINGLETON: Encryptor | None = None


def _reset_for_test():  # pragma: no cover - test helper
    global _SINGLETON
    _SINGLETON = None


def _init_mode_gauge():
    """Return (and lazily create) the encryption_mode Gauge.

    Tests reload this module multiple times with different env settings. The
    prometheus_client library raises ValueError if a metric with the same name
    is registered again. We guard by reusing the existing collector when it
    already exists in the default registry.
    """
    if not Gauge:
        return None
    # If already present in registry, reuse it
    try:
        # Fast path: attempt creation
        return Gauge(
            "encryption_mode",
            "Field encryption mode (0=disabled,1=placeholder,2=aes-gcm)",
        )
    except ValueError:
        # Duplicate – pull the existing one from registry (internal API access acceptable in test context)
        if REGISTRY and hasattr(REGISTRY, "_names_to_collectors"):
            return REGISTRY._names_to_collectors.get("encryption_mode")  # type: ignore[attr-defined]
        return None


_MODE_GAUGE = _init_mode_gauge()

_ACTIVE_KEY_ID: str | None = None  # for rotation introspection
_SECONDARY_KEY: bytes | None = None  # optional old key to allow decrypt-only


def get_encryptor() -> Encryptor:
    global _SINGLETON
    # If strong encryption newly required after initial init, force re-eval
    require_strong = os.getenv("REQUIRE_STRONG_ENCRYPTION", "false").lower() == "true"
    if _SINGLETON is not None and not require_strong:
        return _SINGLETON
    if _SINGLETON is not None and require_strong:
        # If we already have real encryptor it's fine; if placeholder/none, re-init
        if isinstance(_SINGLETON, RealEncryptor):  # type: ignore
            return _SINGLETON
        _SINGLETON = None  # force re-init path below
    feature_on = os.getenv("FEATURE_FIELD_ENCRYPTION", "false").lower() == "true"
    # (require_strong already computed above)
    if feature_on:
        key, mode_code = _resolve_key()
        if key is not None and AESGCM:
            # Dual-key support: if FIELD_ENCRYPTION_SECONDARY_KEY provided, keep decrypt path
            global _ACTIVE_KEY_ID, _SECONDARY_KEY
            sec_b64 = os.getenv("FIELD_ENCRYPTION_SECONDARY_KEY")
            if sec_b64:
                try:
                    _SECONDARY_KEY = base64.b64decode(sec_b64)
                except Exception:
                    _SECONDARY_KEY = None
            active_b64 = (
                os.getenv("FIELD_ENCRYPTION_KEY") if _has_valid_local_key() else None
            )
            _ACTIVE_KEY_ID = (
                "local:primary"
                if active_b64
                else ("kms:data-key" if mode_code == 3 else None)
            )
            primary_encryptor = RealEncryptor(key)
            if _SECONDARY_KEY and len(_SECONDARY_KEY) in (16, 24, 32):

                class DualKeyEncryptor:
                    def __init__(self, primary: RealEncryptor, secondary: bytes):
                        self._primary = primary
                        try:
                            self._secondary = RealEncryptor(secondary)
                        except Exception:
                            self._secondary = None

                    def encrypt(self, value: str) -> str:
                        return self._primary.encrypt(value)

                    def decrypt(self, value: str) -> str:
                        # try primary then secondary
                        plain = self._primary.decrypt(value)
                        if plain == value and self._secondary:
                            return self._secondary.decrypt(value)
                        return plain

                _SINGLETON = DualKeyEncryptor(primary_encryptor, _SECONDARY_KEY)  # type: ignore
            else:
                _SINGLETON = primary_encryptor
        else:
            if require_strong:
                raise RuntimeError(
                    "Strong encryption required but no valid key source (local or KMS) available"
                )
            _SINGLETON = SimpleObfuscator()
            mode_code = 1  # placeholder
        if _MODE_GAUGE:
            if isinstance(_SINGLETON, RealEncryptor):
                _MODE_GAUGE.set(mode_code)  # 2 local, 3 kms
            else:
                _MODE_GAUGE.set(1)
    else:
        if require_strong:
            # Misconfiguration: strong required yet feature disabled
            raise RuntimeError("Strong encryption required but feature flag disabled")
        _SINGLETON = NoopEncryptor()
        if _MODE_GAUGE:
            _MODE_GAUGE.set(0)
    return _SINGLETON


def hash_identifier(identifier: str) -> str:
    salt = os.getenv("PII_HASH_SALT", "default_salt").encode()
    return hmac.new(salt, identifier.encode(), hashlib.sha256).hexdigest()
