import logging
from fastapi import BackgroundTasks, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi_boot.core import Controller, Get, Post, Put, Delete, Head, Options, Patch, Req, Trace, WS, Prefix, use_dep
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)


@Get('/h1', tags=['1. Request methods'])
async def h1():
    return 'hello world'


@Req('/h2', tags=['1. Request methods'])
async def h2():
    return 'hello world'


@WS('/ws-fbv')
async def ws(websocket: WebSocket):
    """
    visit `./single-websocket.html` to use frontend
    """
    try:
        await websocket.accept()
        logging.info('websocket connected...')
        while True:
            data = await websocket.receive_json()
            logging.info(f'receive client message: {data}')
            await websocket.send_json(data)
    except WebSocketDisconnect:
        logging.warning('websocket disconnected')


def use_ua(request: Request):
    return request.headers.get('User-Agent')


class BaseController:
    ua = use_dep(use_ua)


@Controller('/request-methods', tags=['1. Request methods'])
class RequestMethodController(BaseController):
    @Req('/req')
    def req(self):
        print(self.ua)
        return 'req default get'

    @Req('/req', methods=['POST'])
    def req_post(self):
        return 'req post'

    @Get()
    def get(self):
        return 'get'

    @Post()
    def post(self):
        return 'post'

    @Put()
    def put(self):
        return 'put'

    @Delete()
    def delete(self):
        return 'delete'

    @Head(status_code=204)
    def head(self, response: Response):
        response.headers["X-Cat-Dog"] = "Alone in the world"

    @Options()
    def options(self, response: Response):
        response.headers.update({'Access-Control-Allow-Origin': '*'})

    @Trace(description='not supported in some browsers')
    def trace(self):
        return 'trace'

    @Patch()
    def patch(self):
        return 'patch'

    @Prefix()
    class WebSocketController:
        @WS()
        async def ws(self, websocket: WebSocket):
            """
            visit `./single-websocket.html` to use frontend
            """
            try:
                await websocket.accept()
                logging.info('websocket connected...')
                while True:
                    data = await websocket.receive_json()
                    logging.info(f'receive client message: {data}')
                    await websocket.send_json(data)
            except WebSocketDisconnect:
                logging.warning('websocket disconnected')


class MessageDTO(BaseModel):
    msg: str
    time: str

    def to_broadcast_vo(self):
        return f'broadcast message "{self.msg}" at {self.time}'


class Message(MessageDTO):
    user_id: int

    def to_msg_vo(self):
        return f'user {self.user_id} say "{self.msg}" at {self.time}'


@Controller('/chat', tags=['2. chat-app'])
class ChatController:
    def __init__(self) -> None:
        self.clients: dict[int, WebSocket] = {}

    async def send_to_others(self, id: int, msg: Message):
        for k, v in self.clients.items():
            if k != id:
                await v.send_json(msg.to_msg_vo())

    @WS()
    async def chat(self, websocket: WebSocket):
        """
        visit `./chat-app.html` to use frontend
        """
        try:
            user_id = id(websocket)
            await websocket.accept()
            self.clients.update({user_id: websocket})
            logging.info(f'user {user_id} connected...')
            while True:
                data: dict = await websocket.receive_json()
                await self.send_to_others(user_id, Message(user_id=user_id, **data))

        except WebSocketDisconnect:
            logging.warning(f'user {user_id} websocket disconnected')
        except Exception as e:
            print(e)
            logging.error(f'error')

    async def do_broadcast(self, msg: MessageDTO):
        for v in self.clients.values():
            await v.send_json(msg.to_broadcast_vo())

    @Post('/broadcast')
    async def broadcast(self, msg: MessageDTO, task: BackgroundTasks):
        task.add_task(self.do_broadcast, msg)
        return 'ok'


@Controller('/prefix', tags=['3. Prefix'])
class PrefixController:
    @Get()
    def _(self): ...

    @Prefix()
    class Foo:
        @Post()
        def _(self):
            return 'post in prefix'

    @Prefix('/bar')
    class Bar:
        @Put()
        def _(self):
            return 'put in prefix with prefix "bar"'

    @Prefix('/p1')
    class P1:
        @Prefix('/p2')
        class P2:
            @Prefix('/p3')
            class P3:
                @Prefix('/p4')
                class P4:
                    @Prefix('/p5')
                    class P5:
                        @Prefix('/p6')
                        class P6:
                            @Delete()
                            def _(self):
                                return 'level6 put'

                            @Prefix('/p7')
                            class P7:
                                @Prefix('/p8')
                                class P8:
                                    @Prefix('/p9')
                                    class P9:
                                        @Prefix('/p10')
                                        class P10:
                                            @Get()
                                            def _(self):
                                                return 'level 10 get'
