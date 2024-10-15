from enum import Enum
from typing import Literal, TypeAlias


ControllerType: TypeAlias = Literal["CBV", "FBV"]


class RouteType(Enum):
    CBV = "CBV"
    FBV = "FBV"
    ENDPOINT = "ENDPOINT"
