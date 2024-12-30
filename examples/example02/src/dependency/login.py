from fastapi import Header, HTTPException
from fastapi_boot.core import Autowired, Inject
from src.model.config import ProjConfig
from src.util.jwtt import JWTUtil

config = Inject @ ProjConfig
token_key = config.fastapi.jwt.token_key
jwt = Autowired @ JWTUtil


def use_user_login(token: str = Header(alias=config.fastapi.jwt.token_key, default='')) -> str:
    data = jwt.verify(token)
    if data is None:
        raise HTTPException(status_code=401, detail='unAuthorization')
    id: str = data.get('id', '')
    return id
