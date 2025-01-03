# from minio import Minio
from fastapi_boot.core import Bean, Inject
from redis import Redis
from src.model.config import ProjConfig


@Bean
def get_redis() -> Redis:
    c = (Inject @ ProjConfig).redis
    # if has username and password, write them
    return Redis(host=c.host, port=c.port, db=c.db, decode_responses=True)


# if need
# @Bean
# def get_minio_client(c: ProjConfig) -> Minio:
#     return Minio(
#         endpoint=c.minio.endpoint,
#         access_key=c.minio.access_key,
#         secret_key=c.minio.secret_key,
#     )
