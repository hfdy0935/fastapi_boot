from fastapi import HTTPException
from fastapi_boot.core import Service, Inject

from src.dao.demo1 import Demo1Repository
from src.model import Animal, Biology, Plant

dao = Inject(Demo1Repository)

# Service, Repository and Component are same,and can be injected anywhere after app provided


@Service
class Demo1Service:
    dao = Inject@Demo1Repository

    def __init__(self, bio: Biology[Plant]) -> None:
        assert dao == self.dao
        self.bio = bio

    def getall(self):
        return dao.getall()

    def get_by_id(self, id: int):
        return dao.get_by_id(id)

    def add_and_count(self, animal: Animal):
        dao.add(animal)
        return dao.count()

    def delete_and_count(self, id: int):
        if not dao.is_exist(id):
            raise HTTPException(500, f"id {id} doesn't not exists")
        self.dao.pop(id)
        return self.dao.count()

    def update(self, animal: Animal):
        lines = dao.update(animal)
        if lines == 0:
            raise HTTPException(500, 'update fail')
        return {'lines': lines}
