from typing import Annotated
from fastapi import HTTPException
from fastapi_boot import Inject, Injectable

from beans import Animal, User


@Injectable("s1")
class UserService:
    def __init__(self, fish: Annotated[Animal, "fish"], bird: Annotated[Animal, "bird"]) -> None:
        self.user_list: list[User] = [
            Inject(User, "user1"),
            Inject(User, "user2"),
        ]
        self.animal = Animal @ Inject.Qualifier("bird")
        self.fish = fish
        self.bird = bird
        print(self.fish.category, self.bird.category)

    def get_by_id(self, id: str):
        exists_users = [u for u in self.user_list if u.id == id]
        return None if len(exists_users) == 0 else exists_users[0].dict

    def getall(self):
        return [u.dict for u in self.user_list]

    def update_by_id(self, user: User):
        exists_users = [u for u in self.user_list if u.id == user.id]
        if len(exists_users) == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        exists_users[0].update(user)

    def add(self, user: User):
        self.user_list.append(user)

    def delete_by_id(self, id: str):
        exists_users = [u for u in self.user_list if u.id == id]
        if len(exists_users) == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        self.user_list = [u for u in self.user_list if u.id != id]
