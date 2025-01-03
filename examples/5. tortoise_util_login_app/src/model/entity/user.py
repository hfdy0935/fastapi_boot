from typing import Self

from src.enums.user import GenderEnum
from src.model.dto.user import UpdateUserInfoDTO
from src.model.vo.user import UserInfoVO
from tortoise import fields
from tortoise.models import Model


class UserEntity(Model):
    id = fields.CharField(primary_key=True, max_length=50)
    username = fields.CharField(min_length=5, max_length=12, unique=True)
    password = fields.CharField(regex=r'[^\d][0-9a-zA-Z#@_]{7,15}', max_length=50, description='password"s md5')
    age = fields.IntField(ge=0, default=0)
    gender = fields.IntEnumField(GenderEnum, default=GenderEnum.MALE)
    address = fields.JSONField(description='address list', default='[]')

    class Meta:
        table = "user"

    @property
    def jwt_payload(self) -> dict[str, str]:
        return dict(id=self.id, username=self.username)

    @classmethod
    def from_dict(cls, dic: dict) -> Self:
        return cls(**dic)

    def to_userinfo_vo(self) -> UserInfoVO:
        return UserInfoVO(id=self.id, username=self.username, age=self.age, gender=self.gender, address=self.address)

    async def update_by_update_user_info_dto(self, dto: UpdateUserInfoDTO):
        self.age = dto.age
        self.gender = dto.gender
        self.address = dto.address
        await self.save()
