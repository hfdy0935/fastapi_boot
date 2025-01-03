import uvicorn
from fastapi import FastAPI
from fastapi_boot.core import provide_app
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='foo')
provide_app(app)

if __name__ == '__main__':
    uvicorn.run('main:app', port=8001, reload=True)
