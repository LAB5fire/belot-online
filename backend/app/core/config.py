from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    debug: bool = False
    # Comma-separated list of allowed frontend origins. Set in production to the
    # deployed frontend URL(s), e.g. "https://belot-frontend.onrender.com".
    # Bare hostnames and "*" are also accepted. Kept as a string so a single
    # env var (CORS_ORIGINS) parses cleanly across environments.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = {"env_file": ".env", "extra": "allow"}

    @property
    def allowed_origins(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if raw == "*":
            return ["*"]
        origins: list[str] = []
        for part in raw.split(","):
            o = part.strip().rstrip("/")
            if not o:
                continue
            # Promote bare hostnames (e.g. from Render's fromService host) to
            # https:// so they match the browser Origin header.
            if "://" not in o:
                o = f"https://{o}"
            origins.append(o)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
