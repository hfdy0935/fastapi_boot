from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_boot.core import provide_app
import uvicorn

app = provide_app(FastAPI())
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)
