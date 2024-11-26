import tomllib

from fastapi_boot import Bean

from model.config import FastAPIConfig, MinIOConfig, ProjConfig, RedisConfig


@Bean
def _() -> ProjConfig:
    with open('./application.toml', 'rb') as f:
        data = tomllib.load(f)
        return ProjConfig(
            redis=RedisConfig(**data.get('redis', {})),
            minio=MinIOConfig(**data.get('minio', {})),
            fastapi=FastAPIConfig(**data.get('fastapi', {})),
        )
