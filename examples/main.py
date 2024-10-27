from argparse import ArgumentParser, Namespace
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_boot import FastApiBootApplication, Config
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    FastApiBootApplication.run_app(app, config=Config(exclude_scan_path=["fastapi_boot", "controller1"]))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def f():
    return RedirectResponse("/docs")


def main(host: str, port: int, reload: bool):
    # uvicorn启动时会再导入一次本文件
    uvicorn.run("main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--host", default="localhost", type=str, help="ip or domain")
    parser.add_argument("--port", default=8000, type=int, help="端口号")
    parser.add_argument("--reload", default=True, type=bool, help="更新是否自动重新加载")
    args: Namespace = parser.parse_args()
    main(args.host, args.port, args.reload)
