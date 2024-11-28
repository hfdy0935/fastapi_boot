import logging

from fastapi import Request, WebSocket
from fastapi.responses import JSONResponse

from fastapi_boot import Controller

logging.basicConfig(level=logging.INFO)


@Controller('/fbv', tags=['1. fbv']).post('/foo')
def _(request: Request):
    return JSONResponse(content=dict(msg='Hello World', ua=request.headers.get('user-agent')), status_code=200)


@Controller('/fbv').websocket('/chat')
async def _(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            logging.info(f'receive data {data}')
            await websocket.send_text(data)
    except:
        logging.info(f'{websocket} disconnected')
