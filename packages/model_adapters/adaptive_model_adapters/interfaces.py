from __future__ import annotations
from typing import Protocol


class LLMAdapter(Protocol):
    name: str
    version: str

    async def generate(self, prompt: str, context: list[str] | None = None) -> str: ...


class CaptionAdapter(Protocol):
    name: str
    version: str

    async def caption(self, image_bytes: bytes) -> str: ...


class TTSAdapter(Protocol):
    name: str
    version: str

    async def synthesize(self, text: str, voice: str | None = None) -> bytes: ...
