from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Класс конфигурации приложения.

    Атрибуты:
    - db_host (str): Хост базы данных.
    - db_port (int): Порт базы данных.
    - db_name (str): Имя базы данных.
    - db_user (str): Пользователь базы данных.
    - db_password (str): Пароль пользователя базы данных.
    - debug (bool): 
    - telegram_token
    """

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    debug: bool = False
    telegram_token: str

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env")
    )


@lru_cache
def get_config():
    return Config()


def get_db_url() -> str:
    config = get_config()

    return (
        f"postgresql+asyncpg://{config.db_user}:{config.db_password}@"
        f"{config.db_host}:{config.db_port}/{config.db_name}"
    )
