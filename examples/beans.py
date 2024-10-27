from dataclasses import dataclass
from typing import Annotated, Generic, Literal, TypeVar
from fastapi_boot import Bean


@dataclass
class User:
    id: str
    name: str
    age: int

    def update(self, user: "User"):
        self.name = user.name
        self.age = user.age

    @property
    def dict(self):
        return dict(id=self.id, name=self.name, age=self.age)


@Bean("user1")
def get_user1():
    return User(id="1", name="zhangsan", age=1)


@Bean("user2")
def get_user2():
    return User(id="2", name="lisi", age=2)


class Animal:
    name = "animal"

    def __init__(self, ct: str):
        print("animal新建")
        self.category = ct


@Bean("bird")
def get_bird():
    return Animal("bird")


@Bean("fish")
def get_fish():
    return Animal("fish")


class Test:
    name = "text"

    def __init__(self, arg) -> None:
        self.arg = arg


@Bean
def get_test(a: Annotated[Animal, "fish"]):
    return Test(a)


China = Literal["China"]
America = Literal["America"]
UK = Literal["UK"]
T = TypeVar("T", China, America, UK)


class Room(Generic[T]):
    def __init__(self, country: T) -> None:
        self.country = country


# 写了返回类型就按照返回类型作为依赖，适用于有泛型的复杂场景
# 没写会推断返回值类型，适用于简单不带泛型的场景
@Bean
def get_china() -> Room[China]:
    return Room("China")


@Bean
def get_america() -> Room[America]:
    return Room("America")


@Bean
def get_UK() -> Room[UK]:
    return Room("UK")
