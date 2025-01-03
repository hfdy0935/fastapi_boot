from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class BaseResp(BaseModel, Generic[T]):
    code: int = 200
    msg: str = 'success'
    data: T | None = None

    @classmethod
    def ok(cls, msg: str = 'success', data: T | None = None):
        return cls(msg=msg, data=data)

    @classmethod
    def err(cls, code: int, msg: str = 'error', data: T | None = None):
        return cls(code=code, msg=msg, data=data)

    @property
    def dict(self):
        return self.model_dump()
