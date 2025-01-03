from pydantic import BaseModel
from src.enums.user import GenderEnum


class UserInfoVO(BaseModel):
    id: str
    username: str
    age: int
    gender: GenderEnum
    address: list[str]
