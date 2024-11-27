from fastapi import FastAPI
from fastapi_boot import provide_app


app = FastAPI(title='app1')
provide_app(app)
