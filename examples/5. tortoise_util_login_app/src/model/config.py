from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    username: str
    password: str
    expires: int


class MinIOConfig(BaseModel):
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str


class JWTConfig(BaseModel):
    expires: float
    algorithm: str
    secret_key: str
    token_key: str


class TortoiseConfig(BaseModel):
    url: str
    modules: list[str]


class FastAPIConfig(BaseModel):
    session_key: str
    jwt: JWTConfig


class ProjConfig(BaseModel):
    redis: RedisConfig
    minio: MinIOConfig
    fastapi: FastAPIConfig
    tortoise: TortoiseConfig
