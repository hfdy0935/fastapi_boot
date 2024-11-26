from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    password: str
    expires: int


class MinIOConfig(BaseModel):
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str


class FastAPIConfig(BaseModel):
    token_key: str
    session_key: str


class ProjConfig(BaseModel):
    redis: RedisConfig
    minio: MinIOConfig
    fastapi: FastAPIConfig
