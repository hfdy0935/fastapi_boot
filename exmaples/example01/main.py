import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from fastapi_boot import provide_app

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='foo')
# if use vscode live server
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:5500'])
provide_app(app)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
