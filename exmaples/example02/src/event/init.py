from fastapi import FastAPI
from fastapi_boot import Inject, OnAppProvided
from src.model.config import ProjConfig
from tortoise.contrib.starlette import register_tortoise


@OnAppProvided()
def init_db(app: FastAPI):
    cfg = Inject(ProjConfig)
    url = cfg.tortoise.url
    modules = cfg.tortoise.modules
    register_tortoise(app, db_url=url, modules=dict(models=modules))


@OnAppProvided(priority=100)
def f(app: FastAPI):
    print(2)


@OnAppProvided(priority=1000)
def _():
    print(1)
