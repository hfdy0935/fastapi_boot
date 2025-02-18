import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_boot.core import provide_app
import uvicorn
start = time.time_ns()
app = provide_app(FastAPI())
end = time.time_ns()
print(f'provide_app cost {(end-start)/1000000}ms')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)
