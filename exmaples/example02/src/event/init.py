from fastapi import APIRouter, FastAPI
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
def _(_):
    print(1)


router = APIRouter(prefix='/api-router-mount-event')


@router.post('')
def post():
    return 'post'


@OnAppProvided()
def _(app: FastAPI):
    app.include_router(router)
