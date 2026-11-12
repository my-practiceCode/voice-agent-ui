from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str
    groq_llm_model: str
    groq_stt_model: str
    deepgram_api_key: str
    # deepgram_tts_model: str
    deepgram_tts_model_en: str
    deepgram_tts_model_ur: str
    deepgram_tts_model_id: str

    dense_embedding_model: str
    sparse_embedding_model: str

    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    qdrant_url: str
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str

    default_client_id: Optional[str] = None

    
    supabase_url: str
    supabase_service_key: str

    timezone: str


settings = Settings()