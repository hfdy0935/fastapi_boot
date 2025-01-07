from dataclasses import dataclass
from uuid import uuid4

from fastapi_boot.core import Repository
from fastapi_boot.tortoise_util import Select, Delete
from src.enums.user import GenderEnum
from src.model.vo.user import UserInfoVO
from src.model.dto.user import LoginDTO, RegisterDTO
from src.model.entity.user import UserEntity
from src.util.md5 import MD5Util


@dataclass
class UserInfoVO1:
    id: str
    username: str
    age: int
    gender: GenderEnum
    address: list[str]


@Repository
class UserDAO:
    def __init__(self, md5: MD5Util):
        self.md5 = md5

    async def add(self, user: RegisterDTO) -> UserEntity:
        user.password = self.md5.encrypt(user.password)
        qs = UserEntity(**{**user.save_db_dict, 'id': str(uuid4())})
        await qs.save()
        return qs

    async def name_exists(self, name: str) -> bool:
        """return name exists?"""
        return len(await UserEntity.filter(username=name)) > 0

    async def exists_and_get(self, dto: LoginDTO) -> UserEntity | None:
        """return user_entity if user esists else None"""
        db_user = await UserEntity.filter(username=dto.username).first()
        if db_user and self.md5.verify(dto.password, db_user.password):
            return db_user

    @Select("""select id,username,age,gender,address from {user} where username={dto.username}""").fill(
        user=UserEntity.Meta.table
    )
    async def get_user_test(self, dto: LoginDTO): ...

    async def get_by_id1(self, id: str):
        return (
            await Select('select id,username,age,gender,address from {user} where id={user_id}')
            .fill(user=UserEntity.Meta.table, user_id=id)
            .execute(UserInfoVO)
        )

    @Select('select id,username,age,gender,address from {user} where id={user_id}').fill(user=UserEntity.Meta.table)
    async def get_by_id2(self, user_id: str) -> UserInfoVO: ...

    @Delete('delete from {user} where id={id}').fill(user=UserEntity.Meta.table)
    async def test_delete(self, id: str): ...

    @Select('select * from {user} where age>{agelt}').fill(user=UserEntity.Meta.table)
    async def get_by_agelt(self, agelt: int): ...


    CLASS = 'class1'
    # can also get some attributes from self in sql
    # for example
    # @Select('select subject, avg(score) avg_score from user where class={self.CLASS} group by subject}')
    # async def get_subject_avg_score(self): ...
