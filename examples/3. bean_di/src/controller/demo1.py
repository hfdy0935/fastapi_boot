from fastapi import Path
from fastapi_boot.core import Controller, Inject, Get, Post, Put, Delete

from src.model import Animal, Biology, Plant
from src.service.demo1 import Demo1Service


service = Inject(Demo1Service)


@Controller('/bean', tags=['5. Bean DI'])
class BeanController:

    @Get('/bio', response_model=Biology[Plant])
    def _(self):
        return Inject(Biology[Plant])

    @Get('/all', response_model=list[Animal])
    def getall(self):
        return service.getall()

    @Get('/{id}', response_model=Animal | None)
    def get_by_id(self, id: int = Path(description='Animal"s id')):
        return service.get_by_id(id)

    @Post(response_model=dict)
    def add_animal(self, animal: Animal):
        return {'count': service.add_and_count(animal)}

    @Delete('/{id}', response_model=dict)
    def delete_by_id(self, id: int = Path()):
        return {'current count': service.delete_and_count(id)}

    @Put(response_model=dict)
    def update_animal(self, animal: Animal):
        return service.update(animal)
