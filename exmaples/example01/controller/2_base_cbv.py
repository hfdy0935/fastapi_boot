import asyncio
import logging
from dataclasses import asdict, dataclass
from typing import Generic, TypeVar

from exception.exp import WsForbidCharException
from fastapi import HTTPException, Path, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from fastapi_boot import Controller, Delete, Get, Post, Prefix, Put, Req, Socket


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

    @Req('/f', methods=['GET'])
    def f():
        return True

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

    @Prefix()
    class WsController:
        def __init__(self):
            self.socket_client_dict: dict[int, WebSocket] = {}
            self.forbid_char = 'a'

        async def send_to_others(self, sender_id: int, message: str):
            for id, client in self.socket_client_dict.items():
                if id != sender_id:
                    await client.send_text(f'{sender_id} say: {message}')

        async def broadcast(self, message: str):
            await self.send_to_others(-1, message)

        @Socket('/chat')
        async def chat(self, websocket: WebSocket):
            id = -1
            try:
                id = len(self.socket_client_dict) + 1
                await websocket.accept()
                self.socket_client_dict.update({id: websocket})
                while True:
                    message = await websocket.receive_text()
                    # if anyone send a message which contains forbid_char, he will be removed from the chat room.
                    if self.forbid_char in message:
                        self.socket_client_dict.pop(id)
                        raise WsForbidCharException(id, message, self.forbid_char)
                    await self.send_to_others(id, message)
            except WebSocketDisconnect:
                logging.info(f'client {id} disconnected')
                self.socket_client_dict.pop(id)

        @Post('/broadcast')
        async def send_broadcast_msg(self, msg: str = Query()):
            await self.broadcast(msg)
            return 'ok'
