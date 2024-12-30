from datetime import datetime, timedelta

import jwt
from fastapi_boot.core import Component
from src.model.config import ProjConfig


@Component
class JWTUtil:
    def __init__(self, config: ProjConfig):
        self.expires = config.fastapi.jwt.expires
        self.algorithm = config.fastapi.jwt.algorithm
        self.secret_key = config.fastapi.jwt.secret_key

    def create(self, data: dict):
        data.update({'exp': datetime.now() + timedelta(seconds=self.expires)})
        return jwt.encode(data, self.secret_key, self.algorithm)

    def verify(self, token: str) -> dict | None:
        """verify jwt, return payload if success else False"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=['HS256'])
        except:
            pass
