from pydantic import BaseModel, Field

from src.enums.user import GenderEnum


class LoginDTO(BaseModel):
    username: str = Field(min_length=5, max_length=12)
    password: str = Field(pattern=r'[^\d][0-9a-zA-Z#@_]{7,15}')


class RegisterDTO(LoginDTO):
    code: str = Field()

    @property
    def save_db_dict(self):
        return dict(username=self.username, password=self.password)


class UpdateUserInfoDTO(BaseModel):
    age: int = Field(ge=0)
    gender: GenderEnum
    address: list[str]
