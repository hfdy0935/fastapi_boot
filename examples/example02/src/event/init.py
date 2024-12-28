from fastapi import FastAPI
from fastapi_boot import Inject, Lifespan
from tortoise import Tortoise
from src.model.config import ProjConfig


@Lifespan
async def init_db(app: FastAPI):
    cfg = Inject(ProjConfig)
    url = cfg.tortoise.url
    modules = cfg.tortoise.modules
    await Tortoise.init(db_url=url, modules=dict(models=modules))
    yield
