import hashlib


class StubLLMAdapter:
    name = "llm_stub"
    version = "0.0.1"

    async def generate(self, prompt: str, context: list[str] | None = None) -> str:
        ctx_part = " | ".join(context[:2]) if context else ""
        base = f"[LLM_STUB v{self.version}] {prompt} {ctx_part}".strip()
        return base


class StubCaptionAdapter:
    name = "captioner_stub"
    version = "0.0.1"

    async def caption(self, image_bytes: bytes) -> str:
        h = hashlib.sha1(image_bytes).hexdigest()[:8]
        return f"Stub caption {h}"


class StubTTSAdapter:
    name = "tts_stub"
    version = "0.0.1"

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        return f"AUDIO_STUB::{voice or 'default'}::{text[:40]}".encode()
