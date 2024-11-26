from fastapi_boot import Bean, Inject
from minio import Minio
from redis import Redis

from model.config import ProjConfig


@Bean
def get_redis() -> Redis:
    c = (Inject @ ProjConfig).redis
    return Redis(host=c.host, port=c.port, db=c.db, password=c.password)


@Bean
def get_minio_client(c: ProjConfig) -> Minio:
    return Minio(
        endpoint=c.minio.endpoint,
        access_key=c.minio.access_key,
        secret_key=c.minio.secret_key,
    )
