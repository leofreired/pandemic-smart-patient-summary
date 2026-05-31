import os


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class Settings:
    app_port: int = int(os.getenv("APP_PORT", "8080"))
    sample_mode: bool = _to_bool(os.getenv("SAMPLE_MODE", "true"), True)
    lookback_days: int = int(os.getenv("LOOKBACK_DAYS", "180"))

    fhir_base_url: str = os.getenv("FHIR_BASE_URL", "").rstrip("/")
    fhir_bearer_token: str = os.getenv("FHIR_BEARER_TOKEN", "")
    fhir_username: str = os.getenv("FHIR_USERNAME", "")
    fhir_password: str = os.getenv("FHIR_PASSWORD", "")
    fhir_oauth_token_url: str = os.getenv("FHIR_OAUTH_TOKEN_URL", "").rstrip("/")
    fhir_oauth_client_id: str = os.getenv("FHIR_OAUTH_CLIENT_ID", "")
    fhir_oauth_client_secret: str = os.getenv("FHIR_OAUTH_CLIENT_SECRET", "")
    fhir_oauth_scope: str = os.getenv("FHIR_OAUTH_SCOPE", "")
    fhir_verify_tls: bool = _to_bool(os.getenv("FHIR_VERIFY_TLS", "true"), True)

    fhir_sql_endpoint: str = os.getenv("FHIR_SQL_ENDPOINT", "").rstrip("/")
    fhir_sql_username: str = os.getenv("FHIR_SQL_USERNAME", "")
    fhir_sql_password: str = os.getenv("FHIR_SQL_PASSWORD", "")

    ai_hub_base_url: str = os.getenv("AI_HUB_BASE_URL", "").rstrip("/")
    ai_hub_api_key: str = os.getenv("AI_HUB_API_KEY", "")
    ai_hub_model: str = os.getenv("AI_HUB_MODEL", "gpt-4o-mini")
    ai_hub_timeout_seconds: int = int(os.getenv("AI_HUB_TIMEOUT_SECONDS", "30"))


settings = Settings()
