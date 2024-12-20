import random
from collections.abc import Awaitable
from inspect import isawaitable

from fastapi import HTTPException
from fastapi_boot import Autowired, Service
from redis import Redis
from src.dao.user import UserDAO
from src.exception.user import UsernameOrPasswordWrongException
from src.model.config import ProjConfig
from src.model.dto.user import LoginDTO, RegisterDTO, UpdateUserInfoDTO
from src.model.entity.user import UserEntity
from src.model.vo.user import GetUserInfoVO
from src.util.jwtt import JWTUtil

VERIFY_CODE_CHARS = [
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    'a',
    'b',
    'c',
    'd',
    'e',
    'f',
    'g',
    'h',
    'i',
    'j',
    'k',
    'l',
    'm',
    'n',
    'o',
    'p',
    'q',
    'r',
    's',
    't',
    'u',
    'v',
    'w',
    'x',
    'y',
    'z',
    'A',
    'B',
    'C',
    'D',
    'E',
    'F',
    'G',
    'H',
    'I',
    'J',
    'K',
    'L',
    'M',
    'N',
    'O',
    'P',
    'Q',
    'R',
    'S',
    'T',
    'U',
    'V',
    'W',
    'X',
    'Y',
    'Z',
    '@',
    '#',
]


@Service
class UserService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.cache_key_prefix = 'register_verify_code'
        self.expires = Autowired(ProjConfig).redis.expires
        self.user_dao = Autowired @ UserDAO
        self.jwt_util = Autowired @ JWTUtil

    def generate_random_verify_code(self) -> str:
        return ''.join(random.sample(VERIFY_CODE_CHARS, 4))

    def set_cache_code(self, field: str, code: str):
        """set verify code in redis"""
        key = f'{self.cache_key_prefix}__{field}'
        self.redis.set(key, code)
        self.redis.expire(key, self.expires)

    async def verify_cache_code(self, key: str, value: str) -> bool:
        key = f'{self.cache_key_prefix}__{key}'
        v: Awaitable[str] | str = self.redis.get(key)
        return False if v is None else (await v) == value if isawaitable(v) else v == value

    def delete_cache_code(self, key: str):
        key = f'{self.cache_key_prefix}__{key}'
        self.redis.delete(key)

    async def register(self, dto: RegisterDTO) -> str:
        if await self.user_dao.name_exists(dto.username):
            raise HTTPException(402)
        user_entity = await self.user_dao.add(dto)
        token = self.jwt_util.create(user_entity.jwt_payload)
        return token

    async def login(self, dto: LoginDTO) -> str:
        curr_user = await self.user_dao.exists_and_get(dto)
        if curr_user:
            return self.jwt_util.create(curr_user.jwt_payload)
        raise UsernameOrPasswordWrongException(dto)

    async def update(self, id: str, dto: UpdateUserInfoDTO):
        user = await UserEntity.filter(id=id).first()
        if not user:
            raise HTTPException(status_code=400, detail="user doesn't exist")
        await user.update_by_update_user_info_dto(dto)

    async def get(self, id: str) -> GetUserInfoVO | None:
        user = await self.user_dao.get_by_id(id)
        return user.to_userinfo_vo() if user else None
