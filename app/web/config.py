import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class DatabaseConfig:
    type: str = "postgresql"
    driver: str = "asyncpg"
    host: str = "localhost"
    port: str = "5432"
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class ServerConfig:
    host: str = "localhost"


@dataclass
class RabbitMQConfig:
    url: str = "localhost"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    server: ServerConfig = None
    rabbitmq: RabbitMQConfig = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
        ),
        database=DatabaseConfig(**raw_config["database"]),
        server=ServerConfig(host=raw_config["server"]["host"]),
        rabbitmq=RabbitMQConfig(url=raw_config["rabbitmq"]["url"]),
    )
