import os
from .stubs import StubLLMAdapter, StubCaptionAdapter, StubTTSAdapter

ADAPTERS = {
    "llm_stub": StubLLMAdapter,
    "captioner_stub": StubCaptionAdapter,
    "tts_stub": StubTTSAdapter,
}


def get_adapter_factory():
    def factory(kind: str):
        key = os.getenv(f"MODEL_{kind.upper()}_NAME", f"{kind}_stub")
        cls = ADAPTERS.get(key)
        if not cls:
            raise ValueError(f"No adapter for kind={kind} key={key}")
        return cls()

    return factory
