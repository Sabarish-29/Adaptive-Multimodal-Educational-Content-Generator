# Runbook: Encryption Key Rotation

## Scope
Rotate FIELD_ENCRYPTION_KEY used for AES-GCM content field encryption.

## Preconditions
- Keys stored in secure secret manager (e.g., Vault, AWS KMS) not in .env directly.
- Application supports dual-key decrypt (current + previous) (TODO future enhancement).

## Steps (Automated Helper Script)
Use the helper script `python scripts/rotate_encryption_key.py --out secrets/new_field_key.b64` which will:
1. Generate a new 32-byte base64 key.
2. Append an export line to a specified env snippet (optional `--env-update .env`).
3. Optionally record a JSON rotation metadata file with timestamp (`--meta rotations.json`).

Manual / Deployment Flow:
1. Run rotation script: `python scripts/rotate_encryption_key.py --out secrets/field_key_2025_08_19.b64 --meta rotations.json`.
2. Store key securely (vault / secret manager). Do NOT commit raw key.
3. Update deployment secret to include new key as `FIELD_ENCRYPTION_KEY_NEW` (if dual mode) or replace `FIELD_ENCRYPTION_KEY` if single key.
4. (If dual decrypt supported) set `FIELD_ENCRYPTION_SECONDARY_KEY` to previous key for grace window.
5. Deploy application with new env vars.
6. Run `python scripts/reencrypt_fields.py --dry-run` to view objects requiring re-encryption (script currently placeholder; extend when per-record envelopes added).
7. After verification window, remove secondary key env var.

## Verification
- Run encryption round-trip tests in staging.
- Check logs for decryption fallbacks.

## Rollback
- Re-deploy with previous key; ciphertexts remain valid.

## Future Improvements
- Persist encrypted data key ciphertext across restarts to avoid churn.
- Implement key version field in encrypted documents.
- Add automatic background re-encryption job.
