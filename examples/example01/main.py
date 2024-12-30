import time

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_boot.core import provide_app
from starlette.middleware.sessions import SessionMiddleware

start = time.time()
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='foo')
# if use vscode live server
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:5500'])
provide_app(app)
print(time.time() - start)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
