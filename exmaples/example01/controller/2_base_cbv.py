import asyncio
import logging
from dataclasses import asdict, dataclass
from typing import Generic, TypeVar

from fastapi import HTTPException, Path, Query, WebSocket
from fastapi_boot import Controller, Delete, Get, Post, Put, Socket
from pydantic import BaseModel


class Baz(BaseModel):
    baz: str


@dataclass
class Baz1:
    baz1: str


T = TypeVar('T')


class BaseResp(BaseModel, Generic[T]):
    code: int
    msg: str
    data: T | None = None


async def db_delete_by_id(id: str):
    await asyncio.sleep(0.1)
    return True


@Controller('/base-cbv', tags=['2. base cbv'])
class FirstController:

    def __init__(self):
        self.socket_client_dict: dict[WebSocket, int] = {}

    @Get('/foo', response_model=BaseResp[str])
    def get_foo(self):
        return BaseResp(code=200, msg='success', data='foo')

    @Post('/bar')
    def post_bar(self, p: str = Query()):
        return p

    @Put('/baz')
    def put_baz(self, baz: Baz, baz1: Baz1):
        return dict(**baz.model_dump(), **asdict(baz1))

    @Delete('/{id}')
    async def delete_item(self, id: str = Path()):
        if await db_delete_by_id(id):
            return dict(code=200, msg='success')
        raise HTTPException(status_code=500, detail=f'get an error when delete item {id}')

    async def send_to_others(self, websocket: WebSocket, message: str):
        sender = self.socket_client_dict.get(websocket)
        for client, id in self.socket_client_dict.items():
            if client != websocket:
                await client.send_text(f'{sender} say: {message}')

    @Socket('/chat')
    async def chat(self, websocket: WebSocket):
        id = -1
        try:
            await websocket.accept()
            id = len(self.socket_client_dict) + 1
            self.socket_client_dict.update({websocket: id})
            while True:
                message = await websocket.receive_text()
                await self.send_to_others(websocket, message)
        except:
            logging.info(f'client {id} disconnected')
