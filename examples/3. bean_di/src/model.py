
from typing import Generic, Self, TypeVar
from pydantic import BaseModel


class Config(BaseModel):
    field1: str
    field2: int


class Animal(BaseModel):
    id: int
    name: str
    age: int | float
    address: list[str]

    def update_from_other(self, other: Self):
        self.id = other.id
        self.name = other.name
        self.age = other.age
        self.address = other.address


class Plant(BaseModel):
    id: int
    name: str
    age: int | float
    height: int | float


T = TypeVar('T', bound=Animal | Plant)


class Biology(BaseModel, Generic[T]):
    bio: T
