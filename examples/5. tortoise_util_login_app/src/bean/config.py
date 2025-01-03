import tomllib

from fastapi_boot.core import Bean
from src.model.config import FastAPIConfig, MinIOConfig, ProjConfig, RedisConfig, TortoiseConfig


@Bean
def _() -> ProjConfig:
    with open('./resource/application.toml', 'rb') as f:
        data = tomllib.load(f)
        return ProjConfig(
            redis=RedisConfig(**data.get('redis', {})),
            minio=MinIOConfig(**data.get('minio', {})),
            fastapi=FastAPIConfig(**data.get('fastapi', {})),
            tortoise=TortoiseConfig(**data.get('tortoise', {})),
        )
