from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from fastapi_boot import provide_app
import uvicorn

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='foo')
provide_app(app)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
