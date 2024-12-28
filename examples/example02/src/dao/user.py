from uuid import uuid4

from fastapi_boot import Repository
from src.model.dto.user import LoginDTO, RegisterDTO
from src.model.entity.user import UserEntity
from src.util.md5 import MD5Util


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
        print(await UserEntity.all())
        return len(await UserEntity.filter(username=name)) > 0

    async def exists_and_get(self, dto: LoginDTO) -> UserEntity | None:
        """return user_entity if user esists else None"""
        db_user = await UserEntity.filter(username=dto.username).first()
        if db_user and self.md5.verify(dto.password, db_user.password):
            return db_user

    async def get_by_id(self, id: str) -> UserEntity | None:
        return await UserEntity.filter(id=id).first()
