from fastapi import FastAPI
from fastapi_boot.core import Inject, Lifespan, Bean
from tortoise import Tortoise
from src.model.foo import Foo
from src.model.config import ProjConfig


@Lifespan
async def init_db(app: FastAPI):
    cfg = Inject(ProjConfig)
    url = cfg.tortoise.url
    modules = cfg.tortoise.modules
    await Tortoise.init(db_url=url, modules=dict(models=modules))
    # need late inject
    Bean(lambda: Foo('foo', 'fOO'))
    yield
