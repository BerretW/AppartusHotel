from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Databaze
    DATABASE_URL: str

    # Bezpecnost / JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

# Vytvorime jednu jedinou instanci, kterou bude pouzivat cela aplikace
settings = Settings()