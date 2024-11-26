from typing import Annotated

from fastapi_boot import Inject, Service
from minio import Minio
from redis import Redis

from model.config import ProjConfig
from model.user import User

a = Inject(User, 'a')


@Service
class UserService:
    b = User @ Inject.Qualifier('b')

    def __init__(self, c: Annotated[User, 'c']) -> None:
        self.c = c
        assert c == Inject.Qualifier('c') @ User, 'c doesn"t equal another injected c'
        self.users: list[User] = [a, self.b, self.c]
        self.minio = Inject @ Minio
        self.bucket_name = Inject(ProjConfig).minio.bucket_name
        self.redis = Redis @ Inject
        self.expires = Inject(ProjConfig).redis.expires
        print('UserService init', self.minio, self.bucket_name, self.redis, self.expires)

    def getall(self):
        return self.users

    def get_by_name(self, name: str) -> User | None:
        return r[0] if (r := [u for u in self.users if u.name == name]) else None

    def add(self, user: User):
        self.users.append(user)

    def delete_by_name(self, name: str):
        self.users = [u for u in self.users if u.name != name]
