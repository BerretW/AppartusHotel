from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pro načtení proměnných ze souboru .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Databaze
    DATABASE_URL: str

    # Bezpecnost / JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

# Vytvorime jednu jedinou instanci, kterou bude pouzivat cela aplikace
settings = Settings()