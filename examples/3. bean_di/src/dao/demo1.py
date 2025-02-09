from typing import Annotated
from fastapi import HTTPException
from fastapi_boot.core import Repository, Inject

from src.model import Animal, Config

config = Inject(Config)


@Repository
class Demo1Repository:
    def __init__(self, a1: Annotated[Animal, 'animal1']) -> None:
        self.a1 = a1
        self.alist = Inject@list[Animal]
        assert self.a1 == self.alist[0]

    def add(self, animal: Animal):
        for a in self.alist:
            if a.id == animal.id:
                raise HTTPException(500, 'id duplicated')
        self.alist.append(animal)

    def is_exist(self, id: int):
        return any([a.id == id for a in self.alist])

    def getall(self):
        return self.alist

    def get_by_id(self, id: int):
        for a in self.alist:
            if a.id == id:
                return a

    def count(self):
        return len(self.alist)

    def pop(self, index: int):
        return self.alist.pop(index)

    def update(self, animal: Animal):
        for a in self.alist:
            if a.id == animal.id:
                a.update_from_other(animal)
                return 1
        return 0
