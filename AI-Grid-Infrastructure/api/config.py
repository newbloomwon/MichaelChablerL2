from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # silently ignore any extra env vars
    )

    # ERCOT
    ercot_subscription_key: str = ""
    ercot_subscription_key_secondary: str = ""
    ercot_username: str = ""
    ercot_password: str = ""
    ercot_client_id: str = ""
    ercot_token_url: str = "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
    ercot_frequency_endpoint: str = ""
    ercot_frequency_url: str = "https://www.ercot.com/content/cdr/html/real_time_system_conditions.html"
    ercot_base_url: str = "https://api.ercot.com/api/public-reports"

    # ISO-NE
    isone_username: str = ""
    isone_password: str = ""
    isone_base_url: str = "https://webservices.iso-ne.com/api/v1.1"

    # App
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
