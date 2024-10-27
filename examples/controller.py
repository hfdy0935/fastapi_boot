import time
from typing import Annotated

from fastapi import Query, Request
from fastapi_boot import Controller, Inject, Get, Post, Put, Delete, usedep, Prefix

from beans import Animal, Room, Test, User, China, America, UK
from service import UserService


def get_user_agent(request: Request):
    return request.headers.get("user-agent") or ""


@Controller("/user", tags=["用户模块"])
class UserController:
    user_service = Inject(UserService)
    user_service1 = Inject.Qualifier("s1") @ UserService
    user_service2 = UserService @ Inject

    user_agent = usedep(get_user_agent)

    def __init__(
        self,
        animal: Annotated[Animal, "fish"],
        bird: Annotated[Animal, "bird"],
        bird2: Annotated[Animal, "bird"],
        china: Room[China],
        america: Room[America],
        uk: Room[UK],
    ):
        self.user_service3 = Inject(UserService)
        self.user_service4 = Inject @ UserService
        self.user_service5 = UserService @ Inject
        self.animal = animal
        self.test = Test @ Inject
        self.bird = bird
        self.bird2 = bird2

        self.china = china
        self.america = america
        self.uk = uk

    @Get("", summary="测试")
    async def get_by_id(self, id: str = Query()):
        return self.user_service.get_by_id(id)

    @Get("/getall")
    async def getall(self):
        print(self.user_agent)
        print(self.user_service == self.user_service2)
        print(self.animal.name)
        print(self.bird, self.bird2, self.bird == self.bird2)
        print(self.china, self.america, self.uk)
        return self.user_service4.getall()

    @Post()
    async def add(self, user: User):
        self.user_service.add(user)
        return True

    @Put()
    async def update(self, user: User):
        self.user_service.update_by_id(user)
        return True

    @Delete()
    async def delete_by_id(self, id: str = Query()):
        self.user_service.delete_by_id(id)
        return True

    @Get("/test")
    def test_req(self):
        return self.test

    @Prefix("/animal")
    class Animal1:
        user_agent = usedep(get_user_agent)

        def __init__(self, bird: Annotated[Animal, "bird"]):
            self.bird = bird

        @Get("/user-agent")
        def get_user_agent(self):
            return dict(userAgent=self.user_agent, animal=self.bird)

        @Prefix("/layer1")
        class Layer1:
            @Prefix("/layer2")
            class Layer2:
                @Prefix("/layer3")
                class Layer3:
                    @Prefix("/layer4")
                    class Layer4:
                        @Prefix("/layer5")
                        class Layer5:
                            @Prefix("/layer6")
                            class Layer6:
                                @Prefix("/layer7")
                                class Layer7:
                                    @Prefix("/layer8")
                                    class Layer8:
                                        @Prefix("/layer9")
                                        class Layer9:
                                            @Prefix("/layer10")
                                            class Layer10:
                                                @Prefix("/layer11")
                                                class Layer11:
                                                    @Prefix("/layer12")
                                                    class Layer12:
                                                        @Prefix("/layer13")
                                                        class Layer13:
                                                            @Prefix("/layer14")
                                                            class Layer14:
                                                                @Prefix("/layer15")
                                                                class Layer15:
                                                                    @Prefix("/layer16")
                                                                    class Layer16:
                                                                        @Prefix("/layer17")
                                                                        class Layer17:
                                                                            @Prefix("/layer18")
                                                                            class Layer18:
                                                                                @Prefix("/layer19")
                                                                                class Layer19:
                                                                                    @Prefix("/layer20")
                                                                                    class Layer20:
                                                                                        @Post("/layer-route")
                                                                                        def layer_route(
                                                                                            self,
                                                                                        ):
                                                                                            return "You did it!"


@Controller("/fbv-test").get("")
def fbv():
    return dict(code=200, msg="success", data=dict(time=time.time()))
