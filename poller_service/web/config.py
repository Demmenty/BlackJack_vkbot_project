import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class ServerConfig:
    host: str = "localhost"


@dataclass
class RabbitMQConfig:
    url: str = "localhost"


@dataclass
class Config:
    session: SessionConfig = None
    bot: BotConfig = None
    server: ServerConfig = None
    rabbitmq: RabbitMQConfig = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
        ),
        server=ServerConfig(host=raw_config["server"]["host"]),
        rabbitmq=RabbitMQConfig(url=raw_config["rabbitmq"]["url"]),
    )
