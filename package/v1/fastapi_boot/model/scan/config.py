from typing import Annotated, Union
from pydantic import BaseModel, Field


class Config(BaseModel):
    need_pure_api: Annotated[bool, Field(description='是否删除自带的api')] = False
    scan_timeout_second: Annotated[Union[int, float], Field(gt=0,
                                                            description='扫描超时时间，超时未找到报错')] = 10
