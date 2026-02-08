"""NeuroSync AI – Orchestrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "orchestrator"
    host: str = "0.0.0.0"
    port: int = 8010
    debug: bool = False
    log_level: str = "INFO"

    # Agent URLs
    cognitive_guardian_url: str = "http://cognitive-guardian:8011"
    content_architect_url: str = "http://content-architect:8012"
    tutor_agent_url: str = "http://tutor-agent:8013"
    intervention_agent_url: str = "http://intervention-agent:8014"
    progress_analyst_url: str = "http://progress-analyst:8015"
    peer_connector_url: str = "http://peer-connector:8016"

    # External services
    redis_url: str = "redis://localhost:6379/0"
    mongodb_uri: str = "mongodb://localhost:27017/neurosync"

    # OpenAI / LLM
    openai_api_key: str = ""

    class Config:
        env_prefix = "NEUROSYNC_"
        env_file = ".env"


settings = Settings()
