from fastapi import FastAPI
from fastapi_boot.core import provide_app


app = FastAPI(title='app1')
provide_app(app)
